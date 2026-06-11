---
name: c-line-c-sk08-intervention-draft
description: "Use when implementing, checking, expanding, or executing C-SK08 in the C-line P0 governance workflow for SaleAgentNo2: converting sales or customer risk evidence into supervisor intervention draft records without treating AI suggestions as confirmed interventions."
---

# C-SK08 Supervisor Intervention Draft

## 目标

把销售或客户风险转成主管可处理的干预 draft。

## 输入

- C01 周期汇总。
- C01.2 客户推进分析。
- C02 武器命中结果引用。
- B 线风险。

## 处理步骤

1. 读取风险候选。
2. 对同一客户/销售去重，避免重复生成干预 draft。
3. 判断 `trigger_source`：C线预警、销售请求、B线风险、E线机会、人工发现。
4. 写入 `intervention_reason`、`risk_level_before`、`intervention_stage_before`、`customer_rating_before`。
5. 生成建议的 `intervention_action` 和 `manager_instruction`。
6. 设置 `status = open` 或 draft 状态。

## 输出

- C01.5 主管干预 draft。

## 边界

- 只是建议，主管确认后才算正式干预。
- 不替主管自动发指令给销售。
- 不伪造销售推进事实；所有干预触发必须有证据引用。

## 验收

- 高评级停滞客户可生成 C01.5 draft。
- 干预记录包含触发来源和证据引用。
- 同一客户/销售不会重复生成相同原因的干预 draft。
