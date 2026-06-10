---
name: sales-e-template-register
description: Use when E-line output templates or schemas must be registered, versioned, or validated in the E06 template index.
---

# E-BL14 Template Register

## Purpose
Use this skill for E-BL14: register or update E-line output templates in `E06_template_index`.

## Required Workflow
1. Read `references/contract.md`.
2. Prepare input JSON with `template_id`, `template_name`, `output_type`, `target_receiver`, and `applicable_task_type`.
3. Run `python scripts/e_bl14_template_register.py --input input.json --config references/e_line_config.json --dry-run`.
4. Execute only after dry-run is clean.

## Hard Rules
- Do not create new Feishu fields.
- Template registration is not customer confirmation.
- Template schemas must describe output shape, not hidden model reasoning.

## Script
```powershell
python scripts/e_bl14_template_register.py --input input.json --config references/e_line_config.json --dry-run
python scripts/e_bl14_template_register.py --input input.json --config references/e_line_config.json --execute
```
