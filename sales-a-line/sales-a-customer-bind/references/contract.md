# A-SK02 Contract

## Scope
Bind an accepted source lead to a formal A-line customer. Create a new `customer_id` only when there is no unresolved duplicate conflict.

## Inputs
Required:
- `lead_id`
- `customer_name`
- `sales_id`
- one confirmed acceptance field: `sales_accept_status`, `receive_status`, or `receive_confirmed`

Optional:
- `customer_id`
- `chosen_customer_id`
- `source_id`, `source_type`, `source_department`, `source_channel`, `source_contact`
- `contact_info`, `industry`, `company_size`, `cash_flow_signal`
- `consumption_ability`, `budget_range`, `decision_power`, `urgency`
- `demand_summary`, `initial_rating`
- `duplicate_candidate_ids`
- `duplicate_confirm_status`
- `individual_customer_table_url`
- `ledger_table_ref`, `evidence_ref_table_ref`, `artifacts_ref_table_ref`, `handoff_ref_table_ref`, `latest_snapshot_table_ref`
- `individual_customer_base_token`, `individual_customer_table_id`

## Writes
Allowed tables and fields:
- `A03_all_customer_files`: `customer_id`, `customer_name`, `customer_status`, `source_id`, `current_sales_id`, `industry`, `company_size`, `cash_flow`, `consumption_ability`, `decision_power`, `budget_signal`, `individual_customer_table_url`, `ledger_table_ref`, `evidence_ref_table_ref`, `artifacts_ref_table_ref`, `handoff_ref_table_ref`, `latest_snapshot_table_ref`, `created_at`, `updated_at`
- `A06_a_line_index`: `source_map_id`, `source_id`, `source_type`, `source_department`, `raw_customer_name`, `raw_phone`, `candidate_customer_ids`, `linked_customer_id`, `accepted_sales_id`, `mapping_status`, `created_at`, `updated_at`, `remark`
- On `--execute`, if all per-customer refs are missing, create one customer ledger bitable under `01_客户账本/` with title `{customer_id}/`, configure fields `time`, `customer_id`, `ledger`, `latest_snapshot`, `evidence_ref`, `artifacts_ref`, `handoff_ref`, and write the resulting refs back to `A03_all_customer_files`.

## Blocks
Return `needs_confirm` when a duplicate candidate exists but no confirmed selected customer is provided.
Return `rejected` when the lead is not human-confirmed, required fields are missing, or a planned field does not exist in the config/live table.
This skill does not write ledger/evidence/snapshot attachments. If per-customer container refs are missing in dry-run, it reports `result_refs.auto_customer_container_planned=true`; execute creates or reuses the customer ledger table before writing the customer record.

## Customer Ledger Template
When `customer_container_create.template_node_token` is configured, `--execute` copies that clean bitable template into the customer ledger folder, waits for the copied Base to become readable, verifies required fields, and deletes only truly blank default records. Field-by-field construction is only the fallback path.
