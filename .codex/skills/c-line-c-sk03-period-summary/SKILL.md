---
name: c-line-c-sk03-period-summary
description: "Use when implementing, checking, expanding, or executing C-SK03 in the C-line P0 governance workflow for SaleAgentNo2: generating rolling 7/14/30-day and monthly summaries from active daily_fact records with traceable metrics and analysis summaries."
---

# C-SK03 Period Summary

## 目标

基于 `daily_fact` 生成 7/14/30 天和月度汇总，让主管看到销售连续性和趋势。

## 输入

- C01.sales_xxx 中指定周期内的 `daily_fact`。

## 处理步骤

1. 按销售和周期读取 `daily_fact`。
2. 计算周期指标：`active_day_count`、`continuous_active_days`、`avg_session_per_day`、`avg_customer_touched_per_day`、`avg_effective_conversation_per_day`。
3. 计算风险和质量指标：`high_intent_followup_gap_max`、`orphan_confirm_rate`、`artifact_use_rate`、`artifact_hit_rate`。
4. 计算行动地图指标：`action_map_adoption_rate`、`action_map_effective_rate`、`free_exploration_effective_rate`。
5. 生成评分：`followup_continuity_score`、`sales_activity_score`、`sales_quality_score`、`deal_conversion_score`、`dline_usage_score`、`data_completeness_score`。
6. 根据风险和数据断档标记 `manager_attention_required`、`training_required`。
7. 生成周期摘要。
8. 写入 `record_type = rolling_7d / rolling_14d / rolling_30d / monthly_summary`。

## 输出

- C01.sales_xxx 周期汇总记录。

## 边界

- HI 等综合口径只能作为内部计算，不新增字段。
- 分数来源必须写入 `ai_analysis_summary`，避免主管看不懂。
- 只基于 active `daily_fact` 汇总，不使用 draft 事实。

## 验收

- 给定连续 7 天 `daily_fact`，能生成 `rolling_7d`。
- 周期指标、评分、摘要均可追溯。
