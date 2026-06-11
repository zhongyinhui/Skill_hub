# b-material-reference-attach

B-SK05，原始材料接收与引用挂载。它把销售提供的聊天、截图、录音、文件、转写、Codex turns 或 tool outputs 追加到当前 B 线 `01_session.raw_input_refs`，形成可追溯证据链。

## 手动调用

`$b-material-reference-attach`

## 输入

- 当前 `01_session.record_id`
- 材料来源：粘贴文本、截图、录音、文件、转写、会议纪要、Codex turn、tool output
- 来源引用：`codex-session:<id>#turn:<n>`、`local-file:<path>`、`feishu-file-token:<token>` 等
- 旧的 `raw_input_refs/window_log/ai_analysis_summary`
- 运行时 B 线表坐标：`BaseToken/TableId`

## 读取来源

- 当前 Codex session/thread
- 当前 `01_session`
- 已有 `raw_input_refs`
- Codex JSONL 内的 `input_image` 和 `# Files mentioned by the user`
- 本地文件 hash 或外部文件 token

## 写入字段

只写 `01_session`：

| 字段 | 字段 ID |
| --- | --- |
| `raw_input_refs` | `fld6oO3sIZ` |
| `window_log` | `fldoGobDEz` |
| `ai_analysis_summary` | `fldNXsP73x` |
| `updated_at` | `fldXP35X3X` |

不写客户正式事实，不写 FuelTank，不写 A/C/D/E 线。

## 脚本

```powershell
# 读取当前 Session 的材料状态
powershell -ExecutionPolicy Bypass -File modules/sales/skills/b-material-reference-attach/scripts/read-session-material-state.ps1 `
  -RecordId "rec_xxx"

# 从 Codex session JSONL 自动提取已挂载的输入图片和 Files mentioned 文件
powershell -ExecutionPolicy Bypass -File modules/sales/skills/b-material-reference-attach/scripts/extract-session-material-refs.ps1 `
  -SessionPath "C:\Users\<user>\.codex\sessions\...\rollout-xxx.jsonl" `
  -CapturedBy "sales_runtime" `
  -MaxRefs 200

# 文件材料生成引用
powershell -ExecutionPolicy Bypass -File modules/sales/skills/b-material-reference-attach/scripts/new-material-ref.ps1 `
  -MaterialType file `
  -LocalPath "D:\path\quote.png" `
  -SessionId "BSES-..." `
  -CapturedBy "sales_runtime" `
  -AttributionStatus "session_confirmed"

# Codex turn 材料生成引用
powershell -ExecutionPolicy Bypass -File modules/sales/skills/b-material-reference-attach/scripts/new-material-ref.ps1 `
  -MaterialType codex_turn `
  -SourceRef "codex-session:019e...#turn:24" `
  -SessionId "BSES-..." `
  -CapturedBy "sales_runtime" `
  -Summary "客户补充了预算和竞品信息" `
  -AttributionStatus "session_confirmed"

# 追加写回。默认必须传入旧状态，避免覆盖旧 raw_input_refs/window_log。
powershell -ExecutionPolicy Bypass -File modules/sales/skills/b-material-reference-attach/scripts/append-session-material-refs.ps1 `
  -RecordId "rec_xxx" `
  -ExistingRawInputRefsFile ".tmp\old-raw-input-refs.txt" `
  -ExistingWindowLogFile ".tmp\old-window-log.txt" `
  -ExistingAiAnalysisSummaryFile ".tmp\old-ai-summary.txt" `
  -NewMaterialRefsFile ".tmp\new-material-refs.jsonl" `
  -MaterialSummary "新增客户预算截图和一段 Codex turn 证据" `
  -DryRun
```

真实写入前先跑 `-DryRun`，确认 payload 只包含允许字段。

## 关键规则

- 只追加，不覆盖。
- 读取 Codex session 时先自动收割 session 内已有材料，不要求销售重复上传。
- 材料必须有 `source_ref`，摘要不能替代原始证据。
- `input_image` 只写 session 行号引用、hash、大小和 mime，不把 base64 塞进 `raw_input_refs`。
- `# Files mentioned by the user` 文件块默认自动提取；普通文本里的散落路径默认不收割。
- 文件类材料必须记录 hash；以后上传到 Feishu 时新增引用，不改写旧引用。
- 无主材料标记为 `orphan_candidate` 或 `needs_confirm`，留给黑灯处理。
- `ai_analysis_summary` 只是材料摘要，不是 A 线客户事实。

## 当前状态

- 版本：`0.1.0`
- 状态：本地初版，等待验收。
- 同步：未同步到 `.codex/skills/b-material-reference-attach/`；通过验收后再单独同步本 skill。
