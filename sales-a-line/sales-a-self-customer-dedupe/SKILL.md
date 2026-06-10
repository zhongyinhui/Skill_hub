---
name: sales-a-self-customer-dedupe
description: Use when a salesperson reports a self-developed or no-source customer and A-line must dedupe candidates before creating a formal customer record.
---

# A-SK03 Self Customer Dedupe

## Purpose
Use this skill for A-SK03: process a no-source customer, check duplicate candidates, and create a formal A-line customer only when conflict is absent or human-confirmed.

## Required Workflow
1. Read `references/contract.md`.
2. Verify live fields or load the supplied config field snapshot.
3. Run `python scripts/a_sk03_self_customer_dedupe.py --input input.json --config a_line_config.json --dry-run`.
4. If the output is `needs_confirm`, ask the salesperson or manager to confirm candidate resolution.
5. If dry-run shows `auto_customer_container_planned=true`, confirm the generated title is the expected `{customer_id}/` under `01_客户账本/`.
6. Use `--execute` only after confirmation and a clean dry-run. Execution copies the clean ledger template when configured, waits for the copied Base to become readable, and removes blank default records.

## Hard Rules
- A-line does not guess that two customers are the same.
- If duplicate candidates exist, no new formal customer is created until conflict handling is confirmed.
- Do not write AI-only scores or unconfirmed stage/rating fields.
- `customer_id` is the mainline; sales ownership is stored as `current_sales_id`.
- When creating a new formal customer without per-customer refs, create or reuse exactly one customer ledger bitable under `01_客户账本/` and bind its refs into the customer record.
- Customer ledger table setup is allowed only inside the newly created/reused customer-specific bitable; never modify existing A-line master table fields.
- Prefer the configured clean ledger template over field-by-field table construction.
- Delete only truly blank default records; never delete rows with any `customer_id` or attachment content.

## Script
```powershell
python scripts/a_sk03_self_customer_dedupe.py --input input.json --config a_line_config.json --dry-run
python scripts/a_sk03_self_customer_dedupe.py --input input.json --config a_line_config.json --execute
```
