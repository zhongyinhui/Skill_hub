# Release Process

这份文档描述一个 skill 从修改到发布的推荐流程。

## 1. 创建分支

```powershell
git switch -c skill/<module-id>/<skill-name>/<short-change>
```

## 2. 修改 skill

至少检查这些文件：

- `SKILL.md`
- `README.md`
- `VERSION`
- `CHANGELOG.md`
- `examples/`
- `tests/`

## 3. 本地校验

```powershell
powershell -ExecutionPolicy Bypass -File tools/validate-skill.ps1
```

如果已经启用 `.githooks/`，提交和推送时也会自动运行同一套检查。

## 4. 提交

```powershell
git add modules/<module-id>/skills/<skill-name>
git commit -m "skill(<module-id>/<skill-name>): 用中文说明这次改动"
```

## 5. 合并

合并前重点审查：

- 是否有清晰 diff。
- 版本号是否正确。
- CHANGELOG 是否说明原因。
- 示例和测试是否匹配新行为。

## 6. 向 release 分支提交 PR

当 PR 的目标分支是 `release` 时，GitHub Actions 会自动：

1. 校验 skill 格式。
2. 按模块生成 zip。
3. 把每个模块的 zip 上传到 workflow run 的 Artifacts 区域。

只有目标分支是 `release` 的 PR 会触发这个打包流程。

PR 合并到 `release` 后，`release` 分支的 push 会再次运行同一套打包流程，并创建一个带版本号的 GitHub Release。
发布包 tag 使用：

```text
module-skills/vYYYY.MM.DD-<run_number>.<run_attempt>
```

示例：

```text
module-skills/v2026.05.08-42.1
```

GitHub 首页右侧的 Releases 区域会显示最新一次 Release，历史发布包也会保留，方便回溯下载。

## 7. 发布 tag

可以先让脚本检查模块、skill 和版本号：

```powershell
powershell -ExecutionPolicy Bypass -File tools/release-skill.ps1 -ModuleId customer-success -SkillName customer-handover
```

确认无误后再创建 tag：

```powershell
git tag <module-id>/<skill-name>/v<version>
git push origin <module-id>/<skill-name>/v<version>
```

示例：

```powershell
git tag customer-success/customer-handover/v1.2.0
```
