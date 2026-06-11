# A-SK11 Contract

## Scope
Read-only consistency checks across A-line customer profile, alias table, source index, lead pool, and per-customer ledger references.

## Table Alignment
- `All_customer_files｜A线全部客户档案表` is the global customer profile table.
- `customer_alias_mapping` is the customer alias table.
- `source_id_mapping` is the source-to-customer mapping table and owns `source_id`.
- `03_销售待接收线索池` is the raw lead and sales acceptance table and links by `source_map_id`, not `source_id`.
- Individual customer ledgers are one Base per customer, referenced from the global customer profile table.

## Inputs
Required:
- `customer_id` or `source_id`

Optional:
- `source_map_id`
- `include_aliases` defaults to true
- `include_lead_pool` defaults to true when `source_map_id` is available
- `include_index` defaults to true
- `include_customer_profile` defaults to true when `customer_id` is provided

## Reads
- `A03_all_customer_files` by `customer_id`
- `A01_customer_alias` by `customer_id`
- `A06_a_line_index` by `linked_customer_id` or `source_id`
- `03_销售待接收线索池` by `source_map_id`

## Writes
None. `planned_writes` must stay empty.

## Findings
The script can report:
- missing customer profile
- duplicate customer profile
- missing source index
- missing alias records
- missing or partial per-customer ledger refs
- lead pool record not found for `source_id`

## Blocks
Return `rejected` when neither `customer_id` nor `source_id` is provided, or when a required read field is missing from config.
