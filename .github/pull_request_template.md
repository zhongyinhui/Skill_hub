## 本次变更

- `modules/<module-id>/skills/<skill-name>`：说明新增或修改了什么。

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
- [ ] skill 目录名和 frontmatter `name` 使用拼音 / 英文 / ASCII。
- [ ] 已补齐 `SKILL.md`、`README.md`、`VERSION`、`CHANGELOG.md`。
- [ ] 修改 `SKILL.md` 时已同步更新 `CHANGELOG.md`。
- [ ] 影响使用方式、输入输出或兼容性时已更新 `VERSION`。
- [ ] 已运行 `powershell -ExecutionPolicy Bypass -File tools/validate-skill.ps1`。
- [ ] 如需项目内 `$skill-name` 调用，已同步 `.codex/skills/<skill-name>/` 项目可调用入口。
- [ ] 未提交密钥、个人路径、聊天记录、临时日志或 `dist/` 产物。

## 给审核人的说明

请重点说明需要审核人关注的风险、边界或待确认事项。

## 当前阶段与下一步

- 当前阶段：PR 待审核 / 已审核待 merge / 待发布 / 其他。
- 建议下一步：说明是否只需要 review、是否可以 approve、是否等待 `Package Module Zips`、是否需要负责人单独确认 merge。
