# A-SK06 Contract

## Scope
Append one validated fact block to the customer's own individual table/container. The all-customer table is only the index/current-state table.

## Inputs
Required:
- `validated_by_a_sk05`
- `customer_id`
- `sales_id`
- `effective_events_summary`
- `confirm_status`
- `evidence_ids`

Optional:
- `work_date`
- `ledger_record_time`, `record_time`, `event_time`, `created_at`, or `event_date`
- `source_session_ids`
- `individual_customer_table` with `base_token` and `table_id`
- or `individual_customer_base_token` and `individual_customer_table_id`
- or a per-customer `/base/...?...table=tbl...` URL
- `stage_before`, `stage_after`
- `need_delta`, `objection_delta`, `buying_signal_delta`
- `risk_flags`
- `artifact_ids`
- `snapshot_update_required`

## Writes
- `A99_individual_customer_container`: dynamic target resolved from this customer's own refs; write/update one row keyed by `customer_id` + stable ledger record time; attach the full ledger block JSON to attachment field `ledger`
- Re-execution with the same `customer_id` + ledger record time reuses the same row and skips upload when `ledger` already has an attachment.
- The sample `CUST-2026-000001` table is a schema example only and is refused as a default write target.

## Blocks
Return `rejected` when A-SK05 validation is absent, evidence is missing, confirmation is missing, idempotency key already exists, or target fields do not exist.
Return `needs_confirm` when the package is valid but the per-customer ledger target is missing.

