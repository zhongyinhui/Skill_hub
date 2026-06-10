# E-BL08 Contract

## Scope
Write one history row to `E05_weekly_snapshot` or `E05_major_change_log`.

## Weekly Snapshot Required Inputs
- `snapshot_id`
- `week_start`
- `week_end`
- `snapshot_scope`
- `source_state_table`

## Major Change Required Inputs
- `change_id`
- `affected_state_table`
- `affected_factor_id`
- `change_type`
- `change_reason`

## Mode Selection
- Provide `change_id` or `mode=major_change_log` for major-change log.
- Otherwise the script writes weekly snapshot.

## Writes
- `E05_weekly_snapshot`, keyed by `snapshot_id`, or
- `E05_major_change_log`, keyed by `change_id`.

## Blocks
Reject when the selected history mode is missing its required identity or reason fields.
