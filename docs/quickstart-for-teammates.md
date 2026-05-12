# 新同事 10 分钟上手

这份手册给第一次使用 Skill Hub 的同事。你不需要先学会 Git 术语，可以直接让 Codex 帮你按流程做。

## 你要记住的三句话

1. skill 是团队可复用的方法包，不是临时提示词。
2. 普通同事在自己的 `work/<name-pinyin>` 分支上工作。
3. 做完后先验证，再提交，默认先 push 到自己的工作分支；要进入正式分支时才发 PR。

## 第一次拿到仓库

```powershell
git clone <repo-url>
cd Skill_hub
git fetch --all --prune
```

如果你已经有自己的工作分支：

```powershell
git switch work/<name-pinyin>
```

如果你还没有自己的工作分支：

```powershell
git switch -c work/<name-pinyin>
git push -u origin work/<name-pinyin>
```

示例：

```powershell
git switch -c work/zhangsan
git push -u origin work/zhangsan
```

分支名只表达谁在工作，不表达这次改了什么。这次改动内容写在 commit message 和 PR 描述里。

## 你可以直接这样对 Codex 说

创建 skill：

```text
我要做一个 skill，功能是把客户会议记录整理成跟进动作。你先帮我判断模块和命名，再创建。
```

如果你只说“我要创建一个 skill”，Codex 应该先追问细节，不应该马上创建文件。最少要问清：

- 谁会用这个 skill。
- 它解决什么业务场景。
- 输入材料是什么。
- 希望输出什么。
- 做到什么程度算可用。

修改 skill：

```text
帮我改这个 skill，让它支持销售拜访记录。先看 README、CHANGELOG 和测试，再告诉我需要改哪里。
```

上传给负责人看：

```text
把这次 skill 改动整理一下，先跑校验，再准备提交到我的工作分支，最后发 PR 给负责人审核。
```

查看当前状态：

```text
帮我看一下现在改了哪些文件，哪些还没验证，下一步应该做什么。
```

## Codex 必须先问你的问题

如果你要创建、上传、提交或发 PR，Codex 应该确认：

- 这次只是上传到你的个人工作分支，还是要进入 `master` / `release`。
- 这个 skill 具体解决什么场景，输入和输出是什么。
- 这个 skill 最终归属哪个模块。
- 本次是否只处理这些 skill。
- skill 名、目录名、frontmatter `name` 是否使用拼音或英文 ASCII。
- 是否已经运行 `tools/validate-skill.ps1`。
- 是否要 commit、push 或创建 PR。

如果 Codex 没问，你可以直接补一句：

```text
先按 Skill Hub 流程检查模块、命名、分支和校验，不要直接上传。
```

## 创建一个 skill 的标准路径

1. 确认当前分支是 `work/<name-pinyin>`。
2. 问清 skill 场景、用户、输入、输出和可用标准。
3. 确认 skill 归属模块：
   - `_shared（跨部门通用）`
   - `customer-success（客户成功）`
   - `sales（销售）`
   - `ip（IP 部门）`
   - `private-domain（私域部门）`
   - `hr（HR 部门）`
4. 生成功能型 skill 名，使用拼音或英文 ASCII。
5. 确认目录名、`SKILL.md` frontmatter `name` 和 `$skill-name` 调用名一致。
6. 放到 `modules/<module-id>/skills/<skill-name>/`。
7. 补齐 `SKILL.md`、`README.md`、`VERSION`、`CHANGELOG.md`。
8. 有复杂行为时补 `examples/` 或 `tests/`。
9. 运行校验。
10. 做一次最小试运行或样例检查。
11. 如需在本项目里直接 `$skill-name` 调用，确保它也在 `.codex/skills/<skill-name>/`。
12. 提交 commit。
13. push 到自己的工作分支。
14. 如果要进入 `master` 或 `release`，再创建 PR，交给负责人审核。

## 上传和 PR 的区别

普通同事默认先把改动上传到自己的工作分支：

```text
本地电脑 -> origin/work/<name-pinyin>
```

这一步只是保存个人草稿和阶段成果，不需要 PR。

只有当你要让改动进入正式分支时，才需要 PR：

```text
work/<name-pinyin> -> master
work/<name-pinyin> -> release
```

目标分支怎么选：

| 你想做什么 | 默认目标 | 是否需要 PR |
| --- | --- | --- |
| 保存远程草稿 | `work/<name-pinyin>` | 不需要 |
| 让团队正式同步这套规则或 skill | `master` | 需要 |
| 打包生成模块 zip 或发布 | `release` | 需要 |

如果你只说“上传一下”，Codex 应该默认理解为 push 到你的个人工作分支。push 完成后，Codex 再问你是否要继续发 PR 到 `master` 或 `release`。

## 模块怎么选

模块目录必须保留英文机器 ID，避免脚本、分支保护和打包流程出问题；给人看的地方要同时显示中文部门名。

| 机器 ID | 中文名 |
| --- | --- |
| `_shared` | 跨部门通用 |
| `customer-success` | 客户成功 |
| `sales` | 销售 |
| `ip` | IP 部门 |
| `private-domain` | 私域部门 |
| `hr` | HR 部门 |

Codex 提问时应该写成 `customer-success（客户成功）`，不要只给英文列表。

## skill 名和 `$` 调用

一个正式 skill 有三个名字要一致：

```text
modules/<module-id>/skills/<skill-name>/
SKILL.md frontmatter: name: <skill-name>
手动调用名：$<skill-name>
```

`SKILL.md` 这个文件名必须固定，它不是 skill 的调用名。如果 Codex 回复里要引用文件，应该写成“`<skill-name>` 的 `SKILL.md`”，避免看起来像默认模板名。

正式存放位置：

```text
modules/<module-id>/skills/<skill-name>/
```

项目可调用入口：

```text
.codex/skills/<skill-name>/
```

这里的 `.codex/skills/` 是当前项目里的目录，例如：

```text
D:\中隐会\Skills_hub\.codex\skills\<skill-name>\
```

它不是 C 盘全局 Codex 目录。C 盘全局目录通常类似：

```text
C:\Users\<user>\.codex\skills\<skill-name>\
```

区别：

| 位置 | 作用 |
| --- | --- |
| `modules/<module-id>/skills/<skill-name>/` | 正式归档、评审、发布、回滚 |
| `当前项目/.codex/skills/<skill-name>/` | 当前项目里 `$skill-name` 可调用 |
| `C:\Users\<user>\.codex\skills/<skill-name>/` | 用户全局可调用，跨项目使用 |

Skill Hub 现在默认先保证当前项目可调用；跨项目全局安装后面再单独设计。

从正式归档路径刷新到项目可调用入口：

```powershell
powershell -ExecutionPolicy Bypass -File tools/sync-codex-skills.ps1 -SkillName <skill-name>
```

如果同步后 `$<skill-name>` 仍不可见，通常需要新开 Codex 线程或刷新 skill 列表。

## 本地验证

每次提交前运行：

```powershell
powershell -ExecutionPolicy Bypass -File tools/validate-skill.ps1
```

看到下面结果才算通过：

```text
PASS All skill checks passed.
```

如果失败，先修复失败项，不要跳过校验。

## 发给负责人审核

提交前先看状态：

```powershell
git status --short --branch
```

提交示例：

```powershell
git add modules/<module-id>/skills/<skill-name>
git commit -m "skill(<module-id>/<skill-name>): 用中文说明这次改动"
git push
```

如果一次改了流程、文档或多个 skill，可以使用：

```powershell
git commit -m "work(<name-pinyin>): 用中文概括这批改动"
```

PR 描述必须列清楚：

- 改了哪些路径。
- 涉及哪些模块。
- 是新增 skill、修改 skill，还是流程/工具更新。
- 是否更新 `CHANGELOG.md`。
- 是否运行了 `tools/validate-skill.ps1`。
- 需要负责人重点看什么。

## 负责人怎么审核

负责人优先看：

- skill 是否放在正确模块。
- skill 名是否按功能命名。
- 机器识别名是否使用拼音或英文 ASCII。
- `SKILL.md`、`README.md`、`VERSION`、`CHANGELOG.md` 是否齐全。
- 修改 `SKILL.md` 是否同步更新 `CHANGELOG.md`。
- 影响使用方式时是否更新 `VERSION`。
- 是否通过 `Package Module Zips`。

## approve 和 merge 的区别

- approve：负责人认为这次改动可以进入下一步。
- merge：把 PR 真正合进目标分支，会影响后续发布和团队使用。

merge 前要再次核对 diff、校验结果、发布包和目标分支。普通同事不要自己 merge 发布分支 PR。

## merge 后看哪里

面向 `release` 的 PR 合并后，GitHub Actions 会生成模块 zip。到对应 workflow run 的 Artifacts 或仓库 Releases 区域查看。

## 常见卡点

- 看不到最新规则：确认你是否切到了正确分支，运行 `git fetch --all --prune` 后再 `git switch <branch>`。
- 不知道 skill 放哪个模块：先问负责人或让 Codex 给建议，但最终要你确认。
- 校验失败：优先按失败提示修正，不要绕过校验。
- push 没权限：先确认远端地址和 GitHub 权限，让负责人协助。
- Actions 没跑：确认 PR 目标分支是不是 `release`。
