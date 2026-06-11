---
name: b-session-create
description: B-SK04 B线Codex会话读取登记。Use after B-SK01 customer routing when Codex must read an existing Codex session/thread and register exactly one traceable row in the salesperson's B-line 01_session table without creating Codex sessions or hardcoding salesperson, project, or thread IDs.
---

# B-SK04 Codex 会话读取登记

这个 skill 不创建 Codex 会话。Codex 会话在用户打开或继续 Codex thread 时已经存在。

本 skill 的意义是：读取当前或指定的 Codex session/thread，把它登记成销售 B 线知识库里的 `01_session` 一条记录。后续 B-SK05 材料挂载、B-SK06 FuelTank 和夜间黑灯，才能从这条 B 线记录追溯到原始 Codex 会话。

机器名仍保留 `b-session-create`，因为矩阵里 B-SK04 已经这样命名；实际语义按“读取登记 / register”执行。

## 配套脚本

| 脚本 | 作用 |
| --- | --- |
| `scripts/list-local-codex-sessions.ps1` | 本地初版列出 Codex session JSONL 候选文件。 |
| `scripts/read-local-codex-session.ps1` | 读取指定 Codex session JSONL 的 `session_meta` 和基础统计，生成可写入 B 线的来源引用。 |
| `scripts/resolve-runtime-operator.ps1` | 解析运行时操作者身份；优先用飞书本人授权或人工确认，不从 Codex session id 推断本人。 |
| `scripts/resolve-storage-binding.ps1` | 解析“这台电脑/这个 Codex 数据目录当前应该写到哪个销售、哪个 B 线表”。 |
| `scripts/ensure-storage-binding.ps1` | 每次登记或黑灯收割前执行的绑定门禁；有绑定继续，无绑定/冲突则输出需要询问的字段。 |
| `scripts/write-local-storage-binding.ps1` | 本地初版维护销售身份与 B 线表绑定，支持账号续用时关闭旧绑定并新增新绑定。 |
| `scripts/plan-session-binding-segments.ps1` | 按 Codex JSONL 每条事件时间匹配绑定窗口；遇到无缝交接、空窗或重叠时输出分段/待确认计划，不直接写表。 |
| `scripts/make-session-id.ps1` | 根据销售、日期、B线知识库和 Codex session 来源生成稳定的 B 线 `session_id`。 |
| `scripts/find-registered-codex-session.ps1` | 按 Codex 来源引用查 B 线 `01_session` 是否已登记，防止重复写一条。 |
| `scripts/register-codex-session.ps1` | 把已存在 Codex session 登记/更新到 B 线 `01_session`。 |

脚本内置当前本地初版 B 线表坐标；给别人使用时，必须先解析本地存储绑定或外部运行时绑定，再写到对应销售的 B 线知识库，不能固定某个人、某项目、某 thread。

## 默认表坐标

| 线 | 表 | Base token | Table ID |
| --- | --- | --- | --- |
| B | `01_session` | `XtSIbjGLSarQHDs3y2ncaWffnze` | `tbl6u4j3HRjz9Ggk` |

## 运行时输入

- 运行时 `sales_id`、`sales_name`、`work_date`。
- 当前 Codex session/thread，或可读取的 `codex://threads/<threadId>`，或本地初版 Codex JSONL 路径。
- B-SK01 输出的 `session_type`、`session_source`。
- 可选 `customer_id`、`customer_name_snapshot`、待确认客户说明。
- `start_time`、`created_at`，来自 Codex metadata 或运行时绝对时间。
- 销售对应的 B 线知识库定位：初版可用本地绑定文件，正式使用时由运行时路由传入 `BaseToken/TableId`。

## 读取来源

- Codex 当前 session/thread metadata 与 transcript。
- 可选 `codex://threads/<threadId>`。
- 本地初版 `C:\Users\<user>\.codex\sessions/**/*.jsonl`。
- B 线 `01_session`，只用于检查该 Codex session 是否已登记。
- B-SK01/B-SK02/B-SK03 的上一步结果。

## 运行时写入边界

只允许写入销售对应 B 线知识库下的 `01_session` 以下字段：

| 字段 | 字段 ID | 写入规则 |
| --- | --- | --- |
| `session_id` | `fld9l16mCy` | B 线登记 ID，不是 Codex 原生 session id；由销售、日期、B线知识库、Codex 来源稳定生成。 |
| `sales_id` | `fldkHtOef5` | 运行时传入；不从本机用户名、Git 用户名推断。 |
| `sales_name` | `fldqjP1krI` | 运行时传入。 |
| `work_date` | `fldriKhGrE` | 工作日期，格式 `yyyy-MM-dd`。 |
| `customer_id` | `fld0kKgYzg` | 已确认客户才写；没有确认时留空。 |
| `customer_name_snapshot` | `fldGp1MXFd` | 可选，记录本次 Codex 会话里出现的客户名快照。 |
| `session_type` | `fld19k0EHl` | 来自 B-SK01 或人工确认。 |
| `session_source` | `fldihzgeGW` | 来自 B-SK01 或人工确认。 |
| `session_status` | `fldTa42TPL` | 登记后默认 `running`；缺关键身份时可为 `need_confirm`。 |
| `start_time` | `fldt792tJD` | Codex 会话开始时间或运行时登记开始时间。 |
| `created_at` | `fldf1cIedD` | B 线记录创建时间。 |
| `raw_input_refs` | `fld6oO3sIZ` | 必须包含 Codex session/thread 引用，例如 `codex://threads/...` 或 `local-codex-session-jsonl:...`。 |
| `window_log` | `fldoGobDEz` | 记录读取/登记依据、是否复用旧记录。 |
| `remark` | `fldrEib3Wt` | 待确认客户、来源说明、注册备注。 |

禁止写入 `end_time`、`session_result_summary`、`dline_triggered`、`dline_call_ids`、`ready_for_blacklight`、`02_fuel_tank`、A/C/D/E 线或 `05_sync_log`。

## 核心判断

- Codex session 是原始会话层；B 线 `01_session` 是销售业务层索引。
- Codex session id 只证明“这条 Codex 会话存在”，不证明“这条会话属于哪个销售本人”。
- 一个 Codex session 默认登记成销售对应 B 线知识库里一条 `01_session` 记录。
- 如果同一 Codex session 已经登记，则复用已有 `01_session`，不重复写。
- 如果一个 Codex session 内后续识别出多个客户，当前 skill 不拆分；拆分/归属留给材料挂载、FuelTank 或夜间黑灯后续处理。

## 本人身份确认

不能用 `codex-session:<id>` 反推销售本人。登记 `sales_id/sales_name` 前必须有一个身份来源：

| 身份来源 | 是否可直接登记 running | 说明 |
| --- | --- | --- |
| `feishu_self` | 可以 | 当前运行时通过飞书用户授权拿到 `open_id=me`，再映射到销售 ID。 |
| `manual_confirmed` | 可以 | 用户明确确认“本次操作者就是某销售”，并记录确认人/时间。 |
| `external_runtime` | 可以 | 外部系统已经传入可信用户 ID，例如企业 SSO、内部调度器。 |
| `unknown` | 不可以 | 只能登记 `session_status=need_confirm`，并在 `remark` 写明身份未确认。 |

本地初版可先用 `manual_confirmed`；正式多人使用时，应优先用飞书 `open_id` 或企业登录态映射到销售档案。没有身份映射表时，不要把本机用户、Git 用户或 Codex session id 当作本人。

## 存储归属绑定

黑灯通常读取的是本机 Codex session 目录，例如 `C:\Users\<user>\.codex\sessions`。因此在读取 sessions 之前，必须先知道“这个 Codex 数据目录当前归属于哪个销售、应该写到哪个 B 线表”。

每次登记或夜间收割前都必须先跑绑定门禁：

```text
ensure-storage-binding.ps1 -> continue | ask_user
```

- `continue`：已经匹配到唯一绑定，可以继续读 Codex session 并写入目标 B 线表。
- `ask_user`：缺少绑定、绑定过期、时间段冲突或账号续用未登记。此时必须停下来询问，不允许写入默认表。

本地初版使用一个不提交进仓库的绑定文件，默认路径：

```text
%USERPROFILE%\.codex-bline\storage-bindings.json
```

绑定文件只存路由信息，不存密钥：

```json
{
  "schema_version": "1.0",
  "bindings": [
    {
      "binding_id": "bind-20260608-renqc",
      "status": "active",
      "active_from": "2026-06-08 00:00:00",
      "active_to": "",
      "sales_id": "sales_runtime",
      "sales_name": "runtime_sales",
      "identity_source": "manual_confirmed",
      "identity_ref": "confirmed_by=operator",
      "bline_knowledge_base_key": "sales_runtime_bline",
      "session_base_token": "XtSIbjGLSarQHDs3y2ncaWffnze",
      "session_table_id": "tbl6u4j3HRjz9Ggk",
      "handover_reason": "normal"
    }
  ]
}
```

员工离职、换人或账号续用时，不覆盖旧绑定。必须：

1. 给旧绑定写 `active_to`，状态改为 `retired`。
2. 新增一条新员工绑定，写新的 `active_from`。
3. 读取历史 Codex session 时，用 session 发生时间匹配绑定时间段。
4. 找不到绑定或匹配到多条绑定时，不写入正式 `running`，进入 `need_confirm`。

这样，旧员工在离职前的 sessions 仍然进入旧员工 B 线记录；新员工接手后的 sessions 才进入新员工 B 线记录。

### 无绑定时的询问字段

如果 `ensure-storage-binding.ps1` 返回 `ask_user`，Agent 必须只问最少关键项：

| 必问字段 | 说明 |
| --- | --- |
| `sales_id` | 当前这台电脑/Codex 目录要归属的销售 ID。 |
| `sales_name` | 销售姓名。 |
| `identity_source` | `feishu_self`、`manual_confirmed` 或 `external_runtime`。 |
| `identity_ref` | 身份确认依据，例如飞书 open_id、主管确认、交接单号。 |
| `session_base_token` | 该销售 B 线知识库 Base token。 |
| `session_table_id` | 该销售 B 线 `01_session` table id。 |
| `active_from` | 绑定从什么时候开始生效。 |
| `handover_reason` | `normal`、`employee_leave`、`account_reuse`、`device_reassignment` 等。 |

如果是员工离职、换人或账号续用，还要确认是否先关闭旧绑定，旧绑定的 `active_to` 应等于新绑定 `active_from`。

## 新老员工判定与无缝交接

不能从 Codex 账号、电脑用户名、Git 用户名、session id 或“当前谁在用电脑”自动判断新老员工。新老员工的唯一安全判定锚点是已确认的交接生效时间 `cutover_at`，来源可以是飞书本人授权、企业 SSO、主管确认、交接单或人工确认记录。

这不是一个纯技术自动识别问题，必须有管理动作配合：销售换人、员工离职、账号续用、电脑交接或 Codex 数据目录继续给别人使用时，负责人或当前操作者必须主动告诉 Codex“发生了交接”，并提供 `cutover_at`。没有这个通知，Codex 只能进入 `need_confirm`，不能把历史 session 按当前使用人回填。

推荐通知格式：

```text
销售换人通知：
- cutover_at: 2026-06-09 09:00:00
- old_sales_id: <旧销售ID>
- old_sales_name: <旧销售姓名>
- new_sales_id: <新销售ID>
- new_sales_name: <新销售姓名>
- handover_reason: employee_leave | account_reuse | device_reassignment
- handover_proof_ref: <交接单/主管确认/飞书 open_id/SSO 记录>
- new_target_bline: <Base token + 01_session table id>
```

收到该通知后，Agent 才能调用 `write-local-storage-binding.ps1 -RetireActive -ActiveFrom <cutover_at>`，把旧绑定结束在 `cutover_at`，并新增新员工绑定。

绑定时间段按半开区间处理：

```text
旧员工绑定：[old.active_from, old.active_to)
新员工绑定：[new.active_from, new.active_to)
无缝交接：old.active_to == new.active_from == cutover_at
```

无缝衔接时不要覆盖旧绑定，也不要把整台电脑历史都改成新人。正确做法是：

1. 旧绑定写入 `active_to=cutover_at`，状态标记为 `retired`。
2. 新绑定写入 `active_from=cutover_at`。
3. 历史 Codex session 按事件发生时间匹配绑定窗口。
4. 没有 `cutover_at`、交接证据不足、时间段空窗或重叠时，必须输出 `need_confirm`，不能登记为 `running`。

如果没有人提前通知，黑灯最多只能做异常拦截：当发现绑定缺失、过期、冲突，或当前身份来源与绑定不一致时，停下来询问交接信息。它不能从聊天语气、账号名称或最后使用人推断“已经换人”。

如果同一个 Codex JSONL 从交接前一直持续到交接后，不能再把整条 Codex session 固定登记成一个销售的一条记录。必须先运行：

```text
plan-session-binding-segments.ps1
```

分段规则：

- `segment_plan_status=ready`：整条 Codex session 的有时间戳事件都落在同一个绑定窗口，登记一条 `01_session`。
- `segment_plan_status=split_required`：同一条 Codex session 跨过交接时间，按每个 `codex_segment_ref` 分别登记；`raw_input_refs` 必须写入 `codex-session:<id>#binding:<binding_id>`。
- `segment_plan_status=need_confirm`：存在无绑定、绑定冲突或无时间戳事件，停下来询问 `cutover_at`、旧销售、新销售、交接依据和目标 B 线表。

## 工作流

1. 读取当前 Codex session/thread；本地初版可先用 `list-local-codex-sessions.ps1` 定位 JSONL，再用 `read-local-codex-session.ps1` 读取 metadata。
2. 得到 `codex_session_ref`，例如 `codex-session:<id>`、`codex://threads/<threadId>` 或 `local-codex-session-jsonl:<path>`。
3. 如果有本地 Codex JSONL，先运行 `plan-session-binding-segments.ps1`，按事件时间得到登记计划；如果只有 thread metadata，才用 session 开始时间调用 `ensure-storage-binding.ps1`。
4. 如果返回 `ask_user` 或 `segment_plan_status=need_confirm`，按输出的问题收集绑定/交接信息，调用 `write-local-storage-binding.ps1` 写入或切换绑定，然后重新执行门禁或分段计划。
5. 如果 `segment_plan_status=split_required`，对每个已解析 segment 分别执行后续查重、生成 `session_id` 和登记；每段使用自己的 `sales_id`、目标 B 线表和 `codex_segment_ref`。
6. 如果 `continue` 或 `segment_plan_status=ready`，使用返回的销售身份和目标 B 线表。
7. 用 `resolve-runtime-operator.ps1` 补充运行时身份来源；本地绑定已确认时可作为 `local_binding` 证据。
8. 用 `find-registered-codex-session.ps1` 查目标 `01_session.raw_input_refs/remark/session_id` 是否已有该来源或 segment 来源。
9. 若已登记，返回 `registered_status=reused`，后续 skill 使用已有 `01_session`。
10. 若未登记，调用 `make-session-id.ps1` 生成 B 线 `session_id`；跨交接分段时，`CodexSourceRef` 必须传 `codex_segment_ref`。
11. 调用 `register-codex-session.ps1` 写入目标 `01_session`，并把绑定来源写入 `remark`。
12. 下一步通常进入 `$b-material-reference-attach`，把当前 Codex turns、文件、截图、转写等材料挂到这条 B 线记录。

## 硬规则

- 不创建 Codex session，不 fork thread，不固定 thread id。
- 不把 Codex 原生 session id 当成销售系统业务 ID；它只能作为来源引用。
- 不把 Codex session id 当成本人身份；本人必须由飞书/SSO/人工确认等身份来源证明。
- 不把“当前电脑”永久等同于某个销售；必须有带生效时间段的本地/外部绑定。
- 每次收割 session 前都要检查绑定；无绑定、过期或冲突时必须询问并停止写入。
- 员工离职、换人、账号续用时，必须关闭旧绑定并新增新绑定；历史 session 按发生时间归属。
- 新老员工不能由账号或 session 自动推断；必须有 `cutover_at` 交接生效时间和身份确认来源。
- 销售换人、账号续用、电脑交接时，必须主动通知 Codex；未通知时只能 `need_confirm`，不能按当前使用人回填历史。
- 同一条 Codex JSONL 跨过 `cutover_at` 时，必须按绑定窗口拆成多个 `codex_segment_ref` 登记，不能把整条 session 归给一个人。
- 不固定销售 ID、项目 ID、workspace 路径或本机用户。
- 必须写入可追溯 Codex 来源引用。
- 不按客户重复开 session；防重优先按 Codex session 来源。
- 不写 FuelTank，不推荐或触发 D 线。

## 输出格式

```text
B-SK04 Codex 会话登记结果
registered_status: <created|reused|need_confirm|blocked>
codex_session_ref: <codex-session:id | codex://threads/... | local-codex-session-jsonl:path>
bline_session_id: <stable B-line session_id>
record_id: <01_session record id if known>
target_bline_table:
- base_token: <runtime B-line Base token>
- table_id: <runtime 01_session table id>
write_fields:
- 01_session.session_id = ...
- 01_session.sales_id = ...
- 01_session.sales_name = ...
- 01_session.work_date = ...
- 01_session.customer_id = ...
- 01_session.customer_name_snapshot = ...
- 01_session.session_type = ...
- 01_session.session_source = ...
- 01_session.session_status = running
- 01_session.start_time = ...
- 01_session.created_at = ...
- 01_session.raw_input_refs = <codex source ref>
- 01_session.window_log/remark = ...
next_skill: <$b-material-reference-attach | none>
```

## 完成标准

- 已读取到 Codex session/thread 来源。
- 已判断该 Codex session 是否已登记。
- 每个 Codex session 默认只登记一条 B 线 `01_session`。
- 写入字段只落在销售对应 B 线知识库的 `01_session`。
- 没有越界写 FuelTank、A/C/D/E 线或同步日志。
