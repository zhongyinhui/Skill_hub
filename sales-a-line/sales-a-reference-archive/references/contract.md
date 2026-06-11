# A-SK08 Contract

## Scope
Attach references to existing customer facts and snapshot index fields in the customer's own individual table/container.

## Inputs
Required:
- `customer_id`
- at least one of `ledger_block_id`, `evidence_ids`, `artifact_ids`, `handoff_ids`

Optional:
- `evidence_ids`
- `artifact_ids`
- `handoff_ids`
- `ledger_record_time`, `record_time`, `event_time`, `created_at`, `event_date`, or `work_date`
- `individual_customer_table` with `base_token` and `table_id`
- or `individual_customer_base_token` and `individual_customer_table_id`
- or a per-customer `/base/...?...table=tbl...` URL
- `reference_confirm_status`
- `sent_confirm_status`

## Writes
- `A99_individual_customer_container`: dynamic target resolved from this customer's own refs; update the row keyed by `customer_id` + stable ledger record time; attach JSON references to `evidence_ref`, `artifacts_ref`, and `handoff_ref` when provided
- A-SK08 never uploads `ledger`; that field is owned by A-SK06.
- Re-execution skips an attachment field that already has content.
- `A03_all_customer_files`: `customer_id`, `updated_at`

## Blocks
Return `rejected` when no references are provided, required fields are missing, or a planned field does not exist.
Return `needs_confirm` when references are valid but the per-customer reference target is missing.
Do not write `sent_to_customer` even when the input contains it.
