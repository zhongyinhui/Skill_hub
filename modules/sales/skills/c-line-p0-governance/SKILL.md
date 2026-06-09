---
name: c-line-p0-governance
description: "Use when implementing, checking, expanding, or executing the C-line P0 governance workflow for SaleAgentNo2, especially C-BL00, C-SK01, C-SK02, C-SK03, C-SK04, C-SK08, and C-SK16. This stage-level skill orchestrates the minimum C-line supervisor governance loop across the independent P0 skills."
---

# C Line P0 Governance

## Core Rule

Execute only the C-line P0 minimum loop unless the user explicitly asks for later phases.

P0 includes only:

- `C-BL00` via `$c-line-c-bl00-controller`
- `C-SK01` via `$c-line-c-sk01-index`
- `C-SK02` via `$c-line-c-sk02-daily-fact`
- `C-SK03` via `$c-line-c-sk03-period-summary`
- `C-SK04` via `$c-line-c-sk04-customer-progress`
- `C-SK08` via `$c-line-c-sk08-intervention-draft`
- `C-SK16` via `$c-line-c-sk16-system-health`

Do not implement training loops, SOP publishing, product feedback packages, management-office reports, field creation, D/E weight changes, or A-line stage/rating overwrites while using this stage skill.

## Read Order

1. Read `references/00-p0-overview.md` first for the P0 boundary and minimum loop.
2. Use `$c-line-c-bl00-controller` before any scheduling or public-table write design.
3. Use `$c-line-c-sk01-index` before locating or updating per-sales C01 governance table records.
4. Use `$c-line-c-sk02-daily-fact` before syncing B-line daily facts into `C01.sales_xxx`.
5. Use `$c-line-c-sk03-period-summary` before generating rolling or monthly summaries.
6. Use `$c-line-c-sk04-customer-progress` before analyzing customer stagnation, high intent, near-deal, or risk candidates.
7. Use `$c-line-c-sk08-intervention-draft` before creating supervisor intervention draft records.
8. Use `$c-line-c-sk16-system-health` before logging field, sync, permission, blacklight, or write-conflict issues.

## Execution Pattern

Use this sequence for P0 work:

```text
C-BL00 controller
  -> C-SK01 sales C01 index
  -> C-SK02 daily_fact
  -> C-SK03 rolling summaries
  -> C-SK04 customer progress risk
  -> C-SK08 supervisor intervention draft
  -> C-SK16 system health and exception log
```

For every output, keep source references. C line reads A/B/D/E results but does not copy full A-line customer files, mutate B-line process records, or change D/E strategy.

## Human Confirmation

Treat AI output as suggestion by default.

- Supervisor intervention remains draft until a supervisor confirms it.
- System health records may recommend repair actions, but must not change fields, permissions, or table structures automatically.
- Public governance tables must be written through the C-line controller flow, not through multiple sales blacklights concurrently.
