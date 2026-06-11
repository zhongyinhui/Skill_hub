#!/usr/bin/env python3
import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

SKILL_ID = "A-SK10"
REQUIRED_READ_FIELDS = [
    "customer_id", "customer_name", "current_stage", "customer_rating", "latest_snapshot_text",
    "latest_snapshot_json", "core_needs", "current_objections", "buying_signals",
    "evidence_ref", "artifact_ref", "updated_at"
]
OPTIONAL_READ_FIELDS = ["risk_flags"]


def load_json(path, raw):
    if raw:
        return json.loads(raw)
    return json.loads(Path(path).read_text(encoding="utf-8-sig")) if path else {}


def table_fields(config, table):
    return set(config.get("tables", {}).get(table, {}).get("fields") or config.get("tables", {}).get(table, {}).get("existing_fields") or [])


def table_ref(config, table):
    return config.get("tables", {}).get(table, {}).get("table_ref", table)


def resolve_field(config, table, field):
    read_aliases = config.get("read_field_aliases", {}).get(table, {})
    return read_aliases.get(field, config.get("field_aliases", {}).get(table, {}).get(field, field))


def resolve_fields(config, table, fields):
    resolved = []
    for field in fields:
        target = resolve_field(config, table, field)
        if target and target not in resolved:
            resolved.append(target)
    return resolved


def command_for(config, read):
    direct = config.get("lark_cli_base")
    if direct:
        lark_cli = direct.get("lark_cli_ps1") or "lark-cli"
        base_token = direct.get("table_base_tokens", {}).get(read["table"]) or direct.get("base_token")
        if not base_token:
            return None
        identity = direct.get("as", "user")
        table_id = direct.get("table_ids", {}).get(read["table"]) or table_ref(config, read["table"])
        field_args = " ".join(f'--field-id "{field}"' for field in read["fields"])
        return f'powershell -NoProfile -ExecutionPolicy Bypass -File "{lark_cli}" base +record-list --base-token "{base_token}" --table-id "{table_id}" {field_args} --filter-json @<filter-file> --limit 10 --format json --as {identity}'
    templates = config.get("lark_cli_commands") or config.get("commands") or {}
    template = templates.get("A03_all_customer_files.read") or templates.get("read")
    if not template:
        return None
    return template.format(
        table=read["table"],
        table_ref=table_ref(config, read["table"]),
        customer_id=read["customer_id"],
        fields=json.dumps(",".join(read["fields"]), ensure_ascii=False),
    )


def run(commands):
    results = []
    for command in commands:
        completed = subprocess.run(command, shell=True, text=True, capture_output=True, encoding="utf-8", errors="replace")
        results.append({"command": command, "returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr})
        if completed.returncode != 0:
            break
    return results


def run_direct_base_read(config, read):
    direct = config.get("lark_cli_base")
    if not direct:
        return None
    lark_cli = direct.get("lark_cli_ps1") or "lark-cli"
    base_token = direct.get("table_base_tokens", {}).get(read["table"]) or direct.get("base_token")
    if not base_token:
        return [{"command": "", "returncode": 1, "stdout": "", "stderr": f"missing base_token for {read['table']}"}]
    identity = direct.get("as", "user")
    table_id = direct.get("table_ids", {}).get(read["table"]) or table_ref(config, read["table"])
    filter_json = json.dumps({"logic": "and", "conditions": [["customer_id", "==", read["customer_id"]]]}, ensure_ascii=False)
    temp_dir = Path(direct.get("payload_dir") or Path(tempfile.gettempdir()) / "a_line_skill_payloads")
    temp_dir.mkdir(parents=True, exist_ok=True)
    safe_customer_id = "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in str(read["customer_id"]))
    filter_file = temp_dir / f"A-SK10-filter-{safe_customer_id}.json"
    filter_file.write_text(filter_json, encoding="utf-8")
    argv = [
        "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", lark_cli,
        "base", "+record-list",
        "--base-token", base_token,
        "--table-id", table_id,
        "--filter-json", f"@{filter_file.name}",
        "--limit", "10",
        "--format", "json",
        "--as", identity,
    ]
    for field in read["fields"]:
        argv.extend(["--field-id", field])
    completed = subprocess.run(argv, text=True, capture_output=True, cwd=str(temp_dir), encoding="utf-8", errors="replace")
    return [{
        "command": " ".join(argv),
        "filter_file": str(filter_file),
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }]


def plan(data, config):
    blocked = []
    customer_id = data.get("customer_id")
    if not customer_id:
        blocked.append("missing required input: customer_id")
    existing = table_fields(config, "A03_all_customer_files")
    required_fields = resolve_fields(config, "A03_all_customer_files", REQUIRED_READ_FIELDS)
    if not existing:
        blocked.append("missing field snapshot for A03_all_customer_files")
    else:
        missing = sorted(set(required_fields) - existing)
        if missing:
            blocked.append(f"A03_all_customer_files missing read fields: {', '.join(missing)}")
    read_fields = required_fields[:]
    read_fields.extend(field for field in resolve_fields(config, "A03_all_customer_files", OPTIONAL_READ_FIELDS) if field in existing and field not in read_fields)
    if not data.get("include_json", True):
        read_fields.remove("latest_snapshot_json")
    if not data.get("include_refs", True):
        ref_fields = set(resolve_fields(config, "A03_all_customer_files", ["evidence_ref", "artifact_ref"]))
        read_fields = [field for field in read_fields if field not in ref_fields]
    read = {"table": "A03_all_customer_files", "operation": "read", "customer_id": customer_id, "fields": read_fields}
    status = "rejected" if blocked else "pass"
    return status, f"{SKILL_ID}-{customer_id or 'missing'}", {"customer_id": customer_id}, read, blocked, {}


def main():
    parser = argparse.ArgumentParser(description="A-SK10 read-only A-line customer snapshot reader")
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
        status, key, validated, read, blocked, refs = plan(load_json(args.input, args.input_json), config)
        commands = [command_for(config, read)] if status == "pass" else []
        commands = [command for command in commands if command]
        if args.execute and status == "pass":
            direct_results = run_direct_base_read(config, read)
            if direct_results is not None:
                refs["execution_results"] = direct_results
                status = "executed" if all(item["returncode"] == 0 for item in direct_results) else "error"
            elif not commands:
                status = "error"
                blocked.append("missing lark-cli read command template")
            else:
                refs["execution_results"] = run(commands)
                status = "executed" if all(item["returncode"] == 0 for item in refs["execution_results"]) else "error"
        print(json.dumps({
            "status": status,
            "skill_id": SKILL_ID,
            "idempotency_key": key,
            "validated_input": validated,
            "planned_writes": [],
            "blocked_reasons": blocked,
            "lark_cli_commands": commands,
            "result_refs": {"planned_read": read, **refs},
        }, ensure_ascii=False, indent=2))
        sys.exit(0 if status in {"pass", "executed", "needs_confirm"} else 1)
    except Exception as exc:
        print(json.dumps({"status": "error", "skill_id": SKILL_ID, "idempotency_key": "", "validated_input": {}, "planned_writes": [], "blocked_reasons": [str(exc)], "lark_cli_commands": [], "result_refs": {}}, ensure_ascii=False, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
