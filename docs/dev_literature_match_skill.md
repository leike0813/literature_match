# 文献匹配组件（Codex Skill）开发说明（v1）

本组件用于将“待匹配文档”中的参考文献条目，匹配到 Zotero 库中的条目（以 `citekey` 为唯一主键），输出 `match_result.json`。  
目标是在库规模增长（万级条目）时仍能保持可用、可控成本：**规则/检索解决大多数，LLM 只处理疑难**。

## 0. 范围与非目标

### 范围
- 输入：Markdown 文档（Gemini DR / ChatGPT DR / 研究卡片等）+ Zotero 本地 Better BibTeX 导出（`betterbibtexjson`）
- 输出：`match_result.json`（仅结果与候选，不修改原文档）

### 非目标（刻意不做）
- 不为文档插入 `[[citekey]]` 链接（不同文档需要不同插入策略，另写脚本）
- 不写回 Zotero（不自动打标签/改集合）
- 默认不落地缓存文件（不写 `references.json`）；仅内存拉取与处理

## 1. 输入

### 1.1 待匹配文档
- `doc_path`：本地 Markdown 文件路径
- 文档类型（可选）：`gemini_dr | chatgpt_dr | research_card | generic_md`
  - 若不显式指定，则按启发式识别参考文献段落标题（“Works cited/参考文献/References”等）

### 1.2 Zotero 本地库（Better BibTeX 导出）

**只读数据源**：Zotero 本地 HTTP 导出 API（Zotero 运行时可用）

- 推荐 endpoint：`http://127.0.0.1:23119/better-bibtex/export/library?/1/library.betterbibtexjson`
  - 该格式通常包含：`citationKey/itemKey/tags/attachments/...`
  - 对比：`library.json` 多用于引文导出，往往缺少 `tags/attachments/itemKey` 等工作流信息

> 可靠性建议：匹配组件只负责“拉取 + 解析 + 输出”，不承担 Zotero 导出失败的复杂恢复；若 endpoint 不可用则清晰报错（提示“请启动 Zotero + Better BibTeX”）。

## 2. 输出：`match_result.json`

输出文件用于后续组件消费（插入链接脚本、研究卡片管理器等），应满足：
- 可追溯：每条引用保留原始文本与行号定位
- 可复核：每条引用保留 topK 候选列表（含分数与元数据摘要）
- 可联动：返回 `itemKey`、**所有 PDF 附件列表**与 Zotero tags

建议 schema 见第 7 节。

## 3. 总体流程（分层匹配）

### Step A：抽取参考文献条目（Deterministic）
将“参考文献段落”解析成结构化对象：
- `ref_id`：引用编号（如 `[12]` → `12`）
- `line_start/line_end`：所在行号范围（用于后续插入/回写脚本定位）
- `raw_text`：原始引用文本（整行或多行合并）
- `parsed`：尽量抽取以下字段（正则/清洗即可）
  - `doi`（`doi:`、`https://doi.org/...`、文本中的 DOI pattern）
  - `url`（抽取第一个可靠 URL，并做去尾标点清洗）
  - `arxiv`（`1234.56789` 或 `arXiv:1234.56789`）
  - `year`（四位数）
  - `title_guess`（引号内容/分隔符后字段/启发式截取）
  - `author_guess`（第一作者姓氏/作者串）

建议为不同文档实现不同 extractor（同一输出结构），避免把“插入/解析”逻辑耦合到匹配核心：
- `GeminiDRExtractor`
- `ChatGPTDRExtractor`
- `ResearchCardExtractor`
- `GenericMarkdownExtractor`

### Step B：标准化 Zotero 库（In-memory index）
从 `betterbibtexjson.items[]` 构建索引（不落地缓存）：
- `records[citekey] -> record_summary`
- `by_doi[doi_norm] -> citekey`
- `by_arxiv[id] -> citekey`
- `by_url[url_norm] -> [citekey...]`（允许多个）

`record_summary` 推荐包含：
- `citekey`（`citationKey`）
- `itemKey`
- `title`、`year`、`authors`（用于展示候选）
- `doi/url`（用于确定性匹配与展示）
- `zotero_tags[]`（原样；例如 `[{tag: "..."}]` 需转为 `["..."]`）
- `pdf_attachments[]`（**全部 pdf 附件**；每个含 `title/path/url`）

> 注意：不同 Zotero/BBT 版本字段可能略有差异，建议实现时“容错取字段”（例如 `creators` vs `author`，`date` vs `issued` 等），而不是死写字段名。

### Step C：确定性匹配（高精低成本）
对每条引用按优先级尝试：
1) DOI：`doi_norm` 精确命中
2) arXiv：id 精确命中
3) URL：`url_norm` 精确命中

命中即输出 `match.status=matched`，并记录：
- `match.method`: `doi|arxiv|url`
- `match.confidence`: 设为高（例如 `0.99`）

### Step D：文本检索召回 topK（无 LLM，全库可扩展）
对剩余未匹配条目：
- 文本检索主字段：`title_guess`（引用侧） vs `title`（库侧）
- 建议实现：`TF‑IDF(title)` + cosine similarity（`scikit-learn` 可用，万级库可承受）
- 轻量加权（可选）：
  - `year` 一致加分
  - `author_guess`（姓氏）在作者串中出现加分

输出 `candidates[]`（默认 K=10），并依据规则设置初步状态：
- 若 top1 分数很高且与 top2 拉开差距 → 可直接 `matched`（`method=tfidf`）
- 否则 → `needs_llm` 或 `needs_review`（下一步处理）

### Step E：LLM 判别（只处理疑难）

LLM 的职责是**判别**而非检索：它只能在“已召回的 topK 候选”中选择最可能的 `citekey`，或输出 `null`（表示需要人工处理/库中确实不存在）。

#### 触发条件（示例，可调）
- top1 分数低于阈值：`top1_score < T_high`
- top1 与 top2 分差过小：`(top1_score - top2_score) < gap`
- 解析信息不足：缺 DOI/URL/arXiv 且 title_guess 过短

#### LLM 输入（严格控制体积）
对每条 `needs_llm` 引用，只提供：
- `raw_text`（原始引用文本）
- `parsed`（doi/url/arxiv/year/title_guess/author_guess）
- `candidates[]`（最多 K=10，每个只给关键字段：citekey/title/year/authors/doi/url）

不要把整个 `betterbibtexjson` 喂给 LLM；库规模越大越不经济且容易引入幻觉。

#### LLM 输出约束（反幻觉）
- 只允许输出：
  - `citekey`：必须来自 `candidates[].citekey`
  - 或 `null`
- 同时输出一个 `reason`（简短说明为什么选它），便于你复核。

> 实现上建议：让 Codex（订阅模型）在交互中完成该判别，并把结果写回 `match_result.json`；避免在脚本里直接调用付费 API。

### Step F：固化结果（输出 `match_result.json`）
对每条引用输出：
- 最终 `match.status`：`matched|needs_review|unmatched`
- `match.citekey/itemKey`（若 matched）
- `match.method`：`doi|arxiv|url|tfidf|llm|manual`
- `match.confidence`：`0..1`
- `candidates[]`：保留 topK 候选，便于你后续复核与追溯

可选输出（仅建议在需要时启用）：
- `match_cache.json`：将“某种引用写法 → citekey”的人工确认结果缓存，减少重复判别成本。

## 4. 规范化与启发式细节（建议固定，避免漂移）

### 4.1 DOI 规范化（doi_norm）
- 全小写
- 去掉前缀：`https://doi.org/`、`http://doi.org/`、`doi:`、`DOI:`
- 去掉两端标点与空白

### 4.2 URL 规范化（url_norm）
用于“尽可能稳定地命中同一资源”：
- 全小写
- 去协议：`http://`、`https://`
- 去 `www.`
- 去尾部 `/`
- 去明显的尾部标点：`).,;]` 等

可选（谨慎使用，避免误合并）：
- 对 arXiv 做 abs/pdf 归一：
  - `arxiv.org/abs/<id>` 与 `arxiv.org/pdf/<id>.pdf` 归一到同一个 key

### 4.3 arXiv 规范化（arxiv_id）
支持：
- `arXiv:2406.03459`
- `2406.03459`

统一输出：`2406.03459`

## 5. 成本与性能控制（万级库设计点）

### 5.1 只读 + 无落盘缓存的现实代价
你已明确希望“直接从本地 Zotero API 拉取，不缓存”。这会导致：
- 每次运行都要重新拉取库（可接受，取决于库大小与 Zotero 响应速度）
- 每次运行都要重新构建检索向量（TF‑IDF）与索引（对 1–2 万条仍可接受，但要注意一次运行内复用）

建议实现时保证：
- 单次运行内只构建一次 TF‑IDF matrix
- 对同一 `doc_path` 多次运行时，尽量减少重复 IO（例如先把文档抽取结果存内存对象）

### 5.2 LLM 介入比例控制
让 LLM 只处理极少数疑难条目（例如 < 5%），否则会变成成本黑洞。  
实操中可以通过提高确定性与检索召回质量降低 LLM 占比：
- 优先抽 DOI/URL/arXiv（抽取质量比检索更重要）
- 候选召回用 title + year/author 的加权，不要只靠标题相似度

## 6. 失败模式与降级策略

- Zotero 未启动 / endpoint 不可用：
  - 直接报错退出，并提示用户启动 Zotero + Better BibTeX
- 文档找不到参考文献段落：
  - 输出空 `refs` + `stats`，并在 `meta.warnings` 写明原因
- 引用条目格式极度不规范：
  - 抽取尽量保守，匹配失败即进入 `needs_review`，避免误配
- 库中存在同题名多条目：
  - 允许 `candidates` 多个，交给 LLM/人工判别；不要擅自选第一个

## 7. `match_result.json` 建议 schema（可作为实现验收标准）

```json
{
  "meta": {
    "doc_path": "path/to/input.md",
    "generated_at": "YYYY-MM-DDTHH:MM:SSZ",
    "zotero_endpoint": "http://127.0.0.1:23119/better-bibtex/export/library?/1/library.betterbibtexjson",
    "library_item_count": 0,
    "warnings": []
  },
  "refs": [
    {
      "ref_id": "12",
      "line_start": 120,
      "line_end": 121,
      "raw_text": "…",
      "parsed": {
        "doi": "10....",
        "url": "https://...",
        "arxiv": "2406.03459",
        "year": "2024",
        "title_guess": "LW-DETR: ...",
        "author_guess": "Chen"
      },
      "match": {
        "status": "matched",
        "citekey": "chen_lwdetr-transformer_2024",
        "itemKey": "ABCDEF12",
        "method": "doi",
        "confidence": 0.99
      },
      "candidates": [
        {
          "citekey": "chen_lwdetr-transformer_2024",
          "itemKey": "ABCDEF12",
          "score": 0.93,
          "title": "LW-DETR: ...",
          "year": "2024",
          "authors": ["Chen, Qiang", "…"],
          "doi": "10.48550/arXiv.2406.03459",
          "url": "http://arxiv.org/abs/2406.03459",
          "zotero_tags": ["match_status:unmatched"],
          "pdf_attachments": [
            {"title": "...pdf", "path": "C:\\\\...\\\\file.pdf", "url": "https://..."},
            {"title": "...supplement.pdf", "path": "C:\\\\...\\\\supp.pdf", "url": ""}
          ]
        }
      ]
    }
  ],
  "stats": {
    "total": 0,
    "matched": 0,
    "needs_llm": 0,
    "needs_review": 0,
    "unmatched": 0
  }
}
```

> 字段可扩展，但建议保证：`refs[].raw_text/line_*`、`match.*`、`candidates[].citekey`、`pdf_attachments[]` 这几类信息始终存在（哪怕为空）。

## 8. 推荐实现形态（便于 skill 与脚本解耦）

- 脚本负责确定性匹配 + 候选召回：
  - 输入：`doc_path`
  - 输出：初版 `match_result.json`（包含 candidates，未决条目标 `needs_llm`）
- Codex skill 负责：
  - 对 `needs_llm` 条目逐条判别（只在候选集中选）
  - 写回最终 `match_result.json`

这种分工能最大化利用订阅制模型，同时保证大部分工作是确定性的、可测试的。

## 9. 测试建议

- 单元测试：
  - DOI/URL/arXiv 规范化与命中
  - 引用条目抽取（多格式、含多行引用）
  - TF‑IDF 召回（固定输入下输出 topK 稳定）
- 端到端 dry-run：
  - 用 `example/example_entry.md` 跑通，检查输出 JSON 是否可被后续组件消费
