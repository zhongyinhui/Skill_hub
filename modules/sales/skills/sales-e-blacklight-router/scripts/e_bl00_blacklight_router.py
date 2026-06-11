#!/usr/bin/env python3
import argparse
import hashlib
import json
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")

SKILL_ID = "E-BL00"
OK_STATUSES = {"pass", "needs_confirm", "rejected", "error"}

RULE_TABLE_ROUTES = {
    "e02.1": ("sales-e-news-radar", "Maintain E02.1 news/source whitelist"),
    "e02_1": ("sales-e-news-radar", "Maintain E02.1 news/source whitelist"),
    "news_source": ("sales-e-news-radar", "Maintain E02.1 news/source whitelist"),
    "news_source_whitelist": ("sales-e-news-radar", "Maintain E02.1 news/source whitelist"),
    "e02_1_news_source_whitelist": ("sales-e-news-radar", "Maintain E02.1 news/source whitelist"),
    "e02.2": ("sales-e-policy-radar", "Maintain E02.2 policy scan rules"),
    "e02_2": ("sales-e-policy-radar", "Maintain E02.2 policy scan rules"),
    "policy_scan": ("sales-e-policy-radar", "Maintain E02.2 policy scan rules"),
    "policy_scan_rule": ("sales-e-policy-radar", "Maintain E02.2 policy scan rules"),
    "e02_2_policy_scan_rule": ("sales-e-policy-radar", "Maintain E02.2 policy scan rules"),
    "e02.3": ("sales-e-industry-radar", "Maintain E02.3 industry opportunity rules"),
    "e02_3": ("sales-e-industry-radar", "Maintain E02.3 industry opportunity rules"),
    "industry_ai_opportunity_rule": ("sales-e-industry-radar", "Maintain E02.3 industry opportunity rules"),
    "e02_3_industry_ai_opportunity_rule": ("sales-e-industry-radar", "Maintain E02.3 industry opportunity rules"),
    "e04.1": ("sales-e-silent-customer-radar", "Maintain E04.1 silent customer activation rules"),
    "e04_1": ("sales-e-silent-customer-radar", "Maintain E04.1 silent customer activation rules"),
    "silent_customer_activation_rule": ("sales-e-silent-customer-radar", "Maintain E04.1 silent customer activation rules"),
    "e04_1_silent_customer_activation_rule": ("sales-e-silent-customer-radar", "Maintain E04.1 silent customer activation rules"),
    "e04.2": ("sales-e-case-activation", "Maintain E04.2 case activation rules"),
    "e04_2": ("sales-e-case-activation", "Maintain E04.2 case activation rules"),
    "case_activation_rule": ("sales-e-case-activation", "Maintain E04.2 case activation rules"),
    "e04_2_case_activation_rule": ("sales-e-case-activation", "Maintain E04.2 case activation rules"),
    "e04.3": ("sales-e-policy-radar", "Maintain E04.3 policy activation rules"),
    "e04_3": ("sales-e-policy-radar", "Maintain E04.3 policy activation rules"),
    "policy_activation_rule": ("sales-e-policy-radar", "Maintain E04.3 policy activation rules"),
    "e04_3_policy_activation_rule": ("sales-e-policy-radar", "Maintain E04.3 policy activation rules"),
}

SIGNAL_ROUTES = {
    "news": ("sales-e-news-radar", "News signal should be handled by E-BL09"),
    "ai_news": ("sales-e-news-radar", "News signal should be handled by E-BL09"),
    "policy": ("sales-e-policy-radar", "Policy signal should be handled by E-BL10"),
    "government": ("sales-e-policy-radar", "Government signal should be handled by E-BL10"),
    "subsidy": ("sales-e-policy-radar", "Subsidy signal should be handled by E-BL10"),
    "industry": ("sales-e-industry-radar", "Industry signal should be handled by E-BL11"),
    "case": ("sales-e-case-activation", "Case signal should be handled by E-BL12"),
    "a_snapshot": ("sales-e-customer-activation", "A-line snapshot activation should be handled by E-BL03"),
}


def load_json(path, raw):
    if raw:
        return json.loads(raw)
    return json.loads(Path(path).read_text(encoding="utf-8-sig")) if path else {}


def as_text(value):
    if value in (None, "", [], {}):
        return ""
    if isinstance(value, list):
        return " ".join(as_text(item) for item in value)
    if isinstance(value, dict):
        return json.dumps(value, ensure_ascii=False)
    return str(value)


def norm(value):
    return as_text(value).strip().lower().replace("-", "_").replace(" ", "_")


def digest(data):
    raw = json.dumps(data, ensure_ascii=False, sort_keys=True)
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:12].upper()


def add_route(routes, config, skill_name, reason, input_hint=None, confidence=0.9):
    registry = config.get("downstream_skills", {})
    meta = registry.get(skill_name, {})
    routes.append({
        "skill_name": skill_name,
        "skill_id": meta.get("skill_id", ""),
        "script": meta.get("script", ""),
        "purpose": meta.get("purpose", ""),
        "write_targets": meta.get("writes", []),
        "reason": reason,
        "confidence": confidence,
        "next_command": (
            f"cd sales-e-line/{skill_name}; "
            f"python scripts/{Path(meta.get('script', 'script.py')).name} "
            f"--input input.json --config references/e_line_config.json --dry-run"
        ) if meta.get("script") else "",
        "input_hint": input_hint or {},
    })


def has_any(data, fields):
    return any(data.get(field) not in (None, "", [], {}) for field in fields)


def route_pipeline(data, config):
    routes = []
    text = " ".join(norm(data.get(key)) for key in ("intent", "operation", "mode", "task_type", "signal_type", "source_signal_type"))
    add_route(routes, config, "sales-e-blacklight-task-register", "Full blacklight run starts from E01 task registry", {"required": ["e_task_id", "task_name", "task_type", "blacklight_type"]}, 0.75)
    if "policy" in text:
        add_route(routes, config, "sales-e-policy-radar", "Pipeline includes policy radar", {"required": ["e_task_id", "run_batch_id", "source_signal_ref", "recommendation_reason"]}, 0.75)
    elif "industry" in text:
        add_route(routes, config, "sales-e-industry-radar", "Pipeline includes industry radar", {"required": ["e_task_id", "run_batch_id", "source_signal_ref", "recommendation_reason"]}, 0.75)
    elif "news" in text:
        add_route(routes, config, "sales-e-news-radar", "Pipeline includes news radar", {"required": ["e_task_id", "run_batch_id", "source_signal_ref", "recommendation_reason"]}, 0.75)
    else:
        add_route(routes, config, "sales-e-opportunity-scan", "Pipeline includes generic opportunity scan", {"required": ["e_task_id", "run_batch_id", "source_signal_type", "source_signal_ref", "opportunity_type", "recommendation_reason"]}, 0.65)
    if data.get("need_dline_match") or "weapon" in text or "dline" in text:
        add_route(routes, config, "sales-e-dline-weapon-match", "Pipeline asks for D-line weapon matching", {"required": ["customer_id", "recommended_dline_skill_ids", "recommendation_reason"]}, 0.7)
    if data.get("write_to_b") or data.get("need_action_map") or "action_map" in text:
        add_route(routes, config, "sales-e-action-map-generate", "Pipeline asks for B-line action map output", {"required": ["customer_id", "target_sales_id", "recommended_action", "recommendation_reason"]}, 0.7)
    add_route(routes, config, "sales-e-run-state-update", "Pipeline should finish by updating E01 run state", {"required": ["e_task_id", "last_run_status"]}, 0.7)
    return routes


def choose_routes(data, config):
    routes = []
    candidates = []
    blocked = []
    text = " ".join(as_text(data.get(key)).lower() for key in ("intent", "operation", "mode", "task_type", "signal_type", "source_signal_type", "source_type", "target_table", "rule_table"))
    operation = norm(data.get("operation") or data.get("intent") or data.get("mode"))

    requested = norm(data.get("requested_skill") or data.get("skill_name"))
    registry = config.get("downstream_skills", {})
    if requested:
        skill_name = requested.replace("_", "-")
        if skill_name in registry:
            add_route(routes, config, skill_name, "User explicitly requested this downstream skill", confidence=1.0)
            return routes, candidates, blocked
        blocked.append(f"unknown requested_skill: {requested}")
        return routes, candidates, blocked

    if data.get("pipeline") or operation in {"full_run", "blacklight_run", "run_pipeline", "orchestrate"} or "full run" in text or "pipeline" in text:
        return route_pipeline(data, config), candidates, blocked

    rule_key = norm(data.get("rule_table") or data.get("target_table"))
    if rule_key in RULE_TABLE_ROUTES:
        skill_name, reason = RULE_TABLE_ROUTES[rule_key]
        hint = {"mode": "rule_config"}
        if "policy_activation" in rule_key or rule_key in {"e04.3", "e04_3"}:
            hint["mode"] = "policy_activation_rule"
        add_route(routes, config, skill_name, reason, hint, 0.98)
        return routes, candidates, blocked

    if has_any(data, ["last_run_status", "next_run_at", "last_run_at", "error_summary"]) or operation in {"run_state", "run_state_update"}:
        add_route(routes, config, "sales-e-run-state-update", "Run-state fields belong to E-BL16", {"required": ["e_task_id"]}, 0.95)
        return routes, candidates, blocked

    if has_any(data, ["adoption_feedback_status", "actual_action_taken", "customer_response_summary", "c_effect_ref", "final_effect_status", "non_adoption_reason"]) or "feedback" in text:
        add_route(routes, config, "sales-e-feedback-capture", "Feedback fields belong to E-BL06", {"required": ["e_output_id"]}, 0.95)
        return routes, candidates, blocked

    if has_any(data, ["b_action_map_id", "b_action_map_ref", "write_to_b_status", "source_b_record_ref"]) or "sync" in text:
        add_route(routes, config, "sales-e-bline-sync-status", "B-line sync fields belong to E-BL15", {"required": ["e_output_id"]}, 0.92)
        return routes, candidates, blocked

    if data.get("state_table") or has_any(data, ["global_factor_id", "sales_factor_id", "weapon_factor_id", "segment_factor_id", "current_weight"]):
        add_route(routes, config, "sales-e-influence-adjust", "E05 active factor fields belong to E-BL07", {"required": ["state_table"]}, 0.92)
        return routes, candidates, blocked

    if has_any(data, ["snapshot_id", "change_id", "week_start", "affected_factor_id"]) or operation in {"snapshot", "major_change", "change_log"}:
        add_route(routes, config, "sales-e-snapshot-log", "Snapshot/change-log fields belong to E-BL08", {}, 0.92)
        return routes, candidates, blocked

    if has_any(data, ["template_id", "template_ref", "output_schema_ref"]):
        add_route(routes, config, "sales-e-template-register", "Template fields belong to E-BL14", {"required": ["template_id", "template_name", "output_type", "target_receiver", "applicable_task_type"]}, 0.95)
        return routes, candidates, blocked

    if has_any(data, ["task_name", "blacklight_type", "scan_frequency"]) and has_any(data, ["e_task_id", "task_type"]):
        add_route(routes, config, "sales-e-blacklight-task-register", "Task registry fields belong to E-BL01", {"required": ["e_task_id", "task_name", "task_type", "blacklight_type"]}, 0.92)
        return routes, candidates, blocked

    if data.get("recommendations") or data.get("need_action_map") or (data.get("target_sales_id") and data.get("recommended_action")):
        add_route(routes, config, "sales-e-action-map-generate", "B-line action-map preparation belongs to E-BL05", {"required": ["customer_id", "target_sales_id", "recommended_action", "recommendation_reason"]}, 0.9)
        return routes, candidates, blocked

    if has_any(data, ["recommended_dline_skill_ids", "dline_skill_id", "source_d_weapon_ref"]) or "weapon" in text or "dline" in text:
        add_route(routes, config, "sales-e-dline-weapon-match", "D-line weapon recommendation belongs to E-BL04", {"required": ["customer_id", "recommended_dline_skill_ids", "recommendation_reason"]}, 0.9)
        return routes, candidates, blocked

    if has_any(data, ["silent_days_threshold", "last_interaction_type", "last_signal_type"]) or "silent" in text or "沉默" in text:
        add_route(routes, config, "sales-e-silent-customer-radar", "Silent customer activation belongs to E-BL13", {"required": ["customer_id", "source_a_snapshot_ref", "recommendation_reason"]}, 0.9)
        return routes, candidates, blocked

    if has_any(data, ["case_type", "source_case_pool_ref", "recommended_case_ids"]) or "case" in text or "案例" in text:
        add_route(routes, config, "sales-e-case-activation", "Case activation belongs to E-BL12", {"required": ["customer_id", "source_a_snapshot_ref", "source_signal_ref", "recommendation_reason"]}, 0.9)
        return routes, candidates, blocked

    signal_key = norm(data.get("signal_type") or data.get("source_signal_type") or data.get("source_type"))
    if signal_key in SIGNAL_ROUTES:
        skill_name, reason = SIGNAL_ROUTES[signal_key]
        add_route(routes, config, skill_name, reason, {"required": ["e_task_id", "run_batch_id", "source_signal_ref", "recommendation_reason"]}, 0.9)
        return routes, candidates, blocked

    if data.get("customer_id") and ("activation" in text or "激活" in text):
        add_route(routes, config, "sales-e-customer-activation", "Generic customer activation belongs to E-BL03", {"required": ["customer_id", "source_a_snapshot_ref", "recommendation_reason"]}, 0.78)
        return routes, candidates, blocked

    if has_any(data, ["source_signal_ref", "opportunity_type", "recommendation_reason"]):
        add_route(routes, config, "sales-e-opportunity-scan", "Generic external opportunity signal belongs to E-BL02", {"required": ["e_task_id", "run_batch_id", "source_signal_type", "source_signal_ref", "opportunity_type", "recommendation_reason"]}, 0.72)
        return routes, candidates, blocked

    for skill_name in ["sales-e-news-radar", "sales-e-policy-radar", "sales-e-industry-radar", "sales-e-opportunity-scan"]:
        add_route(candidates, config, skill_name, "Potential radar route; input lacks enough signal type detail", confidence=0.45)
    blocked.append("insufficient routing hints: provide signal_type, rule_table, operation, target_table, or key fields")
    return routes, candidates, blocked


def emit(status, key, routes=None, candidates=None, blocked=None, warnings=None):
    print(json.dumps({
        "status": status if status in OK_STATUSES else "error",
        "skill_id": SKILL_ID,
        "idempotency_key": key,
        "no_writes": True,
        "selected_routes": routes or [],
        "candidate_routes": candidates or [],
        "blocked_reasons": blocked or [],
        "warnings": warnings or [],
        "lark_cli_commands": [],
        "planned_writes": [],
    }, ensure_ascii=False, indent=2))


def main():
    parser = argparse.ArgumentParser(description="E-BL00 write-free router for E-line blacklight skills")
    parser.add_argument("--input")
    parser.add_argument("--config")
    parser.add_argument("--input-json")
    parser.add_argument("--config-json")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--execute", action="store_true")
    args = parser.parse_args()
    if args.dry_run and args.execute:
        emit("error", "", blocked=["choose only one of --dry-run or --execute"])
        return 2
    try:
        data = load_json(args.input, args.input_json)
        config = load_json(args.config, args.config_json)
        routes, candidates, blocked = choose_routes(data, config)
        warnings = []
        if args.execute:
            warnings.append("router execute is a no-op; downstream skills must be called separately")
        status = "pass" if routes and not blocked else ("needs_confirm" if candidates else "rejected")
        emit(status, f"{SKILL_ID}-{digest(data)}", routes, candidates, blocked, warnings)
        return 0 if status in {"pass", "needs_confirm"} else 1
    except Exception as exc:
        emit("error", "", blocked=[str(exc)])
        return 2


if __name__ == "__main__":
    raise SystemExit(main())

