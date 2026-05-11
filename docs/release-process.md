# Release Process

这份文档描述一个 skill 从修改到发布的推荐流程。

## 1. 创建分支

普通同事默认使用个人长期工作分支：

```powershell
git switch -c work/<name-pinyin>
```

例如：

```powershell
git switch -c work/renqc
```

单个 skill 或一次明确改动需要短期评审分支时，可以使用：

```powershell
git switch -c skill/<module-id>/<skill-name>/<short-change>
```

分支名必须使用拼音或英文 ASCII，不要使用中文。

## 2. 修改 skill

至少检查这些文件：

- `SKILL.md`
- `README.md`
- `VERSION`
- `CHANGELOG.md`
- `examples/`
- `tests/`

创建或上传 skill 前必须确认所属模块：

- `_shared`
- `customer-success`
- `sales`
- `ip`
- `private-domain`
- `hr`

如果用户没有说明模块，Agent 必须主动提问，不能直接根据当前目录猜测。

## 3. 本地校验

```powershell
powershell -ExecutionPolicy Bypass -File tools/validate-skill.ps1
```

如果已经启用 `.githooks/`，提交和推送时也会自动运行同一套检查。

如果需要在本项目里用 `$skill-name` 手动测试，先刷新项目可调用入口：

```powershell
powershell -ExecutionPolicy Bypass -File tools/sync-codex-skills.ps1 -SkillName <skill-name>
```

正式发布和回滚仍以 `modules/<module-id>/skills/<skill-name>/` 为准；项目内 `$skill-name` 调用以 `.codex/skills/<skill-name>/` 为入口。

## 4. 提交

```powershell
git add modules/<module-id>/skills/<skill-name>
git commit -m "skill(<module-id>/<skill-name>): 用中文说明这次改动"
```

如果在 `work/<name-pinyin>` 分支上一次提交多个 skill，commit message 可以概括批次，但 PR 描述必须逐项列出路径和变化。

## 5. 上传到个人工作分支

提交后，普通同事默认先 push 到自己的个人工作分支：

```powershell
git push origin work/<name-pinyin>
```

这一步只是保存远程草稿和阶段成果，不需要 PR，也不会影响 `master` 或 `release`。

如果用户只说“上传”“保存到远程”，Agent 默认引导到这一步。push 完成后，再询问是否需要进入正式分支。

## 6. 合并

合并前重点审查：

- 是否有清晰 diff。
- 版本号是否正确。
- CHANGELOG 是否说明原因。
- 示例和测试是否匹配新行为。
- 机器识别名是否使用拼音或英文 ASCII。
- PR 描述是否列出所有变更的 skill 路径。

approve 和 merge 要分开看：

- approve：审核人认可这次改动，可以进入下一步。
- merge：改动真实进入目标分支，会影响发布和团队使用。

merge 前必须确认目标分支、检查结果和发布影响。面向 `release` 的 PR 还要确认 `Package Module Zips` 已通过。

## 7. 向正式分支提交 PR

普通同事只有要进入正式分支时，才创建 PR：

- 进入 `master`：用于团队稳定基线，让其他同事后续同步到正式内容。
- 进入 `release`：用于发布打包，生成模块 zip 和 Release。

不要把“push 到个人工作分支”和“创建 PR 进入正式分支”混在一起。

管理者 / owner 自己推进 `master` 时，可以选择两种方式：

- 推荐：创建 PR 作为变更说明和决策留档，检查 diff 和校验结果后由管理者确认 merge；PR 作者不能 approve 自己，不需要伪造自审。
- 例外：管理者明确要求直接更新 `master` 时，可以直接 push；这会绕过 PR 留档，只保留 commit / branch / tag / changelog 等 Git 版本记录。

无论哪种方式，都必须先确认不会把测试内容、临时目录或无关提交带入正式分支。

## 8. 向 release 分支提交 PR

当 PR 的目标分支是 `release` 时，GitHub Actions 会自动：

1. 校验 skill 格式。
2. 按模块生成 zip。
3. 把每个模块的 zip 上传到 workflow run 的 Artifacts 区域。

只有目标分支是 `release` 的 PR 会触发这个打包流程。

PR 标题和描述按 `.github/pull_request_template.md` 填写。面向 `release` 的 PR 必须等待 `Package Module Zips` 通过后再合并。

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

## 9. 发布 tag

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
