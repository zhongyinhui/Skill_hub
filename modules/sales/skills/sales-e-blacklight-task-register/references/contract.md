# E-BL01 Contract

## Scope
Register or update E-line blacklight task configuration in `E01_task_registry`.

## Required Inputs
- `e_task_id`
- `task_name`
- `task_type`
- `blacklight_type`

## Optional Inputs
- `target_customer_scope`
- `input_sources`
- `rule_table_refs`
- `output_template_id`
- `write_to_target`
- `output_type`
- `scan_frequency`
- `priority`
- `status`
- `last_run_at`
- `next_run_at`
- `last_run_status`
- `error_summary`
- `owner`
- `version`
- `remark`

## Writes
- `E01_task_registry`, keyed by `e_task_id`.

## Blocks
Reject when required inputs are missing, fields are absent from config, or select values are outside the configured options.

