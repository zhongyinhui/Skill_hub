# Changelog

## 0.1.0 - 2026-06-08

- 新增 B-SK05 `b-material-reference-attach` 正式 skill 初版。
- 明确只写 B 线 `01_session.raw_input_refs/window_log/ai_analysis_summary/updated_at`。
- 增加材料引用 JSONL 规范，要求每份材料具备 `source_ref`、去重键和归属状态。
- 增加从 Codex session JSONL 自动提取 `input_image` 和 `# Files mentioned by the user` 文件块的脚本。
- 增加读取 Session 材料状态、生成材料引用、追加写回材料引用脚本。
- 明确无主或低置信材料只标记 `needs_confirm/orphan_candidate`，不硬挂客户、不写 A 线正式事实。
