---
name: sales-e-feedback-capture
description: Use when B-line adoption, customer response, C-line effect, or D-line feedback must be written back to E01.2 output records.
---

# E-BL06 Feedback Capture

## Purpose
Use this skill for E-BL06: collect B/C/D feedback into the original E01.2 output row so E05 can learn from adoption and effect.

## Required Workflow
1. Read `references/contract.md`.
2. Prepare input JSON with `e_output_id` and at least one feedback field.
3. Run `python scripts/e_bl06_feedback_capture.py --input input.json --config references/e_line_config.json --dry-run`.
4. Execute only after confirming the feedback refers to the correct E output row.

## Hard Rules
- Feedback updates E01.2 only.
- Do not infer effectiveness without C-line evidence.
- Do not alter the original opportunity reason except through explicit feedback fields.

## Script
``powershell
python scripts/e_bl06_feedback_capture.py --input input.json --config references/e_line_config.json --dry-run
python scripts/e_bl06_feedback_capture.py --input input.json --config references/e_line_config.json --execute
``

