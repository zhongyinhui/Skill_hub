# b-fuel-tank-state-build

B-SK06，B 线 FuelTank 持续追加沉淀。它从当前 `01_session`、Codex session、附件/material refs、tool outputs、销售补充和客户反馈中抽取过程燃料，并追加进 active `02_fuel_tank`，供后续燃料充足度、阶段、异议、购买信号和 D 线触发判断使用。

## 手动调用

`$b-fuel-tank-state-build`

## 输入

- 当前 `01_session.record_id`
- `session_id/customer_id/sales_id/work_date`
- `start_snapshot_ref`
- 同一 active FuelTank 既有 `new_inputs_today`，更新时必须传入
- `raw_input_refs`
- Codex 从 session/附件中抽取的 `ExtractedFuelItems`
- 销售补充、客户反馈、材料说明
- 运行时 B 线表坐标：`01_session` 与 `02_fuel_tank` 的 `BaseToken/TableId`

## 读取来源

- `01_session`
- B-SK05 写入的 `raw_input_refs`
- A 线客户快照引用 `start_snapshot_ref`，可选作为锚点
- 已有 `02_fuel_tank`，用于同一 active FuelTank 的查重和追加

## 写入字段

只写 `02_fuel_tank`：

| 字段 | 字段 ID |
| --- | --- |
| `fuel_tank_id` | `fldP3TwKXy` |
| `session_id` | `fld79G5XL4` |
| `customer_id` | `fld1HVBbuz` |
| `sales_id` | `fldiRPQEzA` |
| `work_date` | `fldifwfyTK` |
| `start_snapshot_ref` | `fldo6WNlQY` |
| `new_inputs_today` | `fldFwqPeqq` |
| `status` | `fldTaPxssT` |
| `updated_at` | `fldGlRTEUC` |

不写 `fuel_sufficiency/missing_information/pending_confirmations/current_customer_stage/objections/buying_signals/risk_flags/confidence_score/should_trigger_dline/trigger_reason/recommended_dline_skills`。

## 脚本

```powershell
# 读取 01_session 中可用于 FuelTank 装配的字段
powershell -ExecutionPolicy Bypass -File modules/sales/skills/b-fuel-tank-state-build/scripts/read-session-fuel-input.ps1 `
  -RecordId "rec_xxx"

# 生成稳定 fuel_tank_id
powershell -ExecutionPolicy Bypass -File modules/sales/skills/b-fuel-tank-state-build/scripts/make-fuel-tank-id.ps1 `
  -SessionId "BSES-20260608-abc123" `
  -CustomerId "CUST-2026-000001" `
  -SalesId "sales_zhangsan" `
  -WorkDate "2026-06-08"

# 生成 new_inputs_today JSON
powershell -ExecutionPolicy Bypass -File modules/sales/skills/b-fuel-tank-state-build/scripts/build-new-inputs-today.ps1 `
  -SessionId "BSES-20260608-abc123" `
  -CustomerId "CUST-2026-000001" `
  -SalesId "sales_zhangsan" `
  -WorkDate "2026-06-08" `
  -StartSnapshotRef "a-snapshot://CUST-2026-000001/2026-06-08" `
  -ExistingFuelTankStateFile ".tmp\existing-new-inputs-today.json" `
  -RawInputRefsFile ".tmp\raw-input-refs.jsonl" `
  -ExtractedFuelItemsFile ".tmp\extracted-fuel-items.json" `
  -SalesSupplement "客户今天补充了预算和上线时间"

# 查找已有 FuelTank，避免重复创建
powershell -ExecutionPolicy Bypass -File modules/sales/skills/b-fuel-tank-state-build/scripts/find-fuel-tank.ps1 `
  -SessionId "BSES-20260608-abc123" `
  -DryRun

# 写入前必须先 dry-run，确认 payload 只有允许字段
powershell -ExecutionPolicy Bypass -File modules/sales/skills/b-fuel-tank-state-build/scripts/write-fuel-tank-state.ps1 `
  -FuelTankId "BFTK-20260608-XXXXXXXXXXXX" `
  -SessionId "BSES-20260608-abc123" `
  -CustomerId "CUST-2026-000001" `
  -SalesId "sales_zhangsan" `
  -WorkDate "2026-06-08" `
  -StartSnapshotRef "a-snapshot://CUST-2026-000001/2026-06-08" `
  -NewInputsTodayFile ".tmp\new-inputs-today.json" `
  -UseFieldIds `
  -DryRun
```

## 关键规则

- 只装配状态，不做判断。
- FuelTank 是持续追加沉淀，每次 session/附件新增输入都追加一个 `fuel_event`。
- A 线快照可选，只作客户锚点；不是构建 FuelTank 的硬前置。
- 一个 `session_id` 正常只维护一个 active FuelTank。
- 没有确认 `customer_id` 时不创建正式 FuelTank，先回 B-SK02/B-SK03。
- `new_inputs_today` 内部保留旧 `fuel_events[]` 并追加新事件，不放完整原始材料。
- `status` 只能是 `active/closed/stale`。
- 不固定销售、项目、thread 或样例表；默认坐标只用于本地初版测试。

## 当前状态

- 版本：`0.1.0`
- 状态：本地初版，等待验收。
- 同步：未同步到 `.codex/skills/b-fuel-tank-state-build/`；通过验收后再单独同步本 skill。
