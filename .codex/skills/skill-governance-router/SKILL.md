---
name: skill-governance-router
description: Use when working in Skill Hub to create, rename, save, upload, submit, review, or publish team skills; enforce pinyin/English machine names, confirmed personal branch identity, project callable entries, iterative refinement checkpoints, module routing, commit messages, and Codex-generated PR applications.
---

# Skill Governance Router

Use this skill as the guardrail before creating, saving, uploading, submitting, reviewing, or publishing a skill in this repository.

## Trigger

Trigger when the user says they want to:

- 创建、制作、封装、改名或更新一个 skill。
- 保存、上传、推送、发起 PR、发布或打包 skill。
- 给同事建立工作分支或整理同事提交的 skill。
- 判断 skill 应该放在哪个部门模块。

## Core Rule

Machine identifiers use pinyin or English ASCII. Human-facing explanations stay Chinese.

Machine identifiers include:

- branch names
- skill directory names
- `SKILL.md` frontmatter `name`
- tags
- GitHub Actions names
- artifact names
- fixed script IDs

## Workflow

1. Confirm the current branch and branch owner.
   - Inspect the current branch and worktree status before creating or switching branches.
   - Normal personal work should happen on `work/<name-pinyin>`.
   - Before creating or switching to a personal work branch, ask for the worker's real name or their explicitly confirmed name pinyin/initials.
   - Do not infer `<name-pinyin>` from the OS username, Git username, or GitHub username unless the user explicitly confirms that value is the desired real-name slug.
   - Create or switch the personal work branch after status inspection and before skill file edits.
   - Do not push directly to `master` or `release`; create a PR for formal branches.

2. Confirm the skill brief before file edits.
   - If the user only says they want to create a skill, ask for the concrete scenario before creating files.
   - Minimum brief: user group, business scenario, input material, expected output, and success standard.
   - If details are still missing, stay in intake and do not create a placeholder skill.
   - For a concrete skill creation, update only that skill's files and required callable entry; do not modify repository governance files unless the user explicitly asks to change the governance mechanism.

3. Confirm the target module before upload.
   - If the user already named a module, restate it and proceed.
   - If the module is missing or ambiguous, ask before creating the final path, pushing, or opening a PR.
   - Do not infer the module only from the current directory.
   - Show module options as machine ID plus Chinese label, such as `customer-success（客户成功）`.

4. Create or validate the skill name.
   - Use a function-based slug, not a person name.
   - Use lowercase pinyin or English, digits, and hyphens only.
   - Keep version numbers in `VERSION`, `CHANGELOG.md`, and tags, not in the directory name.
   - Directory name, `SKILL.md` frontmatter `name`, and manual `$skill-name` call name must match.
   - `SKILL.md` is a fixed entry file name; when linking it in replies, label the link as `<skill-name> 的 SKILL.md` instead of bare `SKILL.md`.

5. Place the skill.
   - Department skill: `modules/<module-id>/skills/<skill-name>/`
   - Shared skill: `modules/_shared/skills/<skill-name>/`
   - Required files: `SKILL.md`, `README.md`, `VERSION`, `CHANGELOG.md`
   - This formal path is the source of truth for review, release, and rollback.

6. Decide whether the skill should be callable in this project.
   - Formal repo path `modules/<module-id>/skills/<skill-name>/` is the review and release source.
   - Project callable path `.codex/skills/<skill-name>/` is what makes the skill appear in this project's `$` skill list.
   - For newly created or renamed skills, maintain the project callable entry by default unless the user explicitly says this is only a formal archive draft.
   - In the selector, project callable skills should show the current project as their source, such as `Skills_hub`.
   - Project `.codex/skills/` is relative to the current repository, such as `D:\...\Skills_hub\.codex\skills\`; it is not the global Codex home.
   - Global user skills live under the user's Codex home, such as `C:\Users\<user>\.codex\skills\`, and are a separate distribution choice.
   - To refresh the callable entry from the formal path, run `tools/sync-codex-skills.ps1`.
   - If `$skill-name` is not visible after sync, tell the user to refresh the skill list or start a new Codex thread; do not promise a fixed automatic load time.

7. Save change information outside the branch name.
   - Long-lived branches only identify the worker, such as `work/renqc`.
   - Commit messages and PR descriptions must list changed modules and skill paths.

8. Confirm the upload target.
   - If the user only says "上传", "保存到远程", or "push", default to pushing the current branch to the user's personal `work/<name-pinyin>` branch.
   - Pushing to a personal work branch does not require a PR because it only saves draft/staged work remotely.
   - If the change needs to enter `master`, `release`, or "团队正式使用", create a PR and require review.
   - If the user says "发布", "打包", "生成模块 zip", or "release", target `release` and wait for `Package Module Zips`.
   - If the user says "发给负责人审核", ask whether the PR target is `master` or `release`.

9. Validate before push or PR.
   - Run `powershell -ExecutionPolicy Bypass -File tools/validate-skill.ps1`.
   - If validation fails, fix it before uploading.

10. Confirm key decisions before formal paths, commit, push, or PR.
   - Codex must prefill the decision sheet from the skill content and current diff; do not hand the user a blank checklist.
   - Required prefilled fields: branch owner/work branch, target module, skill name and formal path, changed-file scope, project callable entry sync, `VERSION` / `CHANGELOG.md` handling, next action, PR title/body, and PR target branch when applicable.
   - If any field is uncertain, state Codex's best recommendation, mark the assumption, and ask a targeted verification question.
   - If the module is unclear, recommend the likely module with a short reason and show all module options as machine ID plus Chinese label.
   - After the user confirms the decision sheet, proceed within that confirmed scope through file changes, validation, commit, push, and PR creation as needed. Stop and reconfirm if the scope or target branch changes.

11. Use an iteration checkpoint at stable points.
   - Skill work is usually iterative, not a single straight line.
   - After local draft, successful validation, commit, or push, ask the user to choose between continuing refinement and moving to the next workflow step.
   - Do not ask this after every small edit; ask only after a meaningful batch or stable stage.
   - If the user chooses refinement, stay in local draft/validation and do not proceed to commit, push, or PR.

12. Generate PR applications for the user.
   - When the user wants reviewer approval, `master`, `release`, or a PR, Codex must inspect the current diff, changed skill files, `VERSION`, `CHANGELOG.md`, validation result, and target branch.
   - Before creating the PR, show a complete drafted PR application, including title, description, checklist state, assumptions, reviewer notes, module, changed-file scope, and target branch.
   - Ask the user to verify only uncertain or high-impact fields; if the user has explicitly delegated the content judgment, use Codex's best-effort draft and clearly label assumptions.
   - Codex must generate the PR title and description itself using `.github/pull_request_template.md`; do not make non-developer teammates write PR copy from scratch.
   - Prefer available GitHub connector or browser flows when local Git, GitHub CLI, or authentication is missing. Use `gh` only when it is available and appropriate in this environment.
   - If no available route can create the PR, provide a complete PR application package and the exact blocker.

## Stage Guidance

After each meaningful stage, summarize current state and guide the user to the next safe step. Do not only say "done".

Use this shape:

```markdown
## 本阶段完成

已完成：
- <completed item>

当前状态：
- <branch / validation / commit / push / PR state>

阶段选择：
1. 继续深化调整：<what to refine next>
2. 进入下一步流程：<validate / commit / push / PR target>

我建议先选 <number>，因为 <short reason>。
```

Keep the guidance short. Prefer two or three next actions, not a long menu.

## Stage Map

Use these stages when working on a Skill Hub change:

| Stage | Completion signal | Required guidance |
| --- | --- | --- |
| Intake | User asks to create, update, upload, submit, review, or publish a skill | Confirm branch, branch owner real-name slug, and missing skill brief details before file edits; do not create a skill from only "我要创建一个 skill" |
| Routing and naming | User has provided enough skill details | Confirm module with Chinese label, propose a functional skill slug, and explain that directory name, frontmatter `name`, and `$skill-name` call name must match |
| Local draft | Skill files or docs were created or edited | Suggest validation, a minimal self-test, local callable sync, or another content pass |
| Validation | `tools/validate-skill.ps1` has passed or failed | If passed, suggest commit or further optimization; if failed, fix before commit or upload |
| Callable entry | User wants to manually call the skill with `$skill-name` | Ensure `.codex/skills/<skill-name>/` exists and matches the formal skill, then explain how to invoke or refresh |
| Decision gate | Before formal path creation, commit, push, or PR | Present a prefilled key decision sheet with Codex recommendations; ask targeted verification questions and proceed only after confirmation |
| Iteration checkpoint | Local draft, validation, commit, or push reached a stable point | Ask only two direction questions: continue refinement, or move to the next workflow step |
| Commit prep | Validation passed and user wants to save | Summarize changed paths and ask before staging/committing |
| Commit complete | Commit succeeded | Ask whether to continue refinement or push to the user's work branch |
| Push complete | Push to personal work branch succeeded | Say remote draft is saved; ask whether to continue refinement or have Codex prepare a PR into `master` or `release` |
| PR prep | User wants reviewer approval, `master`, `release`, or PR | Generate PR title and body from diff/template, confirm target branch, then create the PR through the best available route |
| PR ready | PR exists or is being prepared | Summarize the generated title/body, changed paths, modules, validation result, version/changelog notes, and reviewer risks |
| Review complete | PR is approved or checks passed | Explain that approve is not merge; merge needs explicit confirmation |
| Merge complete | PR was merged | Suggest checking release workflow, generated artifacts, and optional tag/release follow-up |

## Action Classes

Automatic actions:

- Inspect files, branches, diffs, and local status.
- Generate recommendations and checklists.
- Generate commit messages, PR titles, PR descriptions, and reviewer notes from the current diff.
- Run `tools/validate-skill.ps1`.
- Run local examples or tests when they do not mutate external systems.

Ask before actions:

- Create or modify skill files.
- Stage or commit changes.
- Push a branch.
- Create or update a PR.
- Approve a PR.

Strong-confirm actions:

- Merge a PR.
- Create or push a tag.
- Publish a release.
- Delete, deprecate, or rename an existing skill.
- Modify GitHub Actions, branch protection, or release behavior.

For strong-confirm actions, state the target branch, expected effect, and rollback or follow-up concern before acting.

## Module Routing

- `customer-success（客户成功）`: 客户交接、客户过程记录、客户需求与交付、客户健康度、续费、风险、客户会议和行动项。
- `sales（销售）`: 线索、商机、拜访、报价、合同、回款前推进、销售跟进和销售材料。
- `ip（IP 部门）`: IP 内容策划、账号定位、选题、脚本、发布计划、内容资产沉淀。
- `private-domain（私域部门）`: 社群运营、用户分层、私域触达、活动转化、私域数据和过程资料。
- `hr（HR 部门）`: 招聘、面试、候选人跟进、入职、培训、绩效和组织资料。
- `_shared（跨部门通用）`: 两个及以上部门都能复用，或属于 Git/GitHub、文档、表格、会议、知识库、流程治理等通用能力。

If multiple modules match, ask the user to choose. If still unclear and the skill is cross-department, use `_shared` and explain the boundary in `README.md`.

## Required Questions

Before creating a new skill, ask for missing brief details:

```text
这个 skill 具体解决什么场景？请补充：谁会用、输入材料是什么、希望输出什么、做到什么程度算可用。
```

Before creating or switching a personal work branch, ask when the branch owner is missing:

```text
这次工作分支归属谁？请给真实姓名，或确认要使用的姓名拼音/缩写。我不会直接用系统用户名、Git 用户名或 GitHub 用户名来猜分支名。
```

Before upload, push, or PR, ask when missing:

```text
这次是只上传到你的个人工作分支，还是要进入 master / release？
这个 skill 最终归属哪个模块？可选：customer-success（客户成功）、sales（销售）、ip（IP 部门）、private-domain（私域部门）、hr（HR 部门）、_shared（跨部门通用）。
```

Before formal path creation, commit, push, or PR, present this prefilled decision sheet:

```text
我先根据 skill 内容和当前 diff 拟好方案，请你核实关键项后我再继续执行：
1. 模块归属：<recommended module-id（中文名）>，理由：<short reason>
2. skill 名和路径：<skill-name> -> modules/<module-id>/skills/<skill-name>/
3. 工作分支：work/<confirmed-name-pinyin>
4. 本次提交范围：<paths to include>；排除：<paths to exclude>
5. 项目可调用入口：同步 / 暂不同步 `.codex/skills/<skill-name>/`
6. 版本和 CHANGELOG：更新 / 不更新，理由：<reason>
7. PR 标题和描述：<Codex drafted title/body summary>
8. 下一步动作：继续深化 / 校验 / commit / push / PR
9. PR 目标分支：master / release / 暂不创建 PR
10. 需要你核实的点：<only uncertain/high-impact questions>
```

If the user confirms this sheet, continue through the confirmed stage without asking them to write commit or PR content. Reconfirm only if a new file scope, module, branch, PR target, or external action authorization changes.

At stable iteration checkpoints, ask only these two direction questions:

```text
现在有两个方向：继续深化调整，还是进入下一步流程？
如果继续深化，请告诉我想优化内容、示例、测试、触发条件、输出格式还是 README；如果进入下一步，我会按当前阶段推进校验 / commit / push / PR。
```

If the user does not specify a formal target, default to:

```text
我先按“上传到当前个人工作分支”处理，这一步不需要 PR；上传后再问你是否要进入 master 或 release。
```

Before commit, push, PR, or approval, ask only for the missing decision. Do not repeat every question if the user already answered it.

Before merge, always ask explicitly:

```text
这个 PR merge 后会进入 <target-branch>，并影响后续发布/团队使用。你确认现在 merge 吗？
```

When the target seems likely but not explicit:

```text
我判断它更像 customer-success，因为它处理客户会议和交付跟进。你确认放到 customer-success 吗？
```

## Manual Invocation

When a user asks whether the skill can be called manually:

- The callable name is `$<skill-name>`.
- `<skill-name>` comes from the directory name and `SKILL.md` frontmatter `name`.
- The file name `SKILL.md` must stay uppercase and is not the callable name.
- Formal skill source: `modules/<module-id>/skills/<skill-name>/`.
- Project callable entry: `.codex/skills/<skill-name>/`.
- New or renamed skills should be synced to the project callable entry by default so the selector can show them with the current project source, such as `Skills_hub`.
- This project callable entry is not `C:\Users\<user>\.codex\skills\`; it belongs to the current repository and appears in the `$` list with this project's source name.
- Use the global Codex skill directory only when the user explicitly wants the skill available across projects.
- Use `powershell -ExecutionPolicy Bypass -File tools/sync-codex-skills.ps1 -SkillName <skill-name>` to refresh one project callable entry from the formal source.
- If Codex does not show `$<skill-name>` after sync, refresh the skill list or start a new thread; avoid promising a fixed background load time.

## Commit and PR Patterns

Commit examples:

```text
skill(customer-success/kehu-xuqiu-jiaofu-fenxi): 新增逐字稿需求拆解
skill(sales/shangji-genjin-fenxi): 新增商机跟进分析
work(renqc): 补充团队 skill 命名与上传规范
```

PR titles:

```text
work(renqc): 新增客户成功与销售 skill 批次
skill(customer-success/kehu-xuqiu-jiaofu-fenxi): 新增逐字稿需求拆解
```

PR descriptions must include:

- changed skill paths
- involved modules
- whether each skill is new or modified
- validation result
- version and changelog notes
- reviewer risks or boundaries

Codex must generate the PR application package before creating the PR:

```markdown
PR 标题：
<Chinese title with scope>

PR 描述：
## 本次变更
- <paths and content summary>

## 涉及模块
- <module-id（中文名）>

## 变更类型
- <new skill / modified skill / docs / governance / workflow>

## 自检
- <validation result>
- <VERSION / CHANGELOG state>
- <project callable entry state>

## 给审核人的说明
- <risks, boundaries, or questions>

## 当前阶段与下一步
- <review / approve / wait for Package Module Zips / merge requires explicit confirmation>

## 假设与待核实
- <assumptions Codex used>
- <targeted questions, if any>
```

If Git or GitHub CLI is missing, do not stop at tooling advice. Try the available GitHub connector or browser path first. If creation is still blocked, return the complete PR title/body above plus the precise blocker.

## Branch Target Rules

Use these branch target rules:

| User intent | Default action | PR required |
| --- | --- | --- |
| 上传 / 保存到远程 / push | Push current work branch to `origin/work/<name-pinyin>` | No |
| 给负责人审核 | Ask whether target is `master` or `release`, then create PR | Yes |
| 进入正式分支 / 合到 master / 团队都能同步 | Create PR to `master` | Yes |
| 发布 / 打包 / 生成模块 zip / release | Create PR to `release` | Yes |

After pushing a personal work branch, do not automatically create a PR. Ask:

```text
远程个人分支已更新。下一步是否要创建 PR 进入 master 或 release？
```

## References

For detailed rules, read:

- `docs/naming-and-routing.md`
- `docs/team-workflow.md`
- `docs/quickstart-for-teammates.md`
