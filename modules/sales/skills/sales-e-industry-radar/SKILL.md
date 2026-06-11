---
name: sales-e-industry-radar
description: Use when E-line blacklight industry scanning finds a vertical-market AI adoption opportunity that should become an E output record.
---

# E-BL11 Industry Radar

## Purpose
Use this skill for E-BL11: write industry opportunity records to `E01_output_records`.
In explicit `mode=rule_config`, it maintains `E02_3_industry_ai_opportunity_rule`.

## Required Workflow
1. Read `references/contract.md`.
2. Prepare input JSON with task, batch, source signal reference, and recommendation reason.
   For industry rule maintenance, set `mode` to `rule_config`.
3. Run `python scripts/e_bl11_industry_radar.py --input input.json --config references/e_line_config.json --dry-run`.
4. Execute only after dry-run is clean.

## Hard Rules
- Industry opportunities are candidate action signals only.
- Do not rewrite A-line segmentation or rating.
- Do not invent D-line materials.

## Script
``powershell
python scripts/e_bl11_industry_radar.py --input input.json --config references/e_line_config.json --dry-run
python scripts/e_bl11_industry_radar.py --input input.json --config references/e_line_config.json --execute
``

