#!/usr/bin/env python3
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
import time
from datetime import datetime, timezone
from pathlib import Path
from json import JSONDecoder

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

SKILL_ID = "A-SK02"
SKILL_NAME = "sales-a-customer-bind"

CONFIRMED_VALUES = {True, "true", "confirmed", "approved", "accepted", "yes", "已确认", "已接收", "通过", "确认", "接受"}
PROHIBITED_FIELDS = {
    "P(win)", "amount_factor", "urgency_factor", "relationship_factor", "rating_score", "HI",
    "customer_rating", "current_stage", "sent_to_customer"
}


def load_json(path, raw):
    if raw:
        return json.loads(raw)
    if not path:
        return {}
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def now_iso():
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


def as_list(value):
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return value
    return [value]


def hash12(value):
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:12].upper()


def first_text(*values):
    for value in values:
        if value is None or value == "":
            continue
        if isinstance(value, dict):
            for key in ("phone", "mobile", "wechat", "value", "text"):
                if value.get(key):
                    return str(value[key])
            return json.dumps(value, ensure_ascii=False)
        if isinstance(value, list):
            flattened = [first_text(item) for item in value]
            flattened = [item for item in flattened if item]
            if flattened:
                return ",".join(flattened)
            continue
        return str(value)
    return None


def is_confirmed(value):
    if isinstance(value, str):
        value = value.strip().lower()
    return value in CONFIRMED_VALUES


def make_idempotency_key(data, parts):
    if data.get("idempotency_key"):
        return str(data["idempotency_key"])
    seed = "|".join(str(data.get(part, "")) for part in parts)
    return f"{SKILL_ID}-{hashlib.sha256(seed.encode('utf-8')).hexdigest()[:16]}"


def table_fields(config, table):
    table_cfg = config.get("tables", {}).get(table, {})
    return set(table_cfg.get("fields") or table_cfg.get("existing_fields") or [])


def table_ref(config, table):
    return config.get("tables", {}).get(table, {}).get("table_ref", table)


def transform_field_value(config, table, field, value):
    value_map = config.get("value_maps", {}).get(table, {}).get(field, {})
    try:
        if value in value_map:
            value = value_map[value]
    except TypeError:
        pass
    if isinstance(value, str) and value in value_map:
        value = value_map[value]
    field_type = config.get("field_types", {}).get(table, {}).get(field)
    if field_type == "datetime" and isinstance(value, str):
        raw = value.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(raw).strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            return value.replace("T", " ").split("+", 1)[0].split(".", 1)[0]
    if field_type == "text" and isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    return value


def clean(fields):
    return {k: v for k, v in fields.items() if v is not None}


def transform_writes(config, writes):
    transformed = []
    for write in writes:
        table = write["table"]
        attachment_cfg = config.get("attachment_tables", {}).get(table, {})
        if attachment_cfg.get("mode") == "ledger_json":
            original_fields = dict(write.get("fields", {}))
            ledger_block_id = original_fields.get("ledger_block_id") or write.get("idempotency_key", "ledger")
            fields = {
                "time": transform_field_value(config, table, "time", original_fields.get("created_at") or original_fields.get("event_date") or now_iso()),
                "customer_id": original_fields.get("customer_id"),
            }
            new_write = dict(write)
            new_write["fields"] = clean(fields)
            new_write["attachments"] = [{
                "field": attachment_cfg.get("ledger_field", "ledger"),
                "filename": f"{ledger_block_id}.json",
                "content": original_fields,
            }]
            transformed.append(new_write)
            continue
        aliases = config.get("field_aliases", {}).get(table, {})
        drop_fields = set(config.get("drop_fields", {}).get(table, []))
        fields = {}
        for source_field, value in write.get("fields", {}).items():
            if source_field in drop_fields:
                continue
            target_field = aliases.get(source_field, source_field)
            if not target_field:
                continue
            mapped_value = transform_field_value(config, table, source_field, value)
            mapped_value = transform_field_value(config, table, target_field, mapped_value)
            fields[target_field] = mapped_value
        new_write = dict(write)
        new_write["fields"] = fields
        transformed.append(new_write)
    return transformed


def check_fields(config, writes):
    writes = transform_writes(config, writes)
    blocked = []
    for write in writes:
        existing = table_fields(config, write["table"])
        if not existing:
            blocked.append(f"missing field snapshot for {write['table']}")
            continue
        missing = sorted(set(write["fields"]) - existing)
        if missing:
            blocked.append(f"{write['table']} missing fields: {', '.join(missing)}")
        missing_attachment_fields = sorted({item["field"] for item in write.get("attachments", [])} - existing)
        if missing_attachment_fields:
            blocked.append(f"{write['table']} missing attachment fields: {', '.join(missing_attachment_fields)}")
    return blocked


def check_prohibited(writes):
    blocked = []
    for write in writes:
        bad = sorted(set(write["fields"]) & PROHIBITED_FIELDS)
        if bad:
            blocked.append(f"{write['table']} contains prohibited fields: {', '.join(bad)}")
    return blocked


def command_for(config, write):
    direct = config.get("lark_cli_base")
    if direct:
        lark_cli = direct.get("lark_cli_ps1") or "lark-cli"
        base_token = direct.get("table_base_tokens", {}).get(write["table"]) or direct.get("base_token")
        if not base_token:
            return None
        identity = direct.get("as", "user")
        table_id = direct.get("table_ids", {}).get(write["table"]) or table_ref(config, write["table"])
        return f'powershell -NoProfile -ExecutionPolicy Bypass -File "{lark_cli}" base +record-upsert --base-token "{base_token}" --table-id "{table_id}" --json @<payload-file> --as {identity}'
    templates = config.get("lark_cli_commands") or config.get("commands") or {}
    key = f"{write['table']}.{write['operation']}"
    template = templates.get(key) or templates.get(write["operation"])
    if not template:
        return None
    payload = json.dumps(write["fields"], ensure_ascii=False, separators=(",", ":"))
    context = {
        "table": write["table"],
        "table_ref": table_ref(config, write["table"]),
        "operation": write["operation"],
        "payload_json": json.dumps(payload, ensure_ascii=False),
        "idempotency_key": write.get("idempotency_key", ""),
    }
    return template.format(**context)


def execute_commands(commands):
    results = []
    for command in commands:
        completed = subprocess.run(command, shell=True, text=True, capture_output=True, encoding="utf-8", errors="replace")
        results.append({
            "command": command,
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        })
        if completed.returncode != 0:
            break
    return results


def execute_direct_base_writes(config, writes):
    direct = config.get("lark_cli_base")
    if not direct:
        return None
    lark_cli = direct.get("lark_cli_ps1") or "lark-cli"
    default_base_token = direct.get("base_token")
    identity = direct.get("as", "user")
    temp_dir = Path(direct.get("payload_dir") or Path(tempfile.gettempdir()) / "a_line_skill_payloads")
    temp_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for write in writes:
        base_token = direct.get("table_base_tokens", {}).get(write["table"]) or default_base_token
        if not base_token:
            results.append({"command": "", "payload_file": "", "returncode": 1, "stdout": "", "stderr": f"missing base_token for {write['table']}"})
            break
        table_id = direct.get("table_ids", {}).get(write["table"]) or table_ref(config, write["table"])
        lookup_result = lookup_existing_record_id(config, direct, write, base_token, table_id, temp_dir)
        record_id = ""
        if lookup_result:
            results.append(lookup_result)
            if lookup_result["returncode"] != 0:
                break
            record_id = lookup_result.get("record_id", "")
        payload_file = temp_dir / f"{write['idempotency_key']}.json"
        payload_file.write_text(json.dumps(write["fields"], ensure_ascii=False), encoding="utf-8")
        argv = [
            "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", lark_cli,
            "base", "+record-upsert",
            "--base-token", base_token,
            "--table-id", table_id,
        ]
        if record_id:
            argv.extend(["--record-id", record_id])
        argv.extend(["--json", f"@{payload_file.name}", "--as", identity])
        completed = subprocess.run(argv, text=True, capture_output=True, cwd=str(temp_dir), encoding="utf-8", errors="replace")
        results.append({
            "command": " ".join(argv),
            "payload_file": str(payload_file),
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
        })
        if completed.returncode != 0:
            break
        record_id = extract_record_id(completed.stdout) or record_id
        if write.get("attachments") and not record_id:
            results.append({"command": "", "payload_file": "", "returncode": 1, "stdout": completed.stdout, "stderr": "record-upsert did not return a record_id for attachment upload"})
            break
        for attachment in write.get("attachments", []):
            safe_name = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in attachment["filename"])
            attachment_file = temp_dir / safe_name
            attachment_file.write_text(json.dumps(attachment["content"], ensure_ascii=False, indent=2), encoding="utf-8")
            upload_argv = [
                "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", lark_cli,
                "base", "+record-upload-attachment",
                "--base-token", base_token,
                "--table-id", table_id,
                "--record-id", record_id,
                "--field-id", attachment["field"],
                "--file", attachment_file.name,
                "--as", identity,
            ]
            upload_completed = subprocess.run(upload_argv, text=True, capture_output=True, cwd=str(temp_dir), encoding="utf-8", errors="replace")
            results.append({
                "command": " ".join(upload_argv),
                "payload_file": str(attachment_file),
                "returncode": upload_completed.returncode,
                "stdout": upload_completed.stdout,
                "stderr": upload_completed.stderr,
            })
            if upload_completed.returncode != 0:
                break
        if results[-1]["returncode"] != 0:
            break
    return results


def upsert_lookup_key(write):
    fields = write.get("fields", {})
    if write.get("table") == "A03_all_customer_files" and fields.get("customer_id"):
        return "customer_id", fields["customer_id"]
    if write.get("table") == "A06_a_line_index" and fields.get("source_id"):
        return "source_id", fields["source_id"]
    return "", ""


def lookup_existing_record_id(config, direct, write, base_token, table_id, temp_dir):
    key_field, key_value = upsert_lookup_key(write)
    if not key_field:
        return None
    lark_cli = direct.get("lark_cli_ps1") or "lark-cli"
    identity = direct.get("as", "user")
    safe_key = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in str(key_value))
    filter_file = temp_dir / f"{write['idempotency_key']}-{safe_key}-lookup.json"
    filter_file.write_text(json.dumps({"logic": "and", "conditions": [[key_field, "==", key_value]]}, ensure_ascii=False), encoding="utf-8")
    argv = [
        "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", lark_cli,
        "base", "+record-list",
        "--base-token", base_token,
        "--table-id", table_id,
        "--filter-json", f"@{filter_file.name}",
        "--limit", "1",
        "--format", "json",
        "--as", identity,
        "--field-id", key_field,
    ]
    completed = subprocess.run(argv, text=True, capture_output=True, cwd=str(temp_dir), encoding="utf-8", errors="replace")
    return {
        "command": " ".join(argv),
        "payload_file": str(filter_file),
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "record_id": extract_record_id(completed.stdout) if completed.returncode == 0 else "",
        "operation": "lookup_existing_record",
    }


def extract_record_id(stdout):
    try:
        payload = json.loads(stdout)
    except Exception:
        return ""
    candidates = [
        payload.get("record_id"),
        payload.get("id"),
        payload.get("data", {}).get("record_id"),
        payload.get("data", {}).get("id"),
        payload.get("data", {}).get("record", {}).get("record_id"),
        payload.get("data", {}).get("record", {}).get("id"),
    ]
    records = payload.get("data", {}).get("records")
    if isinstance(records, list) and records:
        candidates.extend([records[0].get("record_id"), records[0].get("id")])
    record_id_list = payload.get("data", {}).get("record", {}).get("record_id_list") or payload.get("data", {}).get("record_id_list")
    if isinstance(record_id_list, list) and record_id_list:
        candidates.append(record_id_list[0])
    for candidate in candidates:
        if isinstance(candidate, str) and candidate:
            return candidate
    return ""


def first_json(stdout):
    start = stdout.find("{")
    if start < 0:
        return {}
    try:
        payload, _ = JSONDecoder().raw_decode(stdout[start:])
        return payload if isinstance(payload, dict) else {}
    except Exception:
        return {}


def container_create_config(config):
    return config.get("customer_container_create") or config.get("customer_table_model", {}).get("customer_container_create") or {}


def container_auto_enabled(config):
    cfg = container_create_config(config)
    return cfg.get("enabled", True) is not False


def customer_container_title(config, customer_id):
    cfg = container_create_config(config)
    return (cfg.get("title_template") or "{customer_id}/").format(customer_id=customer_id)


def has_container_refs(data, config):
    ref_fields = config.get("customer_table_model", {}).get("per_customer_ref_fields", [])
    return any(data.get(field) for field in ref_fields) or bool(
        data.get("individual_customer_base_token") and data.get("individual_customer_table_id")
    )


def should_auto_create_container(data, config, refs):
    return bool(
        container_auto_enabled(config)
        and refs.get("missing_customer_container_refs")
        and not has_container_refs(data, config)
    )


def build_container_refs(config, base_token, table_id, node_token, node_url):
    cfg = container_create_config(config)
    if not node_url:
        domain = cfg.get("wiki_domain") or "https://lcnpt5xjzbya.feishu.cn"
        node_url = f"{domain.rstrip('/')}/wiki/{node_token}" if node_token else ""
    table_url = f"{node_url}?table={table_id}" if node_url and table_id and "table=" not in node_url else node_url
    return {
        "individual_customer_table_url": table_url,
        "individual_customer_base_token": base_token,
        "individual_customer_table_id": table_id,
        "ledger_table_ref": f"base:{base_token};table:{table_id};field:ledger",
        "evidence_ref_table_ref": f"base:{base_token};table:{table_id};field:evidence_ref",
        "artifacts_ref_table_ref": f"base:{base_token};table:{table_id};field:artifacts_ref",
        "handoff_ref_table_ref": f"base:{base_token};table:{table_id};field:handoff_ref",
        "latest_snapshot_table_ref": f"base:{base_token};table:{table_id};field:latest_snapshot",
    }


def customer_container_field_specs():
    return [
        {"type": "text", "name": "time", "description": "Unique write timestamp.", "style": {"type": "plain"}},
        {"type": "text", "name": "customer_id", "description": "A-line customer_id.", "style": {"type": "plain"}},
        {"type": "attachment", "name": "ledger", "description": "Immutable ledger JSON attachments."},
        {"type": "attachment", "name": "evidence_ref", "description": "Evidence reference attachments."},
        {"type": "attachment", "name": "artifacts_ref", "description": "Generated artifact attachments."},
        {"type": "attachment", "name": "handoff_ref", "description": "Handoff reference attachments."},
        {"type": "attachment", "name": "latest_snapshot", "description": "Latest snapshot JSON attachments."},
    ]


def run_lark(config, temp_dir, args):
    direct = config.get("lark_cli_base", {})
    lark_cli = direct.get("lark_cli_ps1") or "lark-cli"
    argv = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", lark_cli] + args
    completed = subprocess.run(argv, cwd=str(temp_dir), text=True, capture_output=True, encoding="utf-8", errors="replace")
    return {
        "command": " ".join(argv),
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }


def run_lark_retrying_copy(config, temp_dir, args):
    attempts = int(container_create_config(config).get("copy_ready_retries", 8))
    delay = float(container_create_config(config).get("copy_ready_delay_seconds", 2))
    result = run_lark(config, temp_dir, args)
    for _ in range(max(0, attempts - 1)):
        if result["returncode"] == 0:
            break
        marker = f"{result.get('stdout','')}\n{result.get('stderr','')}"
        if "base is copying" not in marker and "800004046" not in marker:
            break
        time.sleep(delay)
        result = run_lark(config, temp_dir, args)
    return result


def payload_arg(temp_dir, name, payload):
    safe_name = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in name)
    path = temp_dir / safe_name
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return f"@{path.name}", str(path)


def fields_by_name(fields_payload):
    fields = first_json(fields_payload).get("data", {}).get("fields", [])
    return {field.get("name"): field for field in fields if isinstance(field, dict)}


def record_rows_from_list(stdout):
    data = first_json(stdout).get("data", {})
    return data.get("record_id_list") or [], data.get("data") or []


def is_blank_record_row(row):
    return all(value in (None, "", [], {}) for value in row)


def cleanup_blank_records(config, temp_dir, base_token, table_id, results):
    cfg = container_create_config(config)
    if cfg.get("cleanup_blank_records", True) is False:
        return []
    identity = config.get("lark_cli_base", {}).get("as", "user")
    field_names = [spec["name"] for spec in customer_container_field_specs()]
    args = [
        "base", "+record-list",
        "--base-token", base_token,
        "--table-id", table_id,
        "--limit", "200",
        "--format", "json",
        "--as", identity,
    ]
    for field_name in field_names:
        args.extend(["--field-id", field_name])
    list_result = run_lark(config, temp_dir, args)
    results.append(list_result)
    if list_result["returncode"] != 0:
        return []
    record_ids, rows = record_rows_from_list(list_result["stdout"])
    blank_ids = [record_id for record_id, row in zip(record_ids, rows) if is_blank_record_row(row)]
    if not blank_ids:
        return []
    delete_args = [
        "base", "+record-delete",
        "--base-token", base_token,
        "--table-id", table_id,
        "--yes",
        "--format", "json",
        "--as", identity,
    ]
    for record_id in blank_ids:
        delete_args.extend(["--record-id", record_id])
    delete_result = run_lark(config, temp_dir, delete_args)
    delete_result["blank_record_ids"] = blank_ids
    results.append(delete_result)
    return blank_ids if delete_result["returncode"] == 0 else []


def ensure_customer_container(config, customer_id):
    cfg = container_create_config(config)
    direct = config.get("lark_cli_base", {})
    identity = direct.get("as", "user")
    space_id = cfg.get("space_id")
    parent_node_token = cfg.get("parent_node_token")
    if not space_id or not parent_node_token:
        return {"ok": False, "refs": {}, "results": [], "error": "missing customer_container_create.space_id or parent_node_token"}

    temp_dir = Path(direct.get("payload_dir") or Path(tempfile.gettempdir()) / "a_line_skill_payloads")
    temp_dir.mkdir(parents=True, exist_ok=True)
    title = customer_container_title(config, customer_id)
    results = []

    list_result = run_lark(config, temp_dir, ["wiki", "+node-list", "--space-id", space_id, "--parent-node-token", parent_node_token, "--format", "json", "--as", identity])
    results.append(list_result)
    if list_result["returncode"] != 0:
        return {"ok": False, "refs": {}, "results": results, "error": "failed to list customer ledger folder"}

    node = None
    for item in first_json(list_result["stdout"]).get("data", {}).get("nodes", []):
        if item.get("title") == title:
            node = item
            break
    created_node = False
    copied_from_template = False
    if node:
        if node.get("obj_type") != "bitable":
            return {"ok": False, "refs": {}, "results": results, "error": f"existing node {title} is not bitable"}
    else:
        template_node_token = cfg.get("template_node_token")
        if template_node_token:
            create_result = run_lark(config, temp_dir, [
                "wiki", "+node-copy",
                "--space-id", space_id,
                "--node-token", template_node_token,
                "--target-parent-node-token", parent_node_token,
                "--title", title,
                "--yes",
                "--format", "json",
                "--as", identity,
            ])
            copied_from_template = True
        else:
            create_result = run_lark(config, temp_dir, [
                "wiki", "+node-create",
                "--space-id", space_id,
                "--parent-node-token", parent_node_token,
                "--obj-type", "bitable",
                "--title", title,
                "--format", "json",
                "--as", identity,
            ])
        results.append(create_result)
        if create_result["returncode"] != 0:
            return {"ok": False, "refs": {}, "results": results, "error": "failed to create customer ledger node"}
        node = first_json(create_result["stdout"]).get("data", {})
        created_node = True

    base_token = node.get("obj_token")
    node_token = node.get("node_token")
    node_url = node.get("url")
    if not base_token:
        return {"ok": False, "refs": {}, "results": results, "error": "customer ledger node has no base token"}

    table_list = run_lark_retrying_copy(config, temp_dir, ["base", "+table-list", "--base-token", base_token, "--format", "json", "--as", identity])
    results.append(table_list)
    if table_list["returncode"] != 0:
        return {"ok": False, "refs": {}, "results": results, "error": "failed to list customer ledger tables"}
    tables = first_json(table_list["stdout"]).get("data", {}).get("tables", [])
    if not tables:
        return {"ok": False, "refs": {}, "results": results, "error": "new customer ledger base has no table"}
    table_id = tables[0].get("id")
    if tables[0].get("name") != (cfg.get("table_name") or "ledger"):
        results.append(run_lark(config, temp_dir, ["base", "+table-update", "--base-token", base_token, "--table-id", table_id, "--name", cfg.get("table_name") or "ledger", "--format", "json", "--as", identity]))
        if results[-1]["returncode"] != 0:
            return {"ok": False, "refs": {}, "results": results, "error": "failed to rename customer ledger table"}

    field_list = run_lark_retrying_copy(config, temp_dir, ["base", "+field-list", "--base-token", base_token, "--table-id", table_id, "--format", "json", "--as", identity])
    results.append(field_list)
    if field_list["returncode"] != 0:
        return {"ok": False, "refs": {}, "results": results, "error": "failed to list customer ledger fields"}
    fields = fields_by_name(field_list["stdout"])

    if created_node and "time" not in fields and "Text" in fields:
        arg, path = payload_arg(temp_dir, "field_time.json", customer_container_field_specs()[0])
        result = run_lark(config, temp_dir, ["base", "+field-update", "--base-token", base_token, "--table-id", table_id, "--field-id", fields["Text"]["id"], "--json", arg, "--yes", "--format", "json", "--as", identity])
        result["payload_file"] = path
        results.append(result)
    if created_node and "ledger" not in fields and "Attachment" in fields:
        arg, path = payload_arg(temp_dir, "field_ledger.json", customer_container_field_specs()[2])
        result = run_lark(config, temp_dir, ["base", "+field-update", "--base-token", base_token, "--table-id", table_id, "--field-id", fields["Attachment"]["id"], "--json", arg, "--yes", "--format", "json", "--as", identity])
        result["payload_file"] = path
        results.append(result)

    field_list = run_lark_retrying_copy(config, temp_dir, ["base", "+field-list", "--base-token", base_token, "--table-id", table_id, "--format", "json", "--as", identity])
    results.append(field_list)
    fields = fields_by_name(field_list["stdout"])
    for spec in customer_container_field_specs():
        if spec["name"] in fields:
            continue
        arg, path = payload_arg(temp_dir, f"field_{spec['name']}.json", spec)
        result = run_lark(config, temp_dir, ["base", "+field-create", "--base-token", base_token, "--table-id", table_id, "--json", arg, "--format", "json", "--as", identity])
        result["payload_file"] = path
        results.append(result)
        if result["returncode"] != 0:
            return {"ok": False, "refs": {}, "results": results, "error": f"failed to create customer ledger field {spec['name']}"}

    if created_node:
        field_list = run_lark_retrying_copy(config, temp_dir, ["base", "+field-list", "--base-token", base_token, "--table-id", table_id, "--format", "json", "--as", identity])
        results.append(field_list)
        fields = fields_by_name(field_list["stdout"])
        for default_name in ("Single option", "Date"):
            if default_name in fields:
                results.append(run_lark(config, temp_dir, ["base", "+field-delete", "--base-token", base_token, "--table-id", table_id, "--field-id", fields[default_name]["id"], "--yes", "--format", "json", "--as", identity]))
                if results[-1]["returncode"] != 0:
                    return {"ok": False, "refs": {}, "results": results, "error": f"failed to delete default field {default_name}"}

    blank_record_ids = cleanup_blank_records(config, temp_dir, base_token, table_id, results)
    return {
        "ok": True,
        "refs": build_container_refs(config, base_token, table_id, node_token, node_url),
        "results": results,
        "error": "",
        "node_token": node_token,
        "base_token": base_token,
        "table_id": table_id,
        "created_node": created_node,
        "copied_from_template": copied_from_template,
        "blank_records_deleted": len(blank_record_ids),
        "title": title,
    }


def plan(input_data, config):
    blocked = []
    lead_id = input_data.get("lead_id")
    customer_name = input_data.get("customer_name")
    sales_id = input_data.get("sales_id")
    if not lead_id:
        blocked.append("missing required input: lead_id")
    if not customer_name:
        blocked.append("missing required input: customer_name")
    if not sales_id:
        blocked.append("missing required input: sales_id")

    accept_value = input_data.get("sales_accept_status", input_data.get("receive_status", input_data.get("receive_confirmed")))
    if not is_confirmed(accept_value):
        blocked.append("lead is not human-confirmed as accepted")

    duplicate_candidates = as_list(input_data.get("duplicate_candidate_ids"))
    chosen_customer_id = input_data.get("chosen_customer_id") or input_data.get("customer_id")
    if duplicate_candidates and not (chosen_customer_id and is_confirmed(input_data.get("duplicate_confirm_status"))):
        return "needs_confirm", make_idempotency_key(input_data, ["lead_id", "customer_name", "sales_id"]), {}, [], [
            "duplicate candidates exist; confirm chosen_customer_id before binding"
        ], {}

    customer_id = chosen_customer_id or f"CUST-{hashlib.sha256((customer_name or lead_id or '').encode('utf-8')).hexdigest()[:12].upper()}"
    idempotency_key = make_idempotency_key(input_data, ["lead_id", "customer_id", "sales_id"])
    existing_keys = set(config.get("existing_idempotency_keys", []))
    if idempotency_key in existing_keys:
        blocked.append("duplicate idempotency_key; refusing duplicate customer bind")

    created_at = now_iso()
    source_id = first_text(input_data.get("source_id"), lead_id)
    validated = {
        "lead_id": lead_id,
        "customer_id": customer_id,
        "customer_name": customer_name,
        "sales_id": sales_id,
    }
    writes = [
        {
            "table": "A03_all_customer_files",
            "operation": "upsert",
            "idempotency_key": idempotency_key,
            "fields": {
                "customer_id": customer_id,
                "customer_name": customer_name,
                "customer_status": input_data.get("customer_status", "active"),
                "source_id": source_id,
                "current_sales_id": sales_id,
                "industry": input_data.get("industry"),
                "company_size": input_data.get("company_size"),
                "cash_flow": input_data.get("cash_flow_signal"),
                "consumption_ability": input_data.get("consumption_ability"),
                "decision_power": input_data.get("decision_power"),
                "budget_signal": input_data.get("budget_range"),
                "individual_customer_table_url": input_data.get("individual_customer_table_url"),
                "ledger_table_ref": input_data.get("ledger_table_ref"),
                "evidence_ref_table_ref": input_data.get("evidence_ref_table_ref"),
                "artifacts_ref_table_ref": input_data.get("artifacts_ref_table_ref"),
                "handoff_ref_table_ref": input_data.get("handoff_ref_table_ref"),
                "latest_snapshot_table_ref": input_data.get("latest_snapshot_table_ref"),
                "created_at": input_data.get("created_at", created_at),
                "updated_at": created_at,
            },
        },
        {
            "table": "A06_a_line_index",
            "operation": "upsert",
            "idempotency_key": idempotency_key,
            "fields": {
                "source_map_id": input_data.get("source_map_id") or f"SMAP-{hash12(source_id)}",
                "source_id": source_id,
                "source_type": input_data.get("source_type") or input_data.get("source_channel"),
                "source_department": input_data.get("source_department"),
                "raw_customer_name": input_data.get("raw_customer_name") or customer_name,
                "raw_phone": first_text(input_data.get("raw_phone"), input_data.get("source_contact"), input_data.get("contact_info")),
                "candidate_customer_ids": duplicate_candidates or None,
                "linked_customer_id": customer_id,
                "accepted_sales_id": sales_id,
                "mapping_status": input_data.get("mapping_status", "mapped"),
                "created_at": input_data.get("created_at", created_at),
                "updated_at": created_at,
                "remark": input_data.get("remark"),
            },
        },
    ]
    for write in writes:
        write["fields"] = {k: v for k, v in write["fields"].items() if v is not None}
    blocked.extend(check_prohibited(writes))
    blocked.extend(check_fields(config, writes))
    status = "rejected" if blocked else "pass"
    ref_fields = config.get("customer_table_model", {}).get("per_customer_ref_fields", [])
    missing_refs = [field for field in ref_fields if not input_data.get(field)]
    return status, idempotency_key, validated, writes, blocked, {
        "customer_id": customer_id,
        "individual_customer_container_ready": not missing_refs,
        "missing_customer_container_refs": missing_refs,
        "auto_customer_container_planned": should_auto_create_container(input_data, config, {"missing_customer_container_refs": missing_refs}),
        "customer_container_plan": {
            "parent_node_token": container_create_config(config).get("parent_node_token"),
            "title": customer_container_title(config, customer_id) if missing_refs else "",
        } if should_auto_create_container(input_data, config, {"missing_customer_container_refs": missing_refs}) else {},
    }


def main():
    parser = argparse.ArgumentParser(description="A-SK02 customer_id bind/create validator and executor")
    parser.add_argument("--input")
    parser.add_argument("--config")
    parser.add_argument("--input-json")
    parser.add_argument("--config-json")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if args.dry_run and args.execute:
        print(json.dumps({"status": "error", "skill_id": SKILL_ID, "blocked_reasons": ["choose only one of --dry-run or --execute"]}, ensure_ascii=False))
        sys.exit(1)

    try:
        input_data = load_json(args.input, args.input_json)
        config = load_json(args.config, args.config_json)
        status, key, validated, writes, blocked, refs = plan(input_data, config)
        if args.execute and status == "pass" and should_auto_create_container(input_data, config, refs):
            container = ensure_customer_container(config, validated["customer_id"])
            refs["customer_container_creation"] = container
            if not container.get("ok"):
                status = "error"
                blocked.append(container.get("error") or "failed to create customer container")
            else:
                enriched_input = dict(input_data)
                enriched_input.update(container["refs"])
                status, key, validated, writes, blocked, refs_after_container = plan(enriched_input, config)
                refs_after_container["customer_container_creation"] = container
                refs = refs_after_container
        writes = transform_writes(config, writes)
        commands = [command_for(config, write) for write in writes] if status == "pass" else []
        commands = [command for command in commands if command]
        result_refs = refs
        if args.execute and status == "pass":
            direct_results = execute_direct_base_writes(config, writes)
            if direct_results is not None:
                result_refs["execution_results"] = direct_results
                status = "executed" if all(item["returncode"] == 0 for item in direct_results) else "error"
            elif len(commands) != len(writes):
                status = "error"
                blocked.append("missing lark-cli command template for at least one planned write")
            else:
                results = execute_commands(commands)
                result_refs["execution_results"] = results
                status = "executed" if all(item["returncode"] == 0 for item in results) else "error"
        output = {
            "status": status,
            "skill_id": SKILL_ID,
            "idempotency_key": key,
            "validated_input": validated,
            "planned_writes": writes,
            "blocked_reasons": blocked,
            "lark_cli_commands": commands,
            "result_refs": result_refs,
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
        sys.exit(0 if status in {"pass", "executed", "needs_confirm"} else 1)
    except Exception as exc:
        print(json.dumps({
            "status": "error",
            "skill_id": SKILL_ID,
            "idempotency_key": "",
            "validated_input": {},
            "planned_writes": [],
            "blocked_reasons": [str(exc)],
            "lark_cli_commands": [],
            "result_refs": {},
        }, ensure_ascii=False, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
