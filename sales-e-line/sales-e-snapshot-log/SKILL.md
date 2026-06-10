---
name: sales-e-snapshot-log
description: Use when E-line influence-factor history must be preserved as an E05 weekly snapshot or major-change log.
---

# E-BL08 Snapshot And Change Log

## Purpose
Use this skill for E-BL08: preserve E05 learning history through weekly snapshots and major-change logs.

## Required Workflow
1. Read `references/contract.md`.
2. Choose weekly snapshot mode or major change mode.
3. Run `python scripts/e_bl08_snapshot_and_change_log.py --input input.json --config references/e_line_config.json --dry-run`.
4. Execute only after validating the snapshot or change reason.

## Hard Rules
- Active E05 state is not enough; material changes must be traceable.
- Weekly snapshots are history rows, not current-state replacement.
- Major-change logs must include reason and affected factor identity.

## Script
```powershell
python scripts/e_bl08_snapshot_and_change_log.py --input input.json --config references/e_line_config.json --dry-run
python scripts/e_bl08_snapshot_and_change_log.py --input input.json --config references/e_line_config.json --execute
```
