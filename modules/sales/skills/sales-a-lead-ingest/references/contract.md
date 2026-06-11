# A-SK01 Contract

## Scope
Capture raw source leads into the real A-line pending lead pool before customer binding, dedupe, or formal ledger entry.

## Table Alignment
- `03_销售待接收线索池` (`EfJrbbDY7a3K55sZFQBcemL5nkT / tblXEzJVJYfVGHIb`) stores rich raw lead intake and sales acceptance fields.
- `source_id_mapping` (`IJK4bY3HhaWFcnsqwUncAV9rnje / tbl2fHDgqP7f4gyq`) stores source_id-to-customer mapping.
- The lead pool does not own the source identifier directly; it links to `source_id_mapping` through `source_map_id`.

## Inputs
Required:
- `source_id`
- one raw identity field: `raw_customer_name`, `lead_name`, or `raw_company_name`

Optional:
- `source_type`
- `source_department` for `source_id_mapping`
- `source_channel`
- `source_record_url`
- `raw_phone`
- `phone`
- `assigned_sales_id` or `transfer_to_sales_id`
- `recommended_sales_id`
- `candidate_customer_ids`
- `transfer_to_a_status`
- `lead_status`
- `lead_quality`
- `lead_created_at`
- `lead_received_at`
- `ai_summary`
- `remark`
- `write_index` defaults to true

## Writes
- `03_销售待接收线索池`: upsert by `source_map_id` with `lead_name`, `raw_customer_name`, `raw_company_name`, `raw_phone`, `phone`, `customer_display_name`, `source_type`, `source_channel`, `source_record_url`, `source_map_id`, `candidate_customer_ids`, `dedupe_key`, `dedupe_status`, `lead_status`, `lead_quality`, `sales_accept_status`, `recommended_sales_id`, `transfer_to_sales_id`, `transfer_to_a_status`, `lead_created_at`, `lead_received_at`, `lead_remark`, `raw_remark`, `remark`, `ai_summary`, `processed_by`
- `source_id_mapping`: when `write_index` is not false, upsert by `source_id` with `source_map_id`, `source_id`, `source_type`, `source_department`, `raw_customer_name`, `raw_phone`, `candidate_customer_ids`, `mapping_status`, `created_at`, `updated_at`, `remark`

## Blocks
Return `rejected` when `source_id` or raw identity is missing, when a prohibited field is present, or when a planned field does not exist.
Return `needs_confirm` when candidate customers exist and the caller asks to bind in this step; binding belongs to A-SK02/A-SK04.

