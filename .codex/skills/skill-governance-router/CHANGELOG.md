# Changelog

## 0.3.0 - 2026-05-11

### Added

- 增加创建前最小需求追问，避免用户只说“创建一个 skill”时直接落地文件。
- 模块选项改为英文机器 ID + 中文部门名展示，保留目录结构兼容性。
- 明确 skill 目录名、frontmatter `name` 和 `$skill-name` 调用名必须一致。
- 增加正式存放路径与项目 `.codex/skills/` 可调用入口的区别说明。

## 0.2.0 - 2026-05-11

### Added

- 增加阶段式流程引导，要求 Agent 在本地草稿、校验、commit、push、PR、review 和 merge 等节点给出下一步建议。
- 增加动作分级：自动动作、确认后动作、强确认动作。
- 明确 approve 和 merge 分离，merge 前必须说明目标分支和影响并获得明确确认。
- 增加新人 quickstart 文档引用。

## 0.1.0 - 2026-05-08

### Added

- 新增 Skill Hub 团队治理 skill。
- 约束 skill 命名、部门归属确认、个人工作分支、commit 和 PR 描述规则。
- 要求上传、推送或创建 PR 前主动确认目标模块。
