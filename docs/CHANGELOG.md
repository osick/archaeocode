# Changelog

## [0.4.0] - 2026-09-07 — "The Site Archive"

Until now every dig ended with a JSON report and amnesia. This release gives archaeocode a memory.

### Added
- **Knowledge management**: a persistent, queryable knowledge base built on [LightRAG](https://github.com/HKUDS/LightRAG) (GraphRAG: knowledge graph + vector retrieval). See [docs/KNOWLEDGE_MANAGEMENT.md](KNOWLEDGE_MANAGEMENT.md) for the decision record.
  - New workflow node `knowledge_base` (opt-in via `--knowledge-base` / `knowledge_base.enabled`) that writes files, AST entities, dependency edges (incl. circular-dependency markers) and user stories into the graph **without any LLM call**; `--kb-extract` adds LLM extraction of business entities.
  - New MCP server `src/mcp_servers/knowledge_base/knowledge_mcp_server.py` with `kb_query`, `kb_retrieve`, `kb_context`, `kb_graph`, `kb_stats`, `kb_add_documents`, `kb_export_wiki`; registered in `config/langgraph_config.yaml` and the in-process MCP client.
  - New CLI `archaeo-kb` (`query`, `retrieve`, `context`, `graph`, `stats`, `add`, `wiki`).
  - Obsidian-compatible Markdown wiki export (`--kb-wiki DIR`, `archaeo-kb wiki`).
  - Storage back-ends selectable by configuration: NetworkX / Neo4j / Postgres+AGE / Memgraph (graph), nano-vectordb / FAISS / pgvector / Qdrant / Milvus (vectors), JSON / Postgres / Redis / Mongo (KV); workspaces isolate several systems in one back-end. Embeddings via sentence-transformers (default, local), OpenAI, Ollama; LLM via Anthropic, OpenAI, Ollama.
  - Offline mode (`KB_TOKENIZER=bytes`, `KB_EMBEDDING_PROVIDER=hashing`) used by the new test module `tests/test_knowledge_base.py`.
  - Example `examples/knowledge_base/query_knowledge_base.py`; new `knowledge_base` state field and report section.

### Changed
- AST entities now carry `file_path`, so classes/functions/methods can be linked to their file.
- `requirements.txt` adds `lightrag-hku`.

## [0.3.0] - 2026-08-27

First public release, under the new name **archaeocode** (previously `agentic-reverse-engineering`).

### Fixed
- **Package shadowing**: renamed the internal `src/langgraph/` package to `src/orchestration/` — the old name shadowed the installed `langgraph` library and broke the test suite with circular imports.
- **User-story extraction produced zero stories**: the response parser only matched bare `Title:` labels while models answer in markdown (`**Title:**`); every story was silently dropped. The parser is now markdown-tolerant.
- **MCP SDK 2.x compatibility**: migrated all MCP servers from the removed 1.x low-level `Server.call_tool()` decorator to the FastMCP-style tool API, compatible with both `mcp` 1.x and 2.x.
- **Deprecated model**: default model updated to `claude-sonnet-5`; the `temperature` parameter is no longer sent to Claude 5 models.
- Test-suite repairs: `sys.path` hygiene, missing import prefixes, graceful skips when the optional Smalltalk grammar is not built, async tests via `asyncio_mode = "auto"`.

### Changed
- Migrated from the unmaintained `tree-sitter-languages` to the maintained `tree-sitter-language-pack`.
- `requirements.txt` now declares the previously missing `mcp` and `PyYAML` dependencies.
- Replaced `setup.py` with `pyproject.toml`.
- Rewrote `README.md` and `QUICKSTART.md`; docs cleaned up for public release.

### Removed
- Dead code referencing modules that never existed in the repo (`src/orchestration/{agents,tools,models,prompts}`), along with its documentation.
- Internal development-protocol documents.

### Added
- MIT `LICENSE`.
- GitHub Actions CI: pytest on Python 3.10–3.12 plus a CLI smoke test.
- Working example in `examples/user_story_extraction/basic_usage.py`.
- CLI renamed from `reverse` to `archaeo`, now also installable as a console command via `pip install .`.

## [0.1] - 2025-11-07

Initial internal version: LangGraph workflow (discovery, AST analysis, dependency mapping, user-story extraction), MCP servers for static analysis / graph DB / RAG, Smalltalk grammar support (standard + Cincom variants), LangSmith tracing, `reverse` CLI.
