---
name: c-line-c-sk02-daily-fact
description: "Use when implementing, checking, expanding, or executing C-SK02 in the C-line P0 governance workflow for SaleAgentNo2: syncing active B-line daily records and blacklight outputs into per-sales C01 daily_fact records with source references preserved."
---

# C-SK02 Daily Fact Sync

## 目标

把 B 线 active 销售日记录和黑灯输出同步到对应销售的 `C01.sales_xxx`，形成 `daily_fact`。

## 输入

- B 线 daily_sales_record。
- B 线 blacklight_output。
- A 线账本引用。
- D 线反馈引用。
- E 线行动地图引用。
- C01.0 销售个人表索引。

## 处理步骤

1. 从 C01.0 找到目标销售对应 C01 表。
2. 读取该销售指定日期的 B 线 active 日记录。
3. 读取当天相关黑灯输出、客户包、D 线调用、E 线建议与采纳反馈。
4. 映射工作量字段：`session_count`、`customers_touched_count`、`phone_call_count`、`meeting_count`。
5. 映射有效性字段：`effective_conversation_count`、`stage_progress_customer_count`。
6. 映射结果字段：`quote_count`、`deal_count`、`deal_amount_total`。
7. 映射数据质量字段：`orphan_material_count`、`orphan_confirmed_count`、`orphan_pending_count`、`orphan_confirm_rate`。
8. 映射武器字段：`dline_call_count`、`artifact_generated_count`、`artifact_used_count`。
9. 映射行动地图字段：`action_map_recommendation_count`、`action_map_adopted_count`。
10. 映射风险字段：`risk_count`、`risk_flags`。
11. 生成 `daily_summary` 和 `ai_analysis_summary`。
12. 设置 `record_type = daily_fact`，`record_status = active`。
13. 保留 `source_b_daily_record_ids`、`source_b_blacklight_output_ids`、`source_a_ledger_block_ids`、`source_d_feedback_ids`、`source_e_action_map_ids`。

## 输出

- C01.sales_xxx `daily_fact` 记录。
- 同步异常写 C07。

## 边界

- 只同步事实，不做能力判断。
- 不把 draft B 线记录写成 active C 线事实。
- 所有跨线来源必须保留引用。

## 验收

- 给定 1 名销售和 1 天 B 线 active 日记录，能写入 1 条 `daily_fact`。
- 工作量、有效性、结果、风险核心字段正确。
- 来源引用完整。
