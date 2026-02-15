# literature-match（发布包）

本目录是 **Open Agent Skills** 规范下的可发布 skill 包，用于将 Markdown 文档中的参考文献条目匹配到本地 Zotero（Better BibTeX 导出）条目，并生成 `match_result.json`（不修改原文档）。

## 目录结构

- `SKILL.md`：skill 入口说明（包含 agent 指令与 CLI 调用方式）
- `scripts/`：可执行脚本（确定性流水线与工具脚本）

## 快速使用（CLI）

在仓库根目录、`DataProcessing` conda 环境中运行：

1) 生成初版 `match_result.json`：

```bash
conda run --no-capture-output -n DataProcessing \
  python literature-match/scripts/cli.py match \
  --refs-extracted artifacts/<doc_stem>/refs_extracted.json \
  --library-cache examples/example_entry.library.betterbibtexjson
```

2) 应用 `llm_decisions.json` 固化最终结果：

```bash
conda run --no-capture-output -n DataProcessing \
  python literature-match/scripts/cli.py apply-decisions \
  --match-result artifacts/<doc_stem>/match_result.json \
  --llm-decisions artifacts/<doc_stem>/llm_decisions.json
```

3)（可选）Gemini DR 文档链接化（输出 `<doc>_processed.md`）：

```bash
python literature-match/scripts/gemini_dr_link.py \
  --doc-path <doc_path> \
  --match-result artifacts/<doc_stem>/match_result.json
```

## 重要约束

- `SKILL.md` 中标记为 **Agent instructions** 的步骤应由 LLM 直接完成（语义抽取/判别），不要擅自写临时脚本替代，否则通常会降低输出质量与可控性。

