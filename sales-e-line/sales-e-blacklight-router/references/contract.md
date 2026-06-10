# E-BL00 Contract

## Scope
Choose the correct downstream E-line skill for a blacklight request. This router is read-only and write-free.

## Inputs
Accept any of these classification hints:
- `operation`, `intent`, `mode`
- `signal_type`, `source_signal_type`, `source_type`
- `rule_table`, `target_table`
- `task_type`, `blacklight_type`
- `customer_id`, `recommended_action`, `recommended_dline_skill_ids`
- feedback fields such as `adoption_feedback_status`, `c_effect_ref`, `actual_action_taken`
- run-state fields such as `last_run_status`, `next_run_at`, `error_summary`

## Outputs
- `status`: `pass`, `needs_confirm`, `rejected`, or `error`
- `skill_id`: always `E-BL00`
- `selected_routes`: ordered downstream skill suggestions
- `candidate_routes`: alternatives when confirmation is needed
- `blocked_reasons`: why routing failed or needs clarification
- `no_writes`: always `true`

## Routing Summary
- Task registration -> `sales-e-blacklight-task-register`
- External generic opportunity -> `sales-e-opportunity-scan`
- News signal or E02.1 source whitelist -> `sales-e-news-radar`
- Policy signal, E02.2 scan rule, or E04.3 policy activation rule -> `sales-e-policy-radar`
- Industry signal or E02.3 rule -> `sales-e-industry-radar`
- Silent customer activation or E04.1 rule -> `sales-e-silent-customer-radar`
- Case activation or E04.2 rule -> `sales-e-case-activation`
- D-line weapon recommendation -> `sales-e-dline-weapon-match`
- B-line action-map recommendation -> `sales-e-action-map-generate`
- Feedback capture -> `sales-e-feedback-capture`
- E05 influence state update -> `sales-e-influence-adjust`
- E05 snapshot or major change log -> `sales-e-snapshot-log`
- E06 template registration -> `sales-e-template-register`
- B-line sync status update -> `sales-e-bline-sync-status`
- Task run-state update -> `sales-e-run-state-update`

## Non-Scope
This router does not crawl web pages, run schedules, write Feishu, update B-line records, or execute child skills.
