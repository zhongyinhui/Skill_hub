# Skill Governance Router

这是 Skill Hub 的团队治理 skill，用于在创建、保存、上传、提交或发布 skill 前，提醒 Agent 检查命名、部门归属、分支和 PR 描述。

它不只做规则检查，也负责在每个阶段结束后给出下一步引导，帮助不熟悉流程的同事从本地草稿走到验证、提交、push、PR、审核和发布。

## 适用场景

- 创建或封装新 skill。
- 修改已有 skill。
- 上传同事在个人分支上的 skill。
- 判断 skill 应该放到哪个模块。
- 准备 commit、push 或 PR。

## 审核重点

- 是否使用拼音或英文 ASCII 作为机器识别名。
- 是否按功能命名 skill。
- 是否在创建前问清 skill 场景、输入、输出和可用标准。
- 是否在上传前确认部门模块。
- 是否用 commit 和 PR 描述补足长期工作分支缺失的信息。
- 是否运行 `tools/validate-skill.ps1`。
- 是否在阶段结束后说明当前状态和下一步建议。
- 是否把 approve 和 merge 分开处理，merge 前必须明确确认。
- 是否说明正式存放位置和项目 `$skill-name` 调用入口的区别。

## 阶段式引导

Agent 完成一个阶段后，应输出简短的状态提示：

```markdown
## 本阶段完成

已完成：
- 新建 skill 必要文件

当前状态：
- 还未运行 validate
- 还未 commit

建议下一步：
1. 运行校验和最小试运行
2. 继续优化 README 和示例

我建议先选 1，因为现在还没有证明它能通过仓库规则。
```

常见阶段包括：

- 需求确认
- 归属与命名
- 本地草稿
- 校验
- 项目可调用入口刷新
- commit 准备
- commit 完成
- push 完成
- PR 准备
- review / approve 完成
- merge 后检查

## 相关文档

- `docs/naming-and-routing.md`
- `docs/team-workflow.md`
- `docs/quickstart-for-teammates.md`

## 调用位置

正式 skill 放在：

```text
modules/<module-id>/skills/<skill-name>/
```

如果需要在本项目里手动用 `$skill-name` 调用，需要确保入口存在于：

```text
.codex/skills/<skill-name>/
```

从正式归档路径刷新项目可调用入口：

```powershell
powershell -ExecutionPolicy Bypass -File tools/sync-codex-skills.ps1 -SkillName <skill-name>
```

如果刷新后 `$skill-name` 仍不可见，通常需要新开 Codex 线程或刷新 skill 列表。
