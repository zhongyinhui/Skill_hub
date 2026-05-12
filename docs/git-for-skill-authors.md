# Git for Skill Authors

这份文档用 skill 管理的语境解释 Git。

## Git 不是网盘

网盘回答的是：“现在文件是什么样？”

Git 回答的是：

- 谁改了？
- 为什么改？
- 改了哪里？
- 什么时候改？
- 能不能回到以前？
- 哪个版本正式发布过？

对 skill 来说，这些问题比文件本身更重要。因为 skill 会影响 Agent 行为，一次小改动也可能改变输出质量、工作流或安全边界。

## 如果你不会 Git 术语

不用先学会 `commit`、`push`、`merge`、`pull request` 这些词。

你可以直接对 Agent 说普通话：

- "保存一下现在这个版本。"
- "把这版发给同事看看。"
- "看看我改了什么。"
- "这个版本不要了，回到之前。"
- "把这个 skill 发布一版。"

仓库里的 `modules/_shared/skills/git-intent-translator` 会指导 Agent 把这些说法翻译成安全的 Git/GitHub 操作。

如果你说“给负责人审核”或“创建 PR”，PR 标题和描述应由 Codex 根据当前改动、校验结果和仓库模板生成；你只需要确认目标分支和是否提交申请。

## 分支

分支是一条试验线。

团队日常工作默认使用个人长期分支：

```powershell
git switch -c work/renqc
```

这个名字只说明“任起超正在这里工作”，不说明本次改了什么。本次改动要写进 commit message 和 PR 描述。

例如你要增强 `form-filler`：

```powershell
git switch -c skill/form-filler/add-contract-example
```

这表示：我正在为 `form-filler` 增加合同类表单示例。

`skill/...` 更适合短期精确分支，不适合作为每个人长期工作分支。

## Commit

commit 是一个有意义的保存点。

好的 commit：

```text
skill(form-filler): add contract form example
skill(customer-success/kehu-xuqiu-jiaofu-fenxi): 新增逐字稿需求拆解
work(renqc): 补充团队 skill 命名与上传规范
```

不好的 commit：

```text
update
```

因为半年后没人知道 `update` 到底更新了什么。

## Diff

diff 是审查 skill 的核心。

看 diff 时重点关注：

- `SKILL.md` 是否改变了 Agent 行为。
- `README.md` 是否解释了人如何使用。
- `CHANGELOG.md` 是否说明了变化。
- `VERSION` 是否符合变更级别。
- 示例和测试是否仍然匹配新规则。

## Tag

tag 代表正式发布。

多个 skill 在同一个仓库时，推荐 tag 格式：

```text
<module-id>/<skill-name>/v<version>
```

例如：

```text
customer-success/form-filler/v1.2.0
```

这个 tag 的含义是：`customer-success` 模块下的 `form-filler` skill 的 `1.2.0` 版本可以被团队引用、安装或回退。版本主体仍然是 skill，`module-id` 只是命名空间，用来避免不同模块出现同名 skill 时冲突。
