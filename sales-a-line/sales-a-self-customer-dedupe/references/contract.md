# A-SK03 Contract

## Scope
Create or draft a customer record for a self-developed/no-source customer after duplicate checks.

## Inputs
Required:
- `customer_name`
- `sales_id`
- `create_confirmed`

Optional:
- `customer_id`
- `source_id`, `source_record_id`, `source_type`, `source_department`
- `raw_customer_name`, `raw_phone`
- `alias_names`
- `contact_info`, `industry`, `company_size`
- `core_needs`, `remark`, `no_source_reason`
- `duplicate_candidate_ids`
- `duplicate_confirm_status`
- `individual_customer_table_url`
- `ledger_table_ref`, `evidence_ref_table_ref`, `artifacts_ref_table_ref`, `handoff_ref_table_ref`, `latest_snapshot_table_ref`
- `individual_customer_base_token`, `individual_customer_table_id`

## Writes
- `A03_all_customer_files`: `customer_id`, `customer_name`, `customer_status`, `current_sales_id`, `industry`, `company_size`, `core_needs`, `individual_customer_table_url`, `ledger_table_ref`, `evidence_ref_table_ref`, `artifacts_ref_table_ref`, `handoff_ref_table_ref`, `latest_snapshot_table_ref`, `created_at`, `updated_at`
- `A06_a_line_index`: when `source_id` or `source_record_id` exists, upsert one source-to-customer mapping by `source_id`: `source_map_id`, `source_id`, `source_type`, `source_department`, `raw_customer_name`, `raw_phone`, `candidate_customer_ids`, `linked_customer_id`, `accepted_sales_id`, `mapping_status`, `created_at`, `updated_at`, `remark`
- `A01_customer_alias`: `alias_id`, `customer_id`, `alias_name`, `alias_type`, `source_line`, `source_record_id`, `confidence_score`, `confirm_status`, `created_by`, `created_at`, `status`, `remark`
- On `--execute`, if all per-customer refs are missing, create one customer ledger bitable under `01_客户账本/` with title `{customer_id}/`, configure fields `time`, `customer_id`, `ledger`, `latest_snapshot`, `evidence_ref`, `artifacts_ref`, `handoff_ref`, and write the resulting refs back to `A03_all_customer_files`.

## Blocks
Return `needs_confirm` for unresolved duplicate candidates or missing creation confirmation.
Return `rejected` for missing required fields or missing target fields.
This skill does not write ledger/evidence/snapshot attachments. If per-customer container refs are missing in dry-run, it reports `result_refs.auto_customer_container_planned=true`; execute creates or reuses the customer ledger table before writing the customer record.

## Customer Ledger Template
When `customer_container_create.template_node_token` is configured, `--execute` copies that clean bitable template into the customer ledger folder, waits for the copied Base to become readable, verifies required fields, and deletes only truly blank default records. Field-by-field construction is only the fallback path.
