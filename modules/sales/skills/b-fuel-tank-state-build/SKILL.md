---
name: b-fuel-tank-state-build
description: B-SK06 B线FuelTank持续追加沉淀。Use after a B-line 01_session exists or new materials/attachments are added, when Codex must extract process fuel from the current session, raw_input_refs, attachments, tool outputs, and sales supplements, then append a fuel_event into exactly one active 02_fuel_tank state row without judging fuel sufficiency, customer stage, objections, buying signals, risks, or D-line triggers.
---

# B-SK06 FuelTank 实时状态装配

本 skill 负责从当前 Codex session、附件/material refs、tool outputs、销售补充和客户反馈里提取推进燃料，并持续追加到同一个 active `02_fuel_tank`。它不是“判断 skill”，只负责把后续 B-SK07/B-SK08/B-SK11 需要的过程燃料不断沉淀好。

FuelTank 的正确模型是 append-only 过程沉淀：

- 每次 session 或附件有新增输入，就抽取一个 `fuel_event`。
- `fuel_event` 追加进 `new_inputs_today` 内部的 `fuel_events[]`。
- 飞书字段写入是 upsert，但 JSON 内容必须保留旧 `fuel_events[]`，再追加新事件。
- A 线快照只是可选启动参照或客户锚点，不是 B-SK06 的硬前置。

## 配套脚本

| 脚本 | 作用 |
| --- | --- |
| `scripts/read-session-fuel-input.ps1` | 按 `01_session.record_id` 读取 FuelTank 装配需要的 session 字段。 |
| `scripts/make-fuel-tank-id.ps1` | 按 `session_id + customer_id + sales_id + work_date` 生成稳定 `fuel_tank_id`。 |
| `scripts/build-new-inputs-today.ps1` | 从 session/material refs、附件摘要、既有 FuelTank 状态、销售补充中生成 append-only JSON，写入 `new_inputs_today`。 |
| `scripts/find-fuel-tank.ps1` | 按 `session_id` 或 `fuel_tank_id` 查找已有 `02_fuel_tank`，防止重复开槽。 |
| `scripts/write-fuel-tank-state.ps1` | 新建或更新 `02_fuel_tank`，只允许写基础状态字段。 |

脚本内置当前初版 B 线样例表坐标；多人使用时必须由 B-SK04 的销售身份与存储绑定传入对应销售、日期、知识库下的 `BaseToken/TableId`，不能固定某个人、项目或 thread。

## 默认表坐标

| 线 | 表 | Base token | Table ID |
| --- | --- | --- | --- |
| B | `01_session` | `XtSIbjGLSarQHDs3y2ncaWffnze` | `tbl6u4j3HRjz9Ggk` |
| B | `02_fuel_tank` | `Ba0DbuHxaaonj2sxT4tcEwWonZf` | `tbloO6EEgyXFrwFG` |

## 运行时输入

- `01_session.record_id`，或已读取出的 `session_id/customer_id/sales_id/work_date`。
- `start_snapshot_ref`：B-SK02 写入 `01_session` 的 A 线客户快照引用。
- 同一 active FuelTank 既有状态：更新时必须读取旧 `new_inputs_today`，用于保留旧 `fuel_events[]`。
- A 线客户快照内容或快照包文件：可选，只作为客户锚点或初始参照。
- `raw_input_refs`：B-SK05 追加的材料引用 JSONL。
- `extracted_fuel_items`：Codex 从 session、附件、转写、截图或文件中抽取的过程燃料候选。
- 销售补充：本轮口头说明、客户反馈摘要、材料说明。
- 运行时 B 线表坐标：从 B-SK04 的销售身份与存储绑定取得，初版本地可使用默认样例坐标。

## 读取来源

- 当前 `01_session`：读取 session/customer/sales/date/snapshot/material refs。
- A 线客户快照：可选读取 `start_snapshot_ref` 指向的快照内容或 B-SK02 传出的快照包；只作为客户锚点，不作为硬前置。
- 已有 `02_fuel_tank`：按 `session_id` 或 `fuel_tank_id` 查重后更新同一行；读取旧 `new_inputs_today`，保留并追加 `fuel_events[]`。
- B-SK05 生成的 `raw_input_refs`：只读取引用和摘要，不读取或复制大块 base64、录音全文、文件正文。

## 写入字段

只允许写 `02_fuel_tank` 这 9 个基础状态字段：

| 字段 | 字段 ID | 写入规则 |
| --- | --- | --- |
| `fuel_tank_id` | `fldP3TwKXy` | 稳定 ID；同一 `session_id + customer_id + sales_id + work_date` 不变。 |
| `session_id` | `fld79G5XL4` | 来自当前 `01_session.session_id`。 |
| `customer_id` | `fld1HVBbuz` | 必须是 B-SK02 已确认的客户 ID；没有确认客户时先回 B-SK02/B-SK03。 |
| `sales_id` | `fldiRPQEzA` | 来自 B-SK04 身份绑定后的 `01_session.sales_id`。 |
| `work_date` | `fldifwfyTK` | `yyyy-MM-dd`。 |
| `start_snapshot_ref` | `fldo6WNlQY` | A 线快照引用，不写客户事实。 |
| `new_inputs_today` | `fldFwqPeqq` | 累计 JSON，包含 `fuel_events[]`、最新 fuel event、材料引用计数、抽取燃料、销售补充、证据来源。 |
| `status` | `fldTaPxssT` | 只允许真实选项：`active`、`closed`、`stale`。新建默认为 `active`。 |
| `updated_at` | `fldGlRTEUC` | 本次装配时间，`yyyy-MM-dd HH:mm:ss`。 |

禁止写入：`fuel_sufficiency`、`missing_information`、`pending_confirmations`、`current_customer_stage`、`objections`、`buying_signals`、`risk_flags`、`confidence_score`、`should_trigger_dline`、`trigger_reason`、`recommended_dline_skills`、`generated_artifact_ids`、`used_artifact_ids`、`remark`，也禁止写 A/C/D/E 线和 `05_sync_log`。

## 工作流

1. 确认当前 Codex session 已经由 B-SK04 登记到销售对应 B 线 `01_session`，并且 `customer_id` 已由 B-SK02 唯一确认。
2. 运行 `read-session-fuel-input.ps1` 读取 `01_session` 的 `session_id/customer_id/sales_id/work_date/start_snapshot_ref/raw_input_refs`。
3. 运行 `make-fuel-tank-id.ps1` 生成稳定 `fuel_tank_id`。
4. 运行 `find-fuel-tank.ps1`：
   - 没有匹配：可以新建一条 `active` FuelTank。
   - 唯一匹配：更新该行。
   - 多条匹配：停止，人工确认后再写，避免重复槽。
5. 如果更新已有 FuelTank，先读取旧 `new_inputs_today`，作为 `ExistingFuelTankState` 传给脚本，避免覆盖旧沉淀。
6. Codex 从 session、附件和材料引用中抽取本轮过程燃料，写成 `ExtractedFuelItems`；抽取必须保留来源，不做最终判断。
7. 运行 `build-new-inputs-today.ps1` 生成 append-only `new_inputs_today` JSON。脚本会保留旧 `fuel_events[]`，追加本轮 `fuel_event`。
8. 运行 `write-fuel-tank-state.ps1 -DryRun -UseFieldIds` 检查 payload 只包含 9 个允许字段；脚本会拒绝没有 `fuel_events[]` 的输入。
9. Dry-run 无误后再去掉 `-DryRun` 写入。
10. 下一步交给 `$b-fuel-sufficiency-check` 和 `$b-stage-objection-signal-detect`，本 skill 不提前判断。

## 硬规则

- 只装配 FuelTank 基础状态，不判断“燃料是否够”。
- 不判断客户阶段、异议、购买信号、风险，不推荐或触发 D 线。
- 不把行动建议、工作日总结、客户正式事实写进 FuelTank。
- `customer_id` 必须来自唯一高置信确认；没有客户 ID 时先回 B-SK02/B-SK03，不创建正式 FuelTank。
- 一个 `session_id` 正常只能有一个 active FuelTank；发现多候选必须停下来人工确认。
- `new_inputs_today` 必须证据可追溯；只引用 `raw_input_refs/start_snapshot_ref`，不复制完整 base64、录音或文件正文。
- FuelTank 是 B 线过程层的持续追加沉淀；不是每次重算覆盖。
- A 线快照可选，只作锚点；不能因为没有 A 快照内容就阻断 session/附件燃料沉淀。
- 更新已有 FuelTank 时必须读取旧状态并合并，不能丢旧 `fuel_events[]`。
- 不固定销售 ID、项目 ID、Codex thread ID、本机路径或样例张三表；这些都必须来自运行时身份绑定和存储路由。
- `status` 只能写飞书字段真实选项：`active/closed/stale`；不能造 `need_confirm`。

## 输出格式

```text
B-SK06 FuelTank 装配结果
build_status: <dry_run|updated|created|blocked>
fuel_tank_id: <BFTK-...>
session_id: <BSES-...>
target_bline_table:
- base_token: <runtime 02_fuel_tank Base token>
- table_id: <runtime 02_fuel_tank Table ID>
write_fields:
- 02_fuel_tank.fuel_tank_id
- 02_fuel_tank.session_id
- 02_fuel_tank.customer_id
- 02_fuel_tank.sales_id
- 02_fuel_tank.work_date
- 02_fuel_tank.start_snapshot_ref
- 02_fuel_tank.new_inputs_today
- 02_fuel_tank.status
- 02_fuel_tank.updated_at
blocked_reason: <none|missing_customer_id|duplicate_fuel_tank|invalid_status|missing_session>
next_skill: <$b-fuel-sufficiency-check | none>
```

## 完成标准

- 已确认或生成稳定 `fuel_tank_id`。
- 已查重，未重复创建同一个 Session 的 FuelTank。
- `new_inputs_today` 可追溯到 session、附件、`raw_input_refs` 和每个 `fuel_event`。
- 写入 payload 只包含 9 个允许字段。
- 没有写燃料充足度、客户阶段、异议、购买信号、风险或 D 线推荐字段。
