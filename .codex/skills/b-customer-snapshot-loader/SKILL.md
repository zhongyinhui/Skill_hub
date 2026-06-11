---
name: b-customer-snapshot-loader
description: B-SK02 B线客户ID识别与A线快照拉取。Use after B-SK01 when Codex must resolve customer_id from Codex session clues, A-line alias/source/master tables, then write customer_id, customer_name_snapshot, start_snapshot_ref, and pending_items back to 01_session without directly editing A-line records.
---

# B-SK02 客户ID识别与A线快照拉取

本 skill 用于把销售会话里的客户线索，对齐到 A 线正式客户档案，并把启动快照引用写回 B 线 `01_session`。它只做识别与引用，不改 A 线正式事实。

## 配套脚本

| 脚本 | 作用 |
| --- | --- |
| `scripts/search-a-customer-candidates.ps1` | 按关键词查询 A 线别名表、source_id 映射表、客户主档。 |
| `scripts/write-session-customer-snapshot.ps1` | 将已确认的客户 ID、客户名快照、A 线快照引用写回 `01_session`。 |

脚本内置本地初版默认表坐标；正式给其他人使用时可以用参数覆盖。

## 默认表坐标

| 线 | 表 | Base token | Table ID |
| --- | --- | --- | --- |
| B | `01_session` | `XtSIbjGLSarQHDs3y2ncaWffnze` | `tbl6u4j3HRjz9Ggk` |
| A | `All_customer_files｜A线全部客户档案表` | `TqVmbOv2faej8MsJtkSccIv2nKb` | `tblT0pxNirTRQw9H` |
| A | `source_id_mapping` | `IJK4bY3HhaWFcnsqwUncAV9rnje` | `tbl2fHDgqP7f4gyq` |
| A | `customer_alias_mapping` | `H5A7bXQtJaCVd0sqIircwepYnYf` | `tbl86wHfHgKpjfJp` |

## 运行时输入

- 来自 Codex session/thread 的客户线索：客户名、别名、公司、电话、微信 ID、企微 ID、source_id。
- 当前 `session_id` 或 `01_session` record id。
- B-SK01 输出的会话上下文。
- 可选人工确认结果。

## 读取来源

- Codex 当前 session/thread。
- A 线 `customer_alias_mapping`。
- A 线 `source_id_mapping`。
- A 线 `All_customer_files｜A线全部客户档案表`。
- 当前 B 线 `01_session`。

## 运行时写入契约

本 skill 只允许写入或提出写入以下 `01_session` 字段：

| 字段 | 字段 ID | 值规则 |
| --- | --- | --- |
| `customer_id` | `fld0kKgYzg` | 唯一高置信客户 ID；多候选时不写。 |
| `customer_name_snapshot` | `fldGp1MXFd` | 识别当时的客户展示名。 |
| `start_snapshot_ref` | `fldFU71zf6` | A 线主档记录、个体客户容器或快照引用。 |
| `pending_items` | `fldS3vVzep` | 多候选、无候选、低置信或需要销售确认时写明。 |

## 关键字段定位

| 来源 | 字段名 | 字段 ID |
| --- | --- | --- |
| A主档 | `customer_id` | `fld3zQdj2W` |
| A主档 | `customer_name` | `fldCXrp4EA` |
| A主档 | `company_name` | `fldn06FZxa` |
| A主档 | `phone` | `fld8SKqgSv` |
| A主档 | `wecom_id` | `fldUHaTdCD` |
| A主档 | `wechat_id` | `fldoKLamfO` |
| A主档 | `source_id` | `fldwwN3g9g` |
| A主档 | `latest_snapshot_text` | `fldX0yjRMb` |
| A主档 | `latest_snapshot_json` | `fldpzf6zst` |
| A主档 | `individual_customer_table_url` | `fldaLCJY97` |
| source映射 | `source_id` | `fldWa3J7CZ` |
| source映射 | `linked_customer_id` | `fld1YjyVai` |
| source映射 | `candidate_customer_ids` | `fldIStQwyg` |
| source映射 | `raw_customer_name` | `fld0v1zjA9` |
| source映射 | `raw_phone` | `fldY4ZgNxG` |
| 别名表 | `alias_value` | `fldvJB2XZ5` |
| 别名表 | `normalized_alias` | `fldiBLwK1U` |
| 别名表 | `customer_id` | `fldbTJ7xWS` |
| 别名表 | `confidence_score` | `fldyBuDQYc` |
| 别名表 | `conflict_status` | `fldWsjfsxj` |

## Workflow

1. 从当前 Codex session/thread 提取客户线索，不固定 thread id。
2. 优先用 `scripts/search-a-customer-candidates.ps1 -SearchMode All` 查询别名表、source 映射表、A 主档。
3. 若唯一高置信匹配存在，准备写回 `01_session.customer_id/customer_name_snapshot/start_snapshot_ref`。
4. 若出现多候选、冲突、低置信或无候选，只写 `pending_items`，并要求人工确认。
5. 需要落表时，调用 `scripts/write-session-customer-snapshot.ps1`。
6. 无候选时，下一步路由到 `$b-new-customer-intake`。

## 硬规则

- 不直接创建、合并、覆盖 A 线客户档案。
- 不把多个疑似客户自动合并。
- 不从本机路径、系统用户名、Git 用户名推断销售身份或客户身份。
- 不把 `start_snapshot_ref` 当作实时事实；它只是会话启动时的 A 线引用。
- 不写 FuelTank、D 线、E 线、C 线、`05_sync_log`。

## 输出格式

```text
B-SK02 客户识别结果
match_status: <unique|multiple|none|need_confirm>
customer_id: <confirmed id or empty>
customer_name_snapshot: <name or empty>
start_snapshot_ref: <url/ref or empty>
candidate_sources:
- alias: ...
- source_id: ...
- master: ...
write_fields:
- 01_session.customer_id = ...
- 01_session.customer_name_snapshot = ...
- 01_session.start_snapshot_ref = ...
- 01_session.pending_items = ...
next_skill: <$b-session-create | $b-new-customer-intake | none>
```

## 完成标准

- 客户匹配来源和置信理由清楚。
- 唯一高置信才写客户 ID。
- 多候选或无候选时停在人确认，不猜。
- 只写允许的 `01_session` 字段。
