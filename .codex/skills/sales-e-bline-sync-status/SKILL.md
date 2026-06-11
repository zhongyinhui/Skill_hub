---
name: sales-e-bline-sync-status
description: Use when E-line output rows need B-line action-map sync status, B-line refs, or sync errors written back.
---

# E-BL15 B-Line Sync Status

## Purpose
Use this skill for E-BL15: update B-line sync fields on an existing E output row.

## Required Workflow
1. Read `references/contract.md`.
2. Prepare input JSON with `e_output_id` and at least one sync field.
3. Run `python scripts/e_bl15_bline_sync_status.py --input input.json --config references/e_line_config.json --dry-run`.
4. Execute only after confirming the E output row is the intended target.

## Hard Rules
- Update E01.2 sync status only.
- Do not create B-line records here.
- Do not write customer facts or effectiveness feedback.

## Script
``powershell
python scripts/e_bl15_bline_sync_status.py --input input.json --config references/e_line_config.json --dry-run
python scripts/e_bl15_bline_sync_status.py --input input.json --config references/e_line_config.json --execute
``

