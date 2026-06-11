# Changelog

## 0.1.0 - 2026-06-05

### Added

- 新增 B-SK01 会话启动与意图识别 skill。
- 明确输入、读取来源、运行时写入字段、禁止写入范围和关键规则。
- 明确 Codex session/thread 是会话层原始来源，禁止固定销售 ID、项目 ID、workspace 或 thread ID。
- 新增 `scripts/read-active-session.ps1` 和 `scripts/write-session-intent.ps1`，将 `01_session` 读写操作脚本化。
- 在脚本与文档中补充本地初版 `01_session` 的 Base token、table id 和字段 ID，便于 AI 快速定位，且保留运行时覆盖参数。
