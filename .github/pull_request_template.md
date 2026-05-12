> 这份模板默认由 Codex 根据当前 diff、skill 内容、校验结果和目标分支自动填写。普通同事不需要从零写 PR，只需要核实 Codex 拟好的模块、范围、PR 内容、目标分支和是否提交申请。

## 本次变更

- `modules/<module-id>/skills/<skill-name>`：说明新增或修改了什么。
- `.codex/skills/<skill-name>`：如已同步项目可调用入口，请说明同步状态。

## 涉及模块

- [ ] `_shared`
- [ ] `customer-success`
- [ ] `sales`
- [ ] `ip`
- [ ] `private-domain`
- [ ] `hr`

## 变更类型

- [ ] 新增 skill
- [ ] 修改已有 skill
- [ ] 修复问题
- [ ] 文档更新
- [ ] 规则 / 工具 / workflow 更新

## 自检

- [ ] 已确认 skill 归属模块。
- [ ] 已确认个人工作分支使用真实姓名拼音或本人确认的缩写。
- [ ] skill 目录名和 frontmatter `name` 使用拼音 / 英文 / ASCII。
- [ ] 已补齐 `SKILL.md`、`README.md`、`VERSION`、`CHANGELOG.md`。
- [ ] 修改 `SKILL.md` 时已同步更新 `CHANGELOG.md`。
- [ ] 影响使用方式、输入输出或兼容性时已更新 `VERSION`。
- [ ] 已运行 `powershell -ExecutionPolicy Bypass -File tools/validate-skill.ps1`。
- [ ] 新建或改名 skill 时，已同步 `.codex/skills/<skill-name>/` 项目可调用入口。
- [ ] 未提交密钥、个人路径、聊天记录、临时日志或 `dist/` 产物。

## 迭代状态

- 当前选择：继续深化调整 / 进入下一步流程。
- 若继续深化：说明下一轮要打磨内容、示例、测试、触发条件、输出格式还是 README。
- 若进入下一步：说明目标是 commit、push、PR 到 `master`，还是 PR 到 `release`。

## 给审核人的说明

请重点说明需要审核人关注的风险、边界或待确认事项。

## Codex 假设与用户核实

- Codex 基于当前 skill 内容作出的判断：
- 已向用户核实的关键项：
- 尚未核实但已标注的假设：

## 当前阶段与下一步

- 当前阶段：PR 待审核 / 已审核待 merge / 待发布 / 其他。
- 建议下一步：说明是否只需要 review、是否可以 approve、是否等待 `Package Module Zips`、是否需要负责人单独确认 merge。

## 环境与创建方式

- PR 创建方式：GitHub connector / 浏览器 / GitHub CLI / 其他。
- 如果未能直接创建 PR：说明缺少 Git、GitHub CLI、登录认证、远端权限或其他明确阻断原因，并保留本模板作为完整申请包。
