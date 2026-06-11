# B-SK02 客户ID识别与A线快照拉取

本 skill 把 Codex 会话里的客户线索对齐到 A 线客户档案，并把确认结果写回 B 线 `01_session`。它不是 A 线建档 skill，不修改 A 线正式事实。

## 手动调用

`$b-customer-snapshot-loader`

## 输入

- 客户名、别名、公司名、电话、微信 ID、企微 ID、source_id。
- 当前 Codex session/thread。
- 当前 `01_session` record id。
- 人工确认结果，若存在。

## 读取来源

| 来源 | Base token | Table ID |
| --- | --- | --- |
| B线 `01_session` | `XtSIbjGLSarQHDs3y2ncaWffnze` | `tbl6u4j3HRjz9Ggk` |
| A线客户主档 | `TqVmbOv2faej8MsJtkSccIv2nKb` | `tblT0pxNirTRQw9H` |
| A线 source_id 映射 | `IJK4bY3HhaWFcnsqwUncAV9rnje` | `tbl2fHDgqP7f4gyq` |
| A线客户别名 | `H5A7bXQtJaCVd0sqIircwepYnYf` | `tbl86wHfHgKpjfJp` |

## 运行时写入字段

| 表 | 字段 | 字段 ID |
| --- | --- | --- |
| `01_session` | `customer_id` | `fld0kKgYzg` |
| `01_session` | `customer_name_snapshot` | `fldGp1MXFd` |
| `01_session` | `start_snapshot_ref` | `fldFU71zf6` |
| `01_session` | `pending_items` | `fldS3vVzep` |

## 配套脚本

| 脚本 | 作用 |
| --- | --- |
| `scripts/search-a-customer-candidates.ps1` | 查询 A 线别名表、source 映射表、客户主档。 |
| `scripts/write-session-customer-snapshot.ps1` | 写回 B 线 `01_session` 的客户识别结果。 |

## 关键规则

- 唯一高置信才写 `customer_id`。
- 多候选、低置信、无候选时只写 `pending_items`，等人工确认。
- 不创建、不合并、不修改 A 线客户档案。
- 不固定销售 ID、项目 ID、workspace 或 Codex thread ID。
- `start_snapshot_ref` 是会话启动时引用，不是实时客户事实。

## 建设文件

- `modules/sales/skills/b-customer-snapshot-loader/SKILL.md`
- `modules/sales/skills/b-customer-snapshot-loader/README.md`
- `modules/sales/skills/b-customer-snapshot-loader/VERSION`
- `modules/sales/skills/b-customer-snapshot-loader/CHANGELOG.md`
- `modules/sales/skills/b-customer-snapshot-loader/scripts/search-a-customer-candidates.ps1`
- `modules/sales/skills/b-customer-snapshot-loader/scripts/write-session-customer-snapshot.ps1`
