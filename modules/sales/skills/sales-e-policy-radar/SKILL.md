---
name: sales-e-policy-radar
description: Use when E-line blacklight policy scanning finds a regional, industry, subsidy, compliance, or government signal that should become an E output record.
---

# E-BL10 Policy Radar

## Purpose
Use this skill for E-BL10: write policy-triggered opportunity records to `E01_output_records`.
In explicit `mode=rule_config`, it maintains `E02_2_policy_scan_rule`; with `mode=policy_activation_rule`, it maintains `E04_3_policy_activation_rule`.

## Required Workflow
1. Read `references/contract.md`.
2. Prepare input JSON with task, batch, source signal reference, and recommendation reason.
   For policy rule maintenance, set `mode` to `rule_config`, `scan_rule`, or `policy_activation_rule`.
3. Run `python scripts/e_bl10_policy_radar.py --input input.json --config references/e_line_config.json --dry-run`.
4. Execute only after dry-run is clean.

## Hard Rules
- Policy output is a recommendation for B-line action.
- Do not mark the customer as confirmed or advanced.
- Do not write A-line formal facts.

## Script
``powershell
python scripts/e_bl10_policy_radar.py --input input.json --config references/e_line_config.json --dry-run
python scripts/e_bl10_policy_radar.py --input input.json --config references/e_line_config.json --execute
``

