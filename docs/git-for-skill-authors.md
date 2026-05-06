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

## 分支

分支是一条试验线。

例如你要增强 `form-filler`：

```powershell
git switch -c skill/form-filler/add-contract-example
```

这表示：我正在为 `form-filler` 增加合同类表单示例。

## Commit

commit 是一个有意义的保存点。

好的 commit：

```text
skill(form-filler): add contract form example
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
<skill-name>/v<version>
```

例如：

```text
form-filler/v1.2.0
```

这个 tag 的含义是：`form-filler` 的 `1.2.0` 版本可以被团队引用、安装或回退。

