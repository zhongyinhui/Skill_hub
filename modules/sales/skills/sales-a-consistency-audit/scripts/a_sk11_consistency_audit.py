#!/usr/bin/env python3
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

SKILL_ID = "A-SK11"

READ_FIELDS = {
    "A03_all_customer_files": [
        "customer_id", "customer_name", "source_id", "current_sales_id", "current_stage",
        "customer_rating", "latest_snapshot_text", "latest_snapshot_json",
        "individual_customer_table_url", "ledger_table_ref", "evidence_ref_table_ref",
        "artifacts_ref_table_ref", "handoff_ref_table_ref", "latest_snapshot_table_ref",
        "updated_at",
    ],
    "A01_customer_alias": ["alias_id", "customer_id", "alias_value", "status", "updated_at"],
    "A06_a_line_index": ["source_map_id", "source_id", "raw_customer_name", "linked_customer_id", "mapping_status", "updated_at"],
    "A04_sales_lead_pool": [
        "source_map_id", "lead_name", "raw_customer_name", "customer_display_name", "raw_phone",
        "phone", "source_type", "source_channel", "candidate_customer_ids", "dedupe_status",
        "lead_status", "sales_accept_status", "transfer_to_a_status", "processed_by",
        "process_result_summary", "lead_received_at",
    ],
}
REF_FIELDS = [
    "individual_customer_table_url", "ledger_table_ref", "evidence_ref_table_ref",
    "artifacts_ref_table_ref", "handoff_ref_table_ref", "latest_snapshot_table_ref",
]


def load_json(path, raw):
    if raw:
        return json.loads(raw)
    return json.loads(Path(path).read_text(encoding="utf-8-sig")) if path else {}


def table_fields(config, table):
    table_cfg = config.get("tables", {}).get(table, {})
    return set(table_cfg.get("fields") or table_cfg.get("existing_fields") or [])


def table_ref(config, table):
    return config.get("tables", {}).get(table, {}).get("table_ref", table)


def hash12(value):
    return hashlib.sha256(str(value).encode("utf-8")).hexdigest()[:12].upper()


def filter_existing_fields(config, table, fields):
    existing = table_fields(config, table)
    return [field for field in fields if field in existing]


def validate_reads(config, reads):
    blocked = []
    for read in reads:
        existing = table_fields(config, read["table"])
        if not existing:
            blocked.append(f"missing field snapshot for {read['table']}")
            continue
        missing = sorted(set(read["fields"]) - existing)
        if missing:
            blocked.append(f"{read['table']} missing read fields: {', '.join(missing)}")
    return blocked


def planned_reads(data, config):
    reads = []
    customer_id = data.get("customer_id")
    source_id = data.get("source_id")
    source_map_id = data.get("source_map_id") or (f"SMAP-{hash12(source_id)}" if source_id else "")
    if customer_id and data.get("include_customer_profile", True):
        reads.append({
            "table": "A03_all_customer_files",
            "filter": {"logic": "and", "conditions": [["customer_id", "==", customer_id]]},
            "fields": filter_existing_fields(config, "A03_all_customer_files", READ_FIELDS["A03_all_customer_files"]),
        })
    if customer_id and data.get("include_aliases", True):
        reads.append({
            "table": "A01_customer_alias",
            "filter": {"logic": "and", "conditions": [["customer_id", "==", customer_id]]},
            "fields": filter_existing_fields(config, "A01_customer_alias", READ_FIELDS["A01_customer_alias"]),
        })
    if customer_id and data.get("include_index", True):
        reads.append({
            "table": "A06_a_line_index",
            "filter": {"logic": "and", "conditions": [["linked_customer_id", "==", customer_id]]},
            "fields": filter_existing_fields(config, "A06_a_line_index", READ_FIELDS["A06_a_line_index"]),
        })
    if source_id and data.get("include_index", True):
        reads.append({
            "table": "A06_a_line_index",
            "filter": {"logic": "and", "conditions": [["source_id", "==", source_id]]},
            "fields": filter_existing_fields(config, "A06_a_line_index", READ_FIELDS["A06_a_line_index"]),
        })
    if source_map_id and data.get("include_lead_pool", True):
        reads.append({
            "table": "A04_sales_lead_pool",
            "filter": {"logic": "and", "conditions": [["source_map_id", "==", source_map_id]]},
            "fields": filter_existing_fields(config, "A04_sales_lead_pool", READ_FIELDS["A04_sales_lead_pool"]),
        })
    return reads


def command_for(config, read):
    direct = config.get("lark_cli_base")
    if not direct:
        return None
    lark_cli = direct.get("lark_cli_ps1") or "lark-cli"
    base_token = direct.get("table_base_tokens", {}).get(read["table"]) or direct.get("base_token")
    if not base_token:
        return None
    table_id = direct.get("table_ids", {}).get(read["table"]) or table_ref(config, read["table"])
    identity = direct.get("as", "user")
    fields = " ".join(f'--field-id "{field}"' for field in read["fields"])
    return f'powershell -NoProfile -ExecutionPolicy Bypass -File "{lark_cli}" base +record-list --base-token "{base_token}" --table-id "{table_id}" {fields} --filter-json @<filter-file> --limit 20 --format json --as {identity}'


def parse_record_list(stdout):
    try:
        payload = json.loads(stdout)
    except Exception:
        return {"records": [], "record_ids": [], "fields": []}
    data = payload.get("data", {})
    return {
        "records": data.get("data") or data.get("records") or [],
        "record_ids": data.get("record_id_list") or [],
        "fields": data.get("fields") or [],
    }


def run_direct_reads(config, reads):
    direct = config.get("lark_cli_base")
    if not direct:
        return None
    lark_cli = direct.get("lark_cli_ps1") or "lark-cli"
    default_base_token = direct.get("base_token")
    identity = direct.get("as", "user")
    temp_dir = Path(direct.get("payload_dir") or Path(tempfile.gettempdir()) / "a_line_skill_payloads")
    temp_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for idx, read in enumerate(reads, start=1):
        base_token = direct.get("table_base_tokens", {}).get(read["table"]) or default_base_token
        if not base_token:
            results.append({"command": "", "returncode": 1, "stdout": "", "stderr": f"missing base_token for {read['table']}", "table": read["table"]})
            break
        table_id = direct.get("table_ids", {}).get(read["table"]) or table_ref(config, read["table"])
        filter_file = temp_dir / f"{SKILL_ID}-read-{idx}.json"
        filter_file.write_text(json.dumps(read["filter"], ensure_ascii=False), encoding="utf-8")
        argv = [
            "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", lark_cli,
            "base", "+record-list", "--base-token", base_token, "--table-id", table_id,
            "--filter-json", f"@{filter_file.name}", "--limit", "20", "--format", "json", "--as", identity,
        ]
        for field in read["fields"]:
            argv.extend(["--field-id", field])
        completed = subprocess.run(argv, text=True, capture_output=True, cwd=str(temp_dir), encoding="utf-8", errors="replace")
        parsed = parse_record_list(completed.stdout)
        results.append({
            "table": read["table"],
            "filter": read["filter"],
            "command": " ".join(argv),
            "filter_file": str(filter_file),
            "returncode": completed.returncode,
            "stdout": completed.stdout,
            "stderr": completed.stderr,
            "record_count": len(parsed["records"]),
            "record_ids": parsed["record_ids"],
            "fields": parsed["fields"],
            "requested_fields": read["fields"],
            "records": parsed["records"],
        })
        if completed.returncode != 0:
            break
    return results


def row_dict(result, row_index=0):
    records = result.get("records") or []
    fields = result.get("requested_fields") or result.get("fields") or []
    if row_index >= len(records):
        return {}
    row = records[row_index]
    if not isinstance(row, list):
        return row if isinstance(row, dict) else {}
    return {field: row[idx] if idx < len(row) else None for idx, field in enumerate(fields)}


def build_findings(data, reads, results):
    findings = []
    by_table = {}
    for result in results or []:
        by_table.setdefault(result.get("table"), []).append(result)

    customer_id = data.get("customer_id")
    source_id = data.get("source_id")
    profile_results = by_table.get("A03_all_customer_files", [])
    if customer_id and profile_results:
        count = profile_results[0].get("record_count", 0)
        if count == 0:
            findings.append({"level": "error", "code": "missing_customer_profile", "message": "A03 customer profile not found"})
        elif count > 1:
            findings.append({"level": "error", "code": "duplicate_customer_profile", "message": "multiple A03 profiles found for customer_id"})
        else:
            row = row_dict(profile_results[0])
            missing_refs = [field for field in REF_FIELDS if not row.get(field)]
            if missing_refs:
                findings.append({"level": "warning", "code": "partial_customer_refs", "message": "customer ledger refs are incomplete", "fields": missing_refs})

    if customer_id and data.get("include_aliases", True):
        alias_count = sum(result.get("record_count", 0) for result in by_table.get("A01_customer_alias", []))
        if alias_count == 0:
            findings.append({"level": "warning", "code": "missing_alias_records", "message": "no alias records found for customer_id"})

    if customer_id and data.get("include_index", True):
        index_by_customer = [
            result for result in by_table.get("A06_a_line_index", [])
            if any(cond[0] == "linked_customer_id" for cond in result.get("filter", {}).get("conditions", []))
        ]
        if index_by_customer and sum(result.get("record_count", 0) for result in index_by_customer) == 0:
            findings.append({"level": "warning", "code": "missing_customer_index", "message": "no source index rows linked to customer_id"})

    if source_id:
        index_by_source = [result for result in by_table.get("A06_a_line_index", []) if source_id in json.dumps(result.get("records", []), ensure_ascii=False)]
        if data.get("include_index", True) and not index_by_source:
            findings.append({"level": "warning", "code": "missing_source_index", "message": "no source index row found for source_id"})
    source_map_id = data.get("source_map_id") or (f"SMAP-{hash12(source_id)}" if source_id else "")
    if source_map_id:
        lead_count = sum(result.get("record_count", 0) for result in by_table.get("A04_sales_lead_pool", []))
        if data.get("include_lead_pool", True) and lead_count == 0:
            findings.append({"level": "warning", "code": "missing_lead_pool_record", "message": "no lead pool row found for source_map_id"})

    if not findings:
        findings.append({"level": "ok", "code": "no_obvious_consistency_issue", "message": "no obvious A-line consistency issue found"})
    return findings


def plan(data, config):
    blocked = []
    if not data.get("customer_id") and not data.get("source_id"):
        blocked.append("provide customer_id or source_id")
    reads = planned_reads(data, config)
    blocked.extend(validate_reads(config, reads))
    status = "rejected" if blocked else "pass"
    key = f"{SKILL_ID}-{data.get('customer_id') or data.get('source_id') or 'missing'}"
    source_id = data.get("source_id")
    source_map_id = data.get("source_map_id") or (f"SMAP-{hash12(source_id)}" if source_id else "")
    return status, key, {"customer_id": data.get("customer_id"), "source_id": source_id, "source_map_id": source_map_id}, reads, blocked, {}


def main():
    parser = argparse.ArgumentParser(description="A-SK11 read-only A-line consistency auditor")
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
        data = load_json(args.input, args.input_json)
        config = load_json(args.config, args.config_json)
        status, key, validated, reads, blocked, refs = plan(data, config)
        commands = [c for c in (command_for(config, read) for read in reads) if c] if status == "pass" else []
        if args.execute and status == "pass":
            direct_results = run_direct_reads(config, reads)
            if direct_results is not None:
                refs["execution_results"] = direct_results
                refs["audit_findings"] = build_findings(data, reads, direct_results)
                status = "executed" if all(item["returncode"] == 0 for item in direct_results) else "error"
            elif len(commands) != len(reads):
                status = "error"
                blocked.append("missing lark-cli read command template")
        print(json.dumps({
            "status": status,
            "skill_id": SKILL_ID,
            "idempotency_key": key,
            "validated_input": validated,
            "planned_writes": [],
            "blocked_reasons": blocked,
            "lark_cli_commands": commands,
            "result_refs": {"planned_reads": reads, **refs},
        }, ensure_ascii=False, indent=2))
        sys.exit(0 if status in {"pass", "executed", "needs_confirm"} else 1)
    except Exception as exc:
        print(json.dumps({"status": "error", "skill_id": SKILL_ID, "idempotency_key": "", "validated_input": {}, "planned_writes": [], "blocked_reasons": [str(exc)], "lark_cli_commands": [], "result_refs": {}}, ensure_ascii=False, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()

