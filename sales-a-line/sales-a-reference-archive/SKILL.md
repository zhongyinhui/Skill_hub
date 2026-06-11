---
name: sales-a-reference-archive
description: Use when evidence, generated artifacts, or handoff references must be attached to existing A-line customer facts or snapshots.
---

# A-SK08 Reference Archive

## Purpose
Use this skill for A-SK08: archive evidence, artifact, and handoff references without turning generated material into confirmed customer facts.

## Required Workflow
1. Read `references/contract.md`.
2. Verify the target ledger block and customer snapshot fields.
3. Run `python scripts/a_sk08_reference_archive.py --input input.json --config a_line_config.json --dry-run`.
4. Review whether references are evidence, artifacts, or handoff materials.
5. Execute only after the reference mapping is clean.

## Hard Rules
- Evidence reference is not the same as a formal fact.
- Generated artifact is not proof that the customer saw or accepted it.
- Update the existing customer ledger row for the same `customer_id` + ledger record time; do not create a second row for the same B-line package.
- Do not upload or rewrite `ledger`; ledger is owned by A-SK06.
- Empty `artifact_ids` or `handoff_ids` are valid when no D-line output or handoff package exists.
- Do not create `handoff_ref` fields unless they already exist; map handoff material into existing artifact reference fields when needed.
- Do not write `sent_to_customer`.

## Script
```powershell
python scripts/a_sk08_reference_archive.py --input input.json --config a_line_config.json --dry-run
python scripts/a_sk08_reference_archive.py --input input.json --config a_line_config.json --execute
```
