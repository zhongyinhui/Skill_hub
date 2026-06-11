# A-SK07 Contract

## Scope
Write formal customer profile fields only after explicit human confirmation.

## Table Alignment
- `All_customer_files｜A线全部客户档案表` (`TqVmbOv2faej8MsJtkSccIv2nKb / tblT0pxNirTRQw9H`) stores formal customer profile fields.
- `05_A线运行日志` (`OqX3blrtOaitzRsePw1cKXJRn7d / tblOAtmYZTrhBtkm`) stores the audit log. This table name is not the same thing as A-SK07.

## Inputs
Required:
- `customer_id`
- `field_updates`
- `confirm_status`
- `confirmed_by`

Optional:
- `confirmation_id`
- `source_skill_id`
- `source_record_id`
- `confirm_remark`
- `idempotency_key`

## Allowed Field Updates
- `current_stage`
- `customer_rating`
- `next_followup_at`
- `recommended_next_action`
- `last_contact_summary`
- `current_status`
- `budget_level`
- `decision_power`

## Writes
- `All_customer_files｜A线全部客户档案表`: confirmed allowed fields plus `customer_id` and `updated_at`
- `05_A线运行日志`: audit log with confirmation source, confirmed fields, and idempotency key

## Blocks
Return `needs_confirm` when `confirm_status` is not confirmed.
Return `rejected` when required inputs are missing, field updates are empty, a field is outside the allowlist, a prohibited internal field is present, or the target table lacks a planned field.

