# Changelog

## 0.1.0 - 2026-06-08

- 新增 B-SK06 `b-fuel-tank-state-build` 正式归档初版。
- 固化 `02_fuel_tank` 初版 Base/Table/Field 坐标，并提供只写基础状态字段的 PowerShell 脚本。
- 明确本 skill 只装配 FuelTank 状态，不判断燃料充足度、客户阶段、异议、购买信号或 D 线触发。
- 根据验收反馈明确 append-only FuelTank 模型：每次从 session/附件/material refs 抽取 `fuel_event`，追加进 `new_inputs_today.fuel_events[]`；A 线快照仅作为可选锚点，不是构建硬前置。
