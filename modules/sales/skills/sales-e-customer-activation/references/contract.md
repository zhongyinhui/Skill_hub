# E-BL03 Contract

## Scope
Turn silent-customer, policy, or case activation matches into E01.2 output records.

## Required Inputs
- `customer_id`
- `source_a_snapshot_ref`
- `recommendation_reason`

## Optional Inputs
- `e_output_id`
- `e_task_id`
- `run_batch_id`
- `customer_name_snapshot`
- `target_sales_id`
- `target_sales_name`
- `source_signal_ref`
- `source_signal_type`
- `opportunity_type`
- `recommendation_type`
- `recommended_action`
- `confidence_score`
- `priority_score`
- `output_template_id`
- `evidence_refs`

## Writes
- `E01_output_records`, keyed by `e_output_id`.

## Blocks
Reject when A snapshot reference or customer identity is missing.

