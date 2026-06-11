# E-BL09 Contract

## Scope
Write news-triggered opportunity rows to `E01_output_records`.

## Required Inputs
- `e_task_id`
- `run_batch_id`
- `source_signal_ref`
- `recommendation_reason`

## Optional Inputs
- `e_output_id`
- `customer_id`
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
- In explicit `mode=rule_config`: `E02_1_news_source_whitelist`, keyed by `source_id`.

## Rule Config Mode
Use `mode=rule_config` or `mode=source_whitelist` for the E02.1 source whitelist.

Required rule inputs:
- `source_id`
- `source_name`
- `source_url`
- `source_type`
- `domain`
- `trust_level`
- `language`

## Blocks
Reject missing signal identity, missing recommendation reason, missing table fields, or prohibited formal-customer fields.

