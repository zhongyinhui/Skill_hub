# Skill Governance Router

这是 Skill Hub 的团队治理 skill，用于在创建、保存、上传、提交或发布 skill 前，提醒 Agent 检查命名、部门归属、分支和 PR 描述。

它不只做规则检查，也负责在每个阶段结束后给出下一步引导，帮助不熟悉流程的同事从本地草稿走到验证、提交、push、PR、审核和发布。

## 适用场景

- 创建或封装新 skill。
- 修改已有 skill。
- 上传同事在个人分支上的 skill。
- 判断 skill 应该放到哪个模块。
- 准备 commit、push 或 PR。

## 审核重点

- 是否使用拼音或英文 ASCII 作为机器识别名。
- 是否在创建或切换个人工作分支前确认真实姓名或姓名拼音/缩写，而不是从系统用户名、Git 用户名或 GitHub 用户名推断。
- 是否按功能命名 skill。
- 是否在创建前问清 skill 场景、输入、输出和可用标准。
- 是否在上传前确认部门模块。
- 是否用 commit 和 PR 描述补足长期工作分支缺失的信息。
- 是否由 Codex 根据 diff、skill 内容和仓库模板生成 PR 标题与描述，而不是让新人自己写。
- 是否在创建正式路径、commit、push 或 PR 前给出已预填的关键决策确认单，并让用户核实模块、路径、范围、PR 内容和目标分支。
- 是否运行 `tools/validate-skill.ps1`。
- 是否在阶段结束后说明当前状态和下一步建议。
- 是否在本地草稿、校验、commit、push 等稳定节点提供“继续深化调整 / 进入下一步流程”两个出口。
- 是否把 approve 和 merge 分开处理，merge 前必须明确确认。
- 是否说明正式存放位置和项目 `$skill-name` 调用入口的区别。
- 是否区分“push 到个人工作分支”和“创建 PR 进入 master/release”。
- 创建或测试具体 skill 时，是否避免顺手修改通用治理规范。

## 阶段式引导

Agent 完成一个阶段后，应输出简短的状态提示：

```markdown
## 本阶段完成

已完成：
- 新建 skill 必要文件

当前状态：
- 还未运行 validate
- 还未 commit

建议下一步：
1. 运行校验和最小试运行
2. 继续优化 README 和示例

我建议先选 1，因为现在还没有证明它能通过仓库规则。
```

常见阶段包括：

- 需求确认
- 归属与命名
- 本地草稿
- 校验
- 项目可调用入口刷新
- 深化调整或进入下一步
- commit 准备
- commit 完成
- push 完成
- PR 目标确认
- PR 准备
- review / approve 完成
- merge 后检查

## 分支目标规则

- 创建或切换个人工作分支前，先检查当前分支和工作区状态，再询问并确认使用者真实姓名或其确认的姓名拼音/缩写。
- `work/<name-pinyin>` 里的 `<name-pinyin>` 必须来自用户确认；不要直接使用系统用户名、Git 用户名或 GitHub 用户名，除非用户明确确认它就是要用的姓名缩写。
- 用户只说“上传”“保存到远程”“push”时，默认 push 到当前 `work/<name-pinyin>` 个人工作分支，不需要 PR。
- 说“进入正式分支”“合到 master”“团队正式使用”时，创建 PR 到 `master`。
- 用户说“发布”“打包”“生成模块 zip”“release”时，创建 PR 到 `release`，并等待 `Package Module Zips` 通过。
- 用户说“给负责人审核”时，先问清 PR 目标是 `master` 还是 `release`。
- push 到个人工作分支后，不要自动创建 PR；先询问是否要继续进入正式分支。

## 迭代与 PR 申请

skill 开发通常需要反复打磨。Agent 在本地草稿、校验通过、commit 或 push 这类稳定节点，只问两个方向：

```text
现在有两个方向：继续深化调整，还是进入下一步流程？
```

如果选择继续深化，Agent 应继续优化内容、示例、测试、触发条件、输出格式或 README，不推进 commit、push 或 PR。如果选择进入下一步，Agent 再按当前阶段推进校验、commit、push 或 PR。

当用户要进入 `master`、`release`、给负责人审核或创建 PR 时，Agent 必须自己生成 PR 申请包：

- PR 标题。
- PR 描述。
- 变更路径和模块。
- 新增或修改的 skill。
- 校验结果。
- `VERSION` / `CHANGELOG.md` 状态。
- 项目 `.codex/skills/` 可调用入口状态。
- 给审核人的风险、边界和待确认事项。

如果本机缺少 Git、GitHub CLI 或认证，Agent 应优先改用可用的 GitHub connector、网页或浏览器流程。仍无法创建时，输出完整 PR 申请包和明确阻断原因，不要让新人从零写 PR。

在创建正式路径、commit、push 或 PR 前，Agent 还必须先给出关键决策确认单。确认单必须由 Agent 根据 skill 内容和当前 diff 预填，不要把空表交给用户：

- 模块归属和推荐理由。
- skill 名和正式路径。
- 工作分支归属。
- 本次提交范围和排除项。
- 是否同步项目 `.codex/skills/` 可调用入口。
- `VERSION` / `CHANGELOG.md` 是否更新。
- 下一步动作。
- PR 标题、描述、审核说明和假设。
- PR 目标分支。

Agent 可以主动推荐模块、skill 名、PR 标题和目标分支；不确定时标注假设，并只问少量针对性核实问题。用户确认后，Agent 应按确认范围继续完成文件修改、校验、commit、push 和 PR 创建；如果范围、模块、目标分支或外部动作授权变化，再重新确认。

## 相关文档

- `docs/naming-and-routing.md`
- `docs/team-workflow.md`
- `docs/quickstart-for-teammates.md`

## 调用位置

正式 skill 放在：

```text
modules/<module-id>/skills/<skill-name>/
```

如果需要在本项目里手动用 `$skill-name` 调用，需要确保入口存在于：

```text
.codex/skills/<skill-name>/
```

新建或改名 skill 时，默认同步这个项目可调用入口。这样它在 skill 选择器里会显示当前工作目录名作为项目来源，而不是固定写死某个仓库名。

注意：这里的 `.codex/skills/` 是当前仓库里的项目级目录，例如：

```text
D:\...\<workspace-folder-name>\.codex\skills\<skill-name>\
```

它不是 C 盘的全局 Codex 目录。C 盘全局目录通常类似：

```text
C:\Users\<user>\.codex\skills\<skill-name>\
```

项目级 skill 只服务当前项目；全局 skill 才用于多个项目共享。Skill Hub 默认先保证当前项目可调用，跨项目安装以后单独设计。

从正式归档路径刷新项目可调用入口：

```powershell
powershell -ExecutionPolicy Bypass -File tools/sync-codex-skills.ps1 -SkillName <skill-name>
```

如果刷新后 `$skill-name` 仍不可见，通常需要新开 Codex 线程或刷新 skill 列表。
不要承诺固定秒数内后台自动加载；以刷新列表或新开线程后的可见结果为准。
