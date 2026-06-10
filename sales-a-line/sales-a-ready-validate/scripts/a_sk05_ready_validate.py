#!/usr/bin/env python3
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

SKILL_ID = "A-SK05"
CONFIRMED = {True, "true", "confirmed", "approved", "yes", "已确认", "确认", "通过"}
REQUIRED_PACKAGE_FIELDS = {"customer_id", "sales_id", "work_date", "effective_events_summary", "confirm_status", "evidence_ids"}


def load_json(path, raw):
    if raw:
        return json.loads(raw)
    return json.loads(Path(path).read_text(encoding="utf-8-sig")) if path else {}


def now_iso():
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


def as_list(value):
    if value is None or value == "":
        return []
    return value if isinstance(value, list) else [value]


def confirmed(value):
    return value in CONFIRMED or (isinstance(value, str) and value.strip().lower() in CONFIRMED)


def table_fields(config, table):
    return set(config.get("tables", {}).get(table, {}).get("fields") or config.get("tables", {}).get(table, {}).get("existing_fields") or [])


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


def transform_writes(config, writes):
    transformed = []
    for write in writes:
        table = write["table"]
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
    template = templates.get(f"{write['table']}.{write['operation']}") or templates.get(write["operation"])
    if not template:
        return None
    payload = json.dumps(write["fields"], ensure_ascii=False, separators=(",", ":"))
    return template.format(table=write["table"], table_ref=table_ref(config, write["table"]), payload_json=json.dumps(payload, ensure_ascii=False), idempotency_key=write["idempotency_key"])


def validate_fields(config, writes):
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
        base_token = direct.get("table_base_tokens", {}).get(write["table"]) or default_base_token
        if not base_token:
            results.append({"command": "", "payload_file": "", "returncode": 1, "stdout": "", "stderr": f"missing base_token for {write['table']}"})
            break
        table_id = direct.get("table_ids", {}).get(write["table"]) or table_ref(config, write["table"])
        payload_file = temp_dir / f"{write['idempotency_key']}.json"
        payload_file.write_text(json.dumps(write["fields"], ensure_ascii=False), encoding="utf-8")
        argv = [
            "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", lark_cli,
            "base", "+record-upsert",
            "--base-token", base_token,
            "--table-id", table_id,
            "--json", f"@{payload_file.name}",
            "--as", identity,
        ]
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
    return results


def plan(data, config):
    package = data.get("a_ready_package", data)
    if not package:
        return "rejected", "", {}, [], ["a_ready_package is empty"], {}
    missing = sorted(field for field in REQUIRED_PACKAGE_FIELDS if not package.get(field))
    if missing:
        return "rejected", "", {}, [], [f"a_ready_package missing fields: {', '.join(missing)}"], {}
    if not as_list(package.get("evidence_ids")):
        return "rejected", "", {}, [], ["missing evidence_ids; formal A-line fact entry is blocked"], {}
    if package.get("human_confirm_required") and not confirmed(package.get("confirm_status")):
        return "needs_confirm", "", package, [], ["human confirmation required but confirm_status is not confirmed"], {}
    if not confirmed(package.get("confirm_status")):
        return "needs_confirm", "", package, [], ["confirm_status is not confirmed"], {}

    created_at = now_iso()
    source_record_id = package.get("source_record_id") or ",".join(str(v) for v in as_list(package.get("source_session_ids"))) or package.get("work_date")
    key = data.get("idempotency_key") or package.get("idempotency_key") or f"{SKILL_ID}-{hashlib.sha256((package['customer_id'] + source_record_id).encode('utf-8')).hexdigest()[:16]}"
    blocked = []
    if key in set(config.get("existing_idempotency_keys", [])):
        blocked.append("duplicate idempotency_key; refusing duplicate validation log")
    write = {
        "table": "A07_a_line_run_log",
        "operation": "create",
        "idempotency_key": key,
        "fields": {
            "log_id": f"LOG-{key[-16:]}",
            "run_type": SKILL_ID,
            "source_line": "B-line",
            "source_record_id": source_record_id,
            "target_table": "A99_individual_customer_container.ledger",
            "customer_id": package["customer_id"],
            "operation": "validate_a_ready_package",
            "status": "pass",
            "idempotency_key": key,
            "error_message": "",
            "created_at": created_at,
        },
    }
    blocked.extend(validate_fields(config, [write]))
    status = "rejected" if blocked else "pass"
    return status, key, package, [write], blocked, {"validated_package": package}


def main():
    parser = argparse.ArgumentParser(description="A-SK05 B-line a_ready_package validator and executor")
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
                blocked.append("missing lark-cli command template for validation log write")
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
