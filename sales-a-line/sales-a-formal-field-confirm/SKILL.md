---
name: sales-a-formal-field-confirm
description: Use when A-line customer status, rating, follow-up, or other formal profile fields have human confirmation and must be written back.
---

# A-SK07 Formal Field Confirm

## Purpose
Use this skill for A-SK07: write confirmed formal customer profile fields after a human approval step. It is the gate between model suggestions and official A-line customer fields.

## Required Workflow
1. Read `references/contract.md`.
2. Confirm the caller provides `customer_id`, `field_updates`, `confirm_status`, and `confirmed_by`.
3. Run `python scripts/a_sk07_formal_field_confirm.py --input input.json --config references/a_line_config.json --dry-run`.
4. Review the exact official fields to be changed.
5. Execute only after confirmation is explicit.

## Hard Rules
- Unconfirmed suggestions return `needs_confirm`.
- Only fields in the formal write allowlist may be written.
- This skill does not append ledger facts and does not upload evidence/artifact/handoff attachments.
- Do not write AI-internal scoring variables.

## Script
```powershell
python scripts/a_sk07_formal_field_confirm.py --input input.json --config references/a_line_config.json --dry-run
python scripts/a_sk07_formal_field_confirm.py --input input.json --config references/a_line_config.json --execute
```
