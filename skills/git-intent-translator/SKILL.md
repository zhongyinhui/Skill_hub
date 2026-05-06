---
name: git-intent-translator
description: Use when a user wants Git or GitHub work done through ordinary language, avoids terms like commit, push, merge, pull request, branch, tag, diff, or asks to save, share, publish, review, restore, compare, sync, or release repository changes without knowing Git terminology.
---

# Git Intent Translator

Translate ordinary user intent into safe Git and GitHub operations. Do not require the user to know Git terms.

## Core Principle

Speak in the user's words first, Git words second. Execute only after the local state and risk are understood.

## Workflow

1. Inspect the repository state with `git status --short --branch`.
2. If the request may affect remote state, inspect remotes and current branch.
3. Translate the user's wording into a concrete operation.
4. For safe read-only actions, execute directly.
5. For local save/release actions, summarize what will be included before committing or tagging.
6. For destructive actions, ask for explicit confirmation and name the exact files or refs affected.
7. Report the result in ordinary language, with Git terms in parentheses only when useful.

## Intent Map

| User says | Interpret as | Usual action |
| --- | --- | --- |
| 保存一下, 记录一版, 留个版本 | Save a local checkpoint | Review diff, stage intended files, commit |
| 把这版给同事看看, 发给别人评审 | Share for review | Commit, push branch, open or prepare PR |
| 看看我改了什么 | Review changes | `git status`, `git diff` |
| 跟线上同步一下, 更新到最新 | Sync from remote | Fetch, inspect, then pull or rebase based on repo policy |
| 把这个版本定下来, 发布这个 skill | Release version | Validate, check `VERSION`, create skill tag |
| 回到刚才那版, 撤回这个改动 | Restore or revert | Inspect diff/log, ask before destructive checkout/reset |
| 合到主版本里 | Merge completed work | Check clean state, merge or create PR depending on remote policy |
| 我想开个新尝试 | Start isolated work | Create a new branch |
| 对比两个版本 | Compare versions | `git diff`, `git log`, or tag comparison |
| 这次不要了 | Discard work | Ask confirmation, then restore only named files |

## Safety Rules

- Never run destructive commands such as `git reset --hard`, `git clean`, or broad restore commands from ambiguous wording.
- Never stage all files without checking whether unrelated or personal files are present.
- Never assume "发给同事" means pushing to `main`; prefer a branch and PR/review path.
- Never assume "同步" means overwriting local work; protect uncommitted changes first.
- If the user uses a Git term incorrectly, respond to the intent, not the vocabulary mistake.
- If remote GitHub access is unavailable, prepare the local branch/commit and explain the remaining manual step.

## Response Style

Use plain language:

- "我会先保存当前这组改动" instead of "I will commit".
- "我会把这组改动放到一个单独的评审入口" instead of "I will open a PR".
- "这会覆盖本地文件，需要你确认" instead of "This is a destructive checkout".

Use Git terms only as parenthetical labels when they help future learning:

```text
我已经保存了一版（commit）：skill(git-intent-translator): add ordinary-language git mapping
```

## Examples

### Example 1

User: "把现在这个版本保存一下。"

Agent:

1. Checks current branch and changed files.
2. Summarizes included files.
3. Runs validation if the repo defines it.
4. Creates a commit with a meaningful message.
5. Says: "已经保存了一版（commit），以后可以回到这个点。"

### Example 2

User: "发给同事看看。"

Agent:

1. Ensures changes are committed.
2. Checks remote availability.
3. Pushes a review branch if possible.
4. Opens or prepares a pull request.
5. Says: "我已经把它放到评审入口（PR）里，同事可以看 diff 和评论。"

### Example 3

User: "这个不要了，回到之前。"

Agent:

1. Checks what changed.
2. Shows the exact files that would be restored.
3. Asks for confirmation before discarding anything.
4. Restores only confirmed files.

