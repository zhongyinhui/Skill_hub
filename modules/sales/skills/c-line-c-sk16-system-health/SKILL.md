---
name: c-line-c-sk16-system-health
description: "Use when implementing, checking, expanding, or executing C-SK16 in the C-line P0 governance workflow for SaleAgentNo2: monitoring missing fields, broken source references, blacklight failures, permission problems, version conflicts, and public-table write conflicts as C07 health records."
---

# C-SK16 System Health

## 目标

监控字段缺失、数据断链、黑灯失败、权限问题、版本冲突和公共表写入冲突。

## 输入

- A/B/C/D/E 运行日志。
- `C-BL00` 调度结果。
- C01.0 数据质量状态。
- 各 C 表写入失败信息。

## 处理步骤

1. 检查必需字段是否存在。
2. 检查跨线来源引用是否缺失。
3. 检查 C 线黑灯是否未跑、失败或重复写入。
4. 检查销售个人表是否缺失、权限异常、数据断档。
5. 检查公共表是否存在并发写入冲突。
6. 写入 C07，标记影响范围、错误类型、建议修复动作。

## 输出

- C07 系统设计与维护记录。

## 边界

- 只记录和建议修复，不自动改表结构或权限。
- 不静默吞掉同步失败。
- 不把底层系统错误暴露给无关销售。

## 验收

- 字段缺失、同步失败、权限异常能进入 C07。
- C07 记录包含影响范围和建议修复动作。
- 公共表并发写入冲突能被记录并指向 `C-BL00` 调度修复。
