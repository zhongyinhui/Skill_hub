# Skill Hub Agent Instructions

本仓库用于管理团队自研 skill。请把这里的每个 skill 都当作一个可发布、可回滚、可审查的产品单元，而不是一份临时提示词文件。

## Core Rules

- 正式 skill 必须放在 `modules/<module-id>/skills/<skill-name>/` 下。
- 跨部门通用 skill 放在 `modules/_shared/skills/<skill-name>/` 下。
- 新 skill 的复制模板放在 `templates/skill/`，模板不是正式发布的 skill。
- 当前业务模块包括：`customer-success`（客户成功）、`sales`（销售）、`ip`（IP 部门）、`private-domain`（私域部门）、`hr`（HR 部门）。
- 每个 skill 至少包含 `SKILL.md`、`README.md`、`VERSION`、`CHANGELOG.md`。
- 修改 `SKILL.md` 时，必须同步更新该 skill 的 `CHANGELOG.md`。
- 修改影响使用方式、输入输出约定或兼容性时，必须更新 `VERSION`。
- 不要把本机密钥、个人路径、聊天记录、临时日志提交进仓库。
- 不要直接删除旧 skill。弃用时在 `CHANGELOG.md` 和 `README.md` 中标记，并说明替代方案。
- Agent 在修改某个 skill 前，必须先阅读该 skill 的 `README.md`、`CHANGELOG.md` 和现有测试或示例。

## Language Rules

- 本仓库新增或修改的文档默认使用中文，包括 `README.md`、`docs/`、skill 的说明文档、示例说明和变更记录。
- commit message 必须使用中文，必要的英文技术关键词可以保留，例如 `skill`、`hook`、`tag`、`VERSION`。
- PR 标题、PR 描述、PR review 回复和合并说明必须使用中文。
- 如果引用上游工具、命令、错误信息或英文 API 名称，保持原文，不要为了中文化而改写命令或标识符。

## Versioning

skill 使用语义化版本：

```text
MAJOR.MINOR.PATCH
```

- `MAJOR`：不兼容改动，例如输入格式、工作流、文件结构变化。
- `MINOR`：向后兼容的新能力，例如支持新场景、新示例、新脚本。
- `PATCH`：修复问题、改进文字、补充说明，不改变使用方式。

如果要给某个 skill 打正式版本 tag，格式为：

```text
<module-id>/<skill-name>/v<version>
```

示例：

```text
customer-success/customer-handover/v1.2.0
_shared/git-intent-translator/v0.1.0
```

## Git Workflow

推荐流程：

1. 从主分支创建功能分支。
2. 修改 skill 文件。
3. 运行 `tools/validate-skill.ps1`。
4. 提交 commit，commit message 说明改动目的。
5. 如果要给业务同事交付压缩包，提交 PR 到 `release` 分支，让 GitHub Actions 自动按模块打包。
6. 合并前检查 diff、CHANGELOG、版本号和 workflow artifact。
7. 发布时打 tag。

`release` 分支的 PR 会触发 `.github/workflows/package-modules.yml`，按模块生成 zip。不要手工提交 `dist/` 下的打包产物。

推荐分支命名：

```text
skill/<module-id>/<skill-name>/<short-change>
docs/<topic>
fix/<module-id>/<skill-name>/<bug>
```

## Commit Guidelines

commit 应该表达一个清晰意图。推荐格式：

```text
skill(customer-success/customer-handover): 新增客户交接示例
fix(_shared/git-intent-translator): 补充回退确认规则
docs: 解释 skill 版本管理流程
```

避免使用：

```text
update
fix
修改一下
wip
```

## Hooks

本仓库使用 `.githooks/` 作为 Git hooks 目录。首次克隆后运行：

```powershell
git config core.hooksPath .githooks
```

hooks 只做最低限度检查：skill 结构、版本号、CHANGELOG、临时文件。复杂验证放在 `tools/` 脚本里。

如果当前机器的 Git for Windows 无法执行 shell hook，先手动运行：

```powershell
powershell -ExecutionPolicy Bypass -File tools/validate-skill.ps1
```

不要因为 hook 运行环境异常而跳过 skill 校验。

## GitHub Actions

- `.github/workflows/*.yml` 和 `.github/workflows/*.yaml` 中所有 `name:` 字段必须使用英文 ASCII。
- 不要把中文 workflow 名、job 名或 step 名配置为 GitHub Actions 的 `name:`，尤其不要作为分支保护的 required status check。
- release 分支保护规则中的必需检查名必须与实际 GitHub Actions job 名完全一致，目前应使用 `Package Module Zips`。
