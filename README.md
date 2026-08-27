# codelore

[![CI](https://github.com/osick/codelore/actions/workflows/ci.yml/badge.svg)](https://github.com/osick/codelore/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

**Excavate the lore buried in your legacy code.** Point codelore at a legacy codebase — get back business-readable user stories, a dependency map, and structural analysis.

Most reverse-engineering tools stop at syntax: they parse code and draw diagrams. This project goes one step further and recovers the *business intent* hidden in legacy code. An AI agent workflow (LangGraph) orchestrates static-analysis tools (exposed as MCP servers) to turn COBOL, Smalltalk, Fortran, Pascal, or Java code into artifacts that stakeholders can actually read — the raw material for a migration backlog.

## What makes it different

- **User stories from code** — the unique feature: an LLM analyzes each source file and produces user stories with roles, capabilities, benefits, acceptance criteria, priority, and confidence scores. Legacy knowledge becomes a product backlog.
- **Legacy-first language support** — COBOL, Fortran, Pascal, and Smalltalk (including a Cincom/VisualWorks variant with custom tree-sitter grammars), alongside Java, Python, JavaScript, and TypeScript.
- **MCP architecture** — analysis tools (AST parsing, dependency graphs, RAG) are [Model Context Protocol](https://modelcontextprotocol.io/) servers, so any MCP-capable agent can reuse them independently of this workflow.
- **Observable by design** — every workflow run can be traced in [LangSmith](https://docs.smith.langchain.com) (token costs, latency, state snapshots).

## How it works

```
LangGraph Orchestration
    │
[Discovery] ──► [AST Analysis] ──► [Dependency Mapping] ──► [User Stories]
    │                │                     │                     │
file catalog    tree-sitter          graph + cycle          Claude / GPT
                  parsing              detection
```

Each analysis step is an MCP server under `src/mcp_servers/` (static analysis, graph DB, RAG pipeline); the LangGraph workflow under `src/orchestration/` wires them together with checkpointing and state management.

## Quick start

```bash
git clone https://github.com/osick/codelore.git
cd codelore
pip install -r requirements.txt

# Optional but recommended: enable user-story extraction
cp .env.example .env   # add your ANTHROPIC_API_KEY (or OPENAI_API_KEY)
```

Run the workflow against the bundled samples:

```bash
# COBOL analysis
python reverse --source sample_data/cobol --source-lang cobol --target-lang java

# Java (Spring) analysis with report
python reverse --source sample_data/java --source-lang java --target-lang python --report report.json
```

You get a console summary plus a JSON report: file catalog, language breakdown, dependency edges/cycles/layers, and (with an API key) generated user stories.

Or use it from Python:

```python
from src.orchestration.graph import create_graph

graph = create_graph()
result = graph.run(
    source_language="java",
    target_language="python",
    source_path="./sample_data/java",
)

print(result["total_files"], "files analyzed")
for story in result["user_stories"]:
    print("-", story["title"])
```

A complete runnable example is in [`examples/user_story_extraction/basic_usage.py`](examples/user_story_extraction/basic_usage.py).

## Feature status

| Feature | Status |
|---|---|
| Code discovery & cataloging (10+ languages) | ✅ working |
| AST parsing via tree-sitter (MCP server) | ✅ working |
| Dependency mapping, cycle detection, layering | ✅ working |
| AI user-story extraction (Claude / GPT) | ✅ working |
| LangSmith tracing | ✅ working |
| Checkpointing / resumable workflows | ✅ working |
| Smalltalk grammars (standard + Cincom) | ✅ working (grammar build required, see below) |
| RAG semantic code search (MCP server) | 🚧 functional, not yet wired into the workflow |
| Neo4j-backed dependency graphs | 🚧 in-memory fallback works; live Neo4j optional |
| Code generation to target language | 🎯 planned |
| HP NonStop COBOL extensions (TMF, Pathway) | 🎯 planned |

## Requirements

- Python 3.10+
- An Anthropic or OpenAI API key for user-story extraction (everything else runs without one)
- Optional: Neo4j 5.x if you want persistent dependency graphs, LangSmith account for tracing

## Smalltalk support

Standard and Cincom/VisualWorks Smalltalk are parsed with custom tree-sitter grammars:

```bash
python scripts/build_smalltalk_grammar.py
python reverse --source sample_data/smalltalk --source-lang smalltalk --target-lang java
```

See [docs/SMALLTALK_SUPPORT.md](docs/SMALLTALK_SUPPORT.md) and [docs/SMALLTALK_VARIANTS.md](docs/SMALLTALK_VARIANTS.md).

## Project structure

```
├── reverse                     # CLI entry point
├── src/
│   ├── orchestration/          # LangGraph workflow
│   │   ├── graph.py            # Direct workflow (in-process nodes)
│   │   ├── graph_mcp.py        # MCP-backed workflow
│   │   ├── nodes/              # Discovery, AST, dependency, user-story nodes
│   │   ├── state/              # Workflow state schema
│   │   └── utils/              # MCP client, LangSmith tracing
│   ├── mcp_servers/
│   │   ├── static_analysis/    # tree-sitter AST analysis + custom grammars
│   │   ├── graph_db/           # dependency graph (Neo4j / in-memory)
│   │   └── rag_pipeline/       # chunking, embeddings, semantic search
│   └── parsers/                # language-specific parser extensions
├── config/                     # workflow + MCP server configuration
├── sample_data/                # COBOL, Java, Smalltalk, Fortran, Pascal, Python samples
├── tests/                      # pytest suite (runs in CI)
├── examples/                   # runnable usage examples
└── docs/                       # architecture & guides
```

## Testing

```bash
pip install pytest pytest-asyncio
pytest
```

The suite runs in [GitHub Actions](.github/workflows/ci.yml) on Python 3.10–3.12. Smalltalk tests are skipped automatically unless the grammar has been built.

## Documentation

- [Quick Start](QUICKSTART.md)
- [Architecture wireframe](docs/LANGGRAPH_WIREFRAME.md)
- [MCP server architecture](docs/MCP_ARCHITECTURE.md) and [usage](docs/MCP_SERVERS_USAGE.md)
- [LangSmith setup](docs/LANGSMITH_SETUP.md)
- [User story extraction](docs/USER_STORIES.md)
- [Roadmap](docs/ROADMAP.md) · [Changelog](docs/CHANGELOG.md)

## Contributing

Issues and pull requests are welcome. Please run `pytest` before submitting, and open an issue first for larger changes.

## License

[MIT](LICENSE) © 2026 Oliver Sick
