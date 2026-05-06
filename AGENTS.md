# Skill Hub Agent Instructions

这台电脑是林家涛的电脑。林家涛在星陀智能上班，所在的部门是产品研发部。

本仓库用于管理团队自研 skill。请把这里的每个 skill 都当作一个可发布、可回滚、可审查的产品单元，而不是一份临时提示词文件。

## Core Rules

- 每个 skill 必须放在 `skills/<skill-name>/` 下。
- 每个 skill 至少包含 `SKILL.md`、`README.md`、`VERSION`、`CHANGELOG.md`。
- 修改 `SKILL.md` 时，必须同步更新该 skill 的 `CHANGELOG.md`。
- 修改影响使用方式、输入输出约定或兼容性时，必须更新 `VERSION`。
- 不要把本机密钥、个人路径、聊天记录、临时日志提交进仓库。
- 不要直接删除旧 skill。弃用时在 `CHANGELOG.md` 和 `README.md` 中标记，并说明替代方案。
- Agent 在修改某个 skill 前，必须先阅读该 skill 的 `README.md`、`CHANGELOG.md` 和现有测试或示例。

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
<skill-name>/v<version>
```

示例：

```text
form-filler/v1.2.0
lark-base/v0.4.1
```

## Git Workflow

推荐流程：

1. 从主分支创建功能分支。
2. 修改 skill 文件。
3. 运行 `tools/validate-skill.ps1`。
4. 提交 commit，commit message 说明改动目的。
5. 合并前检查 diff、CHANGELOG 和版本号。
6. 发布时打 tag。

推荐分支命名：

```text
skill/<skill-name>/<short-change>
docs/<topic>
fix/<skill-name>/<bug>
```

## Commit Guidelines

commit 应该表达一个清晰意图。推荐格式：

```text
skill(form-filler): add reimbursement form example
fix(lark-base): clarify required permissions
docs: explain skill versioning workflow
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
