# E-BL01 Blacklight Task Register

这个 skill 属于销售模块 E 线，已按 Skill Hub 正式路径归档到 `modules/sales/skills/sales-e-blacklight-task-register/`。

## 适用场景

Use when an E-line blacklight task must be registered, validated, enabled, disabled, or checked against the E01 task registry.

## 使用方式

- 先阅读 `SKILL.md`，确认触发条件、执行顺序和边界规则。
- 再阅读 `references/contract.md`，核对输入、输出、写入表和阻断条件。
- 如需执行脚本，先使用 `--dry-run` 查看计划写入，再由人工确认是否执行。

## 主要脚本

- `scripts/e_bl01_task_registry.py`

## 使用边界

- 不自动新增或修改飞书字段、表结构、权限或选项。
- 不绕过 `SKILL.md` 中的 Hard Rules。
- 涉及写入时必须保留来源引用，并先 dry-run 后确认。

## 归档来源

- 来源分支：`origin/zyh/lvjuntao / PR #15`
- 定向整理：从临时顶层目录整理为销售模块正式 skill 目录，并同步项目可调用入口。

