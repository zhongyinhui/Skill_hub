# E-BL11 Contract

## Scope
Write industry-triggered opportunity rows to `E01_output_records`.

## Required Inputs
- `e_task_id`
- `run_batch_id`
- `source_signal_ref`
- `recommendation_reason`

## Optional Inputs
- `e_output_id`
- `customer_id`
- `customer_name_snapshot`
- `source_a_snapshot_ref`
- `target_sales_id`
- `recommended_action`
- `confidence_score`
- `priority_score`
- `recommended_dline_skill_ids`
- `evidence_refs`

## Writes
- `E01_output_records`, keyed by `e_output_id`.
- In explicit `mode=rule_config`: `E02_3_industry_ai_opportunity_rule`, keyed by `industry_rule_id`.

## Rule Config Mode
Required rule inputs:
- `industry_rule_id`
- `industry`
- `opportunity_type`
- `signal_keywords`
- `value_point`

