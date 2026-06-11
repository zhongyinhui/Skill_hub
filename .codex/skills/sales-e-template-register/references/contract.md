# E-BL14 Contract

## Scope
Register or update rows in `E06_template_index`.

## Required Inputs
- `template_id`
- `template_name`
- `output_type`
- `target_receiver`
- `applicable_task_type`

## Optional Inputs
- `applicable_customer_stage`
- `template_ref`
- `output_schema_ref`
- `required_fields`
- `optional_fields`
- `tone_style`
- `version`
- `status`
- `reviewer`
- `remark`

## Writes
- `E06_template_index`, keyed by `template_id`.

