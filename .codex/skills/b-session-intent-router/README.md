# B-SK01 会话启动与意图识别

本 skill 是 B 线白天会话入口，只负责把销售当前 Codex 会话分流成 `session_type` 和 `session_source`，为后续客户识别、Session 创建、材料挂载、FuelTank 判断做准备。

## 手动调用

`$b-session-intent-router`

## 使用人和场景

- 使用人：销售或代销售处理 B 线会话的 Agent。
- 场景：销售打开 Codex 后第一句话、继续一个销售会话、贴客户回复、上传材料、请求生成方案或处理一批客户。

## 输入

- 销售首句或当前用户请求。
- 当前 Codex conversation。
- 可选 `codex://threads/<threadId>`。
- 运行时 `sales_id`、`sales_name`、`work_date`，有则使用，没有则不猜。
- 活跃 `01_session` 线索，用于判断是否继续旧会话。

## 读取来源

- Codex 当前 session/thread。
- 用户提供的其他 Codex thread。
- 活跃 `01_session`，只用于判断是否继续会话。
- 不读取 A线客户主档、FuelTank、D线 registry、E线行动地图。

## 运行时写入字段

只允许写或提出写入。真实写入优先使用 `scripts/write-session-intent.ps1`：

| 表 | 字段 |
| --- | --- |
| `01_session` | `session_type` |
| `01_session` | `session_source` |
| `01_session` | `window_log` |
| `01_session` | `pending_items` |

## 不写字段

- 不写 `customer_id`、`customer_name_snapshot`、`start_snapshot_ref`。
- 不写 `raw_input_refs`。
- 不写 `02_fuel_tank`。
- 不写 D线、E线、A线、C线、`05_sync_log`。

## 配套脚本

| 脚本 | 作用 |
| --- | --- |
| `scripts/read-active-session.ps1` | 只读 `01_session` 的入口相关字段，判断是否继续已有会话。 |
| `scripts/write-session-intent.ps1` | 只写 `session_type`、`session_source`、`window_log`、`pending_items`。 |

脚本参数必须运行时传入，不能写死飞书 Base token、table id、record id、销售 ID、项目 ID 或 thread ID。

为方便初版快速定位，脚本内置本地默认表坐标；正式给其他人用时用参数覆盖。

| 对象 | 默认值 |
| --- | --- |
| Base token | `XtSIbjGLSarQHDs3y2ncaWffnze` |
| 表名 | `01_session` |
| Table ID | `tbl6u4j3HRjz9Ggk` |

| 字段名 | 字段 ID |
| --- | --- |
| `session_type` | `fld19k0EHl` |
| `session_source` | `fldihzgeGW` |
| `window_log` | `fldoGobDEz` |
| `pending_items` | `fldS3vVzep` |

## 关键规则

- Codex session/thread 是会话层原始来源。
- 初版可读本机当前会话或指定 `codex://threads/<threadId>`。
- 正式使用不能固定销售 ID、项目 ID、workspace、thread ID。
- 不能从系统用户名、Git 用户名、GitHub 用户名、本地目录推断销售身份。
- 只做入口分流，不做客户匹配、FuelTank 判断、D线推荐或行动建议。
- 模糊时写 `pending_items`，不要硬判。

## 验收标准

- 能输出明确的 `session_type` 和 `session_source`。
- 能列出 Codex session 来源。
- 只涉及 4 个允许写入字段。
- 能给出下一步应调用的 B 线 Skill。
- 模糊场景能提出最少澄清问题。

## 建设文件

- `modules/sales/skills/b-session-intent-router/SKILL.md`
- `modules/sales/skills/b-session-intent-router/README.md`
- `modules/sales/skills/b-session-intent-router/VERSION`
- `modules/sales/skills/b-session-intent-router/CHANGELOG.md`
- `modules/sales/skills/b-session-intent-router/scripts/read-active-session.ps1`
- `modules/sales/skills/b-session-intent-router/scripts/write-session-intent.ps1`
