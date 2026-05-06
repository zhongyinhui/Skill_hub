# Skill Hub

Skill Hub 是团队管理自研 skill 的版本仓库。

这里的目标不是“把文件放进 Git”，而是让每个 skill 的变化都能被解释、审查、发布和回滚。

## 这个仓库解决什么问题

- 知道某个 skill 为什么变了。
- 知道某个 skill 从哪个版本开始支持某个能力。
- 出问题时可以回退到旧版本。
- 多个人可以同时修改不同 skill，减少互相覆盖。
- Agent 可以根据统一结构理解、修改和验证 skill。

## Git 对 skill 作者意味着什么

- 分支：我正在尝试一组改动。
- commit：一个可以解释的改动点。
- diff：这次和上次相比到底改了什么。
- tag：某个 skill 的正式发布版本。
- changelog：给人看的版本说明。
- hook：提交前的自动检查。

## 推荐目录

```text
skills/
  <skill-name>/
    SKILL.md
    README.md
    VERSION
    CHANGELOG.md
    examples/
    tests/
    scripts/
docs/
tools/
.githooks/
```

## 已内置的 skill

- `skills/_template`：新建 skill 的复制模板。
- `skills/git-intent-translator`：把普通用户的话翻译成安全的 Git/GitHub 操作，例如“保存一下”“发给同事看看”“这个版本不要了”。

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

复制模板目录：

```powershell
Copy-Item -Recurse skills/_template skills/my-new-skill
```

然后修改：

- `skills/my-new-skill/SKILL.md`
- `skills/my-new-skill/README.md`
- `skills/my-new-skill/VERSION`
- `skills/my-new-skill/CHANGELOG.md`

提交前运行校验：

```powershell
powershell -ExecutionPolicy Bypass -File tools/validate-skill.ps1
```
