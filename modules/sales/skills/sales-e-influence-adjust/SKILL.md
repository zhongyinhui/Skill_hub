---
name: sales-e-influence-adjust
description: Use when E-line feedback must update active E05 influence-factor state for global, sales, weapon, or customer segment weights.
---

# E-BL07 Influence Adjust

## Purpose
Use this skill for E-BL07: update active E05 influence state after B/C/D feedback is available.

## Required Workflow
1. Read `references/contract.md`.
2. Choose `state_table`: `global`, `sales`, `weapon`, or `segment`.
3. Run `python scripts/e_bl07_influence_adjust.py --input input.json --config references/e_line_config.json --dry-run`.
4. Execute only after checking the affected factor and weight change.

## Hard Rules
- E05 active state may be updated, but history must be preserved through E-BL08 when changes are material.
- Major changes require human confirmation before active-state update.
- Do not change A-line customer facts or D-line artifacts.

## Script
``powershell
python scripts/e_bl07_influence_adjust.py --input input.json --config references/e_line_config.json --dry-run
python scripts/e_bl07_influence_adjust.py --input input.json --config references/e_line_config.json --execute
``

