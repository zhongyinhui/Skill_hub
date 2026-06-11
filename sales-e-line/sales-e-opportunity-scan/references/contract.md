# E-BL02 Contract

## Scope
Write scanned news, policy, industry, or other opportunity signals into `E01_output_records`.

## Required Inputs
- `e_task_id`
- `run_batch_id`
- `source_signal_type`
- `source_signal_ref`
- `opportunity_type`
- `recommendation_reason`

## Optional Inputs
- `e_output_id`
- `customer_id`
- `customer_name_snapshot`
- `target_sales_id`
- `target_sales_name`
- `recommended_action`
- `recommendation_type`
- `confidence_score`
- `priority_score`
- `output_template_id`
- `evidence_refs`

## Writes
- `E01_output_records`, keyed by `e_output_id`.

## Blocks
Reject when required signal fields are missing or the write includes fields outside the E01.2 whitelist.
