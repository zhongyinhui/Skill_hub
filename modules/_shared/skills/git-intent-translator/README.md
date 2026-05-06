# Git Intent Translator

这个 skill 让不会 Git/GitHub 术语的同事也能让 AI 正确操作版本工具。

用户可以说：

- "保存一下现在这个版本。"
- "把这版发给同事看看。"
- "看看我改了什么。"
- "这个版本不要了，回到之前。"
- "把这个 skill 发布一版。"

Agent 应该把这些话翻译成合适的 Git 或 GitHub 操作，并且用普通语言解释结果。

## Reviewer Checklist

- 是否避免要求用户先学会 Git 术语。
- 是否区分安全操作和危险操作。
- 是否明确禁止模糊场景下直接丢弃改动。
- 是否覆盖 skill 仓库常见动作：保存、评审、发布、回退、同步。

## Release Notes

这个 skill 适合和 `tools/validate-skill.ps1`、`.githooks/`、`docs/git-for-skill-authors.md` 一起使用。

