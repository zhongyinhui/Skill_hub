# E-BL07 Contract

## Scope
Update active influence-factor state in one of:
- `E05_global_state`
- `E05_sales_state`
- `E05_weapon_state`
- `E05_segment_state`

## Required Inputs
All modes require `state_table`.

For `global`:
- `global_factor_id`
- `factor_key`
- `factor_type`
- `current_weight`
- `update_source`

For `sales`:
- `sales_factor_id`
- `sales_id`
- `factor_type`
- `current_weight`
- `update_source`

For `weapon`:
- `weapon_factor_id`
- `dline_skill_id`
- `weapon_name`
- `current_weight`
- `update_source`

For `segment`:
- `segment_factor_id`
- `customer_segment`
- `opportunity_type`
- `current_weight`

## Writes
- One active E05 state table, keyed by the table's factor ID.

## Blocks
Reject missing state identity or fields outside the selected table. Return `needs_confirm` when `major_change=true` without `human_confirmed` or `review_confirmed`.

