# b-session-create

B-SK04，实际语义是“Codex 会话读取登记”。它不创建 Codex 会话，而是把已经存在的 Codex session/thread 登记成销售对应 B 线知识库里的 `01_session` 一条记录。

机器名暂保留 `b-session-create`，因为矩阵里 B-SK04 已经这样命名；验收时重点看语义是否已经改成读取/登记。

## 使用场景

- Codex 已经有当前会话，销售要把这次会话纳入 B 线记录。
- 用户提供了 `codex://threads/<threadId>`，需要把该 thread 作为原始来源登记。
- 本地初版需要读取 `C:\Users\<user>\.codex\sessions` 下的 JSONL。
- 后续 B-SK05 要把材料、turn、tool output 挂到同一条 B 线 `01_session`。

## 输入

- `sales_id`、`sales_name`、`work_date`
- Codex session 来源：当前 thread、`codex://threads/<threadId>` 或本地 JSONL 路径
- `session_type`、`session_source`
- 可选 `customer_id`、`customer_name_snapshot`
- `start_time`、`created_at`
- 销售对应 B 线知识库的 `BaseToken/TableId`

## 读取来源

- Codex 当前 session/thread。
- 可选 `codex://threads/<threadId>`。
- 本地 Codex JSONL：`C:\Users\<user>\.codex\sessions/**/*.jsonl`。
- B 线 `01_session`，用于检查该 Codex session 是否已登记。
- 本地初版存储绑定：`%USERPROFILE%\.codex-bline\storage-bindings.json`。

## 写入字段

只写销售对应 B 线知识库下的 `01_session`：

| 字段 | 字段 ID |
| --- | --- |
| `session_id` | `fld9l16mCy` |
| `sales_id` | `fldkHtOef5` |
| `sales_name` | `fldqjP1krI` |
| `work_date` | `fldriKhGrE` |
| `customer_id` | `fld0kKgYzg` |
| `customer_name_snapshot` | `fldGp1MXFd` |
| `session_type` | `fld19k0EHl` |
| `session_source` | `fldihzgeGW` |
| `session_status` | `fldTa42TPL` |
| `start_time` | `fldt792tJD` |
| `created_at` | `fldf1cIedD` |
| `raw_input_refs` | `fld6oO3sIZ` |
| `window_log` | `fldoGobDEz` |
| `remark` | `fldrEib3Wt` |

不写 `02_fuel_tank`，不写 A/C/D/E 线，不写 `05_sync_log`。

## 脚本

```powershell
# 列出最近 Codex session JSONL 候选文件
powershell -ExecutionPolicy Bypass -File modules/sales/skills/b-session-create/scripts/list-local-codex-sessions.ps1 -Limit 5

# 读取某个 Codex session JSONL 的 metadata
powershell -ExecutionPolicy Bypass -File modules/sales/skills/b-session-create/scripts/read-local-codex-session.ps1 `
  -SessionPath "C:\Users\<user>\.codex\sessions\...\rollout-xxx.jsonl"

# 解析运行时本人身份。正式多人使用时优先用 feishu_self。
powershell -ExecutionPolicy Bypass -File modules/sales/skills/b-session-create/scripts/resolve-runtime-operator.ps1 `
  -IdentitySource manual_confirmed `
  -SalesId "sales_runtime" `
  -SalesName "runtime_sales" `
  -IdentityRef "confirmed_by=operator; confirmed_at=2026-06-08 11:50"

# 本地初版：写入或切换“这台电脑/Codex目录 -> 销售 -> B线表”的绑定
powershell -ExecutionPolicy Bypass -File modules/sales/skills/b-session-create/scripts/write-local-storage-binding.ps1 `
  -SalesId "sales_runtime" `
  -SalesName "runtime_sales" `
  -IdentitySource "manual_confirmed" `
  -IdentityRef "confirmed_by=operator" `
  -BLineKnowledgeBaseKey "sales_runtime_bline" `
  -SessionBaseToken "XtSIbjGLSarQHDs3y2ncaWffnze" `
  -SessionTableId "tbl6u4j3HRjz9Ggk" `
  -ActiveFrom "2026-06-08 00:00:00" `
  -DryRun

# 员工离职/换人/账号续用：先关闭旧绑定，再新增新绑定
powershell -ExecutionPolicy Bypass -File modules/sales/skills/b-session-create/scripts/write-local-storage-binding.ps1 `
  -RetireActive `
  -SalesId "new_sales" `
  -SalesName "new_runtime_sales" `
  -IdentitySource "manual_confirmed" `
  -IdentityRef "handover_confirmed_by=manager" `
  -BLineKnowledgeBaseKey "new_sales_bline" `
  -SessionBaseToken "<new-or-same-base-token>" `
  -SessionTableId "<new-or-same-01-session-table-id>" `
  -ActiveFrom "2026-06-09 00:00:00" `
  -HandoverReason "account_reuse" `
  -DryRun

# 按 Codex session 发生时间解析应该写到哪个销售、哪个表
powershell -ExecutionPolicy Bypass -File modules/sales/skills/b-session-create/scripts/resolve-storage-binding.ps1 `
  -AtTime "2026-06-08 11:50:00"

# 每次登记/黑灯收割前的门禁检查；无绑定时会输出需要询问的字段
powershell -ExecutionPolicy Bypass -File modules/sales/skills/b-session-create/scripts/ensure-storage-binding.ps1 `
  -AtTime "2026-06-08 11:50:00"

# 本地 JSONL 场景：按每条 Codex 事件时间规划绑定分段。
# 如果账号无缝交接且同一条 session 跨过 cutover_at，会返回 split_required。
powershell -ExecutionPolicy Bypass -File modules/sales/skills/b-session-create/scripts/plan-session-binding-segments.ps1 `
  -SessionPath "C:\Users\<user>\.codex\sessions\...\rollout-xxx.jsonl"

# 根据 Codex 来源生成 B 线登记用 session_id
powershell -ExecutionPolicy Bypass -File modules/sales/skills/b-session-create/scripts/make-session-id.ps1 `
  -SalesId "sales_runtime" `
  -WorkDate "2026-06-08" `
  -CodexSourceRef "codex-session:019e96e6-dcdb-78c2-9122-e5eac19e2084"

# 查该 Codex session 是否已登记
powershell -ExecutionPolicy Bypass -File modules/sales/skills/b-session-create/scripts/find-registered-codex-session.ps1 `
  -CodexSourceRef "codex-session:019e96e6-dcdb-78c2-9122-e5eac19e2084" `
  -DryRun

# 登记到 B 线 01_session
powershell -ExecutionPolicy Bypass -File modules/sales/skills/b-session-create/scripts/register-codex-session.ps1 `
  -SessionId "BSES-20260608-salesruntime-codex1234567890" `
  -SalesId "sales_runtime" `
  -SalesName "runtime_sales" `
  -WorkDate "2026-06-08" `
  -SessionType "老客户跟进" `
  -SessionSource "销售主动" `
  -StartTime "2026-06-08 11:50:00" `
  -CreatedAt "2026-06-08 11:50:00" `
  -CodexSourceRef "codex-session:019e96e6-dcdb-78c2-9122-e5eac19e2084" `
  -OperatorIdentitySource "manual_confirmed" `
  -OperatorIdentityRef "confirmed_by=operator; confirmed_at=2026-06-08 11:50" `
  -DryRun
```

真实运行前先跑 `-DryRun`，确认写入的是销售对应 B 线知识库和 `01_session` 字段。

## 换人通知要求

销售换人、员工离职、账号续用、电脑交接或 Codex 数据目录继续给别人使用时，不能指望 Codex 自动猜出新老员工。负责人或当前操作者必须主动告诉 Codex：

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

收到这条通知后，Agent 才能用 `write-local-storage-binding.ps1 -RetireActive -ActiveFrom <cutover_at>` 关闭旧绑定并新增新绑定。没有通知或缺少 `cutover_at` 时，黑灯只允许输出 `need_confirm`，不能把旧历史按当前使用人回填。

## 关键规则

- Codex session 已经存在，本 skill 只读取并登记。
- Codex session id 不能证明本人；本人身份必须来自飞书本人授权、企业登录态或人工确认。
- 当前电脑也不能永久等同于某个销售；必须用带时间段的绑定决定 sessions 写到哪位销售、哪张表。
- 每次登记或黑灯收割前先检查绑定；无绑定、过期或冲突就停下来询问，不写默认表。
- 员工离职、换人、账号续用时，关闭旧绑定并新增新绑定；历史 session 按发生时间归旧人。
- 新老员工的判定不能靠账号自动猜，只能靠已确认的 `cutover_at`、身份来源和交接依据。
- 销售换人必须主动通知 Codex；没有通知时只能停下确认，不能靠“当前谁在用”自动覆盖历史归属。
- 无缝交接用半开区间 `[active_from, active_to)`：旧绑定的 `active_to` 等于新绑定的 `active_from`。
- 一个 Codex session 在同一个绑定窗口内默认登记成一条 B 线 `01_session`；如果同一条 JSONL 跨过 `cutover_at`，必须按 `codex_segment_ref` 分段登记。
- 防重优先按 Codex session 来源，不按客户重复开。
- `session_id` 是 B 线登记 ID，不是 Codex 原生 session id。
- Codex 来源必须写进 `raw_input_refs`。

## 当前状态

- 版本：`0.1.0`
- 状态：本地初版，等待验收。
- 同步：未同步到 `.codex/skills/b-session-create/`；通过验收后再单独同步本 skill。
