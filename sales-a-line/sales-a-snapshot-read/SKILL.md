---
name: sales-a-snapshot-read
description: Use when B-line, C-line, or E-line work needs a read-only A-line customer snapshot by customer_id.
---

# A-SK10 Snapshot Read

## Purpose
Use this skill for A-SK10: read the current A-line customer snapshot for downstream B/C/E work. It is read-only and must not mutate any table.

## Required Workflow
1. Read `references/contract.md`.
2. Verify the A03 field snapshot.
3. Run `python scripts/a_sk10_snapshot_read.py --input input.json --config a_line_config.json --dry-run` to preview the read command.
4. Run with `--execute` only when an actual lark-cli read command template is configured.

## Hard Rules
- No writes. `planned_writes` must always be empty.
- Return snapshot fields, not the full historical ledger by default.
- Do not infer missing snapshot fields by inventing data.
- If the customer cannot be found, return an error or empty result, not a fabricated snapshot.

## Script
```powershell
python scripts/a_sk10_snapshot_read.py --input input.json --config a_line_config.json --dry-run
python scripts/a_sk10_snapshot_read.py --input input.json --config a_line_config.json --execute
```
