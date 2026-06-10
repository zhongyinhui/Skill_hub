---
name: sales-e-news-radar
description: Use when E-line blacklight news scanning finds an AI, market, competitor, or customer-relevant news signal that should become an E output record.
---

# E-BL09 News Radar

## Purpose
Use this skill for E-BL09: write news-triggered opportunity records to `E01_output_records`.

## Required Workflow
1. Read `references/contract.md`.
2. Prepare input JSON with task, batch, source signal reference, and recommendation reason.
3. Run `python scripts/e_bl09_news_radar.py --input input.json --config references/e_line_config.json --dry-run`.
4. Execute only after dry-run is clean.

## Hard Rules
- News signals are opportunity suggestions only.
- Do not write A-line formal customer facts.
- Do not create D-line weapons.
- Re-run with the same `e_output_id` must update the same E output row.

## Script
```powershell
python scripts/e_bl09_news_radar.py --input input.json --config references/e_line_config.json --dry-run
python scripts/e_bl09_news_radar.py --input input.json --config references/e_line_config.json --execute
```
