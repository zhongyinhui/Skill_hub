---
name: sales-e-blacklight-task-register
description: Use when an E-line blacklight task must be registered, validated, enabled, disabled, or checked against the E01 task registry.
---

# E-BL01 Blacklight Task Register

## Purpose
Use this skill for E-BL01: maintain one row per E-line blacklight task in `E01_task_registry`. E-line tasks are night, periodic, feedback, or event-triggered radar tasks, not daytime sales co-pilot actions.

## Required Workflow
1. Read `references/contract.md`.
2. Prepare input JSON with `e_task_id`, `task_name`, `task_type`, and `blacklight_type`.
3. Run `python scripts/e_bl01_task_registry.py --input input.json --config references/e_line_config.json --dry-run`.
4. Review `planned_writes`, `blocked_reasons`, and the previewed `lark-cli` command.
5. Use `--execute` only after dry-run is clean.

## Hard Rules
- Do not create new fields or select options.
- Do not write A-line customer facts or D-line weapon artifacts.
- One `e_task_id` maps to one task row.
- `task_type`, `blacklight_type`, `target_customer_scope`, `write_to_target`, and `output_type` must match configured E-line options.

## Script
``powershell
python scripts/e_bl01_task_registry.py --input input.json --config references/e_line_config.json --dry-run
python scripts/e_bl01_task_registry.py --input input.json --config references/e_line_config.json --execute
``

