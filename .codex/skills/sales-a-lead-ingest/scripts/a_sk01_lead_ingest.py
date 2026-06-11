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

SKILL_ID = "A-SK01"
PROHIBITED = {
    "customer_rating", "current_stage", "P(win)", "rating_score", "HI",
    "amount_factor", "urgency_factor", "relationship_factor", "sent_to_customer",
}


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
    if write.get("table") == "A04_sales_lead_pool" and fields.get("source_map_id"):
        return "source_map_id", fields["source_map_id"]
    if write.get("table") == "A06_a_line_index" and fields.get("source_id"):
        return "source_id", fields["source_id"]
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
    blocked = []
    source_id = data.get("source_id")
    raw_name = data.get("raw_customer_name") or data.get("lead_name") or data.get("raw_company_name")
    if not source_id:
        blocked.append("missing required input: source_id")
    if not raw_name:
        blocked.append("missing one raw identity field: raw_customer_name, lead_name, or raw_company_name")
    if data.get("linked_customer_id") or data.get("customer_id"):
        return "needs_confirm", "", {}, [], ["raw intake cannot bind customer_id; use A-SK02 or A-SK04"], {}

    created_at = data.get("created_at") or now_iso()
    source_map_id = data.get("source_map_id") or f"SMAP-{hash12(source_id)}"
    key = data.get("idempotency_key") or f"{SKILL_ID}-{hashlib.sha256(str(source_id).encode('utf-8')).hexdigest()[:16]}"
    writes = [{
        "table": "A04_sales_lead_pool",
        "operation": "upsert",
        "idempotency_key": key,
        "fields": clean({
            "source_map_id": source_map_id,
            "lead_name": data.get("lead_name") or raw_name,
            "raw_customer_name": data.get("raw_customer_name") or raw_name,
            "raw_company_name": data.get("raw_company_name"),
            "customer_display_name": data.get("customer_display_name") or raw_name,
            "raw_phone": data.get("raw_phone"),
            "phone": data.get("phone") or data.get("raw_phone"),
            "source_type": data.get("source_type"),
            "source_channel": data.get("source_channel"),
            "source_record_url": data.get("source_record_url"),
            "candidate_customer_ids": as_list(data.get("candidate_customer_ids")) or None,
            "dedupe_key": data.get("dedupe_key"),
            "dedupe_status": data.get("dedupe_status"),
            "lead_status": data.get("lead_status") or data.get("status"),
            "lead_quality": data.get("lead_quality"),
            "sales_accept_status": data.get("sales_accept_status"),
            "recommended_sales_id": data.get("recommended_sales_id"),
            "transfer_to_sales_id": data.get("transfer_to_sales_id") or data.get("assigned_sales_id"),
            "transfer_to_a_status": data.get("transfer_to_a_status"),
            "lead_created_at": data.get("lead_created_at") or data.get("created_at"),
            "lead_received_at": data.get("lead_received_at") or created_at,
            "lead_remark": data.get("lead_remark"),
            "raw_remark": data.get("raw_remark"),
            "remark": data.get("remark"),
            "ai_summary": data.get("ai_summary"),
            "processed_by": data.get("processed_by"),
        }),
    }]
    if data.get("write_index", True) is not False:
        writes.append({
            "table": "A06_a_line_index",
            "operation": "upsert",
            "idempotency_key": f"{key}-INDEX-{hash12(source_id)}",
            "fields": clean({
                "source_map_id": source_map_id,
                "source_id": source_id,
                "source_type": data.get("source_type"),
                "source_department": data.get("source_department"),
                "raw_customer_name": raw_name,
                "raw_phone": data.get("raw_phone"),
                "candidate_customer_ids": as_list(data.get("candidate_customer_ids")) or None,
                "mapping_status": data.get("mapping_status", "pending"),
                "created_at": created_at,
                "updated_at": now_iso(),
                "remark": data.get("remark"),
            }),
        })
    blocked.extend(validate(config, writes))
    status = "rejected" if blocked else "pass"
    return status, key, {"source_id": source_id, "raw_customer_name": raw_name}, writes, blocked, {}


def main():
    parser = argparse.ArgumentParser(description="A-SK01 raw lead intake validator and executor")
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
        print(json.dumps({
            "status": status,
            "skill_id": SKILL_ID,
            "idempotency_key": key,
            "validated_input": validated,
            "planned_writes": writes,
            "blocked_reasons": blocked,
            "lark_cli_commands": commands,
            "result_refs": refs,
        }, ensure_ascii=False, indent=2))
        sys.exit(0 if status in {"pass", "executed", "needs_confirm"} else 1)
    except Exception as exc:
        print(json.dumps({"status": "error", "skill_id": SKILL_ID, "idempotency_key": "", "validated_input": {}, "planned_writes": [], "blocked_reasons": [str(exc)], "lark_cli_commands": [], "result_refs": {}}, ensure_ascii=False, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()

