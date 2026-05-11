# Skill Hub

Skill Hub 是团队管理自研 skill 的版本仓库。

这里的目标不是“把文件放进 Git”，而是让每个 skill 的变化都能被解释、审查、发布和回滚。

## 这个仓库解决什么问题

- 知道某个 skill 为什么变了。
- 知道某个 skill 从哪个版本开始支持某个能力。
- 出问题时可以回退到旧版本。
- 多个人可以同时修改不同 skill，减少互相覆盖。
- Agent 可以根据统一结构理解、修改和验证 skill。

## 新同事从这里开始

第一次使用时，先读：

- `docs/quickstart-for-teammates.md`：10 分钟上手，说明 clone、个人工作分支、创建 skill、校验、PR 和 merge 边界。
- `docs/team-workflow.md`：团队协作流程，说明普通同事、负责人和发布分支怎么配合。
- `docs/naming-and-routing.md`：skill 命名和部门模块归属规则。

如果你不熟悉 Git，可以直接对 Codex 说：

```text
我第一次用 Skill Hub，帮我按新人流程检查当前分支，并引导我创建或修改一个 skill。
```

## Git 对 skill 作者意味着什么

- 分支：我正在尝试一组改动。
- commit：一个可以解释的改动点。
- diff：这次和上次相比到底改了什么。
- tag：某个 skill 的正式发布版本。
- changelog：给人看的版本说明。
- hook：提交前的自动检查。

## 推荐目录

```text
modules/
  _shared/
    skills/
      <skill-name>/
        SKILL.md
        README.md
        VERSION
        CHANGELOG.md
        examples/
        tests/
        scripts/
  customer-success/
    skills/
  sales/
    skills/
  ip/
    skills/
  private-domain/
    skills/
  hr/
    skills/
templates/
  skill/
docs/
tools/
.githooks/
```

## 已内置的 skill

- `templates/skill`：新建 skill 的复制模板。
- `modules/_shared/skills/git-intent-translator`：把普通用户的话翻译成安全的 Git/GitHub 操作，例如“保存一下”“发给同事看看”“这个版本不要了”。
- `modules/_shared/skills/skill-governance-router`：创建、上传或提交 skill 前，检查命名、部门归属、个人工作分支、commit 和 PR 说明。

## 当前模块

- `modules/customer-success`：客户成功。
- `modules/sales`：销售。
- `modules/ip`：IP 部门。
- `modules/private-domain`：私域部门。
- `modules/hr`：HR 部门。
- `modules/_shared`：跨部门通用 skill。

模块目录名保留英文机器 ID，给人看的说明同时写中文部门名，例如 `customer-success（客户成功）`。

## release 分支打包

当有人向 `release` 分支提交 PR，GitHub Actions 会自动按模块生成 zip：

- `_shared-skills.zip`
- `customer-success-skills.zip`
- `sales-skills.zip`
- `ip-skills.zip`
- `private-domain-skills.zip`
- `hr-skills.zip`

这些 zip 会出现在对应 workflow run 的 Artifacts 区域。每个 zip 内保留模块目录，例如 `customer-success/skills/...`。

本地也可以手动打包：

```powershell
powershell -ExecutionPolicy Bypass -File tools/package-modules.ps1 -OutputDir dist/module-zips
```

## 团队工作分支

普通同事默认使用个人长期工作分支：

```text
work/<name-pinyin>
```

例如：

```text
work/renqc
work/zhangsan
work/lisi
```

个人长期分支只表达“谁在工作”，不表达本次改了什么。本次改动范围应写在 commit message、PR 标题和 PR 描述中。

详细规则见：

- `docs/quickstart-for-teammates.md`
- `docs/naming-and-routing.md`
- `docs/team-workflow.md`

## 第一次使用

```powershell
powershell -ExecutionPolicy Bypass -File tools/validate-skill.ps1
```

如果本机 Git hook 环境可用，可以开启自动检查：

```powershell
git config core.hooksPath .githooks
```

如果 Git for Windows 在执行 hook 时出现 `sh.exe` 权限问题，请先手动运行 `tools/validate-skill.ps1`，不要把这个环境问题当成 skill 校验失败。

## 创建新 skill

创建前先确认 skill 的使用场景、输入、输出和所属模块。可选模块包括：

```text
_shared（跨部门通用）
customer-success（客户成功）
sales（销售）
ip（IP 部门）
private-domain（私域部门）
hr（HR 部门）
```

复制模板目录：

```powershell
Copy-Item -Recurse templates/skill modules/customer-success/skills/my-new-skill
```

然后修改：

- `modules/customer-success/skills/my-new-skill/SKILL.md`
- `modules/customer-success/skills/my-new-skill/README.md`
- `modules/customer-success/skills/my-new-skill/VERSION`
- `modules/customer-success/skills/my-new-skill/CHANGELOG.md`

提交前运行校验：

```powershell
powershell -ExecutionPolicy Bypass -File tools/validate-skill.ps1
```

如果需要在本项目里直接用 `$my-new-skill` 调用，确保它也出现在项目可调用入口：

```powershell
powershell -ExecutionPolicy Bypass -File tools/sync-codex-skills.ps1 -SkillName my-new-skill
```

正式归档路径仍然是 `modules/<module-id>/skills/<skill-name>/`；项目可调用入口是 `.codex/skills/<skill-name>/`。提交给团队使用时，两处都要保持一致。
