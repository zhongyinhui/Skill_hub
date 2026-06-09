---
name: c-line-c-sk04-customer-progress
description: "Use when implementing, checking, expanding, or executing C-SK04 in the C-line P0 governance workflow for SaleAgentNo2: identifying customer stagnation, high-intent, near-deal, handoff, and supervisor-intervention risk candidates from A/B/C facts."
---

# C-SK04 Customer Progress Risk

## 目标

从客户视角识别停滞、临门一脚、高意向、换手掉速和风险。

## 输入

- A 线 latest_snapshot。
- A 线 ledger。
- B 线客户当日包。
- C01.sales_xxx 销售事实记录。

## 处理步骤

1. 选取分析客户范围：高评级客户、近周期被触达客户、阶段停留过长客户、有报价/承诺/交付/投诉/流失风险客户。
2. 读取 A 线快照和账本，只取推进状态、阶段、评级、最近触达、最近有效事件、需求、异议、购买信号、风险。
3. 读取 B 线客户包，补充当天实际动作。
4. 计算或判断 `stage_change_count`、`days_in_current_stage`、`last_contact_at`、`last_effective_event_at`。
5. 标记 `high_intent_flag`、`near_deal_flag`、`stagnation_risk`、`handoff_count`、`needs_supervisor_intervention`。
6. 生成 `recommended_manager_action` 和 `analysis_summary`。
7. 写入 C01.2。

## 输出

- C01.2 客户长周期推进记录。

## 边界

- 不复制 A 线客户完整档案。
- 不自动修改 A 线 `current_stage` 或 `customer_rating`。
- 输出必须包含 A/B 来源引用。

## 验收

- 高评级停滞客户能被标记为中/高停滞风险。
- 临门一脚客户能生成主管建议动作。
- 输出包含 A/B 来源引用。
