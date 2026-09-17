# archaeocode

[![CI](https://github.com/osick/archaeocode/actions/workflows/ci.yml/badge.svg)](https://github.com/osick/archaeocode/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)

**Automated software archaeology.** Somewhere in your company there is a COBOL program older than most of your colleagues. Its author retired, its documentation is a rumour, and it still moves money every night. archaeocode is the expedition you send in: point it at a legacy codebase and get back business-readable user stories, a dependency map, structural analysis — and, since v0.4, a **knowledge base that remembers everything the dig uncovered**, so you never have to excavate the same site twice.

Most reverse-engineering tools stop at syntax: they parse code and draw diagrams. That is like cataloguing potsherds without asking what the pot was for. archaeocode goes one step further and recovers the *business intent* buried in legacy code. An AI agent workflow (LangGraph) orchestrates static-analysis tools (exposed as MCP servers) to turn COBOL, Smalltalk, Fortran, Pascal, or Java into artifacts that stakeholders can actually read: the raw material for a migration backlog.

## What makes it different

- **User stories from code** — the signature find. An LLM reads each source file and writes user stories with roles, capabilities, benefits, acceptance criteria, priority, and confidence scores. Forty-year-old business rules become a product backlog your product owner can argue about.
- **A knowledge base that doesn't forget** — every run can be persisted into a [GraphRAG knowledge base](docs/KNOWLEDGE_MANAGEMENT.md) (powered by [LightRAG](https://github.com/HKUDS/LightRAG)). Files, entities, dependency edges, and user stories become a knowledge graph you can *interrogate*: "which programs touch the customer master file?", "what breaks if we retire this copybook?". Ask from the terminal with `archaeo-kb`, from any agent via MCP, or browse the exported Obsidian-style wiki like a museum catalogue. Runs on plain files on your laptop, or on Neo4j / Postgres / Qdrant when the site is the size of a bank.
- **Legacy-first language support** — COBOL, Fortran, Pascal, and Smalltalk get first-class treatment, next to Java, Python, JavaScript, and TypeScript. See the [language matrix](#language-support).
- **MCP architecture** — every tool (AST parsing, dependency graphs, RAG, knowledge base) is a [Model Context Protocol](https://modelcontextprotocol.io/) server. Claude Desktop, Claude Code, or your own agent can borrow the trowel without adopting the whole expedition.
- **Observable by design** — every run can be traced in [LangSmith](https://docs.smith.langchain.com): token costs, latency, state snapshots. No mystery boxes on a mystery-box project.

## How the dig works

```
LangGraph Orchestration
    │
[Discovery] ──► [AST Analysis] ──► [Dependency Mapping] ──► [User Stories] ──► [Knowledge Base]
    │                │                     │                     │                   │
 survey the      tree-sitter          graph + cycle          Claude / GPT       LightRAG GraphRAG
   site            parsing              detection          (what was it for?)  (the site archive,
                                                                                  --knowledge-base)
```

1. **Discovery** surveys the site: every source file is catalogued with language and size.
2. **AST analysis** brushes off the dirt: tree-sitter turns files into classes, functions, methods, imports, and complexity scores.
3. **Dependency mapping** reconstructs who talked to whom: import/call edges, circular dependencies, and layering.
4. **User story extraction** asks the important question, *what was this for?*, and writes the answer as user stories.
5. **Knowledge base** (opt-in) files every find in a knowledge graph so the next question doesn't need a new dig.

Each step is an MCP server under `src/mcp_servers/`; the LangGraph workflow under `src/orchestration/` wires them together with checkpointing and state management.

## Quick start

```bash
git clone https://github.com/osick/archaeocode.git
cd archaeocode
pip install -r requirements.txt

# Optional: install the `archaeo` and `archaeo-kb` commands onto your PATH
pip install -e .

# Optional but recommended: enable user-story extraction
cp .env.example .env   # add your ANTHROPIC_API_KEY (or OPENAI_API_KEY)
```

Break ground on the bundled samples:

```bash
# COBOL analysis
python archaeo --source sample_data/cobol --source-lang cobol --target-lang java

# Java (Spring) analysis with report
python archaeo --source sample_data/java --source-lang java --target-lang python --report report.json
```

![archaeo analyzing the bundled COBOL sample](docs/assets/archaeo-demo.svg)

You get a console summary plus a JSON report: file catalog, language breakdown, dependency edges/cycles/layers, and (with an API key) generated user stories.

### Keep the finds: the knowledge base

A JSON report is a photo of the excavation. The knowledge base is the museum.

```bash
# persist the run into the knowledge base (+ an Obsidian-compatible wiki)
python archaeo --source sample_data/cobol --source-lang cobol --knowledge-base --kb-wiki ./wiki

# then interrogate it
archaeo-kb query "Which programs touch the customer master file?"   # needs an LLM key
archaeo-kb retrieve "PAYMENT" --mode local                          # no LLM needed
archaeo-kb graph "PAYMENT.cob"                                      # walk the neighbourhood
archaeo-kb add docs/runbook.md                                      # add non-code lore
```

Indexing needs no LLM at all: files, entities, and dependency edges come straight from static analysis, so the graph is exact and free. Add `--kb-extract` and the LLM also mines the code for *business* concepts (customers, tariffs, invoice runs) and files them next to the technical ones. Details, query modes, and the scaling ladder: [docs/KNOWLEDGE_MANAGEMENT.md](docs/KNOWLEDGE_MANAGEMENT.md).

### From Python

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

Runnable examples: [`examples/user_story_extraction/basic_usage.py`](examples/user_story_extraction/basic_usage.py) and [`examples/knowledge_base/query_knowledge_base.py`](examples/knowledge_base/query_knowledge_base.py).

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
| Knowledge base: GraphRAG over files, entities, dependencies, stories (LightRAG, MCP server, `archaeo-kb`) | ✅ working (opt-in per run) |
| Knowledge base: LLM extraction of business entities | ✅ working (`--kb-extract`, needs API key) |
| Knowledge base: Obsidian-compatible wiki export | ✅ working |
| RAG semantic code search (MCP server) | 🚧 mock; superseded by the knowledge base |
| Neo4j-backed dependency graphs | 🚧 in-memory fallback works; the knowledge base can already use Neo4j |
| Code generation to target language | 🎯 planned |
| HP NonStop COBOL extensions (TMF, Pathway) | 🎯 planned |

## Requirements

- Python 3.10+
- An Anthropic or OpenAI API key for user-story extraction and knowledge-base questions (everything else runs without one)
- Optional: Neo4j 5.x / PostgreSQL+pgvector / Qdrant to scale the knowledge base beyond local files; a LangSmith account for tracing

## Language support

| Language | Discovery & catalog | Dependency map | User stories | AST parsing (tree-sitter) |
|---|:---:|:---:|:---:|:---:|
| COBOL | ✅ | ✅ | ✅ | 🎯 planned |
| Fortran | ✅ | ✅ | ✅ | 🎯 planned |
| Pascal | ✅ | ✅ | ✅ | 🎯 planned |
| Smalltalk (standard + Cincom) | ✅ | ✅ | ✅ | ✅ ¹ |
| Java | ✅ | ✅ | ✅ | ✅ |
| Python | ✅ | ✅ | ✅ | ✅ |
| JavaScript / TypeScript | ✅ | ✅ | ✅ | ✅ |

The AST MCP server additionally parses C, C++, C#, Go, Rust, Ruby, PHP, and Bash. Every language ships with a sample under [`sample_data/`](sample_data/) so you can try it immediately.

¹ Smalltalk uses custom tree-sitter grammars — build them once with `python scripts/build_smalltalk_grammar.py` (details: [SMALLTALK_SUPPORT](docs/SMALLTALK_SUPPORT.md), [SMALLTALK_VARIANTS](docs/SMALLTALK_VARIANTS.md)).

## Project structure

```
├── archaeo                     # CLI entry point (`archaeo-kb` after pip install -e .)
├── src/
│   ├── orchestration/          # LangGraph workflow
│   │   ├── graph.py            # Direct workflow (in-process nodes)
│   │   ├── graph_mcp.py        # MCP-backed workflow
│   │   ├── kb_cli.py           # archaeo-kb: interrogate the knowledge base
│   │   ├── nodes/              # Discovery, AST, dependency, user-story, knowledge-base nodes
│   │   ├── state/              # Workflow state schema
│   │   └── utils/              # MCP client, LangSmith tracing
│   ├── mcp_servers/
│   │   ├── static_analysis/    # tree-sitter AST analysis + custom grammars
│   │   ├── graph_db/           # dependency graph (Neo4j / in-memory)
│   │   ├── rag_pipeline/       # chunking, embeddings, semantic search
│   │   └── knowledge_base/     # GraphRAG knowledge base (LightRAG adapter + MCP server)
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

The suite runs in [GitHub Actions](.github/workflows/ci.yml) on Python 3.10–3.12. Smalltalk tests are skipped automatically unless the grammar has been built. The knowledge-base tests run fully offline (no API key, no downloads), so CI never has to phone home.

## Documentation

- [Quick Start](QUICKSTART.md) — your first dig in five minutes
- [Knowledge management](docs/KNOWLEDGE_MANAGEMENT.md) — the site archive: why GraphRAG, why LightRAG, how to query and scale it
- [Architecture wireframe](docs/LANGGRAPH_WIREFRAME.md)
- [MCP server architecture](docs/MCP_ARCHITECTURE.md) and [usage](docs/MCP_SERVERS_USAGE.md)
- [LangSmith setup](docs/LANGSMITH_SETUP.md)
- [User story extraction](docs/USER_STORIES.md)
- [Roadmap](docs/ROADMAP.md) · [Changelog](docs/CHANGELOG.md)

## Contributing

Issues and pull requests are welcome. Please run `pytest` before submitting, and open an issue first for larger changes. Bring your own legacy horror stories; the sample data can always use another stratum.

## License

[MIT](LICENSE) © 2026 Oliver Sick

The bundled [Spring PetClinic sample](sample_data/spring-petclinic/) is third-party code from [spring-projects/spring-petclinic](https://github.com/spring-projects/spring-petclinic), redistributed under its own [Apache License 2.0](sample_data/spring-petclinic/LICENSE).
