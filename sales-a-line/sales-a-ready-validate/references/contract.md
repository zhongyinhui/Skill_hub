# A-SK05 Contract

## Scope
Gate B-line packages before A-line entry and write only validation/audit logs.

## Required Package Fields
- `customer_id`
- `sales_id`
- `work_date`
- `effective_events_summary`
- `confirm_status`
- `evidence_ids`

Recommended package fields:
- `source_session_ids`
- `stage_before`, `stage_after`
- `need_delta`, `objection_delta`, `buying_signal_delta`
- `risk_flags`
- `artifact_ids`
- `snapshot_update_required`
- `human_confirm_required`

## Writes
- `A07_a_line_run_log`: `log_id`, `run_type`, `source_line`, `source_record_id`, `target_table`, `customer_id`, `operation`, `status`, `idempotency_key`, `error_message`, `created_at`

## Blocks
Return `rejected` for empty package, missing evidence, missing required fields, or field snapshot mismatch.
Return `needs_confirm` when human confirmation is required but not confirmed.
