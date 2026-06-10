---
name: sales-a-ledger-append
description: Use when a validated B-line package must be appended as an immutable A-line customer fact ledger block.
---

# A-SK06 Ledger Append

## Purpose
Use this skill for A-SK06: append a validated A-line fact block to the individual customer ledger. Ledger append is additive and idempotent; it never overwrites old facts.

## Required Workflow
1. Read `references/contract.md`.
2. Confirm A-SK05 validation has passed.
3. Run `python scripts/a_sk06_ledger_append.py --input input.json --config a_line_config.json --dry-run`.
4. Check idempotency and planned A02 write.
5. Execute only after dry-run is clean.

## Hard Rules
- Never append unvalidated B-line content.
- Missing evidence or unconfirmed package blocks formal entry.
- One validated B-line package maps to one customer ledger row, keyed by `customer_id` + stable ledger record time.
- Repeated execution must update the same row and skip an existing `ledger` attachment instead of duplicating it.
- Do not overwrite, merge, delete, freeze, or reclassify old customer facts.
- Do not write formal `current_stage` or `customer_rating`.

## Script
```powershell
python scripts/a_sk06_ledger_append.py --input input.json --config a_line_config.json --dry-run
python scripts/a_sk06_ledger_append.py --input input.json --config a_line_config.json --execute
```
