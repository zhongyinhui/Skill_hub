---
name: b-session-intent-router
description: B-SK01 B线会话启动与意图识别。Use when a sales user starts or continues a Codex sales work session and Codex must classify the entry request into 01_session.session_type and 01_session.session_source from runtime Codex session/thread context without hardcoding salesperson, project, or thread IDs.
---

# B-SK01 会话启动与意图识别

本 skill 是 B 线销售会话入口，只负责把 Codex 会话分流为 `session_type` 和 `session_source`。客户匹配、Session 创建、材料挂载、FuelTank 判断、D 线推荐都在后续 skill 做。

机器标识使用英文 `b-session-intent-router`；正文、验收、规则默认使用中文。

## 配套脚本

- `scripts/read-active-session.ps1`：只读 `01_session` 的入口相关字段，用于判断是否继续已有会话。
- `scripts/write-session-intent.ps1`：只写本 skill 允许的四个字段：`session_type`、`session_source`、`window_log`、`pending_items`。

脚本必须由运行时传入 `BaseToken`、`TableId`、`RecordId` 等参数，不允许写死销售 ID、项目 ID、workspace、thread ID 或飞书表 token。

脚本内置本地初版默认定位坐标，便于 AI 快速找到表；正式给其他人使用时必须覆盖这些参数。

| 对象 | 默认值 |
| --- | --- |
| Base token | `XtSIbjGLSarQHDs3y2ncaWffnze` |
| 表名 | `01_session` |
| Table ID | `tbl6u4j3HRjz9Ggk` |

## 运行时输入

- 销售首句或当前用户请求。
- 当前 Codex conversation。
- 可选 `codex://threads/<threadId>`，用于读取另一个 Codex 会话。
- 运行时身份：`sales_id`、`sales_name`、`work_date`，有则使用，没有则不猜。
- 活跃 `01_session` 线索，用于判断是否继续旧会话。

## 读取来源

- Codex 当前 session/thread 的对话与工具活动。
- 用户提供且可读取的 `codex://threads/<threadId>`。
- 活跃 `01_session`，仅用于判断是否继续已有会话；读取时优先使用 `scripts/read-active-session.ps1`。
- 本 skill 不读取 A 线客户主档、FuelTank、D 线 registry、E 线行动地图。

## 运行时写入契约

本 skill 只允许写入或提出写入以下 `01_session` 字段。真实写入优先使用 `scripts/write-session-intent.ps1`。

| 字段 | 值规则 |
| --- | --- |
| `session_type` | `新建客户`、`老客户跟进`、`上传材料`、`生成方案`、`批量处理`、`其他` 之一。 |
| `session_source` | `销售主动`、`行动地图建议`、`客户回复触发`、`黑灯待确认`、`其他` 之一。 |
| `window_log` | 简短记录分流依据，必要时包含 Codex thread/source 引用。 |
| `pending_items` | 意图或来源不清时的澄清问题、缺失上下文。 |

字段定位：

| 字段名 | 字段 ID |
| --- | --- |
| `session_type` | `fld19k0EHl` |
| `session_source` | `fldihzgeGW` |
| `window_log` | `fldoGobDEz` |
| `pending_items` | `fldS3vVzep` |

禁止写入 `customer_id`、`customer_name_snapshot`、`start_snapshot_ref`、`raw_input_refs`、FuelTank 字段、D 线字段、跨线同步字段。

## 分类规则

- 用户明确说新客户，或当前请求无法确认已有客户身份时，`session_type = 新建客户`。
- 请求围绕已知或被点名客户继续推进时，`session_type = 老客户跟进`。
- 主要动作是接收聊天、截图、录音、转写、文件时，`session_type = 上传材料`。
- 请求起草方案、话术、报价辅助、案例、客户侧材料时，`session_type = 生成方案`。
- 请求处理多个客户、多个会话、多个文件、多个记录时，`session_type = 批量处理`。
- 以上都不适合时才用 `其他`，并在 `window_log` 解释原因。
- 销售主动发起工作时，`session_source = 销售主动`。
- 明确来自 E 线行动地图时，`session_source = 行动地图建议`。
- 客户回复或客户材料触发时，`session_source = 客户回复触发`。
- 回复黑灯待确认事项时，`session_source = 黑灯待确认`。

## Workflow

1. 解析 Codex 会话来源：当前 conversation、用户给出的 `codex://threads/<threadId>`、或运行时导出的 session 材料。
2. 如需判断是否继续已有会话，调用 `scripts/read-active-session.ps1` 读取入口相关字段。
3. 基于当前请求和 Codex 会话证据判断 `session_type`、`session_source`。
4. 如用户点名客户，下一步路由到 `$b-customer-snapshot-loader`；本 skill 不解析客户。
5. 如用户说明是新客户，下一步路由到 `$b-new-customer-intake`。
6. 如请求只是接收材料，先确认是否已有 Session；没有则下一步路由到 `$b-session-create`，再到 `$b-material-reference-attach`。
7. 如请求生成方案或销售材料，仍先完成会话分流；D 线触发必须等 FuelTank 和 `$b-dline-trigger-recommend`。
8. 意图或来源不清时，只问最小澄清问题，并将不确定项写入 `pending_items`。
9. 需要落表时，调用 `scripts/write-session-intent.ps1`，只写四个允许字段。

## 硬规则

- 不固定销售 ID、项目 ID、workspace 路径、Codex thread ID、飞书 Base token 或 table id。
- 不从系统用户名、Git 用户名、GitHub 用户名、本地目录推断 `sales_id`。
- 不创造 `customer_id`。
- 不判断 FuelTank 充足度。
- 不推荐或触发 D 线。
- 不生成 E 线下一步行动。
- 不把闲聊算作有效沟通；有效沟通必须有需求、预算、决策链、异议、购买信号、确认下一步、方案反馈或阶段变化等信息增量。

## 输出格式

返回紧凑路由结果：

```text
B-SK01 路由结果
session_type: <one enum>
session_source: <one enum>
codex_session_source: <current | codex://threads/... | provided export | unknown>
write_fields:
- 01_session.session_type = ...
- 01_session.session_source = ...
- 01_session.window_log = ...
- 01_session.pending_items = ...
next_skill: <$b-... or none>
needs_human_confirmation: <true|false>
```

## 完成标准

- 请求有可解释的 `session_type` 和 `session_source`。
- 只写或提出写入四个允许字段。
- 下一步 B 线 skill 明确。
- 不确定项进入 `pending_items`，不靠猜。
