# Changelog

## 0.1.0 - 2026-06-08

- 新增 B-SK04 `b-session-create` 正式 skill 初版。
- 根据验收反馈修正语义：本 skill 不创建 Codex 会话，只读取并登记已有 Codex session/thread。
- 明确一个 Codex session 默认登记为销售对应 B 线知识库下 `01_session` 一条记录。
- 补充本人身份确认规则：Codex session id 不等于销售本人，登记前必须有飞书本人授权、外部可信登录态或人工确认。
- 补充本机 Codex session 存储归属绑定：按时间段把本机 sessions 路由到对应销售和 B 线表，支持员工离职、换人和账号续用。
- 新增绑定门禁机制：每次登记或黑灯收割前检查绑定；无绑定、过期或冲突时输出询问字段并停止写入。
- 补充新老员工判定规则：不能从 Codex 账号、电脑用户名或 session id 自动推断，只能依赖已确认的 `cutover_at`、身份来源和交接依据。
- 补充销售换人通知要求：员工离职、账号续用、电脑交接或 Codex 数据目录续用时，负责人/操作者必须主动提供换人通知；未通知时只能 `need_confirm`，不能按当前使用人回填历史。
- 新增无缝交接分段脚本 `plan-session-binding-segments.ps1`：同一条 Codex JSONL 跨过交接时间时，按绑定窗口生成多个 `codex_segment_ref`，避免整条 session 被错误归给旧人或新人。
- 增加本地 Codex session JSONL 列表、metadata 读取、B 线 `session_id` 生成、登记查重、登记写入脚本。
- 内置当前初版 B 线 `01_session` Base/table/field 坐标，支持运行时参数覆盖，不固定销售、项目或 Codex thread。
