#!/usr/bin/env python3
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

SKILL_ID = "A-SK07"
CONFIRMED = {True, "true", "confirmed", "approved", "yes", "accepted", "确认", "已确认", "通过"}
ALLOWED_FIELDS = {
    "current_stage", "customer_rating", "next_followup_at", "recommended_next_action",
    "last_contact_summary", "current_status", "budget_level", "decision_power",
}
PROHIBITED = {
    "P(win)", "amount_factor", "urgency_factor", "relationship_factor", "rating_score",
    "HI", "sent_to_customer", "latest_snapshot_json", "latest_snapshot_text",
}


def load_json(path, raw):
    if raw:
        return json.loads(raw)
    return json.loads(Path(path).read_text(encoding="utf-8-sig")) if path else {}


def now_iso():
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


def confirmed(value):
    return value in CONFIRMED or (isinstance(value, str) and value.strip().lower() in CONFIRMED)


def clean(fields):
    return {k: v for k, v in fields.items() if v is not None and v != []}


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
    if (field_type == "datetime" or field.endswith("_at")) and isinstance(value, str):
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
        new_write["fields"] = clean(fields)
        transformed.append(new_write)
    return transformed


def validate(config, writes):
    writes = transform_writes(config, writes)
    blocked = []
    for write in writes:
        bad = sorted(set(write.get("fields", {})) & PROHIBITED)
        if bad:
            blocked.append(f"{write['table']} contains prohibited fields: {', '.join(bad)}")
        existing = table_fields(config, write["table"])
        if not existing:
            blocked.append(f"missing field snapshot for {write['table']}")
            continue
        missing = sorted(set(write.get("fields", {})) - existing)
        if missing:
            blocked.append(f"{write['table']} missing fields: {', '.join(missing)}")
    return blocked


def command_for(config, write):
    direct = config.get("lark_cli_base")
    if direct:
        lark_cli = direct.get("lark_cli_ps1") or "lark-cli"
        base_token = direct.get("table_base_tokens", {}).get(write["table"]) or direct.get("base_token")
        if not base_token:
            return None
        table_id = direct.get("table_ids", {}).get(write["table"]) or table_ref(config, write["table"])
        identity = direct.get("as", "user")
        return f'powershell -NoProfile -ExecutionPolicy Bypass -File "{lark_cli}" base +record-upsert --base-token "{base_token}" --table-id "{table_id}" --json @<payload-file> --as {identity}'
    return None


def upsert_lookup_key(write):
    fields = write.get("fields", {})
    if write.get("table") == "A03_all_customer_files" and fields.get("customer_id"):
        return "customer_id", fields["customer_id"]
    if write.get("table") == "A07_a_line_run_log" and fields.get("log_id"):
        return "log_id", fields["log_id"]
    return "", ""


def extract_record_id(stdout):
    try:
        payload = json.loads(stdout)
    except Exception:
        return ""
    candidates = [
        payload.get("record_id"), payload.get("id"),
        payload.get("data", {}).get("record_id"), payload.get("data", {}).get("id"),
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


def lookup_existing_record_id(direct, write, base_token, table_id, temp_dir):
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
        "base", "+record-list", "--base-token", base_token, "--table-id", table_id,
        "--filter-json", f"@{filter_file.name}", "--limit", "1", "--format", "json",
        "--as", identity, "--field-id", key_field,
    ]
    completed = subprocess.run(argv, text=True, capture_output=True, cwd=str(temp_dir), encoding="utf-8", errors="replace")
    return {
        "operation": "lookup_existing_record",
        "command": " ".join(argv),
        "payload_file": str(filter_file),
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "record_id": extract_record_id(completed.stdout) if completed.returncode == 0 else "",
    }


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
            results.append({"command": "", "returncode": 1, "stdout": "", "stderr": f"missing base_token for {write['table']}"})
            break
        table_id = direct.get("table_ids", {}).get(write["table"]) or table_ref(config, write["table"])
        lookup_result = lookup_existing_record_id(direct, write, base_token, table_id, temp_dir)
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
            "base", "+record-upsert", "--base-token", base_token, "--table-id", table_id,
        ]
        if record_id:
            argv.extend(["--record-id", record_id])
        argv.extend(["--json", f"@{payload_file.name}", "--as", identity])
        completed = subprocess.run(argv, text=True, capture_output=True, cwd=str(temp_dir), encoding="utf-8", errors="replace")
        results.append({"command": " ".join(argv), "payload_file": str(payload_file), "returncode": completed.returncode, "stdout": completed.stdout, "stderr": completed.stderr})
        if completed.returncode != 0:
            break
    return results


def plan(data, config):
    blocked = []
    customer_id = data.get("customer_id")
    updates = data.get("field_updates") or {}
    if not customer_id:
        blocked.append("missing required input: customer_id")
    if not isinstance(updates, dict) or not updates:
        blocked.append("missing required input: field_updates")
    if not data.get("confirmed_by"):
        blocked.append("missing required input: confirmed_by")
    if not confirmed(data.get("confirm_status")):
        return "needs_confirm", "", {"customer_id": customer_id, "field_updates": updates}, [], ["formal fields require human confirmation"], {}

    outside = sorted(set(updates) - ALLOWED_FIELDS)
    if outside:
        blocked.append(f"field_updates outside allowlist: {', '.join(outside)}")
    bad = sorted(set(updates) & PROHIBITED)
    if bad:
        blocked.append(f"field_updates contains prohibited fields: {', '.join(bad)}")

    created_at = now_iso()
    seed = f"{customer_id}|{json.dumps(updates, ensure_ascii=False, sort_keys=True)}|{data.get('confirmation_id','')}"
    key = data.get("idempotency_key") or f"{SKILL_ID}-{hashlib.sha256(seed.encode('utf-8')).hexdigest()[:16]}"
    profile_fields = clean({"customer_id": customer_id, **{k: v for k, v in updates.items() if k in ALLOWED_FIELDS}, "updated_at": created_at})
    writes = [
        {"table": "A03_all_customer_files", "operation": "update", "idempotency_key": key, "fields": profile_fields},
        {"table": "A07_a_line_run_log", "operation": "create", "idempotency_key": key, "fields": clean({
            "log_id": f"LOG-{key[-16:]}",
            "run_type": SKILL_ID,
            "source_line": data.get("source_skill_id", "human_confirm"),
            "source_record_id": data.get("source_record_id") or data.get("confirmation_id"),
            "target_table": "A03_all_customer_files",
            "customer_id": customer_id,
            "operation": "formal_field_confirm",
            "status": "pass",
            "idempotency_key": key,
            "created_at": created_at,
            "input_payload_summary": {"confirmed_by": data.get("confirmed_by"), "field_updates": list(updates)},
            "output_payload_summary": {"updated_fields": profile_fields},
            "remark": data.get("confirm_remark"),
        })},
    ]
    blocked.extend(validate(config, writes))
    status = "rejected" if blocked else "pass"
    return status, key, {"customer_id": customer_id, "field_updates": updates, "confirmed_by": data.get("confirmed_by")}, writes, blocked, {}


def main():
    parser = argparse.ArgumentParser(description="A-SK07 confirmed formal field writer")
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
        print(json.dumps({"status": status, "skill_id": SKILL_ID, "idempotency_key": key, "validated_input": validated, "planned_writes": writes, "blocked_reasons": blocked, "lark_cli_commands": commands, "result_refs": refs}, ensure_ascii=False, indent=2))
        sys.exit(0 if status in {"pass", "executed", "needs_confirm"} else 1)
    except Exception as exc:
        print(json.dumps({"status": "error", "skill_id": SKILL_ID, "idempotency_key": "", "validated_input": {}, "planned_writes": [], "blocked_reasons": [str(exc)], "lark_cli_commands": [], "result_refs": {}}, ensure_ascii=False, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()

