---
name: sales-a-alias-map
description: Use when customer aliases, names, phone or source identifiers must be normalized and mapped to a formal A-line customer_id.
---

# A-SK04 Alias Map

## Purpose
Use this skill for A-SK04: normalize customer aliases and identity clues, then map them to a confirmed `customer_id` without auto-resolving conflicts.

## Required Workflow
1. Read `references/contract.md`.
2. Verify A01/A06 fields from live tables or config.
3. Run `python scripts/a_sk04_alias_map.py --input input.json --config a_line_config.json --dry-run`.
4. Resolve conflicts manually when the script returns `needs_confirm`.
5. Execute only after the mapping is confirmed.

## Hard Rules
- Alias mapping is not customer merging.
- A-line can suggest candidates, but cannot arbitrate multi-customer or multi-sales conflicts.
- Low confidence or conflicting candidates must stay pending.
- Do not create a new field such as `phone_wechat` unless it already exists.

## Script
```powershell
python scripts/a_sk04_alias_map.py --input input.json --config a_line_config.json --dry-run
python scripts/a_sk04_alias_map.py --input input.json --config a_line_config.json --execute
```
