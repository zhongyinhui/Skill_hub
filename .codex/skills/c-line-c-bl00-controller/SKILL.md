---
name: c-line-c-bl00-controller
description: "Use when implementing, checking, expanding, or executing C-BL00 in the C-line P0 governance workflow for SaleAgentNo2: controller scheduling, ordered C-line task queues, public governance table write coordination, and C07 exception logging without generating sales judgments."
---

# C-BL00 Controller

## 目标

统一调度 C 线日更、周更、月更和事件触发任务，控制公共治理表写入顺序，避免多个销售黑灯同时写公共表。

## 输入

- C00 治理规则。
- C01.0 销售个人治理表索引。
- A/B/D/E 运行结果与运行日志。
- 上一次 C 线黑灯状态。

## 处理步骤

1. 读取 C00 中 active 状态的治理规则。
2. 读取 C01.0，获取 active 销售、对应 C01 表、主管、权限、最近记录日期、数据质量状态。
3. 按任务类型生成调度队列：日更、周更、月更、事件触发。
4. 先执行个人表写入类任务，再执行公共表汇总类任务。
5. 对每个任务记录开始时间、结束时间、成功/失败、影响表、错误信息。
6. 失败任务写入 C07，不阻塞其它无依赖任务。

## 输出

- C07 调度日志与异常记录。
- 各 C 表生成状态。
- C01.0 中 `last_blacklight_run_at`、`data_quality_status` 等状态字段更新建议。

## 边界

- `C-BL00` 不是业务 Skill，不生成销售判断。
- 不直接改 A/B/D/E 原始记录。
- 公共表写入必须经由总控调度，不能由多个销售黑灯并发写入。

## 验收

- 能生成日更、周更、月更任务队列。
- 公共表写入任务不会被多个销售黑灯并发执行。
- 任一任务失败时，C07 有明确异常记录。
