# E-BL10 Contract

## Scope
Write policy-triggered opportunity rows to `E01_output_records`.

## Required Inputs
- `e_task_id`
- `run_batch_id`
- `source_signal_ref`
- `recommendation_reason`

## Optional Inputs
- `e_output_id`
- `customer_id`
- `source_a_snapshot_ref`
- `target_sales_id`
- `recommended_action`
- `confidence_score`
- `priority_score`
- `evidence_refs`

## Writes
- `E01_output_records`, keyed by `e_output_id`.
- In explicit `mode=rule_config` or `mode=scan_rule`: `E02_2_policy_scan_rule`, keyed by `policy_rule_id`.
- In explicit `mode=policy_activation_rule`: `E04_3_policy_activation_rule`, keyed by `policy_activation_rule_id`.

## Rule Config Mode
Required E02.2 scan-rule inputs:
- `policy_rule_id`
- `region`
- `policy_type`
- `keywords`
- `policy_source_name`
- `policy_source_url`

Required E04.3 activation-rule inputs:
- `policy_activation_rule_id`
- `policy_type`
- `region`
- `policy_match_condition`
- `activation_angle`

## Blocks
Reject missing policy signal identity or fields outside the E output whitelist.
