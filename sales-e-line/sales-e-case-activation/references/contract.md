# E-BL12 Contract

## Scope
Write case-triggered activation opportunities to `E01_output_records`.

## Required Inputs
- `customer_id`
- `source_a_snapshot_ref`
- `source_signal_ref`
- `recommendation_reason`

## Optional Inputs
- `e_output_id`
- `e_task_id`
- `run_batch_id`
- `customer_name_snapshot`
- `target_sales_id`
- `recommended_action`
- `recommended_dline_skill_ids`
- `confidence_score`
- `priority_score`
- `evidence_refs`

## Writes
- `E01_output_records`, keyed by `e_output_id`.
