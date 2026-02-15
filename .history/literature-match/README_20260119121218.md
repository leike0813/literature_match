# literature-match（发布包）

本目录是 **Open Agent Skills** 规范下的可发布 skill 包，用于将 Markdown 文档中的参考文献条目匹配到本地 Zotero（Better BibTeX 导出）条目，并生成 `match_result.json`（不修改原文档）。

## 目录结构

- `SKILL.md`：skill 入口说明（包含 agent 指令与 CLI 调用方式）
- `scripts/`：可执行脚本（确定性流水线与工具脚本）

## 安装

将发布包放在agent skill目录中，如“~/.codex/skills

## 使用

在Agent工具中使用如下提示词调用skill：

```text
$literature-match：调用skill，对<input.md>进行文献匹配。
```

