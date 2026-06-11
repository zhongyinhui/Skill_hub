# E-BL06 Contract

## Scope
Write B-line adoption, actual action, customer response, C-line effect, and rejection reason back to `E01_output_records`.

## Required Inputs
- `e_output_id`
- At least one of:
  - `adoption_feedback_status`
  - `actual_action_taken`
  - `customer_response_summary`
  - `c_effect_ref`
  - `final_effect_status`
  - `non_adoption_reason`

## Optional Inputs
- `source_b_record_ref`
- `source_c_feedback_ref`
- `b_action_map_id`
- `b_action_map_ref`
- `write_to_b_status`
- `sync_status`
- `error_message`

## Writes
- `E01_output_records`, keyed by `e_output_id`.

## Blocks
Reject when `e_output_id` or all feedback fields are missing.

