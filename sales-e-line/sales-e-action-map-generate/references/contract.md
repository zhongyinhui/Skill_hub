# E-BL05 Contract

## Scope
Generate E01.2 rows that B-line can consume as next-day action map candidates.

## Required Inputs
- `customer_id`
- `target_sales_id`
- `recommended_action`
- `recommendation_reason`

For batch input, put the fields above inside each item of `recommendations`.

## Optional Inputs
- `e_output_id`
- `e_task_id`
- `run_batch_id`
- `customer_name_snapshot`
- `target_sales_name`
- `source_a_snapshot_ref`
- `source_d_weapon_ref`
- `recommended_dline_skill_ids`
- `output_template_id`
- `b_action_map_id`
- `b_action_map_ref`

## Writes
- `E01_output_records`, keyed by `e_output_id`.

## Blocks
Reject when customer, salesperson, action, or reason is missing.
