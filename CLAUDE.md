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

### Frontend-backend contract

- Chat: `POST /chat` with `{prompt, history}`, returns streaming NDJSON with `{history, updates, image, graph, wiki}`
- Graph: `GET /graph` returns full graph JSON with `{nodes, links, sents, categories}`
- Entity: `GET /entity/<name>` returns subgraph for a specific entity

### ECharts graph visualization

Graph data uses integer node IDs. Links must have `source`/`target` as integers matching node `id` values. The `categories` field is required for node coloring. Frontend converts string IDs via `parseInt` as a safety measure.

### Domain

The knowledge graph covers Chinese naval ship damage control and diving technology. Schema defined in `data/schema/schema_v4.py` with 13 entity types and their relations.

## Known Issues

- Wikipedia API is slow/blocked in China — mitigated by 5-second threading timeout.
- PaddlePaddle 3.x is incompatible with the wordtag inference model (PIR format) — NER uses jieba fallback instead.

## Caching Architecture

The backend uses three module-level caches to avoid redundant computation:
- **`_data_cache`** (`graph_utils.py`): loads `server/data/data.json` once at import time
- **`_graph_cache`** (`main_api.py`): per-request graph search results, reset on each `/chat` call
- **`_wiki_cache`** (`main_api.py`): Wikipedia results keyed by entity name, persists across requests

## NER Pipeline

`server/app/utils/ner_api.py` — `NerAPI` singleton (accessed via `get_ner()`):
- Loads entity names from `data.json` into jieba user dictionary at init
- Loads synonym/alias mappings from `server/data/synonyms.json` (e.g., "军舰"→"舰艇")
- `predict()` returns entities sorted by confidence: exact (1.0) > synonym (0.9) > entity-in-text (0.8) > combo (0.7) > fuzzy (0.5)
- Multi-word combo matching: adjacent jieba tokens are recombined to catch entities split by the tokenizer

## Frontend Details

- **State persistence**: ChatView stores `messages` + `history` in localStorage; restores on page refresh
- **Graph format**: ECharts `webkitDep` layout. Nodes need integer `id`, `symbolSize`, `category`. Links need integer `source`/`target`. The `categories` array drives node coloring.
- **Entity highlighting**: Backend returns `entities` list in the final chat chunk. Frontend renders these with green background via `v-html`; clicking navigates to `/kg?entity=XXX`
- **API proxy**: Vite dev server proxies `/api/*` → `VITE_API_URL` (default `http://localhost:8000`)

## Configuration

All config via environment variables in `.env` (copy from `.env.example`). The `config/settings.py` `Settings` dataclass reads `.env` with a custom parser (no `python-dotenv` dependency). Key settings:
- `USE_API_MODE=true` — enables external LLM API (required for web app)
- `API_BASE_URL`, `API_KEY`, `API_MODEL_NAME` — OpenAI-compatible endpoint
- `HISTORY_WINDOW=10` — multi-turn context window (0 = unlimited)
- `SCHEMA_VERSION=v4` — selects entity/relation schema from `data/schema/`

## Deployment

Docker Compose runs two services:
- `backend` (Python, port 8000): `Dockerfile`
- `frontend` (Nginx, port 80): `Dockerfile.frontend` builds Vue app, serves via `nginx.conf`
- Nginx proxies `/api/` to `backend:8000` with 120s timeout and buffering off (required for SSE streaming)

```bash
docker compose up --build
```
