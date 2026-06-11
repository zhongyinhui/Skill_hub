---
name: b-new-customer-intake
description: B-SK03 B线新客户建档会话。Use after B-SK02 when no reliable customer_id exists or sales says this is a new customer; collect the minimum filing package, check A-line duplicates, write only B-line session/candidate fields, and never create formal A-line customer records directly.
---

# B-SK03 新客户建档会话

本 skill 用于 B 线白天会话里“疑似新客户”的最小建档收集。它先做 A 线查重，再把当前会话能确定的客户名称、来源、初始需求和证据引用写回 B 线；需要夜间沉淀时，只生成 `03_blacklight_output` 的候选包，等待人工确认和 A 线入账流程。

## 配套脚本

| 脚本 | 作用 |
| --- | --- |
| `scripts/check-new-customer-duplicates.ps1` | 按客户名、公司、电话、企微ID、微信ID、source_id 等线索查 A 线主档、source 映射和别名表，判断是否疑似重复。 |
| `scripts/write-new-customer-session.ps1` | 把新客户会话的最小建档信息写入 B 线 `01_session`。 |
| `scripts/write-new-customer-candidate.ps1` | 把夜间可处理的新客户候选包写入 B 线 `03_blacklight_output`。 |

脚本内置当前本地初版 Base/table/field 坐标；后续给别人使用时，可通过参数覆盖 Base token 和 Table ID，不允许写死销售、项目或 Codex thread。

## 默认表坐标

| 线 | 表 | Base token | Table ID |
| --- | --- | --- | --- |
| B | `01_session` | `XtSIbjGLSarQHDs3y2ncaWffnze` | `tbl6u4j3HRjz9Ggk` |
| B | `03_blacklight_output` | `QznJbdaDKaM8O0s2GFqcMkjsncc` | `tbldZtvYSwT5C8KB` |
| A | `All_customer_files｜A线全部客户档案表` | `TqVmbOv2faej8MsJtkSccIv2nKb` | `tblT0pxNirTRQw9H` |
| A | `source_id_mapping` | `IJK4bY3HhaWFcnsqwUncAV9rnje` | `tbl2fHDgqP7f4gyq` |
| A | `customer_alias_mapping` | `H5A7bXQtJaCVd0sqIircwepYnYf` | `tbl86wHfHgKpjfJp` |

## 运行时输入

- 新客户名称、公司、联系人、电话、微信ID、企微ID、source_id、来源渠道。
- 初始需求、客户原话摘要、销售补充、首次沟通材料。
- Codex 当前 session/thread 引用，例如当前会话、`codex://threads/<threadId>`、turn/tool output 引用。
- 当前 `01_session` record id、`sales_id`、`work_date`，如果已经由前序 skill 建立。

## 读取来源

- Codex 当前 session/thread transcript，用作原始证据来源。
- B 线当前 `01_session`，读取已存在的 `session_type`、`raw_input_refs`、`pending_items`，避免覆盖。
- A 线 `All_customer_files｜A线全部客户档案表`、`source_id_mapping`、`customer_alias_mapping`，只用于查重和候选识别。

## 运行时写入边界

### `01_session` 允许写入

| 字段 | 字段 ID | 写入规则 |
| --- | --- | --- |
| `session_type` | `fld19k0EHl` | 固定写为 `新客户建档` 或等价已配置选项；不代表 A 线正式建档完成。 |
| `customer_name_snapshot` | `fldGp1MXFd` | 当前销售输入的新客户展示名，必须来自会话证据。 |
| `raw_input_refs` | `fld6oO3sIZ` | Codex session/thread、粘贴材料、文件、截图、转写等可追溯引用；追加而不是覆盖。 |
| `pending_items` | `fldS3vVzep` | 缺少电话、公司、来源、重复确认等待办。 |
| `window_log` | `fldoGobDEz` | 记录“进入新客户建档/查重结果/待确认项”。 |
| `ai_analysis_summary` | `fldNXsP73x` | 对最小建档包的结构化摘要，不写成 A 线事实。 |
| `session_status` | `fldTa42TPL` | 常用值：`need_confirm`、`active`、`ready_for_blacklight`。 |
| `ready_for_blacklight` | `fldlf734Ar` | 只有最小包足够且需夜间处理时才写 `true`。 |

### `03_blacklight_output` 允许写入

| 字段 | 字段 ID | 写入规则 |
| --- | --- | --- |
| `blacklight_output_id` | `fldDK5Aegp` | 新客户候选包的稳定运行内 ID。 |
| `output_type` | `fldyiXR2fZ` | 默认 `a_ready_package`；低置信无主材料可用 `orphan_confirm`。 |
| `target_line` | `fldHxSt8oS` | 默认 `["A"]`，表示只交给 A 线待入账，不直写 A 线。 |
| `confirm_status` | `fldwXd47fE` | 默认 `need_confirm`。 |
| `human_confirm_required` | `fldcgq6nGr` | 新客户候选默认 `true`。 |
| `orphan_items` | `fldr5wl4Ks` | 无法稳定归属或重复风险说明。 |
| `a_ready_package` | `fld7rNsZAl` | 候选 A 线建档包 JSON/text。 |
| `source_session_ids` | `fldmnNlJQR` | 来源 B 线 session id 列表或文本。 |
| `source_raw_input_refs` | `fldxY0v2EH` | 原始证据引用列表或文本。 |
| `sales_id` | `fldoOZmfAH` | 运行时传入，不从本机或 git 推断。 |
| `customer_id` | `fldgWlq0wW` | 新客户阶段通常留空；疑似重复时只可填待确认候选说明，不当作正式确认。 |
| `work_date` | `fldGIh5vTZ` | 运行时日期，使用绝对日期。 |
| `created_by` | `fldZqijdD1` | 运行时操作者或 `b-new-customer-intake`。 |
| `target_status` | `fldgpjIyVq` | 默认 `pending_a_confirm` 或当前表内等价状态。 |
| `remark` | `fldmS6XsUy` | 重复风险、缺失项、人工确认说明。 |
| `effective_events_summary` | `fldpT6zXPM` | 当日有效事件摘要。 |

## A 线查重字段坐标

| 来源 | 字段名 | 字段 ID |
| --- | --- | --- |
| A 主档 | `customer_id` | `fld3zQdj2W` |
| A 主档 | `customer_name` | `fldCXrp4EA` |
| A 主档 | `company_name` | `fldn06FZxa` |
| A 主档 | `phone` | `fld8SKqgSv` |
| A 主档 | `wecom_id` | `fldUHaTdCD` |
| A 主档 | `wechat_id` | `fldoKLamfO` |
| A 主档 | `source_id` | `fldwwN3g9g` |
| source 映射 | `source_id` | `fldWa3J7CZ` |
| source 映射 | `linked_customer_id` | `fld1YjyVai` |
| source 映射 | `candidate_customer_ids` | `fldIStQwyg` |
| source 映射 | `raw_customer_name` | `fld0v1zjA9` |
| source 映射 | `raw_phone` | `fldY4ZgNxG` |
| 别名表 | `alias_value` | `fldvJB2XZ5` |
| 别名表 | `normalized_alias` | `fldiBLwK1U` |
| 别名表 | `customer_id` | `fldbTJ7xWS` |
| 别名表 | `confidence_score` | `fldyBuDQYc` |
| 别名表 | `conflict_status` | `fldWsjfsxj` |

## 工作流

1. 从当前 Codex session/thread 提取新客户线索和原始材料引用，不固定 thread id。
2. 调用 `scripts/check-new-customer-duplicates.ps1 -SearchMode All` 查 A 线主档、source 映射、别名表。
3. 如果存在唯一高置信客户，停止新客户流程，转回 `$b-customer-snapshot-loader` 或人工确认。
4. 如果多候选、冲突或低置信，写 `pending_items`，不要自动建新客户。
5. 如果无可靠重复候选，收集最小建档包：客户名、公司/联系人、至少一种联系或来源线索、初始需求、证据引用。
6. 用 `scripts/write-new-customer-session.ps1` 写回 `01_session` 的允许字段。
7. 需要夜间沉淀时，用 `scripts/write-new-customer-candidate.ps1` 创建 `03_blacklight_output` 候选包，等待人工确认和 A 线入账。

## 硬规则

- 不创建、不更新、不合并 A 线正式客户主档。
- 不伪造 `customer_id`，不从新客户材料直接生成正式 A 线客户 ID。
- 疑似重复必须人工确认；低置信不得自动归属。
- 不固定销售 ID、项目 ID、Codex thread ID、本机路径或系统用户名。
- 只收最小建档包，不让销售填长表。
- `raw_input_refs` 必须可追溯；没有主材料时进入 `pending_items` 或 `orphan_items`。
- 不写 `02_fuel_tank`、D 线、E 线、C 线、`05_sync_log`。

## 输出格式

```text
B-SK03 新客户建档结果
duplicate_status: <none|multiple|need_confirm|matched_existing>
customer_name_snapshot: <name>
minimum_package_status: <complete|missing_required|need_confirm>
raw_input_refs:
- <codex/session/file/chat ref>
pending_items:
- <missing or confirmation item>
write_fields:
- 01_session.session_type = 新客户建档
- 01_session.customer_name_snapshot = ...
- 01_session.raw_input_refs = ...
- 01_session.pending_items = ...
- 03_blacklight_output.output_type = a_ready_package
- 03_blacklight_output.a_ready_package = ...
next_skill: <$b-material-reference-attach | $b-session-create | none>
```

## 完成标准

- 已完成 A 线查重，且查重来源清楚。
- 已形成最小建档包或明确列出缺失项。
- 只写 B 线允许字段，未直写 A 线。
- 夜间候选包有来源 session 和原始材料引用。
