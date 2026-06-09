---
name: c-line-c-sk01-index
description: "Use when implementing, checking, expanding, or executing C-SK01 in the C-line P0 governance workflow for SaleAgentNo2: maintaining each sales owner C01 table path, permission scope, manager mapping, active status, and data-quality exception routing."
---

# C-SK01 Sales C01 Index

## 目标

维护每个销售对应的 C01 个人治理表路径、权限、状态和最近数据质量。

## 输入

- 销售名单。
- 组织关系：销售、销售组、主管。
- C01 个人表链接和状态。
- 最近黑灯运行结果。

## 处理步骤

1. 检查销售名单与 C01.0 是否一致。
2. 新销售加入时生成索引记录，状态为 active 或待建表。
3. 销售离职、转组、停用时更新 `sales_status`。
4. 校验 `c01_personal_table_name`、`c01_personal_table_url` 是否存在。
5. 写入或更新 `manager_id`、`manager_name`、`permission_scope`。
6. 根据最近黑灯结果更新 `latest_record_date`、`latest_daily_record_status`、`latest_period_summary_status`、`last_blacklight_run_at`、`data_quality_status`。

## 输出

- C01.0 索引记录。
- 缺表、权限、状态、数据质量异常写入 C07。

## 边界

- 只维护索引和状态。
- 不生成销售能力判断。
- 不创建或删除飞书表，缺表只标记异常。

## 验收

- 给定 1 个 active 销售，能定位其 C01 个人表。
- 给定 1 个转组销售，主管信息和权限范围能更新。
- 给定 1 个缺表销售，能标记为缺失并写 C07。
