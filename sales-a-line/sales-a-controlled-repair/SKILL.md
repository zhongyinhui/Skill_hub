---
name: sales-a-controlled-repair
description: Use when A-line audit findings need confirmed repair, backfill, or reference maintenance without changing existing skill behavior.
---

# A-SK12 Controlled Repair

## Purpose
Use this skill for A-SK12: apply confirmed A-line maintenance repairs after A-SK11 or manual review identifies a specific consistency issue.

## Required Workflow
1. Read `references/contract.md`.
2. Confirm every repair action has `type`, required identifiers, and a human confirmation.
3. Run `python scripts/a_sk12_controlled_repair.py --input input.json --config references/a_line_config.json --dry-run`.
4. Review planned writes and skipped actions.
5. Execute only when the repair is explicit and reversible by audit trail.

## Hard Rules
- This skill cannot delete records.
- This skill cannot merge customers.
- This skill cannot write ledger facts or attach evidence/artifacts/handoffs.
- This skill only repairs indexes, customer refs, and maintenance timestamps from an allowlist.

## Script
```powershell
python scripts/a_sk12_controlled_repair.py --input input.json --config references/a_line_config.json --dry-run
python scripts/a_sk12_controlled_repair.py --input input.json --config references/a_line_config.json --execute
```
