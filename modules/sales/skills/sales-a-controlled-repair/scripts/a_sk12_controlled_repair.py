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

SKILL_ID = "A-SK12"
CONFIRMED = {True, "true", "confirmed", "approved", "yes", "accepted", "确认", "已确认", "通过"}
REF_FIELDS = {
    "individual_customer_table_url", "ledger_table_ref", "evidence_ref_table_ref",
    "artifacts_ref_table_ref", "handoff_ref_table_ref", "latest_snapshot_table_ref",
}
PROHIBITED = {
    "delete", "merge", "remove", "customer_rating", "current_stage", "P(win)",
    "rating_score", "HI", "sent_to_customer", "ledger", "evidence_ref",
    "artifacts_ref", "handoff_ref", "latest_snapshot",
}


def load_json(path, raw):
    if raw:
        return json.loads(raw)
    return json.loads(Path(path).read_text(encoding="utf-8-sig")) if path else {}


def now_iso():
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


def confirmed(value):
    return value in CONFIRMED or (isinstance(value, str) and value.strip().lower() in CONFIRMED)


def as_list(value):
    if value is None or value == "":
        return []
    return value if isinstance(value, list) else [value]


def clean(fields):
    return {k: v for k, v in fields.items() if v is not None and v != []}


def hash12(value):
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:12].upper()


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
    if write.get("table") == "A06_a_line_index" and fields.get("source_id"):
        return "source_id", fields["source_id"]
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


def backfill_index_action(action, key, created_at):
    source_id = action.get("source_id")
    customer_id = action.get("customer_id")
    if not source_id or not customer_id:
        return None, "backfill_index requires source_id and customer_id"
    return {
        "table": "A06_a_line_index",
        "operation": "upsert",
        "idempotency_key": f"{key}-INDEX-{hash12(source_id)}",
        "fields": clean({
            "source_map_id": action.get("source_map_id") or f"SMAP-{hash12(source_id)}",
            "source_id": source_id,
            "source_type": action.get("source_type"),
            "source_department": action.get("source_department"),
            "raw_customer_name": action.get("raw_customer_name"),
            "raw_phone": action.get("raw_phone"),
            "candidate_customer_ids": as_list(action.get("candidate_customer_ids")) or None,
            "linked_customer_id": customer_id,
            "accepted_sales_id": action.get("accepted_sales_id"),
            "mapping_status": action.get("mapping_status", "mapped"),
            "created_at": action.get("created_at", created_at),
            "updated_at": created_at,
            "remark": action.get("remark"),
        }),
    }, ""


def backfill_customer_refs_action(action, key, created_at):
    customer_id = action.get("customer_id")
    if not customer_id:
        return None, "backfill_customer_refs requires customer_id"
    ref_updates = {field: action.get(field) for field in REF_FIELDS if action.get(field)}
    if not ref_updates:
        return None, "backfill_customer_refs requires at least one customer ledger ref field"
    return {
        "table": "A03_all_customer_files",
        "operation": "update",
        "idempotency_key": f"{key}-REFS-{customer_id}",
        "fields": clean({"customer_id": customer_id, **ref_updates, "updated_at": created_at}),
    }, ""


def refresh_updated_at_action(action, key, created_at):
    customer_id = action.get("customer_id")
    if not customer_id:
        return None, "refresh_updated_at requires customer_id"
    return {
        "table": "A03_all_customer_files",
        "operation": "update",
        "idempotency_key": f"{key}-TOUCH-{customer_id}",
        "fields": {"customer_id": customer_id, "updated_at": created_at},
    }, ""


ACTION_BUILDERS = {
    "backfill_index": backfill_index_action,
    "backfill_customer_refs": backfill_customer_refs_action,
    "refresh_updated_at": refresh_updated_at_action,
}


def plan(data, config):
    blocked = []
    actions = data.get("repair_actions")
    if not isinstance(actions, list) or not actions:
        blocked.append("missing required input: repair_actions")
    if not data.get("confirmed_by"):
        blocked.append("missing required input: confirmed_by")
    if not confirmed(data.get("confirm_status")):
        return "needs_confirm", "", {"repair_actions": actions or []}, [], ["controlled repairs require human confirmation"], {}

    created_at = now_iso()
    seed = json.dumps(actions or [], ensure_ascii=False, sort_keys=True) + str(data.get("audit_id") or "")
    key = data.get("idempotency_key") or f"{SKILL_ID}-{hashlib.sha256(seed.encode('utf-8')).hexdigest()[:16]}"
    writes = []
    skipped = []
    for index, action in enumerate(actions or [], start=1):
        action_type = action.get("type")
        if action_type in {"delete", "merge", "remove", "merge_customer"}:
            blocked.append(f"unsupported destructive action: {action_type}")
            continue
        builder = ACTION_BUILDERS.get(action_type)
        if not builder:
            blocked.append(f"unsupported repair action: {action_type}")
            continue
        write, reason = builder(action, f"{key}-{index}", created_at)
        if reason:
            skipped.append({"action_index": index, "type": action_type, "reason": reason})
            blocked.append(reason)
        elif write:
            writes.append(write)

    writes.append({"table": "A07_a_line_run_log", "operation": "create", "idempotency_key": key, "fields": clean({
        "log_id": f"LOG-{key[-16:]}",
        "run_type": SKILL_ID,
        "source_line": "A-SK11/manual_audit",
        "source_record_id": data.get("audit_id"),
        "target_table": "A-line maintenance",
        "operation": "controlled_repair",
        "status": "pass",
        "idempotency_key": key,
        "operation_level": "maintenance",
        "created_at": created_at,
        "input_payload_summary": {"confirmed_by": data.get("confirmed_by"), "action_count": len(actions or [])},
        "output_payload_summary": {"planned_write_count": len(writes), "skipped": skipped},
        "remark": data.get("repair_reason"),
    })})
    blocked.extend(validate(config, writes))
    status = "rejected" if blocked else "pass"
    return status, key, {"repair_action_count": len(actions or []), "confirmed_by": data.get("confirmed_by")}, writes, blocked, {"skipped_actions": skipped}


def main():
    parser = argparse.ArgumentParser(description="A-SK12 confirmed controlled repair executor")
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

