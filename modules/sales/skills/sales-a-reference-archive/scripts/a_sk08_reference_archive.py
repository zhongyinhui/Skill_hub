#!/usr/bin/env python3
import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import parse_qs, urlparse

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

SKILL_ID = "A-SK08"
PROHIBITED = {"sent_to_customer", "handoff_ref", "handoff_refs", "current_stage", "customer_rating"}


def load_json(path, raw):
    if raw:
        return json.loads(raw)
    return json.loads(Path(path).read_text(encoding="utf-8-sig")) if path else {}


def now_iso():
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


def normalize_record_time(value):
    if not value:
        return ""
    if not isinstance(value, str):
        value = str(value)
    raw = value.strip().replace("Z", "+00:00")
    if not raw:
        return ""
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", raw):
        return f"{raw} 00:00:00"
    try:
        return datetime.fromisoformat(raw).strftime("%Y-%m-%d %H:%M:%S")
    except ValueError:
        return raw.replace("T", " ").split("+", 1)[0].split(".", 1)[0]


def ledger_record_time(data):
    for key in ("ledger_record_time", "record_time", "event_time", "created_at", "event_date", "work_date"):
        normalized = normalize_record_time(data.get(key))
        if normalized:
            return normalized
    for key in ("ledger_block_id", "source_record_id", "source_id"):
        value = data.get(key)
        if not isinstance(value, str):
            continue
        match = re.search(r"(20\d{2})(\d{2})(\d{2})", value)
        if match:
            return f"{match.group(1)}-{match.group(2)}-{match.group(3)} 00:00:00"
    return now_iso()


def as_list(value):
    if value is None or value == "":
        return []
    return value if isinstance(value, list) else [value]


def table_fields(config, table):
    return set(config.get("tables", {}).get(table, {}).get("fields") or config.get("tables", {}).get(table, {}).get("existing_fields") or [])


def table_ref(config, table):
    return config.get("tables", {}).get(table, {}).get("table_ref", table)


def token_from_base_url(value):
    if not isinstance(value, str):
        return ""
    parsed = urlparse(value)
    parts = [part for part in parsed.path.split("/") if part]
    if "base" in parts:
        idx = parts.index("base")
        if idx + 1 < len(parts):
            return parts[idx + 1]
    return ""


def table_id_from_url(value):
    if not isinstance(value, str):
        return ""
    parsed = urlparse(value)
    table_id = (parse_qs(parsed.query).get("table") or [""])[0]
    return table_id if table_id.startswith("tbl") else ""


def individual_container_target(data, config):
    target = data.get("individual_customer_table") or data.get("customer_individual_table") or {}
    if isinstance(target, str):
        target = {"url": target}
    refs = [
        target.get("url"),
        data.get("evidence_ref_table_ref"),
        data.get("artifacts_ref_table_ref"),
        data.get("handoff_ref_table_ref"),
        data.get("individual_customer_table_url"),
        data.get("customer_table_url"),
    ]
    ref = next((item for item in refs if item), "")
    base_token = (
        target.get("base_token")
        or data.get("individual_customer_base_token")
        or data.get("reference_base_token")
        or token_from_base_url(ref)
    )
    table_id = (
        target.get("table_id")
        or data.get("individual_customer_table_id")
        or data.get("reference_table_id")
        or table_id_from_url(ref)
    )
    sample_url = config.get("customer_table_model", {}).get("sample_individual_customer_table_url", "")
    is_sample = bool(ref and "QKeTwIrZEiqbaBkYdh5cRLpPndh" in ref) or bool(sample_url and ref == sample_url)
    return {"base_token": base_token, "table_id": table_id, "source_ref": ref, "is_sample": is_sample}


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


def transform_writes(config, writes):
    transformed = []
    for write in writes:
        table = write["table"]
        attachment_cfg = config.get("attachment_tables", {}).get(table, {})
        if attachment_cfg.get("mode") == "ledger_json":
            original_fields = dict(write.get("fields", {}))
            ledger_block_id = original_fields.get("ledger_block_id") or write.get("idempotency_key", "ledger")
            customer_id = original_fields.get("customer_id")
            evidence_refs = as_list(original_fields.get("evidence_refs"))
            raw_artifact_refs = as_list(original_fields.get("artifact_refs"))
            handoff_refs = [item[len("handoff:"):] for item in raw_artifact_refs if isinstance(item, str) and item.startswith("handoff:")]
            artifact_refs = [item for item in raw_artifact_refs if not (isinstance(item, str) and item.startswith("handoff:"))]
            fields = {
                "time": transform_field_value(config, table, "time", original_fields.get("ledger_record_time") or original_fields.get("record_time") or original_fields.get("event_date") or original_fields.get("created_at") or now_iso()),
                "customer_id": customer_id,
            }
            attachments = []
            if evidence_refs:
                attachments.append({
                    "field": attachment_cfg.get("evidence_field", "evidence_ref"),
                    "filename": f"EVIDENCE-{write.get('idempotency_key', ledger_block_id)}.json",
                    "content": {"customer_id": customer_id, "ledger_block_id": original_fields.get("ledger_block_id"), "evidence_refs": evidence_refs},
                })
            if artifact_refs:
                attachments.append({
                    "field": attachment_cfg.get("artifacts_field", "artifacts_ref"),
                    "filename": f"ARTIFACTS-{write.get('idempotency_key', ledger_block_id)}.json",
                    "content": {"customer_id": customer_id, "ledger_block_id": original_fields.get("ledger_block_id"), "artifact_refs": artifact_refs},
                })
            if handoff_refs:
                attachments.append({
                    "field": attachment_cfg.get("handoff_field", "handoff_ref"),
                    "filename": f"HANDOFF-{write.get('idempotency_key', ledger_block_id)}.json",
                    "content": {"customer_id": customer_id, "ledger_block_id": original_fields.get("ledger_block_id"), "handoff_refs": handoff_refs},
                })
            new_write = dict(write)
            new_write["fields"] = clean(fields)
            new_write["attachments"] = attachments
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


def clean(fields):
    return {k: v for k, v in fields.items() if v is not None}


def command_for(config, write):
    direct = config.get("lark_cli_base")
    if direct:
        lark_cli = direct.get("lark_cli_ps1") or "lark-cli"
        base_token = write.get("base_token") or direct.get("table_base_tokens", {}).get(write["table"]) or direct.get("base_token")
        if not base_token:
            return None
        identity = direct.get("as", "user")
        table_id = write.get("table_id") or direct.get("table_ids", {}).get(write["table"]) or table_ref(config, write["table"])
        return f'powershell -NoProfile -ExecutionPolicy Bypass -File "{lark_cli}" base +record-upsert --base-token "{base_token}" --table-id "{table_id}" --json @<payload-file> --as {identity}'
    templates = config.get("lark_cli_commands") or config.get("commands") or {}
    template = templates.get(f"{write['table']}.{write['operation']}") or templates.get(write["operation"])
    if not template:
        return None
    payload = json.dumps(write["fields"], ensure_ascii=False, separators=(",", ":"))
    return template.format(table=write["table"], table_ref=table_ref(config, write["table"]), payload_json=json.dumps(payload, ensure_ascii=False), idempotency_key=write["idempotency_key"])


def validate(config, writes):
    writes = transform_writes(config, writes)
    blocked = []
    for write in writes:
        bad = sorted(set(write["fields"]) & PROHIBITED)
        if bad:
            blocked.append(f"{write['table']} contains prohibited fields: {', '.join(bad)}")
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


def run(commands):
    results = []
    for command in commands:
        completed = subprocess.run(command, shell=True, text=True, capture_output=True, encoding="utf-8", errors="replace")
        results.append({"command": command, "returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr})
        if completed.returncode != 0:
            break
    return results


def run_direct_base_writes(config, writes):
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
        base_token = write.get("base_token") or direct.get("table_base_tokens", {}).get(write["table"]) or default_base_token
        if not base_token:
            results.append({"command": "", "payload_file": "", "returncode": 1, "stdout": "", "stderr": f"missing base_token for {write['table']}"})
            break
        table_id = write.get("table_id") or direct.get("table_ids", {}).get(write["table"]) or table_ref(config, write["table"])
        record_id = write.get("record_id") or ""
        existing_fields = {}
        if not record_id:
            lookup_result = lookup_existing_record_id(config, direct, write, base_token, table_id, temp_dir)
        else:
            lookup_result = None
        if lookup_result:
            results.append(lookup_result)
            if lookup_result["returncode"] != 0:
                break
            record_id = lookup_result.get("record_id", "")
            existing_fields = lookup_result.get("fields", {})
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
        results.append({"command": " ".join(argv), "payload_file": str(payload_file), "returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr})
        if completed.returncode != 0:
            break
        record_id = extract_record_id(completed.stdout) or record_id
        if write.get("attachments") and not record_id:
            results.append({"command": "", "payload_file": "", "returncode": 1, "stdout": completed.stdout, "stderr": "record-upsert did not return a record_id for attachment upload"})
            break
        for attachment in write.get("attachments", []):
            if attachment_field_has_value(existing_fields, attachment["field"]):
                results.append({"command": "", "payload_file": "", "returncode": 0, "stdout": "", "stderr": "", "operation": "skip_existing_attachment", "field": attachment["field"], "record_id": record_id})
                continue
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
            results.append({"command": " ".join(upload_argv), "payload_file": str(attachment_file), "returncode": upload_completed.returncode, "stdout": upload_completed.stdout, "stderr": upload_completed.stderr})
            if upload_completed.returncode != 0:
                break
        if results[-1]["returncode"] != 0:
            break
    return results


def upsert_lookup_key(write):
    fields = write.get("fields", {})
    if write.get("table") == "A99_individual_customer_container" and fields.get("customer_id") and fields.get("time"):
        return [["customer_id", "==", fields["customer_id"]], ["time", "==", fields["time"]]]
    if write.get("table") == "A03_all_customer_files" and fields.get("customer_id"):
        return [["customer_id", "==", fields["customer_id"]]]
    return []


def lookup_existing_record_id(config, direct, write, base_token, table_id, temp_dir):
    conditions = upsert_lookup_key(write)
    if not conditions:
        return None
    lark_cli = direct.get("lark_cli_ps1") or "lark-cli"
    identity = direct.get("as", "user")
    safe_key = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in str(write.get("idempotency_key", "lookup")))
    filter_file = temp_dir / f"{write['idempotency_key']}-{safe_key}-lookup.json"
    filter_file.write_text(json.dumps({"logic": "and", "conditions": conditions}, ensure_ascii=False), encoding="utf-8")
    field_ids = []
    for field, _, _ in conditions:
        if field not in field_ids:
            field_ids.append(field)
    for attachment in write.get("attachments", []):
        field = attachment.get("field")
        if field and field not in field_ids:
            field_ids.append(field)
    argv = [
        "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", lark_cli,
        "base", "+record-list",
        "--base-token", base_token,
        "--table-id", table_id,
        "--filter-json", f"@{filter_file.name}",
        "--limit", "1",
        "--format", "json",
        "--as", identity,
    ]
    for field_id in field_ids:
        argv.extend(["--field-id", field_id])
    completed = subprocess.run(argv, text=True, capture_output=True, cwd=str(temp_dir), encoding="utf-8", errors="replace")
    return {
        "command": " ".join(argv),
        "payload_file": str(filter_file),
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "record_id": extract_record_id(completed.stdout) if completed.returncode == 0 else "",
        "fields": extract_record_fields(completed.stdout) if completed.returncode == 0 else {},
        "operation": "lookup_existing_record",
    }


def extract_record_fields(stdout):
    try:
        payload = json.loads(stdout)
    except Exception:
        return {}
    table_data = payload.get("data", {})
    rows = table_data.get("data")
    names = table_data.get("fields")
    if isinstance(rows, list) and rows and isinstance(names, list):
        return dict(zip(names, rows[0]))
    records = payload.get("data", {}).get("records")
    if isinstance(records, list) and records:
        fields = records[0].get("fields")
        return fields if isinstance(fields, dict) else {}
    for candidate in (payload.get("fields"), payload.get("data", {}).get("fields"), payload.get("data", {}).get("record", {}).get("fields")):
        if isinstance(candidate, dict):
            return candidate
    return {}


def attachment_field_has_value(fields, field):
    value = fields.get(field)
    return value not in (None, "", [], {})


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


def plan(data, config):
    blocked = []
    customer_id = data.get("customer_id")
    ledger_block_id = data.get("ledger_block_id")
    evidence = as_list(data.get("evidence_ids"))
    artifacts = as_list(data.get("artifact_ids"))
    handoffs = [f"handoff:{item}" for item in as_list(data.get("handoff_ids"))]
    artifact_refs = artifacts + handoffs
    if not customer_id:
        blocked.append("missing required input: customer_id")
    if not (ledger_block_id or evidence or artifact_refs):
        blocked.append("no ledger_block_id, evidence_ids, artifact_ids, or handoff_ids provided")
    if data.get("sent_to_customer") and not data.get("sent_confirm_status"):
        blocked.append("input claims sent_to_customer without sent_confirm_status; field will not be written")

    created_at = now_iso()
    record_time = ledger_record_time(data)
    seed = f"{customer_id}|{ledger_block_id}|{json.dumps(evidence + artifact_refs, ensure_ascii=False)}"
    key = data.get("idempotency_key") or f"{SKILL_ID}-{hashlib.sha256(seed.encode('utf-8')).hexdigest()[:16]}"
    if key in set(config.get("existing_idempotency_keys", [])):
        blocked.append("duplicate idempotency_key; refusing duplicate reference archive")

    target = individual_container_target(data, config)
    if target["is_sample"] and not config.get("customer_table_model", {}).get("sample_is_write_target"):
        blocked.append("individual customer target points to the sample CUST-2026-000001 table; refusing to write sample table")

    writes = []
    if ledger_block_id or evidence or artifact_refs:
        writes.append({"table": "A99_individual_customer_container", "operation": "update", "idempotency_key": key, "base_token": target.get("base_token"), "table_id": target.get("table_id"), "target_ref": target.get("source_ref"), "fields": clean({
            "ledger_block_id": ledger_block_id,
            "customer_id": customer_id,
            "ledger_record_time": record_time,
            "evidence_refs": evidence,
            "artifact_refs": artifact_refs,
        })})
    writes.append({"table": "A03_all_customer_files", "operation": "update", "idempotency_key": key, "fields": clean({
        "customer_id": customer_id,
        "updated_at": created_at,
    })})
    blocked.extend(validate(config, writes))
    has_hard_block = bool(blocked)
    missing_target = bool(ledger_block_id or evidence or artifact_refs) and not (target.get("base_token") and target.get("table_id"))
    if missing_target:
        blocked.append("missing per-customer reference target: provide individual_customer_base_token + individual_customer_table_id, or a resolvable per-customer base URL")
    status = "rejected" if has_hard_block else "needs_confirm" if missing_target else "pass"
    return status, key, {"customer_id": customer_id, "ledger_block_id": ledger_block_id, "ledger_record_time": record_time, "evidence_ids": evidence, "artifact_ids": artifacts, "handoff_ids": as_list(data.get("handoff_ids"))}, writes, blocked, {
        "reference_refs_mapped_to": "A99_individual_customer_container attachment fields",
        "individual_customer_target": target,
    }


def main():
    parser = argparse.ArgumentParser(description="A-SK08 evidence/artifact/handoff reference archiver")
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
        config = load_json(args.config, args.config_json)
        status, key, validated, writes, blocked, refs = plan(load_json(args.input, args.input_json), config)
        writes = transform_writes(config, writes)
        commands = [c for c in (command_for(config, write) for write in writes) if c] if status == "pass" else []
        if args.execute and status == "pass":
            direct_results = run_direct_base_writes(config, writes)
            if direct_results is not None:
                refs["execution_results"] = direct_results
                status = "executed" if all(item["returncode"] == 0 for item in direct_results) else "error"
            elif len(commands) != len(writes):
                status = "error"
                blocked.append("missing lark-cli command template for at least one planned write")
            else:
                refs["execution_results"] = run(commands)
                status = "executed" if all(item["returncode"] == 0 for item in refs["execution_results"]) else "error"
        print(json.dumps({"status": status, "skill_id": SKILL_ID, "idempotency_key": key, "validated_input": validated, "planned_writes": writes, "blocked_reasons": blocked, "lark_cli_commands": commands, "result_refs": refs}, ensure_ascii=False, indent=2))
        sys.exit(0 if status in {"pass", "executed", "needs_confirm"} else 1)
    except Exception as exc:
        print(json.dumps({"status": "error", "skill_id": SKILL_ID, "idempotency_key": "", "validated_input": {}, "planned_writes": [], "blocked_reasons": [str(exc)], "lark_cli_commands": [], "result_refs": {}}, ensure_ascii=False, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()

