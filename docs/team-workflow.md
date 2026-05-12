# 团队 Skill 工作流程

这份文档给同事和负责人一起使用。普通同事不需要先学会 Git 术语，只要让 Codex 按这里的规则做。

如果是第一次使用，先读 `docs/quickstart-for-teammates.md`，再回到这里看完整流程。

## 分支怎么用

```text
master：稳定基线，大家从这里同步最新规则和正式 skill。
release：发布打包分支，PR 到这里会自动生成模块 zip。
work/<name-pinyin>：个人长期工作分支，一个人可以创建多个 skill。
skill/<module-id>/<skill-name>/<short-change>：短期精确分支，用于单个 skill 或一次明确改动。
docs/<topic>：文档分支。
fix/<module-id>/<skill-name>/<bug>：修复分支。
```

普通同事默认只使用自己的个人分支：

```text
work/zhangsan
work/lisi
work/renqc
```

创建或切换个人工作分支前，Codex 必须先检查当前分支和工作区状态，再询问并确认使用者真实姓名或其确认的姓名拼音/缩写。`work/<name-pinyin>` 不应从系统用户名、Git 用户名或 GitHub 用户名推断，除非用户明确确认它就是要用的姓名缩写。

## 上传目标怎么判断

Codex 遇到“上传”“保存到远程”“push”“发给别人看”这类说法时，必须先分清楚目标分支。

默认判断：

```text
只说“上传 / 保存到远程” -> 默认 push 到当前个人 work/<name-pinyin> 分支，不需要 PR。
普通同事说“进入正式分支 / 合到 master / 团队都能用” -> 必须创建 PR 到 master。
说“发布 / 打包 / 生成模块 zip / release” -> 必须创建 PR 到 release，并等待 Package Module Zips 通过。
说“给负责人审核” -> 创建 PR；目标分支需要再次确认是 master 还是 release。
```

权限和审核边界：

| 动作 | 默认目标 | 是否需要 PR | 说明 |
| --- | --- | --- | --- |
| 本地 commit | 当前本地分支 | 不需要 | 只是本机保存点 |
| push 到个人工作分支 | `origin/work/<name-pinyin>` | 不需要 | 保存个人草稿和阶段成果 |
| 从个人分支进入 `master` | `master` | 必须 | 影响团队稳定基线 |
| 从个人分支进入 `release` | `release` | 必须 | 影响打包发布和 Release |
| merge PR | PR 目标分支 | 必须明确确认 | approve 不等于 merge |

技术上可以给个人工作分支也设计 PR，但通常没有必要。个人工作分支就是草稿区和个人工作台，不应让每次保存草稿都变成审核流程。

高风险改动即使只是 push 到个人分支，也建议先做提交范围自检；但这不等于必须创建 PR。高风险包括 workflow、发布脚本、权限、分支保护、跨部门通用 skill 或敏感资料相关改动。

## 同事创建 skill 的流程

同事可以直接对 Codex 说：

```text
我要做一个 skill，功能是把客户会议记录整理成跟进动作。
```

Codex 应该：

1. 确认当前分支和工作区状态，并确认使用者真实姓名或姓名拼音/缩写；如需创建或切换个人分支，先进入 `work/<name-pinyin>`。
2. 如果用户没有讲清楚，先追问这个 skill 的使用人、业务场景、输入材料、输出结果和可用标准。
3. 询问或确认这个 skill 属于哪个模块，模块选项要显示“英文 ID + 中文名”。
4. 用拼音或英文生成功能型 skill 名。
5. 确认目录名、frontmatter `name` 和 `$skill-name` 调用名一致。
6. 放到 `modules/<module-id>/skills/<skill-name>/`。
7. 补齐 `SKILL.md`、`README.md`、`VERSION`、`CHANGELOG.md`。
8. 运行 `tools/validate-skill.ps1`。
9. 新建或改名 skill 时，默认同步 `.codex/skills/<skill-name>/` 项目可调用入口，确保本项目可手动调用。
10. 保存 commit，commit message 写清楚模块和 skill。
11. 上传前再次确认模块归属。

## 每个阶段结束后的引导

Codex 不应该只说“完成了”，而应该说明当前状态和下一步选择。

标准格式：

```markdown
## 本阶段完成

已完成：
- <已经完成的事情>

当前状态：
- <分支、校验、commit、push、PR 状态>

建议下一步：
1. <推荐动作>
2. <备选动作>

我建议先选 <number>，因为 <原因>。
```

常见节点：

- 需求不清时：先追问场景、输入、输出和可用标准，不创建文件。
- 创建文件后：建议运行校验、最小试运行或继续优化内容。
- 校验通过后：只问两个方向：继续深化调整，或进入下一步流程。
- 需要手动调用时：建议刷新 `.codex/skills/<skill-name>/`，再用 `$skill-name` 测试；同步后如果选择器暂时不可见，刷新 skill 列表或新开 Codex 线程。
- commit 后：只问继续深化调整，还是 push 到个人工作分支。
- push 到个人工作分支后：说明已完成远程草稿保存；再问继续深化调整，还是由 Codex 准备进入 `master` / `release` 的 PR。
- PR 检查通过后：提醒 approve 不等于 merge。
- merge 前：必须让负责人明确确认目标分支和影响。

动作分级：

- 自动动作：读文件、看 diff、跑 `tools/validate-skill.ps1`、做不影响外部系统的本地测试。
- 确认后动作：改文件、commit、push、创建 PR、approve。
- 强确认动作：merge、tag、release、删除或废弃 skill、修改 workflow 或分支保护相关规则。

## 上传前必须问的问题

当同事说“上传”“保存到远程”“发起 PR”“给负责人审核”时，Codex 必须确认：

```text
这次是只上传到你的个人工作分支，还是要进入 master / release？
这个 skill 最终归属哪个模块？
这个 skill 具体解决什么场景，输入和输出是什么？
本次是否只上传这些 skill？
是否已经确认机器命名没有中文？
是否已经同步 `.codex/skills/` 项目可调用入口，以便 `$skill-name` 手动调用并显示项目来源？
是否已经运行 validate？
```

如果用户没有明确模块，不要直接上传。
但 Codex 不能只问空问题。它应该先根据 skill 内容推荐模块、skill 名、提交范围、版本处理和 PR 内容，再让用户核实关键项。

如果用户没有明确目标分支，默认先引导为“push 到当前个人 `work/<name-pinyin>` 分支，不需要 PR”。push 完成后，再询问是否要发起 PR 进入 `master` 或 `release`。

上传前还要说明本次准备提交的路径清单。如果本次新增或修改的是可调用 skill，要同时列出 `modules/...` 正式归档路径和 `.codex/skills/...` 项目可调用入口，避免漏交或带上无关改动。

这里的 `.codex/skills/...` 指当前仓库里的项目级目录，例如 `D:\...\<workspace-folder-name>\.codex\skills\...`，不是 C 盘全局 Codex 目录。全局目录通常是 `C:\Users\<user>\.codex\skills\...`，只有明确要跨项目使用时才考虑。项目入口在选择器中应显示当前工作目录名作为来源，不应固定写死某个项目名；同步后不要承诺固定秒数自动加载，以刷新 skill 列表或新开线程后的可见结果为准。

## 反复打磨与下一步

skill 开发不要求一次直线走完。Codex 到达本地草稿、校验通过、commit、push 这些稳定节点时，只需要问两个方向：

```text
现在有两个方向：继续深化调整，还是进入下一步流程？
```

如果同事选择继续深化，Codex 应继续处理内容、示例、测试、触发条件、输出格式或 README，不推进 commit、push 或 PR。如果同事选择进入下一步，Codex 再按当前状态推进校验、commit、push 或 PR。这样既不会一直催下一步，也不会让新人做完一步后不知道接下来该干什么。

## PR 由 Codex 生成

当同事说“给负责人审核”“进入 master”“进入 release”“创建 PR”时，Codex 应自动完成 PR 申请材料，而不是让同事自己写。

Codex 创建 PR 前必须先整理：

- 当前 diff 和变更路径。
- 涉及模块和 skill 名。
- 新增、修改、文档、治理或 workflow 类型。
- `VERSION` 和 `CHANGELOG.md` 是否已更新。
- `.codex/skills/<skill-name>/` 项目可调用入口是否已同步。
- `tools/validate-skill.ps1` 结果。
- 给审核人的风险、边界或待确认事项。

PR 标题和描述按 `.github/pull_request_template.md` 自动填好。创建 PR 前只需要让同事确认目标分支是 `master` 还是 `release`，以及是否提交申请。

创建正式路径、commit、push 或 PR 前，Codex 应给出一份已预填的关键决策确认单：

- 推荐模块和理由。
- skill 名、正式路径和项目可调用入口。
- 工作分支归属。
- 本次提交范围和排除项。
- `VERSION` / `CHANGELOG.md` 处理。
- PR 标题、描述摘要、审核说明和假设。
- 下一步动作和 PR 目标分支。

如果信息不确定，Codex 只问少量针对性问题，例如“我判断归到 customer-success，因为它处理客户会议和交付跟进，你确认吗？”。用户确认后，Codex 按确认范围继续完成文件、校验、commit、push 和 PR。

如果本机没有 Git、GitHub CLI 或登录认证，Codex 不应停在“你自己去 GitHub 写 PR”。应优先使用可用的 GitHub connector、网页或浏览器流程；如果仍然无法创建，输出完整 PR 标题、描述和明确阻断原因。

## 负责人审核流程

负责人看 PR 时，优先看：

- 是否放在正确模块。
- skill 名是否按功能命名。
- 机器识别名是否使用拼音/英文 ASCII。
- 是否有 `SKILL.md`、`README.md`、`VERSION`、`CHANGELOG.md`。
- 修改 `SKILL.md` 是否同步更新 `CHANGELOG.md`。
- 影响使用方式时是否更新 `VERSION`。
- 是否通过 `Package Module Zips`。

负责人可以 approve 表示认可这次改动；merge 会真实进入目标分支，必须单独确认。面向 `release` 的 PR merge 后会触发发布打包流程。

## 为什么不用一个 skill 一个长期分支

公司后续会有很多 skill。如果每个 skill 都占一个长期分支，分支会太多，审核和清理都会变难。

所以长期分支按人建：

```text
work/<name-pinyin>
```

本次改了什么，通过 commit、PR 标题和 PR 描述表达。
