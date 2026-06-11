# C-SK08 Supervisor Intervention Draft

这个 skill 用于把销售或客户风险证据转换为主管干预 draft，供主管人工确认和后续跟踪。

## 适用场景

- 需要根据 C 线预警、销售请求、B 线风险、E 线机会或人工发现生成干预草稿。
- 需要为主管提供建议动作、证据引用和跟进期限。
- 需要避免 AI 直接确认主管干预。

## 使用边界

- 输出永远是 draft，不能写成已确认干预。
- 不替主管做最终决策，不直接标记干预结果。
- 干预草稿必须保留触发来源和相关证据。

## 评审重点

- 是否明确 trigger_source 和 risk evidence。
- 是否把 manager_instruction 写成建议而不是命令执行事实。
- 是否保留 followup_required 和 followup_deadline 的人工确认空间。

