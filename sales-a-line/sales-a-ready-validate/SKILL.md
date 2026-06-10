---
name: sales-a-ready-validate
description: Use when a B-line a_ready_package must be checked before any facts are allowed to enter the formal A-line customer ledger.
---

# A-SK05 Ready Validate

## Purpose
Use this skill for A-SK05: validate B-line `a_ready_package` before any A-line formal entry. This skill decides whether the package is pass, needs confirmation, rejected, or executable for logging.

## Required Workflow
1. Read `references/contract.md`.
2. Confirm the B-line package contains structured facts, evidence, and confirmation status.
3. Run `python scripts/a_sk05_ready_validate.py --input input.json --config a_line_config.json --dry-run`.
4. If clean, pass the validated package to A-SK06.
5. Execute only to write validation/audit logs, not to append formal ledger facts.

## Hard Rules
- Empty package means no A-line entry.
- Missing evidence means no formal fact.
- `human_confirm_required=true` with unconfirmed `confirm_status` means no formal fact.
- This skill does not write A02 customer ledger facts; A-SK06 does that after validation.

## Script
```powershell
python scripts/a_sk05_ready_validate.py --input input.json --config a_line_config.json --dry-run
python scripts/a_sk05_ready_validate.py --input input.json --config a_line_config.json --execute
```
