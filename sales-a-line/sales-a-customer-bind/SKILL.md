---
name: sales-a-customer-bind
description: Use when an A-line sales lead has been accepted or confirmed and must be bound to an existing customer_id or converted into a new formal customer record.
---

# A-SK02 Customer Bind

## Purpose
Use this skill for A-SK02: after a salesperson or manager confirms a lead, bind it to an existing `customer_id` or create a new `customer_id`. A-line keeps the formal customer memory; it does not decide ownership disputes by itself.

## Required Workflow
1. Read `references/contract.md` before running the script.
2. Verify the current Feishu/Base fields from the live table or the supplied config.
3. Prepare an input JSON with the confirmed lead, selected customer if any, and sales owner.
4. Run `python scripts/a_sk02_customer_bind.py --input input.json --config a_line_config.json --dry-run`.
5. Review `blocked_reasons`, `planned_writes`, and `lark_cli_commands`.
6. If dry-run shows `auto_customer_container_planned=true`, confirm the generated title is the expected `{customer_id}/` under `01_客户账本/`.
7. Run with `--execute` only after the dry-run is clean and the human confirmation is present. Execution copies the clean ledger template when configured, waits for the copied Base to become readable, and removes blank default records.

## Hard Rules
- `customer_id` is the customer mainline. `current_sales_id` is only the current operator.
- Do not auto-accept or auto-reject a lead. `sales_accept_status` or equivalent confirmation must already be confirmed.
- If duplicate candidates exist and no chosen `customer_id` is confirmed, return `needs_confirm`.
- Do not create new fields, new select options, or model-only score fields.
- When creating a new formal customer without per-customer refs, create or reuse exactly one customer ledger bitable under `01_客户账本/` and bind its refs into the customer record.
- Customer ledger table setup is allowed only inside the newly created/reused customer-specific bitable; never modify existing A-line master table fields.
- Prefer the configured clean ledger template over field-by-field table construction.
- Delete only truly blank default records; never delete rows with any `customer_id` or attachment content.
- Do not write `customer_rating` or `current_stage` from AI suggestions.

## Script
Run:

```powershell
python scripts/a_sk02_customer_bind.py --input input.json --config a_line_config.json --dry-run
python scripts/a_sk02_customer_bind.py --input input.json --config a_line_config.json --execute
```

The script is self-contained and does not import code from other A-line skills.
