---
name: sales-a-lead-ingest
description: Use when a raw A-line source lead must be captured before customer binding, dedupe, or formal ledger entry.
---

# A-SK01 Lead Ingest

## Purpose
Use this skill for A-SK01: capture a raw source lead into the A-line lead pool and optional source index before it is bound to a formal `customer_id`.

## Required Workflow
1. Read `references/contract.md`.
2. Confirm the input is a raw lead/source event, not a validated customer fact.
3. Run `python scripts/a_sk01_lead_ingest.py --input input.json --config references/a_line_config.json --dry-run`.
4. Review planned writes to `03_销售待接收线索池` and `source_id_mapping`.
5. Execute only when source ownership and raw identity fields are acceptable.

## Hard Rules
- This skill never creates a formal customer record.
- This skill never writes customer ledger facts or attachments.
- If `linked_customer_id` is known, use A-SK02/A-SK04 instead of treating it as raw intake.
- The lead pool links to source mapping through `source_map_id`; do not assume the lead pool has a writable `source_id` field.
- Do not add fields, options, or model-internal scoring values.

## Script
``powershell
python scripts/a_sk01_lead_ingest.py --input input.json --config references/a_line_config.json --dry-run
python scripts/a_sk01_lead_ingest.py --input input.json --config references/a_line_config.json --execute
``

