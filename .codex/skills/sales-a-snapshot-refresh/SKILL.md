---
name: sales-a-snapshot-refresh
description: Use when A-line must refresh latest_snapshot_text or latest_snapshot_json after validated customer ledger changes.
---

# A-SK09 Snapshot Refresh

## Purpose
Use this skill for A-SK09: refresh the A-line customer snapshot after validated ledger updates. It can summarize the current state, but it cannot silently change formal stage or rating.

## Required Workflow
1. Read `references/contract.md`.
2. Load the previous snapshot and latest validated ledger blocks.
3. Run `python scripts/a_sk09_snapshot_refresh.py --input input.json --config a_line_config.json --dry-run`.
4. Review omitted formal fields, pending confirmations, and whether `individual_latest_snapshot_attachment_ready` is true.
5. Execute only after dry-run is clean.

## Hard Rules
- `latest_snapshot_text` and `latest_snapshot_json` may be refreshed.
- Every formal ledger update must refresh the latest snapshot.
- If a customer-specific ledger table is bound, archive `latest_snapshot_json` to the same customer ledger row for `customer_id` + ledger record time.
- Repeated execution must update the same row and skip an existing `latest_snapshot` attachment instead of duplicating it.
- `current_stage` and `customer_rating` require explicit human confirmation before formal write-back.
- Suggested stage/rating must stay in snapshot JSON or reason fields when unconfirmed.
- Never write the sample `CUST-2026-000001/` table.
- Do not write AI-internal scoring fields.

## Script
``powershell
python scripts/a_sk09_snapshot_refresh.py --input input.json --config a_line_config.json --dry-run
python scripts/a_sk09_snapshot_refresh.py --input input.json --config a_line_config.json --execute
``

