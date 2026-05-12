# Skill Hub Agent Instructions

本仓库用于管理团队自研 skill。请把这里的每个 skill 都当作一个可发布、可回滚、可审查的产品单元，而不是一份临时提示词文件。

## Core Rules

- 正式 skill 必须放在 `modules/<module-id>/skills/<skill-name>/` 下。
- 跨部门通用 skill 放在 `modules/_shared/skills/<skill-name>/` 下。
- 新 skill 的复制模板放在 `templates/skill/`，模板不是正式发布的 skill。
- 当前业务模块包括：`customer-success`（客户成功）、`sales`（销售）、`ip`（IP 部门）、`private-domain`（私域部门）、`hr`（HR 部门）。
- 每个 skill 至少包含 `SKILL.md`、`README.md`、`VERSION`、`CHANGELOG.md`。
- 修改 `SKILL.md` 时，必须同步更新该 skill 的 `CHANGELOG.md`。
- 修改影响使用方式、输入输出约定或兼容性时，必须更新 `VERSION`。
- skill 命名按功能命名，版本号写入 `VERSION`、`CHANGELOG.md` 和正式 tag；不要为了版本迭代频繁改 skill 目录名。
- 分支名、skill 目录名、`SKILL.md` frontmatter `name`、手动调用名 `$skill-name`、tag、workflow name、job name、artifact name 等机器识别标识必须使用拼音或英文 ASCII，推荐小写字母、数字和连字符。
- skill 目录名、`SKILL.md` frontmatter `name` 和手动调用名 `$skill-name` 必须一致；`SKILL.md` 是固定入口文件名，不是 skill 名。
- 新建或改名正式 skill 时，默认同时维护正式归档路径和当前仓库 `.codex/skills/<skill-name>/` 项目可调用入口，让它能在本项目 skill 选择器中以项目来源（如 `Skills_hub`）出现；只有用户明确说明只做正式归档草稿时才可暂不同步。
- 更新 `.codex/skills/` 后，Agent 必须提示用户刷新 skill 列表或新开 Codex 线程；不要承诺后台会在固定秒数内自动加载。
- 如果用户只说要创建一个 skill，Agent 必须先追问使用人、业务场景、输入材料、输出结果和可用标准，不要直接创建文件。
- 不要把本机密钥、个人路径、聊天记录、临时日志提交进仓库。
- 不要直接删除旧 skill。弃用时在 `CHANGELOG.md` 和 `README.md` 中标记，并说明替代方案。
- Agent 在修改某个 skill 前，必须先阅读该 skill 的 `README.md`、`CHANGELOG.md` 和现有测试或示例。
- 处理某个具体 skill 的创建、修改或测试时，不要顺手修改 `AGENTS.md`、`docs/` 流程文档、`skill-governance-router` 等底层治理规范；只有用户明确要求调整治理机制时才修改这些通用规则。
- 用户表示第一次使用、不会流程、想创建/修改/上传 skill 但没有给出完整步骤时，Agent 必须主动进入引导模式：先检查分支和工作区状态，再按“需求确认 -> 模块归属 -> 命名 -> 文件修改 -> 校验 -> commit -> push -> PR”逐步推进，不要等用户自己问流程。
- 创建或切换个人工作分支前，Agent 必须先询问并确认使用者真实姓名或其确认的姓名拼音/缩写；不得直接从系统用户名、Git 用户名或 GitHub 用户名推断。分支创建或切换应在检查工作区状态之后、修改文件之前完成。
- Agent 在完成需求确认、本地草稿、校验、commit、push、PR、review 或 merge 等阶段后，必须简短说明当前状态和建议下一步，不能只说“完成了”。
- skill 开发不是单向流水线。完成本地草稿、校验通过、commit 或 push 等稳定节点后，Agent 必须给两个出口：继续深化调整，或进入下一步流程；用户选择继续深化时，不要推进 commit、push 或 PR。
- 当用户要“给负责人审核”、进入 `master` / `release` 或创建 PR 时，Agent 必须根据当前 diff、skill 内容、CHANGELOG、VERSION 和校验结果自动生成 PR 标题与描述，按 `.github/pull_request_template.md` 填好申请材料；不要要求没有开发经验的同事自己写 PR。
- 如果本机缺少 Git、GitHub CLI 或相关认证导致 PR 流程失真，Agent 必须先改用可用的 GitHub connector、网页或浏览器流程；仍无法创建时，输出完整 PR 申请包和明确阻断原因，不要把问题简化成“请你自己去写 PR”。
- 在创建正式路径、commit、push 或 PR 前，Agent 必须先形成“关键决策确认单”：根据 skill 内容预填模块、skill 名、路径、提交范围、版本/CHANGELOG 处理、PR 标题/描述和目标分支建议，再用少量针对性问题让用户核实关键项；不要把空白 PR 模板丢给用户填写。用户确认后，Agent 再按确认范围继续完成文件修改、校验、commit、push 和 PR 创建；范围、模块、目标分支或外部动作授权变化时必须重新确认。

## Module Routing Rules

- 创建或上传 skill 前，Agent 必须确认 skill 所属模块；用户未明确说明时，要主动提问，不要只按当前目录猜测。
- 如果用户只说了业务场景，Agent 可以先根据 skill 内容给出建议模块和理由，但在创建正式路径、提交、推送或创建 PR 前必须让用户确认；模块选项必须显示英文机器 ID 和中文部门名。
- `customer-success`：客户交接、客户过程记录、客户需求与交付、客户健康度、续费、风险、客户会议和行动项。
- `sales`：线索、商机、拜访、报价、合同、回款前推进、销售跟进和销售材料。
- `ip`：IP 内容策划、账号定位、选题、脚本、发布计划、内容资产沉淀。
- `private-domain`：社群运营、用户分层、私域触达、活动转化、私域数据和过程资料。
- `hr`：招聘、面试、候选人跟进、入职、培训、绩效和组织资料。
- `_shared`：两个及以上部门都能复用，或属于 Git/GitHub、文档、表格、会议、知识库、流程治理等通用能力。
- 若一个 skill 同时适合多个部门，优先问用户归属；无法确定时放入 `_shared`，并在 `README.md` 说明适用部门。
- 正式 skill 的归档路径是 `modules/<module-id>/skills/<skill-name>/`；本仓库默认同时维护 `.codex/skills/<skill-name>/` 项目可调用入口，以便在本项目中手动 `$skill-name` 调用并在选择器中显示项目来源。项目 `.codex/skills/` 不是 C 盘全局 Codex skill 目录；全局安装只有在用户明确要求跨项目使用时才处理。

## Language Rules

- 本仓库新增或修改的文档默认使用中文，包括 `README.md`、`docs/`、skill 的说明文档、示例说明和变更记录。
- commit message 必须使用中文，必要的英文技术关键词可以保留，例如 `skill`、`hook`、`tag`、`VERSION`。
- PR 标题、PR 描述、PR review 回复和合并说明必须使用中文。
- 如果引用上游工具、命令、错误信息或英文 API 名称，保持原文，不要为了中文化而改写命令或标识符。
- 专有名词如 `skill`、`Agent`、`GitHub Actions`、`workflow`、`release`、`PR`、`CI`、`tag`、`module` 可以保留英文。

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
<module-id>/<skill-name>/v<version>
```

示例：

```text
customer-success/customer-handover/v1.2.0
_shared/git-intent-translator/v0.1.0
```

## Git Workflow

推荐流程：

1. 普通工作从个人长期分支开始。先检查当前分支和工作区状态，再询问并确认使用者真实姓名或其确认的姓名拼音/缩写，然后创建或切换到 `work/<name-pinyin>`，例如 `work/renqc`。
2. 修改 skill 文件。
3. 运行 `tools/validate-skill.ps1`。
4. 提交 commit，commit message 说明改动目的。
5. 如果要给业务同事交付压缩包，提交 PR 到 `release` 分支，让 GitHub Actions 自动按模块打包。
6. 合并前检查 diff、CHANGELOG、版本号和 workflow artifact。
7. 发布时打 tag。

`release` 分支的 PR 会触发 `.github/workflows/package-modules.yml`，按模块生成 zip。不要手工提交 `dist/` 下的打包产物。

用户只说“上传”“保存到远程”或 “push” 时，默认上传到当前个人 `work/<name-pinyin>` 分支，不需要 PR；如果普通同事要进入 `master`、`release` 或正式团队使用，必须创建 PR 并审核。

用户说“给负责人审核”时，Agent 必须先确认 PR 目标是 `master` 还是 `release`。

推荐分支命名：

```text
work/<name-pinyin>
skill/<module-id>/<skill-name>/<short-change>
docs/<topic>
fix/<module-id>/<skill-name>/<bug>
```

- `work/<name-pinyin>` 是个人长期工作分支，一个人可以在这里创建多个 skill。
- `work/<name-pinyin>` 中的 `<name-pinyin>` 必须来自用户确认的真实姓名拼音或缩写；不要直接使用系统用户名、Git 用户名或 GitHub 用户名，除非用户明确确认它就是要用的姓名缩写。
- `skill/<module-id>/<skill-name>/<short-change>` 是短期精确分支，用于单个 skill 或一次明确改动的评审，不要求每个 skill 长期占用一个分支。
- 分支名不能使用中文；姓名使用拼音或姓名拼音缩写。
- 长期分支名只表达“谁在工作”，本次改了什么必须通过 commit message、PR 标题和 PR 描述表达。

## Commit Guidelines

commit 应该表达一个清晰意图。推荐格式：

```text
skill(customer-success/customer-handover): 新增客户交接示例
fix(_shared/git-intent-translator): 补充回退确认规则
docs: 解释 skill 版本管理流程
work(renqc): 补充 skill 命名与上传规范
```

避免使用：

```text
update
fix
修改一下
wip
```

如果一次提交涉及多个 skill，commit message 要概括批次目的；PR 描述必须逐项列出每个 skill 的模块、路径和变化。

## Pull Request Guidelines

- PR 标题必须说明变更范围，例如 `work(renqc): 补充团队 skill 命名与上传规范` 或 `skill(customer-success/customer-handover): 新增客户交接 skill`。
- PR 描述必须包含：本次变更清单、涉及模块、是否新增或修改 skill、是否更新 `CHANGELOG.md`、是否运行 `tools/validate-skill.ps1`。
- 从 `work/<name-pinyin>` 发起的 PR 可能包含多个 skill，但必须在 PR 描述中列清楚；不要依赖分支名表达改动内容。
- 面向 `release` 的 PR 必须等待 `Package Module Zips` 检查通过后再合并。
- approve 和 merge 分开处理：approve 表示审核认可；merge 会真实进入目标分支，必须单独确认。

## GitHub Actions

- `.github/workflows/*.yml` 和 `.github/workflows/*.yaml` 中所有 `name:` 字段必须使用英文 ASCII。
- 不要把中文 workflow 名、job 名或 step 名配置为 GitHub Actions 的 `name:`，尤其不要作为分支保护的 required status check。
- release 分支保护规则中的必需检查名必须与实际 GitHub Actions job 名完全一致，目前应使用 `Package Module Zips`。

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
