# E-BL15 Contract

## Scope
Update B-line sync fields on `E01_output_records`.

## Required Inputs
- `e_output_id`
- At least one of:
  - `b_action_map_id`
  - `b_action_map_ref`
  - `write_to_b_status`
  - `sync_status`
  - `error_message`
  - `source_b_record_ref`

## Writes
- `E01_output_records`, keyed by `e_output_id`.

## Blocks
Reject missing `e_output_id` or missing sync update fields.

