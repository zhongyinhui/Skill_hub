# E-BL16 Contract

## Scope
Update run state fields in `E01_task_registry`.

## Required Inputs
- `e_task_id`
- At least one of:
  - `last_run_at`
  - `next_run_at`
  - `last_run_status`
  - `status`
  - `error_summary`

## Optional Inputs
- `owner`
- `version`
- `remark`

## Writes
- `E01_task_registry`, keyed by `e_task_id`.

