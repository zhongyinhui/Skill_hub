# E-BL10 Contract

## Scope
Write policy-triggered opportunity rows to `E01_output_records`.

## Required Inputs
- `e_task_id`
- `run_batch_id`
- `source_signal_ref`
- `recommendation_reason`

## Optional Inputs
- `e_output_id`
- `customer_id`
- `source_a_snapshot_ref`
- `target_sales_id`
- `recommended_action`
- `confidence_score`
- `priority_score`
- `evidence_refs`

## Writes
- `E01_output_records`, keyed by `e_output_id`.

## Blocks
Reject missing policy signal identity or fields outside the E output whitelist.
