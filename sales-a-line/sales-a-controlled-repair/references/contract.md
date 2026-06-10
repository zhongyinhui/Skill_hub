# A-SK12 Contract

## Scope
Apply confirmed, narrow A-line repairs and backfills after A-SK11 or manual audit.

## Table Alignment
- `All_customer_files｜A线全部客户档案表` stores formal customer profile refs and maintenance timestamps.
- `source_id_mapping` stores `source_id` and the source-to-customer mapping.
- `05_A线运行日志` stores repair audit records. This table name is not the same thing as A-SK07.
- `03_销售待接收线索池` links to `source_id_mapping` through `source_map_id`; A-SK12 does not repair lead pool contents in this version.

## Inputs
Required:
- `repair_actions`
- `confirm_status`
- `confirmed_by`

Optional:
- `audit_id`
- `repair_reason`
- `idempotency_key`

## Supported Actions
- `backfill_index`: requires `source_id` and `customer_id`; writes `A06_a_line_index`
- `backfill_customer_refs`: requires `customer_id` and one or more customer ledger ref fields; writes `A03_all_customer_files`
- `refresh_updated_at`: requires `customer_id`; writes `A03_all_customer_files.updated_at`

## Writes
- `source_id_mapping` for source/customer mapping repairs
- `All_customer_files｜A线全部客户档案表` for customer ledger ref backfill or maintenance timestamp
- `05_A线运行日志` for repair audit trail

## Blocks
Return `needs_confirm` when confirmation is absent.
Return `rejected` for unsupported actions, missing action identifiers, prohibited fields, deletion/merge requests, or field snapshot mismatches.
