# A-SK10 Contract

## Scope
Read the current customer snapshot from `A03_all_customer_files`.

## Inputs
Required:
- `customer_id`

Optional:
- `include_json`
- `include_refs`

## Reads
- `A03_all_customer_files`: `customer_id`, `customer_name`, `current_stage`, `customer_rating`, `latest_snapshot_text`, `latest_snapshot_json`, `core_needs`, `current_objections`, `buying_signals`, `evidence_ref`, `artifact_ref`, `updated_at`
- Optional when the live field exists: `risk_flags`

## Blocks
Return `rejected` for missing `customer_id` or missing read-field snapshot.
Never produce planned writes.
