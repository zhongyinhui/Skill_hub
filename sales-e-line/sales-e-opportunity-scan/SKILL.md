---
name: sales-e-opportunity-scan
description: Use when E-line blacklight scanning finds external news, policy, industry, or source signals that must become E01.2 opportunity output records.
---

# E-BL02 Opportunity Scan

## Purpose
Use this skill for E-BL02: convert a scanned external signal into an E-line opportunity or recommendation row in `E01_output_records`.
E02 rule config tables are maintained by the specialized radar skills: E09 for news sources, E10 for policy scan rules, and E11 for industry opportunity rules.

## Required Workflow
1. Read `references/contract.md`.
2. Prepare input JSON with task, batch, source signal, opportunity type, and recommendation reason.
3. Run `python scripts/e_bl02_opportunity_scan.py --input input.json --config references/e_line_config.json --dry-run`.
4. Execute only when the dry-run is clean.

## Hard Rules
- E-BL02 records opportunity signals; it does not write A-line formal facts.
- It may reference A/B/C/D records but must not mutate them.
- Repeated execution with the same `e_output_id` updates the same E01.2 row.

## Script
```powershell
python scripts/e_bl02_opportunity_scan.py --input input.json --config references/e_line_config.json --dry-run
python scripts/e_bl02_opportunity_scan.py --input input.json --config references/e_line_config.json --execute
```
