# A-SK09 Contract

## Scope
Refresh the latest customer snapshot in `A03_all_customer_files`.

## Inputs
Required:
- `customer_id`
- `latest_snapshot_text` or enough `latest_ledger_blocks` to generate one

Optional:
- `latest_snapshot_json`
- `ledger_record_time`, `record_time`, `event_time`, `created_at`, `event_date`, or `work_date`
- `core_needs`
- `current_objections`
- `buying_signals`
- `risk_flags`
- `individual_customer_base_token`
- `individual_customer_table_id`
- `latest_snapshot_table_ref`
- `individual_customer_table_url`
- `stage_suggestion`
- `stage_confirm_status`
- `rating_suggestion`
- `rating_confirm_status`

## Writes
- `A03_all_customer_files`: `customer_id`, `latest_snapshot_text`, `latest_snapshot_json`, `core_needs`, `current_objections`, `buying_signals`, `current_stage`, `customer_rating`, `updated_at`
- If a per-customer table target is present: update the row keyed by `customer_id` + stable ledger record time and upload `LATEST-SNAPSHOT-{customer_id}.json` to `latest_snapshot`.
- Re-execution skips upload when `latest_snapshot` already has an attachment.

## Blocks
Return `rejected` for missing customer/snapshot data or missing target fields.
Unconfirmed stage/rating are omitted from formal fields and reported in `result_refs.pending_confirmations`.
If the per-customer latest snapshot attachment target is missing, the skill still updates the all-customer current-state fields and reports the missing container refs in `result_refs`.
The sample `CUST-2026-000001/` table must never be used as the write target.
