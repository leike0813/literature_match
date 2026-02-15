# 文献管理工作流（解耦架构）开发说明总览（v1）

本文档用于“冻结”当前解耦方案的全局约定与组件边界，便于在后续独立 session 中按需加载对应组件文档开发，避免上下文互相污染。

## 0. 核心不变式（Invariants）

- 全流程唯一主键：**Better BibTeX `citekey`**（视为全局唯一索引/SSOT）。
- 组件解耦：各组件通过**文件契约**交互（JSON/Markdown/目录约定），互不强依赖内部实现。
- 读写边界清晰：
  - 文献匹配组件：只读输入文档 + 只读 Zotero 本地导出 API；输出 `match_result.json`；**不修改原文档**。
  - 研究卡片组件：只管理 `Card/`（通用卡片）；项目内容由项目目录管理；**不污染卡片**。
  - PDF 解析组件：单文件 CLI，只负责 PDF→MinerU→落盘；不改卡片、不做匹配。

## 1. Vault 与目录约定

### 1.1 Research Vault

- Vault 根目录：`OneDrive/Research/`
- 研究卡片目录（全局唯一）：`OneDrive/Research/Card/`
- 项目目录（扁平，避免路径过深）：`OneDrive/Research/<project_name>/`

> 说明：项目目录不是 `OneDrive/Research/Projects/<project_name>/`，而是直接放在 `OneDrive/Research/` 下。

### 1.2 研究卡片（Card）落盘规则

- 文件名强制：`<citekey>.md`（避免标题变化导致重复/断链）
- 分桶：按年份分桶，目录为：
  - `OneDrive/Research/Card/<year>/<citekey>.md`
  - `OneDrive/Research/Card/NoYear/<citekey>.md`（无 year 或不稳定条目）

### 1.3 PDF 与 MinerU 解析产物（推荐约定）

为满足“输出到 PDF 同文件夹且不发生 Images 冲突”的需求，建议 **每篇文献一个 PDF 目录，且目录末级为 citekey**：

- PDF 示例：`.../<citekey>/<citekey>.pdf`
- MinerU 解析产物由 CLI 输出到同目录：
  - `.../<citekey>/<citekey>.md`
  - `.../<citekey>/Images/`

> 若你采用 Zotero/Attanger 管理附件位置，也可以只要求：研究卡片里能解析出一个指向该 PDF 的路径，并满足“末级目录=citekey”的约定。

## 2. 组件列表与职责

### 2.1 文献匹配组件（Codex skill）

- 输入：待匹配文档（DR 报告/研究卡片等）+ Zotero 本地 `betterbibtexjson`
- 输出：`match_result.json`
- 目标：在库规模变大时仍可控成本（确定性→检索召回→LLM 判别）
- 组件文档：`docs/dev_literature_match_skill.md`

### 2.2 研究卡片组件（Card Manager + 补全 skill）

- 管理 `Card/` 的卡片生命周期：缺失/仅元数据/完整/归档
- 与 Zotero 元数据同步（以 `citekey` 对齐）
- 调用 PDF 解析 CLI 生成 MinerU 产物；生成“待补全任务”交给订阅制 Codex skill 执行总结回填
- 组件文档：`docs/dev_research_card_component.md`

### 2.3 PDF 解析组件（MinerU 单文件 CLI）

- 单参 CLI：只接收 `pdf_path`；默认从配置文件读取 MinerU endpoint/api_key，允许单次运行参数覆盖
- 输出：解包 zip，重命名 `full.md` 为与 PDF 同名的 `*.md`，并输出 `Images/` 到同目录
- 组件文档：`docs/dev_mineru_pdf_cli.md`

## 3. 组件间文件契约（Contracts）

### 3.1 `match_result.json`

- 由“文献匹配组件”生成
- 被“插入 Obsidian 链接脚本（另做）”与“研究卡片组件”消费
- 关键字段：引用条目定位（行号/编号）、匹配结果（citekey/itemKey）、候选列表、PDF 附件列表、tags

### 3.2 研究卡片 `.md`

- 文件名：`citekey.md`
- Front‑Matter 至少包含：`citekey` 与 `zotero_itemKey`
- 推荐包含：`attachments_pdf`（全部 pdf 附件）、`zotero_tags`、`links`（zotero/pdf/mineru）
- 正文包含“自动区块”（用于工具/skill 回填，不覆盖手写内容）

### 3.3 MinerU 解析产物

- 由 PDF 解析 CLI 落盘到 PDF 同目录
- 文件名与目录结构固定，以便卡片组件无需猜测路径

## 4. 明确不在本轮范围内的部分（避免耦合）

- “为不同文档格式插入 Obsidian 链接”的逻辑：独立脚本分别实现（Gemini DR / ChatGPT DR / 研究卡片等各自策略）。
- “Zotero 写回（打标签/改集合）”：若未来需要，走 Zotero Web API（云端）+ API key；不与匹配组件强耦合。
