---
name: sales-e-customer-activation
description: Use when E-line blacklight rules identify silent-customer, policy, or case activation opportunities from A-line customer snapshots.
---

# E-BL03 Customer Activation

## Purpose
Use this skill for E-BL03: create an activation opportunity in `E01.2` from A-line customer snapshots and E04 activation rules.
E04 rule config tables are maintained by E13 silent-customer radar, E12 case activation, and E10 policy radar in explicit rule config mode.

## Required Workflow
1. Read `references/contract.md`.
2. Prepare input JSON with `customer_id`, `source_a_snapshot_ref`, and `recommendation_reason`.
3. Run `python scripts/e_bl03_customer_activation.py --input input.json --config references/e_line_config.json --dry-run`.
4. Execute only after verifying that the output is a suggestion for B-line action, not an A-line formal fact.

## Hard Rules
- Read A-line snapshots only; never write A-line `current_stage` or `customer_rating`.
- Do not say the customer confirmed anything unless B/C feedback later proves it.
- Activation output remains an E01.2 opportunity until B-line acts.

## Script
``powershell
python scripts/e_bl03_customer_activation.py --input input.json --config references/e_line_config.json --dry-run
python scripts/e_bl03_customer_activation.py --input input.json --config references/e_line_config.json --execute
``

