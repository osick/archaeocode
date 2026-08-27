# Changelog

## [0.2.0] - 2026-08-27

First public release, under the new name **codelore** (previously `agentic-reverse-engineering`).

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

## [0.1] - 2025-11-07

Initial internal version: LangGraph workflow (discovery, AST analysis, dependency mapping, user-story extraction), MCP servers for static analysis / graph DB / RAG, Smalltalk grammar support (standard + Cincom variants), LangSmith tracing, `reverse` CLI.
