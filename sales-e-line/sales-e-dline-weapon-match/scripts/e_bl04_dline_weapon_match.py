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

SCRIPT_NAME = Path(__file__).name

SPECS = {
    "e_bl01_task_registry.py": {
        "skill_id": "E-BL01",
        "table": "E01_task_registry",
        "id_field": "e_task_id",
        "required": ["e_task_id", "task_name", "task_type", "blacklight_type"],
        "lookup": ["e_task_id"],
        "write_fields": [
            "e_task_id", "task_name", "task_type", "blacklight_type", "target_customer_scope",
            "input_sources", "rule_table_refs", "output_template_id", "write_to_target",
            "output_type", "scan_frequency", "priority", "status", "last_run_at",
            "next_run_at", "last_run_status", "error_summary", "owner", "version", "remark",
        ],
    },
    "e_bl02_opportunity_scan.py": {
        "skill_id": "E-BL02",
        "table": "E01_output_records",
        "id_field": "e_output_id",
        "required": ["e_task_id", "run_batch_id", "source_signal_type", "source_signal_ref", "opportunity_type", "recommendation_reason"],
        "lookup": ["e_output_id"],
        "defaults": {"sync_status": "pending"},
        "write_fields": [
            "e_output_id", "e_task_id", "run_batch_id", "run_date", "created_at", "updated_at",
            "customer_id", "customer_name_snapshot", "target_sales_id", "target_sales_name",
            "source_a_snapshot_ref", "source_b_record_ref", "source_c_feedback_ref",
            "source_d_weapon_ref", "source_signal_ref", "source_signal_type", "opportunity_type",
            "recommendation_type", "recommended_action", "recommendation_reason",
            "confidence_score", "priority_score", "recommended_dline_skill_ids",
            "output_template_id", "evidence_refs", "sync_status", "error_message",
        ],
    },
    "e_bl03_customer_activation.py": {
        "skill_id": "E-BL03",
        "table": "E01_output_records",
        "id_field": "e_output_id",
        "required": ["customer_id", "source_a_snapshot_ref", "recommendation_reason"],
        "lookup": ["e_output_id"],
        "defaults": {"opportunity_type": "客户激活", "recommendation_type": "activation", "sync_status": "pending"},
        "write_fields": [
            "e_output_id", "e_task_id", "run_batch_id", "run_date", "created_at", "updated_at",
            "customer_id", "customer_name_snapshot", "target_sales_id", "target_sales_name",
            "source_a_snapshot_ref", "source_signal_ref", "source_signal_type", "opportunity_type",
            "recommendation_type", "recommended_action", "recommendation_reason",
            "confidence_score", "priority_score", "output_template_id", "evidence_refs",
            "sync_status", "error_message",
        ],
    },
    "e_bl04_dline_weapon_match.py": {
        "skill_id": "E-BL04",
        "table": "E01_output_records",
        "id_field": "e_output_id",
        "required": ["customer_id", "recommended_dline_skill_ids", "recommendation_reason"],
        "lookup": ["e_output_id"],
        "defaults": {"opportunity_type": "D线武器匹配", "recommendation_type": "dline_weapon_recommendation", "sync_status": "pending"},
        "write_fields": [
            "e_output_id", "e_task_id", "run_batch_id", "run_date", "created_at", "updated_at",
            "customer_id", "customer_name_snapshot", "target_sales_id", "target_sales_name",
            "source_a_snapshot_ref", "source_d_weapon_ref", "source_signal_ref",
            "source_signal_type", "opportunity_type", "recommendation_type",
            "recommended_action", "recommendation_reason", "confidence_score", "priority_score",
            "recommended_dline_skill_ids", "output_template_id", "evidence_refs",
            "sync_status", "error_message",
        ],
    },
    "e_bl05_action_map_generate.py": {
        "skill_id": "E-BL05",
        "table": "E01_output_records",
        "id_field": "e_output_id",
        "required": ["customer_id", "target_sales_id", "recommended_action", "recommendation_reason"],
        "lookup": ["e_output_id"],
        "defaults": {"recommendation_type": "next_day_action_map", "write_to_b_status": "pending", "sync_status": "pending"},
        "write_fields": [
            "e_output_id", "e_task_id", "run_batch_id", "run_date", "created_at", "updated_at",
            "customer_id", "customer_name_snapshot", "target_sales_id", "target_sales_name",
            "source_a_snapshot_ref", "source_d_weapon_ref", "source_signal_ref",
            "source_signal_type", "opportunity_type", "recommendation_type",
            "recommended_action", "recommendation_reason", "confidence_score", "priority_score",
            "recommended_dline_skill_ids", "output_template_id", "evidence_refs",
            "b_action_map_id", "b_action_map_ref", "write_to_b_status", "sync_status", "error_message",
        ],
    },
    "e_bl06_feedback_capture.py": {
        "skill_id": "E-BL06",
        "table": "E01_output_records",
        "id_field": "e_output_id",
        "required": ["e_output_id"],
        "requires_any": [
            "adoption_feedback_status", "actual_action_taken", "customer_response_summary",
            "c_effect_ref", "final_effect_status", "non_adoption_reason",
        ],
        "lookup": ["e_output_id"],
        "write_fields": [
            "e_output_id", "updated_at", "source_b_record_ref", "source_c_feedback_ref",
            "b_action_map_id", "b_action_map_ref", "write_to_b_status",
            "adoption_feedback_status", "actual_action_taken", "customer_response_summary",
            "c_effect_ref", "final_effect_status", "non_adoption_reason", "sync_status", "error_message",
        ],
    },
    "e_bl07_influence_adjust.py": {
        "skill_id": "E-BL07",
        "dynamic_state": True,
        "required": ["state_table"],
    },
    "e_bl08_snapshot_and_change_log.py": {
        "skill_id": "E-BL08",
        "snapshot_or_change": True,
    },
}

STATE_TABLES = {
    "global": {
        "table": "E05_global_state",
        "id_field": "global_factor_id",
        "required": ["global_factor_id", "factor_key", "factor_type", "current_weight", "update_source"],
        "fields": [
            "global_factor_id", "factor_key", "factor_type", "current_weight", "previous_weight",
            "weight_delta", "positive_feedback_count", "negative_feedback_count", "adoption_rate_7d",
            "effectiveness_rate_7d", "confidence_score", "update_source", "last_update_reason",
            "status", "updated_at",
        ],
    },
    "sales": {
        "table": "E05_sales_state",
        "id_field": "sales_factor_id",
        "required": ["sales_factor_id", "sales_id", "factor_type", "current_weight", "update_source"],
        "fields": [
            "sales_factor_id", "sales_id", "sales_name", "factor_type", "current_weight",
            "previous_weight", "adoption_rate_30d", "effectiveness_rate_30d",
            "top_rejection_reason", "do_not_recommend_flag", "confidence_score",
            "update_source", "updated_at", "remark",
        ],
    },
    "weapon": {
        "table": "E05_weapon_state",
        "id_field": "weapon_factor_id",
        "required": ["weapon_factor_id", "dline_skill_id", "weapon_name", "current_weight"],
        "fields": [
            "weapon_factor_id", "dline_skill_id", "weapon_name", "customer_stage",
            "customer_segment", "current_weight", "previous_weight", "hit_rate_30d",
            "use_rate_30d", "recent_positive_feedback", "recent_negative_feedback",
            "risk_penalty", "recommendation_status", "d06_version_status",
            "c02_metric_ref", "updated_at",
        ],
    },
    "segment": {
        "table": "E05_segment_state",
        "id_field": "segment_factor_id",
        "required": ["segment_factor_id", "customer_segment", "opportunity_type", "current_weight"],
        "fields": [
            "segment_factor_id", "customer_segment", "customer_stage", "customer_rating",
            "opportunity_type", "current_weight", "previous_weight", "response_rate_30d",
            "effectiveness_rate_30d", "confidence_score", "status", "updated_at",
        ],
    },
}

PROHIBITED_FIELDS = {
    "current_stage", "customer_rating", "rating_score", "p_win", "P(win)", "HI",
    "internal_reasoning", "model_hidden_state", "model_private_notes",
}

ALLOWED_STATUS = {"pass", "needs_confirm", "rejected", "executed", "error"}


def spec():
    if SCRIPT_NAME not in SPECS:
        raise RuntimeError(f"unsupported script name: {SCRIPT_NAME}")
    return SPECS[SCRIPT_NAME]


def skill_id():
    return spec()["skill_id"]


def load_json(path, raw):
    if raw:
        return json.loads(raw)
    return json.loads(Path(path).read_text(encoding="utf-8-sig")) if path else {}


def now_iso():
    return datetime.now().astimezone().replace(microsecond=0).isoformat()


def clean(fields):
    return {k: v for k, v in fields.items() if v not in (None, "", [], {})}


def as_list(value):
    if value in (None, ""):
        return []
    return value if isinstance(value, list) else [value]


def stable_digest(parts):
    raw = "|".join(str(part) for part in parts if part not in (None, "", [], {}))
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12].upper()


def generated_id(prefix, data, fields):
    parts = [data.get(field) for field in fields]
    parts.append(skill_id())
    return f"{prefix}-{stable_digest(parts)}"


def table_meta(config, table):
    return config.get("tables", {}).get(table, {})


def table_fields(config, table):
    meta = table_meta(config, table)
    return set(meta.get("fields") or meta.get("existing_fields") or [])


def table_ref(config, table):
    return table_meta(config, table).get("table_ref", table)


def table_base_token(config, table):
    direct = config.get("lark_cli_base", {})
    return direct.get("table_base_tokens", {}).get(table) or table_meta(config, table).get("base_token") or direct.get("base_token")


def table_id(config, table):
    direct = config.get("lark_cli_base", {})
    return direct.get("table_ids", {}).get(table) or table_meta(config, table).get("table_id") or table_ref(config, table)


def aliases(config, table):
    return config.get("field_aliases", {}).get(table, {})


def drop_fields(config, table):
    return set(config.get("drop_fields", {}).get(table, []))


def transform_value(config, table, field, value):
    target_type = config.get("field_types", {}).get(table, {}).get(field)
    if target_type == "text" and isinstance(value, (dict, list)):
        return json.dumps(value, ensure_ascii=False)
    if target_type == "number" and isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return value
    if target_type == "multi_select" and value not in (None, ""):
        return as_list(value)
    return value


def normalize_fields(config, table, fields):
    output = {}
    field_aliases = aliases(config, table)
    drops = drop_fields(config, table)
    for source_field, value in fields.items():
        if source_field in drops:
            continue
        target = field_aliases.get(source_field, source_field)
        if not target:
            continue
        output[target] = transform_value(config, table, target, value)
    return clean(output)


def apply_defaults(data, defaults):
    merged = dict(defaults or {})
    merged.update(data)
    return merged


def output_id_for(data, id_field):
    if data.get(id_field):
        return data[id_field]
    if id_field == "e_output_id":
        return generated_id("EOUT", data, ["e_task_id", "run_batch_id", "customer_id", "source_signal_ref", "recommended_action"])
    if id_field:
        return generated_id(id_field.upper(), data, ["task_name", "task_type", "customer_id"])
    return ""


def one_output_write(data, config, current_spec):
    data = apply_defaults(data, current_spec.get("defaults"))
    data.setdefault("created_at", now_iso())
    data.setdefault("updated_at", now_iso())
    data.setdefault("run_date", data.get("run_date") or data.get("work_date") or datetime.now().strftime("%Y-%m-%d"))
    id_field = current_spec["id_field"]
    data[id_field] = output_id_for(data, id_field)
    fields = {field: data.get(field) for field in current_spec["write_fields"]}
    table = current_spec["table"]
    return {
        "table": table,
        "operation": "upsert",
        "idempotency_key": f"{current_spec['skill_id']}-{data.get(id_field)}",
        "lookup": {field: data.get(field) for field in current_spec.get("lookup", []) if data.get(field)},
        "fields": normalize_fields(config, table, fields),
    }


def build_writes(data, config):
    current_spec = spec()
    if current_spec.get("dynamic_state"):
        state_key = str(data.get("state_table", "")).strip().lower()
        state_key = {
            "global_state": "global",
            "sales_state": "sales",
            "weapon_state": "weapon",
            "dline_weapon": "weapon",
            "segment_state": "segment",
            "customer_segment": "segment",
        }.get(state_key, state_key)
        state = STATE_TABLES.get(state_key)
        if not state:
            return [], [f"unknown state_table: {data.get('state_table')}"], {}, "rejected"
        merged = dict(data)
        merged.setdefault("updated_at", now_iso())
        fields = {field: merged.get(field) for field in state["fields"]}
        write = {
            "table": state["table"],
            "operation": "upsert",
            "idempotency_key": f"{current_spec['skill_id']}-{merged.get(state['id_field'], 'missing')}",
            "lookup": {state["id_field"]: merged.get(state["id_field"])},
            "fields": normalize_fields(config, state["table"], fields),
        }
        blocked = require_fields(merged, state["required"])
        needs_confirm = []
        if data.get("major_change") and not confirmed(data.get("review_confirmed") or data.get("human_confirmed")):
            needs_confirm.append("major influence change requires human confirmation before active-state update")
        status = "needs_confirm" if needs_confirm and not blocked else ("rejected" if blocked else "pass")
        return [write], blocked + needs_confirm, {"state_table": state_key}, status

    if current_spec.get("snapshot_or_change"):
        mode = str(data.get("mode") or data.get("operation") or "").strip().lower()
        is_change = bool(data.get("change_id")) or mode in {"change", "major_change", "major_change_log"}
        if is_change:
            table = "E05_major_change_log"
            id_field = "change_id"
            required = ["change_id", "affected_state_table", "affected_factor_id", "change_type", "change_reason"]
            fields = [
                "change_id", "affected_state_table", "affected_factor_id", "change_type",
                "old_value", "new_value", "change_reason", "evidence_refs", "impact_scope",
                "review_required", "review_status", "reviewer", "effective_at", "created_at", "remark",
            ]
        else:
            table = "E05_weekly_snapshot"
            id_field = "snapshot_id"
            required = ["snapshot_id", "week_start", "week_end", "snapshot_scope", "source_state_table"]
            fields = [
                "snapshot_id", "week_start", "week_end", "snapshot_scope", "source_state_table",
                "metrics_summary", "major_changes", "snapshot_json", "created_by", "created_at", "remark",
            ]
        merged = dict(data)
        merged.setdefault("created_at", now_iso())
        write = {
            "table": table,
            "operation": "upsert",
            "idempotency_key": f"{current_spec['skill_id']}-{merged.get(id_field, 'missing')}",
            "lookup": {id_field: merged.get(id_field)},
            "fields": normalize_fields(config, table, {field: merged.get(field) for field in fields}),
        }
        blocked = require_fields(merged, required)
        return [write], blocked, {"mode": "major_change_log" if is_change else "weekly_snapshot"}, "rejected" if blocked else "pass"

    records = data.get("recommendations") if current_spec["skill_id"] == "E-BL05" else None
    if isinstance(records, list) and records:
        writes = []
        blocked = []
        for index, item in enumerate(records, start=1):
            item_data = dict(data)
            item_data.pop("recommendations", None)
            item_data.update(item)
            item_data.setdefault("e_output_id", generated_id("EOUT", item_data, ["run_batch_id", "customer_id", "target_sales_id", "recommended_action", index]))
            writes.append(one_output_write(item_data, config, current_spec))
            blocked.extend(require_fields(item_data, current_spec.get("required", []), prefix=f"recommendations[{index}]"))
        return writes, blocked, {"recommendation_count": len(writes)}, "rejected" if blocked else "pass"

    if current_spec["table"] == "E01_task_registry":
        merged = dict(data)
        merged.setdefault("version", config.get("version"))
        fields = {field: merged.get(field) for field in current_spec["write_fields"]}
        write = {
            "table": current_spec["table"],
            "operation": "upsert",
            "idempotency_key": f"{current_spec['skill_id']}-{merged.get(current_spec['id_field'], 'missing')}",
            "lookup": {field: merged.get(field) for field in current_spec["lookup"] if merged.get(field)},
            "fields": normalize_fields(config, current_spec["table"], fields),
        }
    else:
        write = one_output_write(data, config, current_spec)
    blocked = require_fields(data, current_spec.get("required", []))
    if current_spec.get("requires_any") and not any(data.get(field) not in (None, "", [], {}) for field in current_spec["requires_any"]):
        blocked.append(f"missing at least one feedback field: {', '.join(current_spec['requires_any'])}")
    return [write], blocked, {}, "rejected" if blocked else "pass"


def confirmed(value):
    if value is True:
        return True
    if not isinstance(value, str):
        return False
    return value.strip().lower() in {"true", "confirmed", "approved", "yes", "确认", "已确认", "通过"}


def require_fields(data, fields, prefix="input"):
    missing = [field for field in fields if data.get(field) in (None, "", [], {})]
    return [f"{prefix} missing required field: {field}" for field in missing]


def validate_options(config, write):
    table = write["table"]
    options = config.get("select_options", {}).get(table, {})
    blocked = []
    for field, allowed in options.items():
        if field not in write["fields"] or write["fields"][field] in (None, "", [], {}):
            continue
        values = as_list(write["fields"][field])
        invalid = [value for value in values if value not in allowed]
        if invalid:
            blocked.append(f"{table}.{field} invalid option: {', '.join(map(str, invalid))}")
    return blocked


def validate_writes(config, writes):
    blocked = []
    normalized = []
    for write in writes:
        table = write["table"]
        existing = table_fields(config, table)
        fields = normalize_fields(config, table, write.get("fields", {}))
        write = dict(write)
        write["fields"] = fields
        bad = sorted(set(fields) & PROHIBITED_FIELDS)
        if bad and table != "E05_segment_state":
            blocked.append(f"{table} contains prohibited fields: {', '.join(bad)}")
        if not existing:
            blocked.append(f"missing field snapshot for {table}")
        else:
            missing = sorted(set(fields) - existing)
            if missing:
                blocked.append(f"{table} missing fields: {', '.join(missing)}")
        blocked.extend(validate_options(config, write))
        if not table_base_token(config, table):
            blocked.append(f"missing base token for {table}")
        if not table_id(config, table):
            blocked.append(f"missing table id for {table}")
        normalized.append(write)
    return normalized, blocked


def command_for(config, write):
    direct = config.get("lark_cli_base", {})
    lark_cli = direct.get("lark_cli_ps1") or "lark-cli"
    identity = direct.get("as", "user")
    return (
        f'powershell -NoProfile -ExecutionPolicy Bypass -File "{lark_cli}" base +record-upsert '
        f'--base-token "{table_base_token(config, write["table"])}" '
        f'--table-id "{table_id(config, write["table"])}" --json @<payload-file> --as {identity}'
    )


def safe_name(value):
    return "".join(ch if ch.isalnum() or ch in "._-" else "_" for ch in str(value))[:120] or "payload"


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
    for container in (payload.get("data", {}), payload.get("data", {}).get("record", {})):
        record_id_list = container.get("record_id_list") if isinstance(container, dict) else None
        if isinstance(record_id_list, list) and record_id_list:
            candidates.append(record_id_list[0])
    for candidate in candidates:
        if isinstance(candidate, str) and candidate:
            return candidate
    return ""


def lookup_existing(config, write, temp_dir):
    lookup = clean(write.get("lookup", {}))
    if not lookup:
        return "", None
    direct = config.get("lark_cli_base", {})
    lark_cli = direct.get("lark_cli_ps1") or "lark-cli"
    identity = direct.get("as", "user")
    conditions = [[field, "==", value] for field, value in lookup.items()]
    filter_file = temp_dir / f"{safe_name(write['idempotency_key'])}-lookup.json"
    filter_file.write_text(json.dumps({"logic": "and", "conditions": conditions}, ensure_ascii=False), encoding="utf-8")
    argv = [
        "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", lark_cli,
        "base", "+record-list",
        "--base-token", table_base_token(config, write["table"]),
        "--table-id", table_id(config, write["table"]),
        "--filter-json", f"@{filter_file.name}",
        "--limit", "1",
        "--format", "json",
        "--as", identity,
    ]
    completed = subprocess.run(argv, text=True, capture_output=True, cwd=str(temp_dir), encoding="utf-8", errors="replace")
    result = {
        "operation": "lookup_existing_record",
        "command": " ".join(argv),
        "payload_file": str(filter_file),
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }
    if completed.returncode != 0:
        return "", result
    record_id = extract_record_id(completed.stdout)
    result["record_id"] = record_id
    return record_id, result


def execute_writes(config, writes):
    direct = config.get("lark_cli_base", {})
    lark_cli = direct.get("lark_cli_ps1") or "lark-cli"
    identity = direct.get("as", "user")
    temp_dir = Path(direct.get("payload_dir") or Path(tempfile.gettempdir()) / "e_line_skill_payloads")
    temp_dir.mkdir(parents=True, exist_ok=True)
    results = []
    for write in writes:
        record_id, lookup_result = lookup_existing(config, write, temp_dir)
        if lookup_result:
            results.append(lookup_result)
            if lookup_result["returncode"] != 0:
                break
        payload_file = temp_dir / f"{safe_name(write['idempotency_key'])}.json"
        payload_file.write_text(json.dumps(write["fields"], ensure_ascii=False), encoding="utf-8")
        argv = [
            "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", lark_cli,
            "base", "+record-upsert",
            "--base-token", table_base_token(config, write["table"]),
            "--table-id", table_id(config, write["table"]),
        ]
        if record_id:
            argv.extend(["--record-id", record_id])
        argv.extend(["--json", f"@{payload_file.name}", "--as", identity])
        completed = subprocess.run(argv, text=True, capture_output=True, cwd=str(temp_dir), encoding="utf-8", errors="replace")
        results.append({
            "operation": "record_upsert",
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
    writes, semantic_blocked, refs, status = build_writes(data, config)
    writes, validation_blocked = validate_writes(config, writes)
    blocked = semantic_blocked + validation_blocked
    if blocked and status != "needs_confirm":
        status = "rejected"
    key_source = [write.get("idempotency_key") for write in writes] or [skill_id(), stable_digest([data])]
    idempotency_key = key_source[0] if len(key_source) == 1 else f"{skill_id()}-{stable_digest(key_source)}"
    return status, idempotency_key, writes, blocked, refs


def output(status, key="", validated=None, writes=None, blocked=None, commands=None, refs=None):
    status = status if status in ALLOWED_STATUS else "error"
    print(json.dumps({
        "status": status,
        "skill_id": skill_id(),
        "idempotency_key": key,
        "validated_input": validated or {},
        "planned_writes": writes or [],
        "blocked_reasons": blocked or [],
        "lark_cli_commands": commands or [],
        "result_refs": refs or {},
    }, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description=f"{skill_id()} E-line blacklight validator and executor")
    parser.add_argument("--input")
    parser.add_argument("--config")
    parser.add_argument("--input-json")
    parser.add_argument("--config-json")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if args.dry_run and args.execute:
        output("error", blocked=["choose only one of --dry-run or --execute"])
        sys.exit(1)
    try:
        data = load_json(args.input, args.input_json)
        config = load_json(args.config, args.config_json)
        status, key, writes, blocked, refs = plan(data, config)
        commands = [command_for(config, write) for write in writes] if status == "pass" else []
        if args.execute and status == "pass":
            refs["execution_results"] = execute_writes(config, writes)
            status = "executed" if all(item.get("returncode") == 0 for item in refs["execution_results"]) else "error"
        output(status, key, {"script": SCRIPT_NAME, **{k: data.get(k) for k in ("e_task_id", "e_output_id", "customer_id", "run_batch_id", "state_table") if data.get(k)}}, writes, blocked, commands, refs)
        sys.exit(0 if status in {"pass", "executed", "needs_confirm"} else 1)
    except Exception as exc:
        output("error", blocked=[str(exc)])
        sys.exit(1)


if __name__ == "__main__":
    main()
