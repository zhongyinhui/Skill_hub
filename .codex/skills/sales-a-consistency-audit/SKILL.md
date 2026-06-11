---
name: sales-a-consistency-audit
description: Use when A-line customer files, aliases, source index, or per-customer ledger refs need read-only consistency checking.
---

# A-SK11 Consistency Audit

## Purpose
Use this skill for A-SK11: perform a read-only audit across A-line customer profile, alias, `source_id_mapping`, `03_销售待接收线索池`, and customer ledger references.

## Required Workflow
1. Read `references/contract.md`.
2. Provide `customer_id`, `source_id`, or both.
3. Run `python scripts/a_sk11_consistency_audit.py --input input.json --config references/a_line_config.json --dry-run`.
4. Execute to read Feishu tables and return audit findings.
5. Pass confirmed repair decisions to A-SK12; this skill must not repair anything itself.

## Hard Rules
- This skill is read-only.
- `planned_writes` must always be empty.
- Do not create, update, delete, or upload attachments.
- Findings are diagnostic; repairs require A-SK12 with human confirmation.
- Lead pool lookup is by `source_map_id`; `source_id` belongs to `source_id_mapping`.

## Script
``powershell
python scripts/a_sk11_consistency_audit.py --input input.json --config references/a_line_config.json --dry-run
python scripts/a_sk11_consistency_audit.py --input input.json --config references/a_line_config.json --execute
``

