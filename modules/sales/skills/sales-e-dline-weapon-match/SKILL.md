---
name: sales-e-dline-weapon-match
description: Use when E-line blacklight matching must recommend existing D-line weapons or skill IDs for a customer opportunity.
---

# E-BL04 D-Line Weapon Match

## Purpose
Use this skill for E-BL04: write D-line weapon recommendations to E01.2 from E03 mapping rules and current D-line weapon state.
E03 mapping sources are read-only docs: `value_point_to_dline_skill_map.json` and `customer_stage_to_weapon_map.json`.

## Required Workflow
1. Read `references/contract.md`.
2. Prepare input JSON with `customer_id`, `recommended_dline_skill_ids`, and `recommendation_reason`.
3. Run `python scripts/e_bl04_dline_weapon_match.py --input input.json --config references/e_line_config.json --dry-run`.
4. Execute only when the recommendation references existing D-line weapons.

## Hard Rules
- Recommend existing D-line skills only.
- Do not generate, archive, or modify D-line weapon artifacts.
- Do not write customer stage or customer rating into A-line tables.

## Script
``powershell
python scripts/e_bl04_dline_weapon_match.py --input input.json --config references/e_line_config.json --dry-run
python scripts/e_bl04_dline_weapon_match.py --input input.json --config references/e_line_config.json --execute
``

