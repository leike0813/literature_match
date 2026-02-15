# 文献匹配组件（Match Skill）- 项目约定（AGENTS.md）

本项目目标：将输入 Markdown 文档中的参考文献条目，匹配到 Zotero 库条目（以 Better BibTeX `citekey` 为唯一主键），输出 `match_result.json`。
通用协作规则沿用用户级全局 AGENTS.md；本文件仅补充项目特有约定。

## 1. 交付物与边界
- 交付物：`match_result.json`（机器可消费、可复核、可追溯）。
- 不修改输入文档（不插入 Obsidian 链接；不同文档插入逻辑由独立脚本处理）。
- 不写回 Zotero（不自动打标签/改集合；未来如需写回另开组件）。

## 2. 数据源（只读）与字段要求
- Zotero 本地 Better BibTeX 导出 API（只读）：
  - 默认拉取：`http://127.0.0.1:23119/better-bibtex/export/library?/1/library.betterbibtexjson`
- 输出必须包含（若库中存在）：
  - `citekey`、`itemKey`、`zotero_tags`
  - **全部 PDF 附件**：`pdf_attachments[]`（每个包含 `title/path/url`）

## 3. 匹配策略（成本可控）
- 分层策略固定为：
  1) 引用条目抽取（行号/编号/raw_text/解析出的 doi/url/arxiv/year/title_guess/author_guess）
  2) 确定性匹配：doi → arxiv → url
  3) 文本检索召回 topK 候选（推荐 TF‑IDF title 为主，year/author 轻量加权）
  4) LLM 仅对 “needs_llm” 条目判别，且只能在 topK 候选内选择 citekey 或输出 null
- 禁止将整个库（betterbibtexjson 全量）交给 LLM。

## 4. `match_result.json` 约定（验收标准）
- `refs[]` 中每条必须包含：
  - `ref_id`、`line_start/line_end`、`raw_text`
  - `match.status/method/confidence`
  - `candidates[]`（允许为空，但字段要存在）
- `candidates[]` 每个候选应包含：`citekey/itemKey/score/title/year/authors/doi/url/zotero_tags/pdf_attachments`

## 5. 跨平台约定
- Zotero 附件 `path` 视为不透明字符串：不在本组件内做路径映射/重写。
- 所有文本默认 UTF‑8 读写；输出 JSON 需 `ensure_ascii=false`。

## 6. 输出文件管理
- `match_result.json` 属于可再生成产物，默认不纳入版本控制（如需纳入仅提交脱敏/小样例）。

## 7. 最小自测
- 至少保证：
  - Zotero endpoint 不可用时给出可读错误信息
  - 抽取不到参考文献段落时输出空 refs + warnings
  - 同一输入在相同库状态下输出结构稳定（字段不缺失）