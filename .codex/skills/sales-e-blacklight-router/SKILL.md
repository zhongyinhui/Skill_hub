---
name: sales-e-blacklight-router
description: Use when an E-line blacklight request, signal, rule update, feedback event, or run-state event must be routed to the correct downstream E-line skill without writing Feishu.
---

# E-BL00 Blacklight Router

## Purpose
Use this skill as the E-line entry point. It classifies the request and returns the downstream skill to call next. It never writes Feishu and never calls `lark-cli`.

## Required Workflow
1. Read `references/contract.md` when the routing boundary is unclear.
2. Prepare input JSON with any available intent fields such as `operation`, `mode`, `signal_type`, `rule_table`, `target_table`, `task_type`, `customer_id`, or feedback/status fields.
3. Run `python scripts/e_bl00_blacklight_router.py --input input.json --config references/router_config.json --dry-run`.
4. Use the returned `selected_routes` to call the suggested downstream skill with that skill's own dry-run first.

## Hard Rules
- Do not write Feishu from this router.
- Do not call downstream scripts automatically.
- Do not infer confirmed customer facts.
- If multiple downstream skills may fit, return `needs_confirm` with candidates.
- If the input asks for a full automated blacklight run, return a pipeline plan only; execution is still handled by the downstream skills.

## Script
``powershell
python scripts/e_bl00_blacklight_router.py --input input.json --config references/router_config.json --dry-run
``

The script also accepts `--execute` for interface consistency, but execution remains a no-op and produces no writes.

