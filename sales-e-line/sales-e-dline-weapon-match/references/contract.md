# E-BL04 Contract

## Scope
Record D-line weapon recommendations in `E01_output_records`.

## Required Inputs
- `customer_id`
- `recommended_dline_skill_ids`
- `recommendation_reason`

## Optional Inputs
- `e_output_id`
- `e_task_id`
- `run_batch_id`
- `customer_name_snapshot`
- `target_sales_id`
- `target_sales_name`
- `source_a_snapshot_ref`
- `source_d_weapon_ref`
- `recommended_action`
- `confidence_score`
- `priority_score`
- `output_template_id`
- `evidence_refs`

## Writes
- `E01_output_records`, keyed by `e_output_id`.

## Read-Only Rule Sources
- `E03_value_point_to_dline_skill_map`
- `E03_customer_stage_to_weapon_map`

These E03 JSON docs guide matching only. This skill does not write them.

## Blocks
Reject when no D-line skill ID is supplied or write fields are outside E01.2.
