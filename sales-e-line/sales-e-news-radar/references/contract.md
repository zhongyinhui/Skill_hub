# E-BL09 Contract

## Scope
Write news-triggered opportunity rows to `E01_output_records`.

## Required Inputs
- `e_task_id`
- `run_batch_id`
- `source_signal_ref`
- `recommendation_reason`

## Optional Inputs
- `e_output_id`
- `customer_id`
- `customer_name_snapshot`
- `target_sales_id`
- `target_sales_name`
- `recommended_action`
- `confidence_score`
- `priority_score`
- `output_template_id`
- `evidence_refs`

## Writes
- `E01_output_records`, keyed by `e_output_id`.

## Blocks
Reject missing signal identity, missing recommendation reason, missing table fields, or prohibited formal-customer fields.
