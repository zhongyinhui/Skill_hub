---
name: sales-e-case-activation
description: Use when E-line blacklight case matching finds a customer activation opportunity based on an existing case or D-line proof asset.
---

# E-BL12 Case Activation

## Purpose
Use this skill for E-BL12: record case-based customer activation opportunities in `E01_output_records`.

## Required Workflow
1. Read `references/contract.md`.
2. Prepare input JSON with customer, A snapshot reference, case signal reference, and recommendation reason.
3. Run `python scripts/e_bl12_case_activation.py --input input.json --config references/e_line_config.json --dry-run`.
4. Execute only after dry-run is clean.

## Hard Rules
- Case activation points to existing proof; it does not generate case assets.
- Do not treat case match as customer confirmation.
- Do not write A-line formal fields.

## Script
```powershell
python scripts/e_bl12_case_activation.py --input input.json --config references/e_line_config.json --dry-run
python scripts/e_bl12_case_activation.py --input input.json --config references/e_line_config.json --execute
```
