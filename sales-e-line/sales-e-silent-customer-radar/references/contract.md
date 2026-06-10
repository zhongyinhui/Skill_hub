# E-BL13 Contract

## Scope
Write silent-customer activation opportunities to `E01_output_records`.

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
- `recommended_action`
- `confidence_score`
- `priority_score`
- `output_template_id`
- `evidence_refs`

## Writes
- `E01_output_records`, keyed by `e_output_id`.
- In explicit `mode=rule_config`: `E04_1_silent_customer_activation_rule`, keyed by `silent_rule_id`.

## Rule Config Mode
Required rule inputs:
- `silent_rule_id`
- `silent_days_threshold`
- `activation_type`
- `recommended_message_angle`
