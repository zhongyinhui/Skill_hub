---
name: sales-e-silent-customer-radar
description: Use when E-line blacklight detects a silent, stalled, or long-uncontacted customer that should become a B-line activation recommendation.
---

# E-BL13 Silent Customer Radar

## Purpose
Use this skill for E-BL13: record silent-customer activation opportunities in `E01_output_records`.

## Required Workflow
1. Read `references/contract.md`.
2. Prepare input JSON with customer, A snapshot reference, and recommendation reason.
3. Run `python scripts/e_bl13_silent_customer_radar.py --input input.json --config references/e_line_config.json --dry-run`.
4. Execute only after dry-run is clean.

## Hard Rules
- Silent-customer detection is a prompt for B-line action.
- Do not mark the customer as active or responsive.
- Do not write formal A-line stage or rating.

## Script
```powershell
python scripts/e_bl13_silent_customer_radar.py --input input.json --config references/e_line_config.json --dry-run
python scripts/e_bl13_silent_customer_radar.py --input input.json --config references/e_line_config.json --execute
```
