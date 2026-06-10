---
name: sales-e-run-state-update
description: Use when E-line blacklight task run state, last-run status, next-run time, or batch error summary must be written to E01.
---

# E-BL16 Run State Update

## Purpose
Use this skill for E-BL16: update run state fields on E-line blacklight tasks in `E01_task_registry`.

## Required Workflow
1. Read `references/contract.md`.
2. Prepare input JSON with `e_task_id` and at least one run-state field.
3. Run `python scripts/e_bl16_run_state_update.py --input input.json --config references/e_line_config.json --dry-run`.
4. Execute only after dry-run is clean.

## Hard Rules
- Update task run metadata only.
- Do not change task type or field schema.
- Do not write output recommendations here.

## Script
```powershell
python scripts/e_bl16_run_state_update.py --input input.json --config references/e_line_config.json --dry-run
python scripts/e_bl16_run_state_update.py --input input.json --config references/e_line_config.json --execute
```
