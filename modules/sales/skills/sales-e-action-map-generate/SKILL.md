---
name: sales-e-action-map-generate
description: Use when E-line blacklight recommendations must be assembled into next-day B-line action-map output records.
---

# E-BL05 Action Map Generate

## Purpose
Use this skill for E-BL05: generate next-day action-map output rows in E01.2 for B-line execution.

## Required Workflow
1. Read `references/contract.md`.
2. Prepare one recommendation or a `recommendations` list.
3. Run `python scripts/e_bl05_action_map_generate.py --input input.json --config references/e_line_config.json --dry-run`.
4. Execute only after confirming the rows are recommendations for B-line, not direct customer-fact writes.

## Hard Rules
- E-BL05 prepares B-line action map records; it does not execute the sales action.
- Do not mark customer response, C-line effect, or adoption status before feedback exists.
- Re-run should reuse the same `e_output_id`.

## Script
``powershell
python scripts/e_bl05_action_map_generate.py --input input.json --config references/e_line_config.json --dry-run
python scripts/e_bl05_action_map_generate.py --input input.json --config references/e_line_config.json --execute
``

