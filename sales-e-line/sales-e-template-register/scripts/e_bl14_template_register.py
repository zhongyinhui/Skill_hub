#!/usr/bin/env python3
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

SCRIPT_NAME = Path(__file__).name

OUTPUT_FIELDS = [
    "e_output_id", "e_task_id", "run_batch_id", "run_date", "created_at", "updated_at",
    "customer_id", "customer_name_snapshot", "target_sales_id", "target_sales_name",
    "source_a_snapshot_ref", "source_b_record_ref", "source_c_feedback_ref",
    "source_d_weapon_ref", "source_signal_ref", "source_signal_type", "opportunity_type",
    "recommendation_type", "recommended_action", "recommendation_reason",
    "confidence_score", "priority_score", "recommended_dline_skill_ids",
    "output_template_id", "evidence_refs", "b_action_map_id", "b_action_map_ref",
    "write_to_b_status", "sync_status", "error_message",
    "adoption_feedback_status", "actual_action_taken", "customer_response_summary",
    "c_effect_ref", "final_effect_status", "non_adoption_reason",
]

SPECS = {
    "e_bl09_news_radar.py": {
        "skill_id": "E-BL09",
        "table": "E01_output_records",
        "id_field": "e_output_id",
        "required": ["e_task_id", "run_batch_id", "source_signal_ref", "recommendation_reason"],
        "lookup": ["e_output_id"],
        "defaults": {"source_signal_type": "news", "opportunity_type": "news_opportunity", "recommendation_type": "news_radar", "sync_status": "pending"},
        "write_fields": OUTPUT_FIELDS,
    },
    "e_bl10_policy_radar.py": {
        "skill_id": "E-BL10",
        "table": "E01_output_records",
        "id_field": "e_output_id",
        "required": ["e_task_id", "run_batch_id", "source_signal_ref", "recommendation_reason"],
        "lookup": ["e_output_id"],
        "defaults": {"source_signal_type": "policy", "opportunity_type": "policy_opportunity", "recommendation_type": "policy_radar", "sync_status": "pending"},
        "write_fields": OUTPUT_FIELDS,
    },
    "e_bl11_industry_radar.py": {
        "skill_id": "E-BL11",
        "table": "E01_output_records",
        "id_field": "e_output_id",
        "required": ["e_task_id", "run_batch_id", "source_signal_ref", "recommendation_reason"],
        "lookup": ["e_output_id"],
        "defaults": {"source_signal_type": "industry", "opportunity_type": "industry_opportunity", "recommendation_type": "industry_radar", "sync_status": "pending"},
        "write_fields": OUTPUT_FIELDS,
    },
    "e_bl12_case_activation.py": {
        "skill_id": "E-BL12",
        "table": "E01_output_records",
        "id_field": "e_output_id",
        "required": ["customer_id", "source_a_snapshot_ref", "source_signal_ref", "recommendation_reason"],
        "lookup": ["e_output_id"],
        "defaults": {"source_signal_type": "case", "opportunity_type": "case_activation", "recommendation_type": "case_activation", "sync_status": "pending"},
        "write_fields": OUTPUT_FIELDS,
    },
    "e_bl13_silent_customer_radar.py": {
        "skill_id": "E-BL13",
        "table": "E01_output_records",
        "id_field": "e_output_id",
        "required": ["customer_id", "source_a_snapshot_ref", "recommendation_reason"],
        "lookup": ["e_output_id"],
        "defaults": {"source_signal_type": "a_snapshot", "opportunity_type": "silent_customer_activation", "recommendation_type": "silent_customer_radar", "sync_status": "pending"},
        "write_fields": OUTPUT_FIELDS,
    },
    "e_bl14_template_register.py": {
        "skill_id": "E-BL14",
        "table": "E06_template_index",
        "id_field": "template_id",
        "required": ["template_id", "template_name", "output_type", "target_receiver", "applicable_task_type"],
        "lookup": ["template_id"],
        "write_fields": [
            "template_id", "template_name", "output_type", "target_receiver",
            "applicable_task_type", "applicable_customer_stage", "template_ref",
            "output_schema_ref", "required_fields", "optional_fields", "tone_style",
            "version", "status", "reviewer", "updated_at", "remark",
        ],
    },
    "e_bl15_bline_sync_status.py": {
        "skill_id": "E-BL15",
        "table": "E01_output_records",
        "id_field": "e_output_id",
        "required": ["e_output_id"],
        "requires_any": ["b_action_map_id", "b_action_map_ref", "write_to_b_status", "sync_status", "error_message", "source_b_record_ref"],
        "lookup": ["e_output_id"],
        "write_fields": [
            "e_output_id", "updated_at", "source_b_record_ref", "b_action_map_id",
            "b_action_map_ref", "write_to_b_status", "sync_status", "error_message",
        ],
    },
    "e_bl16_run_state_update.py": {
        "skill_id": "E-BL16",
        "table": "E01_task_registry",
        "id_field": "e_task_id",
        "required": ["e_task_id"],
        "requires_any": ["last_run_at", "next_run_at", "last_run_status", "status", "error_summary"],
        "lookup": ["e_task_id"],
        "write_fields": [
            "e_task_id", "last_run_at", "next_run_at", "last_run_status",
            "error_summary", "status", "owner", "version", "remark",
        ],
    },
}

RULE_TABLE_ALIASES = {
    "e02.1": "E02_1_news_source_whitelist",
    "e02_1": "E02_1_news_source_whitelist",
    "news_source": "E02_1_news_source_whitelist",
    "news_source_whitelist": "E02_1_news_source_whitelist",
    "ai_news_source_whitelist": "E02_1_news_source_whitelist",
    "e02.2": "E02_2_policy_scan_rule",
    "e02_2": "E02_2_policy_scan_rule",
    "policy_scan": "E02_2_policy_scan_rule",
    "policy_scan_rule": "E02_2_policy_scan_rule",
    "region_policy_scan_rule": "E02_2_policy_scan_rule",
    "e02.3": "E02_3_industry_ai_opportunity_rule",
    "e02_3": "E02_3_industry_ai_opportunity_rule",
    "industry_ai_opportunity": "E02_3_industry_ai_opportunity_rule",
    "industry_ai_opportunity_rule": "E02_3_industry_ai_opportunity_rule",
    "e04.1": "E04_1_silent_customer_activation_rule",
    "e04_1": "E04_1_silent_customer_activation_rule",
    "silent_customer": "E04_1_silent_customer_activation_rule",
    "silent_customer_activation": "E04_1_silent_customer_activation_rule",
    "silent_customer_activation_rule": "E04_1_silent_customer_activation_rule",
    "e04.2": "E04_2_case_activation_rule",
    "e04_2": "E04_2_case_activation_rule",
    "case_activation": "E04_2_case_activation_rule",
    "case_activation_rule": "E04_2_case_activation_rule",
    "e04.3": "E04_3_policy_activation_rule",
    "e04_3": "E04_3_policy_activation_rule",
    "policy_activation": "E04_3_policy_activation_rule",
    "policy_activation_rule": "E04_3_policy_activation_rule",
}

RULE_MODE_VALUES = {
    "rule_config",
    "rule_table",
    "source_whitelist",
    "scan_rule",
    "activation_rule",
    "policy_activation_rule",
}

SCRIPT_RULE_DEFAULTS = {
    "e_bl09_news_radar.py": "E02_1_news_source_whitelist",
    "e_bl10_policy_radar.py": "E02_2_policy_scan_rule",
    "e_bl11_industry_radar.py": "E02_3_industry_ai_opportunity_rule",
    "e_bl12_case_activation.py": "E04_2_case_activation_rule",
    "e_bl13_silent_customer_radar.py": "E04_1_silent_customer_activation_rule",
}

SCRIPT_RULE_ALLOWED = {
    "e_bl09_news_radar.py": {"E02_1_news_source_whitelist"},
    "e_bl10_policy_radar.py": {"E02_2_policy_scan_rule", "E04_3_policy_activation_rule"},
    "e_bl11_industry_radar.py": {"E02_3_industry_ai_opportunity_rule"},
    "e_bl12_case_activation.py": {"E04_2_case_activation_rule"},
    "e_bl13_silent_customer_radar.py": {"E04_1_silent_customer_activation_rule"},
}

RULE_SPECS = {
    "E02_1_news_source_whitelist": {
        "id_field": "source_id",
        "id_prefix": "NEWSRC",
        "lookup": ["source_id"],
        "required": ["source_id", "source_name", "source_url", "source_type", "domain", "trust_level", "language"],
        "defaults": {"status": "active"},
        "write_fields": [
            "source_id", "source_name", "source_url", "source_type", "domain",
            "trust_level", "language", "target_industries", "scan_frequency",
            "last_scanned_at", "exclude_keywords", "crawl_method", "last_hit_count",
            "owner", "keywords", "max_items_per_scan", "status", "remark",
        ],
    },
    "E02_2_policy_scan_rule": {
        "id_field": "policy_rule_id",
        "id_prefix": "POLSCAN",
        "lookup": ["policy_rule_id"],
        "required": ["policy_rule_id", "region", "policy_type", "keywords", "policy_source_name", "policy_source_url"],
        "defaults": {"status": "active"},
        "write_fields": [
            "policy_rule_id", "region", "city", "policy_type", "keywords",
            "policy_source_name", "policy_source_url", "industry_scope",
            "customer_match_fields", "customer_match_rule", "opportunity_threshold",
            "priority_weight", "evidence_requirement", "recommended_activation_type",
            "recommended_dline_skill_ids", "last_scanned_at", "version", "status", "remark",
        ],
    },
    "E02_3_industry_ai_opportunity_rule": {
        "id_field": "industry_rule_id",
        "id_prefix": "INDRULE",
        "lookup": ["industry_rule_id"],
        "required": ["industry_rule_id", "industry", "opportunity_type", "signal_keywords", "value_point"],
        "defaults": {"status": "active"},
        "write_fields": [
            "industry_rule_id", "industry", "sub_industry", "opportunity_type",
            "signal_keywords", "exclude_keywords", "source_types", "customer_segment",
            "pain_point_match", "value_point", "activation_angle",
            "recommended_activation_type", "recommended_dline_skill_ids",
            "priority_weight", "version", "owner", "status", "updated_at",
        ],
    },
    "E04_1_silent_customer_activation_rule": {
        "id_field": "silent_rule_id",
        "id_prefix": "SILENT",
        "lookup": ["silent_rule_id"],
        "required": ["silent_rule_id", "silent_days_threshold", "activation_type", "recommended_message_angle"],
        "defaults": {"status": "active"},
        "write_fields": [
            "silent_rule_id", "silent_days_threshold", "customer_stage",
            "customer_rating", "last_interaction_type", "last_signal_type",
            "activation_type", "recommended_message_angle", "required_evidence",
            "recommended_dline_skill_ids", "max_retry_count", "cooldown_days",
            "priority_weight", "version", "status", "remark",
        ],
    },
    "E04_2_case_activation_rule": {
        "id_field": "case_rule_id",
        "id_prefix": "CASERULE",
        "lookup": ["case_rule_id"],
        "required": ["case_rule_id", "case_type", "case_match_condition", "activation_angle"],
        "defaults": {"status": "active"},
        "write_fields": [
            "case_rule_id", "case_type", "customer_industry", "customer_segment",
            "customer_stage", "customer_pain_point", "case_match_condition",
            "source_case_pool_ref", "recommended_case_ids", "activation_angle",
            "recommended_dline_skill_ids", "permission_level_required", "risk_boundary",
            "priority_weight", "version", "status", "updated_at",
        ],
    },
    "E04_3_policy_activation_rule": {
        "id_field": "policy_activation_rule_id",
        "id_prefix": "POLACT",
        "lookup": ["policy_activation_rule_id"],
        "required": ["policy_activation_rule_id", "policy_type", "region", "policy_match_condition", "activation_angle"],
        "defaults": {"status": "active"},
        "write_fields": [
            "policy_activation_rule_id", "policy_type", "region", "industry",
            "customer_segment", "customer_stage", "policy_match_condition",
            "activation_angle", "recommended_dline_skill_ids", "cooldown_days",
            "priority_weight", "version", "status", "remark",
        ],
    },
}

PROHIBITED_FIELDS = {"current_stage", "customer_rating", "rating_score", "p_win", "P(win)", "HI", "internal_reasoning", "model_hidden_state", "model_private_notes"}
OK_STATUSES = {"pass", "needs_confirm", "rejected", "executed", "error"}
URL_FIELD_NAMES = {
    "source_a_snapshot_ref",
    "source_b_record_ref",
    "source_c_feedback_ref",
    "source_d_weapon_ref",
    "source_signal_ref",
    "b_action_map_ref",
    "source_url",
    "policy_source_url",
    "template_ref",
    "output_schema_ref",
}
PLACEHOLDER_URL_HOSTS = {
    "example.com",
    "www.example.com",
    "example.org",
    "www.example.org",
    "example.net",
    "www.example.net",
    "localhost",
    "127.0.0.1",
}


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
    return {key: value for key, value in fields.items() if value not in (None, "", [], {})}


def as_list(value):
    if value in (None, ""):
        return []
    return value if isinstance(value, list) else [value]


def stable_digest(parts):
    raw = "|".join(str(part) for part in parts if part not in (None, "", [], {}))
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12].upper()


def generated_id(prefix, data):
    return f"{prefix}-{stable_digest([skill_id(), data.get('e_task_id'), data.get('run_batch_id'), data.get('customer_id'), data.get('source_signal_ref'), data.get('recommended_action')])}"


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


def transform_value(config, table, field, value):
    target_type = config.get("field_types", {}).get(table, {}).get(field)
    if target_type == "url" and isinstance(value, str):
        return value.strip()
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
    field_aliases = config.get("field_aliases", {}).get(table, {})
    drops = set(config.get("drop_fields", {}).get(table, []))
    normalized = {}
    for source_field, value in fields.items():
        if source_field in drops:
            continue
        target_field = field_aliases.get(source_field, source_field)
        if not target_field:
            continue
        normalized[target_field] = transform_value(config, table, target_field, value)
    return clean(normalized)


def required_blocks(data, fields, prefix="input"):
    return [f"{prefix} missing required field: {field}" for field in fields if data.get(field) in (None, "", [], {})]


def prepare_data(data, current_spec):
    merged = dict(current_spec.get("defaults") or {})
    merged.update(data)
    merged.setdefault("updated_at", now_iso())
    if current_spec["table"] == "E01_output_records":
        merged.setdefault("created_at", now_iso())
        merged.setdefault("run_date", merged.get("run_date") or merged.get("work_date") or datetime.now().strftime("%Y-%m-%d"))
    id_field = current_spec["id_field"]
    if not merged.get(id_field):
        prefix = "EOUT" if id_field == "e_output_id" else id_field.upper()
        merged[id_field] = generated_id(prefix, merged)
    return merged


def wants_rule_config(data):
    mode = str(data.get("mode") or data.get("operation") or "").strip().lower()
    return bool(data.get("rule_table")) or mode in RULE_MODE_VALUES


def normalize_rule_table_name(value):
    if value in (None, "", [], {}):
        return ""
    raw = str(value).strip()
    return RULE_TABLE_ALIASES.get(raw.lower(), raw)


def default_rule_table(data):
    mode = str(data.get("mode") or data.get("operation") or "").strip().lower()
    if SCRIPT_NAME == "e_bl10_policy_radar.py" and mode in {"activation_rule", "policy_activation_rule"}:
        return "E04_3_policy_activation_rule"
    return SCRIPT_RULE_DEFAULTS.get(SCRIPT_NAME, "")


def build_rule_write(data, config):
    allowed = SCRIPT_RULE_ALLOWED.get(SCRIPT_NAME, set())
    requested_table = normalize_rule_table_name(data.get("rule_table")) or default_rule_table(data)
    table = requested_table if requested_table in allowed else (default_rule_table(data) or requested_table)
    rule_spec = RULE_SPECS.get(table, {})
    if not rule_spec:
        return {
            "table": table or "unknown_rule_table",
            "operation": "upsert",
            "idempotency_key": f"{skill_id()}-unknown-rule-table",
            "lookup": {},
            "fields": {},
        }, [f"{SCRIPT_NAME} does not support rule_table: {data.get('rule_table') or data.get('mode')}"], dict(data)
    merged = dict(rule_spec.get("defaults") or {})
    merged.update(data)
    merged["rule_table"] = table
    id_field = rule_spec["id_field"]
    if not merged.get(id_field):
        merged[id_field] = generated_id(rule_spec["id_prefix"], merged)
    if "updated_at" in rule_spec["write_fields"]:
        merged.setdefault("updated_at", now_iso())
    fields = {field: merged.get(field) for field in rule_spec["write_fields"]}
    write = {
        "table": table,
        "operation": "upsert",
        "idempotency_key": f"{skill_id()}-{table}-{merged.get(id_field)}",
        "lookup": {field: merged.get(field) for field in rule_spec.get("lookup", []) if merged.get(field) not in (None, "", [], {})},
        "fields": normalize_fields(config, table, fields),
    }
    blocked = required_blocks(merged, rule_spec.get("required", []))
    if requested_table and requested_table not in allowed:
        blocked.append(f"{SCRIPT_NAME} cannot write rule_table: {requested_table}")
    return write, blocked, merged


def build_write(data, config):
    if wants_rule_config(data):
        return build_rule_write(data, config)
    current_spec = spec()
    merged = prepare_data(data, current_spec)
    table = current_spec["table"]
    fields = {field: merged.get(field) for field in current_spec["write_fields"]}
    write = {
        "table": table,
        "operation": "upsert",
        "idempotency_key": f"{current_spec['skill_id']}-{merged.get(current_spec['id_field'], 'missing')}",
        "lookup": {field: merged.get(field) for field in current_spec.get("lookup", []) if merged.get(field) not in (None, "", [], {})},
        "fields": normalize_fields(config, table, fields),
    }
    blocked = required_blocks(merged, current_spec.get("required", []))
    if current_spec.get("requires_any") and not any(merged.get(field) not in (None, "", [], {}) for field in current_spec["requires_any"]):
        blocked.append(f"missing at least one update field: {', '.join(current_spec['requires_any'])}")
    return write, blocked, merged


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


def extract_url(value):
    if not isinstance(value, str):
        return ""
    text = value.strip()
    if text.endswith(")") and "](" in text:
        return text[text.rfind("](") + 2:-1].strip()
    return text


def url_fields_for(config, table):
    typed = {
        field
        for field, target_type in config.get("field_types", {}).get(table, {}).items()
        if target_type == "url"
    }
    known = set(table_fields(config, table)) & URL_FIELD_NAMES
    return typed | known


def validate_url_fields(config, write):
    table = write["table"]
    blocked = []
    for field in sorted(url_fields_for(config, table) & set(write.get("fields", {}))):
        value = write["fields"].get(field)
        if value in (None, "", [], {}):
            continue
        for item in as_list(value):
            url = extract_url(item)
            parsed = urlparse(url)
            host = parsed.netloc.lower().split("@")[-1].split(":")[0]
            if parsed.scheme not in {"http", "https"} or not host:
                blocked.append(f"{table}.{field} must be an http(s) URL")
            elif host in PLACEHOLDER_URL_HOSTS or host.endswith(".example.com"):
                blocked.append(f"{table}.{field} cannot use placeholder URL: {url}")
    return blocked


def validate_writes(config, writes):
    blocked = []
    normalized = []
    for write in writes:
        table = write["table"]
        fields = normalize_fields(config, table, write.get("fields", {}))
        write = dict(write)
        write["fields"] = fields
        allowed_names = set(config.get("allowed_prohibited_field_names", {}).get(table, []))
        bad = sorted((set(fields) & PROHIBITED_FIELDS) - allowed_names)
        if bad:
            blocked.append(f"{table} contains prohibited fields: {', '.join(bad)}")
        existing = table_fields(config, table)
        if not existing:
            blocked.append(f"missing field snapshot for {table}")
        else:
            missing = sorted(set(fields) - existing)
            if missing:
                blocked.append(f"{table} missing fields: {', '.join(missing)}")
        blocked.extend(validate_options(config, write))
        blocked.extend(validate_url_fields(config, write))
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
    filter_file = temp_dir / f"{safe_name(write['idempotency_key'])}-lookup.json"
    filter_file.write_text(json.dumps({"logic": "and", "conditions": [[field, "==", value] for field, value in lookup.items()]}, ensure_ascii=False), encoding="utf-8")
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
    result["record_id"] = extract_record_id(completed.stdout)
    return result["record_id"], result


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
    write, semantic_blocked, merged = build_write(data, config)
    writes, validation_blocked = validate_writes(config, [write])
    blocked = semantic_blocked + validation_blocked
    status = "rejected" if blocked else "pass"
    return status, write["idempotency_key"], merged, writes, blocked, {}


def emit(status, key="", validated=None, writes=None, blocked=None, commands=None, refs=None):
    status = status if status in OK_STATUSES else "error"
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
        emit("error", blocked=["choose only one of --dry-run or --execute"])
        sys.exit(1)
    try:
        data = load_json(args.input, args.input_json)
        config = load_json(args.config, args.config_json)
        status, key, validated, writes, blocked, refs = plan(data, config)
        commands = [command_for(config, write) for write in writes] if status == "pass" else []
        if args.execute and status == "pass":
            refs["execution_results"] = execute_writes(config, writes)
            status = "executed" if all(item.get("returncode") == 0 for item in refs["execution_results"]) else "error"
        summary_keys = (
            "e_task_id", "e_output_id", "customer_id", "template_id", "run_batch_id",
            "rule_table", "source_id", "policy_rule_id", "industry_rule_id",
            "silent_rule_id", "case_rule_id", "policy_activation_rule_id",
        )
        emit(status, key, {"script": SCRIPT_NAME, **{k: validated.get(k) for k in summary_keys if validated.get(k)}}, writes, blocked, commands, refs)
        sys.exit(0 if status in {"pass", "executed", "needs_confirm"} else 1)
    except Exception as exc:
        emit("error", blocked=[str(exc)])
        sys.exit(1)


if __name__ == "__main__":
    main()
