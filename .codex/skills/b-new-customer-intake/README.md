# b-new-customer-intake

B-SK03，B 线新客户建档会话 skill。当前用于销售在 Codex 会话里提出“这是新客户”或 B-SK02 找不到可靠 `customer_id` 时，先查重、再收集最小建档包，最后只写 B 线会话和夜间候选包。

## 使用场景

- 销售说“这是一个新客户”“帮我先记一下这个客户”。
- B-SK02 查不到唯一高置信 `customer_id`。
- 当前会话里有客户名、公司、联系人、来源、需求、截图、聊天记录、转写等新客户线索。

## 输入

- 客户名、公司、联系人、电话、微信ID、企微ID、source_id。
- 来源渠道、初始需求、客户反馈、销售补充。
- Codex 当前 session/thread、turn 引用、文件/截图/录音/转写等材料引用。
- 当前 `01_session` record id、`sales_id`、`work_date`。

## 读取来源

- Codex 当前 session/thread。
- B 线 `01_session`。
- A 线 `All_customer_files｜A线全部客户档案表`。
- A 线 `source_id_mapping`。
- A 线 `customer_alias_mapping`。

## 写入字段

只允许写：

- `01_session.session_type`
- `01_session.customer_name_snapshot`
- `01_session.raw_input_refs`
- `01_session.pending_items`
- `01_session.window_log`
- `01_session.ai_analysis_summary`
- `01_session.session_status`
- `01_session.ready_for_blacklight`
- `03_blacklight_output.blacklight_output_id`
- `03_blacklight_output.output_type`
- `03_blacklight_output.target_line`
- `03_blacklight_output.confirm_status`
- `03_blacklight_output.human_confirm_required`
- `03_blacklight_output.orphan_items`
- `03_blacklight_output.a_ready_package`
- `03_blacklight_output.source_session_ids`
- `03_blacklight_output.source_raw_input_refs`
- `03_blacklight_output.sales_id`
- `03_blacklight_output.customer_id`
- `03_blacklight_output.work_date`
- `03_blacklight_output.created_by`
- `03_blacklight_output.target_status`
- `03_blacklight_output.remark`
- `03_blacklight_output.effective_events_summary`

不写 A 线正式表，不写 `02_fuel_tank`、D/E/C 线和 `05_sync_log`。

## 脚本

```powershell
# 查重，默认查 A 线别名表、source 映射、主档
powershell -ExecutionPolicy Bypass -File modules/sales/skills/b-new-customer-intake/scripts/check-new-customer-duplicates.ps1 `
  -Keyword "王总" -SearchMode All -DryRun

# 写当前 01_session 的新客户最小包
powershell -ExecutionPolicy Bypass -File modules/sales/skills/b-new-customer-intake/scripts/write-new-customer-session.ps1 `
  -RecordId "rec_xxx" `
  -SessionType "新客户建档" `
  -CustomerNameSnapshot "王总" `
  -RawInputRefs "codex://threads/<threadId>#turn-12" `
  -PendingItems "待补公司名、电话；需确认不是已有客户" `
  -DryRun

# 写 03_blacklight_output 的 A 线待入账候选包
powershell -ExecutionPolicy Bypass -File modules/sales/skills/b-new-customer-intake/scripts/write-new-customer-candidate.ps1 `
  -BlacklightOutputId "B-SK03-20260608-001" `
  -SourceSessionIds "B-SESSION-001" `
  -SourceRawInputRefs "codex://threads/<threadId>#turn-12" `
  -AReadyPackage '{"customer_name":"王总","initial_need":"了解报价"}' `
  -SalesId "sales_runtime" `
  -WorkDate "2026-06-08" `
  -DryRun
```

所有脚本都使用文件式 JSON 写入 Base，避免 PowerShell 命令行直接拼中文 JSON。`a_ready_package` 如果是复杂 JSON，优先先保存成 UTF-8 文件，再用 `-AReadyPackageFile <path>` 传入，避免命令行吞掉双引号。

## 关键规则

- 新客户只进入 B 线候选，不直接进入 A 线正式账本。
- 查到多候选或低置信时，必须写待确认项，不自动归属。
- 不固定销售 ID、项目 ID、Codex thread ID。
- 原始材料必须可追溯，没有证据就不要写成客户事实。

## 当前状态

- 版本：`0.1.0`
- 状态：本地初版，等待验收。
- 同步：未同步到 `.codex/skills/b-new-customer-intake/`；通过验收后再单独同步本 skill。
