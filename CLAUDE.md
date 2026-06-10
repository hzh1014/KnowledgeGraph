# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

ChatKG — a Chinese knowledge graph Q&A system. Two independent workflows share this repo:

1. **KG Construction** (`main.py`): GPU-intensive offline pipeline using UIE + SPN4RE to extract entities/relations from raw text and iteratively build a knowledge graph.
2. **Web Application** (`start.py`): Lightweight Flask + Vue 3 app that serves the pre-built graph, performs NER-based entity lookup, queries Wikipedia, and streams LLM responses via an OpenAI-compatible API.

## Commands

### One-click start (recommended)
```bash
python start.py
```
Launches backend (Flask, port 8000) and frontend (Vite, port 5173), opens browser.

### Backend only
```bash
python server/main_api.py
```

### Frontend only
```bash
cd chat-kg
npm run dev      # dev server on port 5173
npm run build    # production build
npm run lint     # ESLint
npm run format   # Prettier
```

### Tests
```bash
pytest                          # all tests
pytest tests/test_settings.py   # single file
pytest -k "test_name"           # by pattern
```

### KG construction (requires GPU + PaddlePaddle)
```bash
python main.py --project my_project --gpu 0
python main.py --project my_project --resume <checkpoint_path> --gpu 0
```

## Architecture

```
Frontend (Vue 3 + Vite, port 5173)
    │  /api/* proxy → localhost:8000/*
    ▼
Backend (Flask, port 8000)
    ├── NER (jieba + graph entity matching) — server/app/utils/ner_api.py
    ├── Graph retrieval — server/app/utils/graph_utils.py
    ├── Wikipedia search (5s timeout) — server/app/utils/query_wiki.py
    ├── Image search (hardcoded keywords) — server/app/utils/image_searcher.py
    └── LLM streaming (OpenAI-compatible API) — server/main_api.py
```

### Key data flow (chat request)

`POST /chat` → NER extracts entities → graph triples retrieved → Wikipedia searched → reference material injected into system prompt → streamed to external LAPI → response streamed back as newline-delimited JSON.

### Configuration

All config via environment variables in `.env` (copy from `.env.example`). Key settings:
- `USE_API_MODE=true` — enables external LLM API (required for web app)
- `API_BASE_URL`, `API_KEY`, `API_MODEL_NAME` — OpenAI-compatible endpoint
- `config/settings.py` — `Settings` dataclass singleton, reads `.env` at import time

### Frontend-backend contract

- Chat: `POST /chat` with `{prompt, history}`, returns streaming NDJSON with `{history, updates, image, graph, wiki}`
- Graph: `GET /graph` returns full graph JSON with `{nodes, links, sents, categories}`
- Entity: `GET /entity/<name>` returns subgraph for a specific entity

### ECharts graph visualization

Graph data uses integer node IDs. Links must have `source`/`target` as integers matching node `id` values. The `categories` field is required for node coloring. Frontend converts string IDs via `parseInt` as a safety measure.

### Domain

The knowledge graph covers Chinese naval ship damage control and diving technology. Schema defined in `data/schema/schema_v4.py` with 13 entity types and their relations.

## Known Issues

- ~~`graph_utils.py:search_node_item()` mutates shared graph data in-place~~ — **fixed**: deep-copy nodes/edges before modifying.
- ~~`graph_utils.py` re-reads `data.json` on every call~~ — **fixed**: module-level cache (`_data_cache`).
- ~~`ner_api.py` recomputes `short_entities` filter on every `predict()` call~~ — **fixed**: moved to `__init__`.
- Wikipedia API is slow/blocked in China — mitigated by 5-second threading timeout.
- PaddlePaddle 3.x is incompatible with the wordtag inference model (PIR format) — NER uses jieba fallback instead.

## Optimization Roadmap

按优先级分轮次，每轮聚焦一个主题。完成一轮后在此打勾。

### Round 1 — 后端数据层修复（正确性）✅

- [x] `graph_utils.py`: `search_node_item()` 改为深拷贝节点/边，不再变异共享数据
- [x] `graph_utils.py`: `data.json` 改为模块级缓存，启动时读取一次
- [x] `ner_api.py`: `short_entities` 过滤移入 `__init__`，避免每次 predict 重复计算
- [x] `graph_utils.py`: 修复 `serch_node` 拼写错误
- [x] 为以上修复补充 pytest 用例（21 个新用例，全量 65 通过）

### Round 2 — 流式响应优化（性能）✅

- [x] `main_api.py` 流式响应：中间 chunk 只发 `updates`，最终 chunk 再发完整 `graph`/`wiki`/`image`
- [x] `ChatView.vue`: 修复 off-by-one bug（最后 chunk 元数据未应用到 UI）+ 防止 undefined 覆盖
- [x] Wikipedia 结果加内存缓存（`_wiki_cache`，同一实体不重复查询）
- [x] 图谱搜索结果缓存（`_graph_cache`，独立搜索 + 合并，避免累积污染）
- [x] `main_api.py`: `import threading` 移至文件顶部
- [x] 新增 8 个缓存测试（全量 73 通过）

### Round 3 — NER 增强（准确性）✅

- [x] 引入同义词/别名词典 `server/data/synonyms.json`（如"军舰"→"舰艇"），加载时构建反向映射
- [x] 支持多词组合实体匹配（相邻 jieba 分词重新组合，如"灭火"+"训练"→"灭火训练"）
- [x] NER 结果按置信度排序（exact 1.0 > synonym 0.9 > substring 0.8 > combo 0.7 > fuzzy 0.5）
- [x] 新增 22 个 NER 测试（同义词、组合匹配、置信度、排序），全量 82 通过

### Round 4 — 前端体验优化 ✅

- [x] GraphView: 添加节点搜索框，输入关键词高亮匹配节点
- [x] GraphView: 点击节点显示详情面板（名称、分类、关联节点标签、关联边列表、相关句子）
- [x] GraphView: 添加重置缩放按钮（ECharts restore action）
- [x] KnowledgeGraph.vue: 组件尺寸改为响应式（width: 100%, min-width: 300px）
- [x] ChatView: 对话中命中的实体高亮显示（绿色背景），可点击跳转图谱页面（`/kg?entity=XXX`）
- [x] GraphView: 接收 `entity` query param，自动高亮并显示该节点详情
- [x] MessageList: 支持 `v-html` 渲染实体高亮（仅 received 消息有 entities 时）
- [x] 后端: 最终 chunk 新增 `entities` 字段
- [x] 修复 GraphView.vue 中 `webkitDep.nodes.map` 对原数据的变异（改用 spread）
- [x] GraphView 响应式布局（移动端上下排列）

### Round 5 — 功能扩展 ✅

- [x] 多轮对话记忆：`HISTORY_WINDOW` 环境变量配置上下文窗口（默认 10 轮，0=不限）
- [x] 对话历史持久化：localStorage 存储 messages + history，页面刷新后恢复，清除对话时同步删除
- [x] 导出功能：GraphView 支持导出 PNG（ECharts getDataURL）和 JSON（Blob 下载）
- [x] `.env.example` 补充 API 模式和 HISTORY_WINDOW 配置项
- [x] 新增 11 个 R5 测试（history 窗口截断、导出数据结构、localStorage key），全量 93 通过

### Round 6 — 生产化 ✅

- [x] Docker 化：`Dockerfile`（Python 后端）+ `Dockerfile.frontend`（Node 构建 + Nginx）+ `docker-compose.yml` + `nginx.conf`（`/api/` 反代到 backend:8000）
- [x] 错误处理统一：`error_response()` helper 返回 `{error: {code, message, request_id}}`
- [x] 日志规范化：`query_wiki.py` print 替换为 logger；`/entity` 端点添加错误日志
- [x] 前端错误提示：ChatView fetch 添加 `.catch()` + `response.ok` 检查，失败时显示错误消息
- [x] `.env.example` 已包含所有 API 配置项（R5 完成）
- [x] CI：GitHub Actions（`.github/workflows/ci.yml`）— pytest + npm lint
- [x] `.dockerignore` 排除无关文件
