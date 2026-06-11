---
name: b-material-reference-attach
description: B-SK05 B线原始材料接收与引用挂载。Use when sales uploads or pastes chat text, screenshots, audio, files, transcripts, Codex turns, or tool outputs and Codex must append traceable material references to the current B-line 01_session without overwriting old raw_input_refs or turning summaries into formal customer facts.
---

# B-SK05 原始材料接收与引用挂载

本 skill 负责把销售给出的原始材料挂到当前 B 线 Session。它不分析客户阶段，不判断燃料是否充足，不把摘要写成 A 线事实。它只做一件事：把材料变成可追溯引用，并追加到销售对应 B 线知识库的 `01_session.raw_input_refs`。

## 配套脚本

| 脚本 | 作用 |
| --- | --- |
| `scripts/read-session-material-state.ps1` | 按 `record_id` 读取当前 `01_session` 的材料相关字段，只投影本 skill 需要的字段。 |
| `scripts/extract-session-material-refs.ps1` | 从 Codex session JSONL 自动提取已挂在会话里的输入材料，包括 `input_image` 和 `# Files mentioned by the user` 文件块。 |
| `scripts/new-material-ref.ps1` | 把文件、文本文件、外部链接、Codex turn/tool output 等来源整理成标准材料引用 JSON。 |
| `scripts/append-session-material-refs.ps1` | 合并旧 `raw_input_refs/window_log/ai_analysis_summary` 与新材料引用，去重后写回 `01_session`。 |

脚本内置当前初版 B 线 `01_session` 坐标；多人使用时必须由 B-SK04 的存储绑定或运行时路由传入对应销售的 `BaseToken/TableId`，不能固定本地测试表。

## 默认表坐标

| 线 | 表 | Base token | Table ID |
| --- | --- | --- | --- |
| B | `01_session` | `XtSIbjGLSarQHDs3y2ncaWffnze` | `tbl6u4j3HRjz9Ggk` |

## 运行时输入

- 当前 `01_session.record_id` 或已确认的 `session_id` 对应记录。
- 材料来源：粘贴文本、截图、录音、文件、转写、会议纪要、Codex turns、tool outputs、外部链接或 Feishu 文件 token。
- 材料来源引用：`codex-session:<id>#turn:<n>`、`codex-session:<id>#tool:<call_id>`、`local-file:<path>`、`feishu-file-token:<token>`、`external-url:<url>` 等。
- 可选 `customer_id/customer_name_snapshot`，只作为归属上下文，不创建客户事实。
- 运行时用户/销售身份和 B 线表路由，通常来自 B-SK04 的绑定结果。

## 读取来源

- 当前 Codex session/thread 内容和用户本轮粘贴/上传材料。
- 当前 `01_session` 的 `raw_input_refs/window_log/ai_analysis_summary`。
- B-SK04 已登记的 Codex session 或 segment 引用。
- 本地 Codex session JSONL 里的 `input_image` 内容和 `# Files mentioned by the user` 文件块。
- 本地文件元数据或文件 hash；不读取无法访问的外部系统内容。

## 运行时写入边界

只允许写入销售对应 B 线知识库下的 `01_session` 以下字段：

| 字段 | 字段 ID | 写入规则 |
| --- | --- | --- |
| `raw_input_refs` | `fld6oO3sIZ` | 追加 JSONL 材料引用；必须保留旧行；按 `material_ref_id/source_ref/content_sha256` 去重。 |
| `window_log` | `fldoGobDEz` | 追加本次挂载日志，说明材料数量、来源和是否需要人工确认。 |
| `ai_analysis_summary` | `fldNXsP73x` | 可选追加短摘要；只能描述材料内容，不得沉淀为客户正式事实。 |
| `updated_at` | `fldXP35X3X` | 写本次材料挂载时间。 |

禁止写入 `customer_id/customer_name_snapshot/session_status/pending_items/end_time/session_result_summary/dline_triggered/dline_call_ids/ready_for_blacklight`，也禁止写 `02_fuel_tank`、A/C/D/E 线或 `05_sync_log`。

## 材料引用格式

`raw_input_refs` 采用一行一个 JSON 对象的 JSONL 格式；旧的纯文本引用必须原样保留。

```json
{
  "schema": "b.material_ref.v1",
  "material_ref_id": "mref-20260608183000-abc12345",
  "material_type": "codex_turn",
  "source_ref": "codex-session:019e...#turn:24",
  "source_kind": "codex",
  "content_sha256": "optional_hash",
  "file_name": "",
  "file_size": 0,
  "mime_type": "",
  "local_path": "",
  "codex_line": 0,
  "codex_content_index": 0,
  "captured_at": "2026-06-08 18:30:00",
  "captured_by": "sales_runtime",
  "session_id": "BSES-...",
  "customer_id": "",
  "attribution_status": "session_confirmed",
  "summary": "客户补充了报价预算截图",
  "evidence_note": "from current Codex turn"
}
```

`source_ref` 必须能让后续 Agent 回到原材料；只有摘要没有来源时，不允许写成正式材料引用。

当材料已经挂在 Codex session 中时，优先使用 session 自动提取：

- `input_image`：原始图片通常以内联 `data:image/...;base64,...` 形式存在 JSONL。`raw_input_refs` 只写 `codex-session:<id>#line:<n>#content:<i>`、`content_sha256`、`mime_type` 和大小，不复制 base64。
- `# Files mentioned by the user`：Codex 会把用户上传/选择的本地文件以文本块形式放进用户消息。脚本会提取文件路径，能访问时计算 hash、大小和文件名。
- 普通用户文本里的散落本地路径默认不收割；只有显式传 `-IncludeLoosePaths` 才会当候选材料，避免把 cwd、项目路径、说明文字误当资料。

## 工作流

1. 确认当前 B 线 `01_session.record_id`；如果没有 Session，先回到 B-SK04。
2. 运行 `read-session-material-state.ps1` 读取旧 `raw_input_refs/window_log/ai_analysis_summary`。
3. 如果有本地 Codex JSONL，先运行 `extract-session-material-refs.ps1` 自动收割该 session 已挂载的输入材料。
4. 对脚本未覆盖的外部材料，再运行 `new-material-ref.ps1` 生成材料引用；文件类材料必须记录路径或文件 token + hash。
5. 判断归属：
   - 明确属于当前 Session：`attribution_status=session_confirmed`。
   - 明确属于当前客户：`attribution_status=customer_confirmed`，但仍不写 A 线事实。
   - 材料来源不清：`attribution_status=needs_confirm`。
   - 没有客户或 Session 归属：`attribution_status=orphan_candidate`，留给黑灯无主材料归属。
6. 运行 `append-session-material-refs.ps1` 合并旧状态和新引用；默认必须提供旧状态，避免覆盖旧材料。
7. 如果输出里有 `human_confirm_required=true`，本 skill 只在材料引用中标记待确认，不额外写 `pending_items`。
8. 下一步进入 `$b-fuel-tank-state-build`，让 FuelTank 基于新材料重建状态。

## 硬规则

- 材料必须可追溯；不得只写“客户说了什么”的摘要。
- 读取 Codex session 时必须先尝试自动提取 session 内已有输入材料；不要要求销售重复上传一遍。
- 不覆盖旧 `raw_input_refs`；旧纯文本引用也要保留。
- 新材料按 `material_ref_id/source_ref/content_sha256` 去重。
- 无主材料和低置信材料只能标记 `needs_confirm/orphan_candidate`，不能硬挂客户。
- `ai_analysis_summary` 只能写材料摘要，不能变成 A 线客户事实。
- 不创建客户、不修正客户 ID、不写 FuelTank、不触发 D 线。
- 不固定销售 ID、项目 ID、Codex thread ID 或本地文件路径；这些必须来自运行时输入。
- 截图、录音、文件如果只有本地路径，必须同时记录 hash；如果以后上传到 Feishu，再新增引用而不是改写旧引用。

## 输出格式

```text
B-SK05 材料挂载结果
attach_status: <updated|dry_run|need_confirm|blocked>
session_record_id: <01_session record id>
target_bline_table:
- base_token: <runtime Base token>
- table_id: <runtime 01_session table id>
material_refs:
- <material_ref_id> <material_type> <source_ref> <attribution_status>
write_fields:
- 01_session.raw_input_refs = append only
- 01_session.window_log = append attach log
- 01_session.ai_analysis_summary = optional append summary
- 01_session.updated_at = <absolute datetime>
human_confirm_required: <true|false>
next_skill: <$b-fuel-tank-state-build | none>
```

## 完成标准

- 已读取旧材料状态或明确允许首次空写。
- 每份材料都有 `source_ref` 和可追溯证据。
- 新引用已追加、去重，不覆盖旧引用。
- 只写 `01_session.raw_input_refs/window_log/ai_analysis_summary/updated_at`。
- 无主或低置信材料已标记待确认，没有硬挂到客户。
