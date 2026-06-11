# A-SK04 Contract

## Scope
Map an alias or external identity clue to a formal `customer_id`, and refresh A-line index keywords.

## Inputs
Required:
- `customer_id`
- `alias_name`
- `confirm_status`

Optional:
- `alias_type`
- `source_line`, `source_record_id`, `source_id`
- `source_type`, `source_department`, `raw_customer_name`, `raw_phone`, `accepted_sales_id`
- `confidence_score`
- `created_by`
- `conflict_status`
- `candidate_customer_ids`

## Writes
- `A01_customer_alias`: `alias_id`, `customer_id`, `alias_name`, `alias_type`, `source_line`, `source_record_id`, `confidence_score`, `confirm_status`, `created_by`, `created_at`, `updated_at`, `status`, `remark`
- `A06_a_line_index`: when `source_id` or `source_record_id` exists, upsert by `source_id` with `source_map_id`, `source_id`, `source_type`, `source_department`, `raw_customer_name`, `raw_phone`, `candidate_customer_ids`, `linked_customer_id`, `accepted_sales_id`, `mapping_status`, `created_at`, `updated_at`, `remark`

## Blocks
Return `needs_confirm` when `confirm_status` is not confirmed, confidence is low, or candidate conflicts exist.
Return `rejected` for missing required inputs or field snapshot mismatches.
