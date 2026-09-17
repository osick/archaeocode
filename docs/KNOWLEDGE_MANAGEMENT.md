# Knowledge Management: The Site Archive

Every archaeological dig produces two things: a pile of finds, and a *record* of
where each find was, what it sat next to, and what the team thinks it was for.
Lose the record and you have a box of interesting rocks.

Until v0.4, archaeocode was excellent at the first part and terrible at the
second. Each run surveyed the site, catalogued every file, reconstructed the
dependency graph, and wrote user stories — then packed it all into a JSON
report and forgot about it. Ask a follow-up question next week and you were
back in the trench with a shovel.

The **knowledge base** is the site archive. Every run can now be filed into a
persistent knowledge graph that people interrogate with `archaeo-kb` and that
agents interrogate through the `knowledge-base` MCP server. This document
records what was chosen, why, and how to use and scale it.

## The decision: GraphRAG, with a wiki as the museum gift shop

Three ways of remembering were on the table.

| Approach | What it is | Fit for legacy-system knowledge |
|---|---|---|
| **LLM wiki** (Karpathy-style: an LLM maintains a Markdown wiki) | Human-readable pages, incrementally curated by the model | Lovely to read, terrible to *ask*. No retrieval layer, so it does not scale to millions of LOC; every update is an LLM call; and "what depends on copybook X?" means re-reading pages until you find it. A wiki is a gift shop, not a catalogue. |
| **Vanilla RAG** (chunks + vector search) | Embed text chunks, retrieve top-k | Fine for "find code that looks like this". Poor for multi-hop and global questions ("which business processes touch the tariff tables?"), and it throws away the one thing static analysis handed us for free: the exact dependency graph. Like searching a dig by the colour of the dirt. |
| **GraphRAG** (knowledge graph + vectors) | Entities and relations in a graph, chunks and entities embedded, retrieval walks both | Matches the material. A codebase *is* a graph. Multi-hop questions, global summaries, and exact structural facts coexist, and the graph can be seeded deterministically from the AST/dependency analysis so the LLM is only spent on the interesting part: business meaning. |

**Choice: GraphRAG, with the wiki as a projection of the graph** rather than as
the system of record. You still get the human-facing "LLM wiki" experience (one
page per entity, `[[wikilinks]]`, opens in Obsidian) without giving up a
queryable, scalable backbone. The graph is the archive; the wiki is printed
from it whenever you like.

### Why LightRAG and not one of the other shovels

The brief was: *reuse a fitting solution that integrates best and scales by all
dimensions.* Candidates were assessed on integration fit (Python, LangGraph,
MCP, Neo4j already in the stack, Anthropic first), incremental updates, storage
back-ends, cost control, query capabilities, licence and maturity.

| Candidate | Verdict |
|---|---|
| **[LightRAG](https://github.com/HKUDS/LightRAG)** (HKUDS, MIT) | **Chosen.** Pure-Python library, async, pluggable LLM/embedding functions (Anthropic, OpenAI, Ollama, HuggingFace adapters built in), storage back-ends for NetworkX/Neo4j/Memgraph/Postgres+AGE (graph), nano-vectordb/FAISS/pgvector/Qdrant/Milvus (vectors), JSON/Postgres/Redis/Mongo (KV). Incremental inserts with document tracking and deletion. **`insert_custom_kg`** lets us write the exact dependency graph without any LLM — the feature that decided it. Query modes local/global/hybrid/naive/mix, structured retrieval without LLM (`query_data`), graph export. Workspaces isolate multiple systems in one back-end. |
| Microsoft GraphRAG | A batch indexer built around community summaries: expensive to (re)index, weak incremental story, parquet/LanceDB-centric, and no clean way to hand it a graph we already computed. Superb for a static document corpus, wrong shape for a codebase that keeps changing. |
| Cognee | Solid "AI memory" engine with graph + vector and an MCP server, but more opinionated pipelines ("cognify"), telemetry on by default, and less direct control over inserting a prebuilt graph. Close second. |
| Graphiti (Zep) | Temporal knowledge graph aimed at agent memory; Neo4j/FalkorDB mandatory, extraction is LLM-first. Excellent for facts that change over time, over-engineered for code corpora. |
| neo4j-graphrag (official Neo4j) | Clean and Neo4j-native, but Neo4j is mandatory (no zero-infrastructure mode for laptops or CI) and there is no global/community retrieval. |
| LlamaIndex PropertyGraphIndex | Capable, but drags a second orchestration framework in next to LangGraph. One expedition leader is enough. |

## Architecture

```
archaeo run
  Discovery ─► AST ─► Dependencies ─► User stories ─► Knowledge Base node
                                                            │
                     deterministic (no LLM) ────────────────┤
                       files, classes, functions, methods   │
                       import/call edges, circular deps     │  LightRAG
                       user stories ⟷ files                 │  ┌────────────┐
                                                            ├─►│ graph store │  NetworkX | Neo4j | Postgres/AGE | Memgraph
                     optional LLM extraction ───────────────┤  │ vector db   │  nano-vectordb | pgvector | Qdrant | Milvus | FAISS
                       business entities & relations        │  │ kv / status │  JSON | Postgres | Redis | Mongo
                       (customers, invoices, tariffs, ...)  │  └────────────┘
                                                            │
        archaeo-kb CLI ◄──── query / retrieve / graph ◄─────┤
        knowledge-base MCP server ◄─────────────────────────┤
        Obsidian wiki (index.md + entities/*.md) ◄──────────┘
```

Two streams feed the archive:

- **The deterministic stream** is the field record. Files, classes, functions,
  methods, import/call edges, circular dependencies, and user stories are
  written straight into the graph. No LLM is involved, so it is exact, free,
  and idempotent: re-run the dig and the record is upserted, not duplicated.
- **The optional LLM stream** (`--kb-extract`) is the interpretation. LightRAG's
  entity/relation extraction reads the sources and files *business* concepts
  (customers, invoice runs, tariff tables) next to the technical ones, in the
  same graph. This is the only step that costs tokens, and it is off by default.

Code lives in:

- `src/mcp_servers/knowledge_base/knowledge_base.py` — the adapter (`KnowledgeBase`, `KnowledgeBaseConfig`, `build_custom_kg`)
- `src/mcp_servers/knowledge_base/knowledge_mcp_server.py` — MCP tools
- `src/orchestration/nodes/knowledge_node.py` — workflow node
- `src/orchestration/kb_cli.py` — `archaeo-kb`

### What gets filed

| Source in workflow state | Graph entities | Relations | Embedded chunks |
|---|---|---|---|
| `code_artifacts` | one `file` entity per file (language, size, complexity, defined members) | | source windows of ~`chunk_token_size` tokens with a `File: path (lines a-b)` header |
| `parsed_entities` (tree-sitter) | `class` / `function` / `method` entities named `path::Name` | `file —contains→ member` | (linked to the chunk containing the definition) |
| `dependency_graph` | `external_dependency` entities for targets outside the sources | `file —imports/calls→ file/external`, `circular-dependency` keyword on cycle edges | |
| `user_stories` | `user_story` entities with role, capability, benefit, criteria | `story —derived_from→ file` | the story as Markdown |
| documents added later (`archaeo-kb add`, `kb_add_documents`) | `document` entities | via LLM extraction (optional) | document windows |

That last row matters more than it looks. Runbooks, ticket exports, and the
notes from your interview with the one person who still remembers why the
batch job runs at 02:17 all go into the same graph as the code. The archive
holds the folklore as well as the finds.

## Usage

### File a dig

```bash
# zero infrastructure: NetworkX + nano-vectordb under data/knowledge_base,
# local sentence-transformers embeddings, no LLM needed
python archaeo --source ./legacy --source-lang cobol --knowledge-base --kb-wiki ./wiki

# with an API key: also let the LLM extract business entities
python archaeo --source ./legacy --source-lang cobol --knowledge-base --kb-extract
```

Flags: `--knowledge-base/--kb`, `--kb-dir`, `--kb-workspace`, `--kb-extract`,
`--kb-wiki DIR`, `--kb-embeddings {sentence-transformers,openai,ollama,hashing}`.
The same settings live under `knowledge_base:` in `config/langgraph_config.yaml`
and as `KB_*` environment variables (`.env.example`).

### Interrogate the archive

```bash
archaeo-kb query "Which programs update the customer master file, and what business rules apply?"
archaeo-kb query "Summarize the payment domain" --mode global
archaeo-kb retrieve "PROCESS-PAYMENT" --mode local        # no LLM: entities, relations, chunks
archaeo-kb context "SQLCA"                                 # prompt-ready evidence block
archaeo-kb graph "PAYMENT.cob" --depth 2
archaeo-kb stats
archaeo-kb add docs/runbook.md docs/interview-notes.md     # file the folklore
archaeo-kb wiki ./wiki                                     # print the museum catalogue
```

Query modes (LightRAG): `local` (entity neighbourhood: "tell me about this
thing"), `global` (relations and themes: "tell me about this area"), `hybrid`,
`naive` (chunks only, classic RAG), `mix` (default: graph + chunks).
`query` needs an LLM (Anthropic → OpenAI → Ollama, picked from the keys
present); `retrieve`, `context`, `graph`, `stats`, `wiki` never do, so the
archive is useful even on a machine with no keys and no network.

### From Python

```python
from src.mcp_servers.knowledge_base import KnowledgeBase, KnowledgeBaseConfig

config = KnowledgeBaseConfig(working_dir="data/knowledge_base")

async def ask(kb: KnowledgeBase):
    return await kb.query("Which files implement invoice calculation?", mode="mix")

print(KnowledgeBase.run_with(ask, config))
```

### From an agent (MCP)

`python src/mcp_servers/knowledge_base/knowledge_mcp_server.py` exposes
`kb_query`, `kb_retrieve`, `kb_context`, `kb_graph`, `kb_stats`,
`kb_add_documents`, `kb_export_wiki`. Add it to Claude Desktop / Claude Code like
the other servers (see `docs/MCP_SERVERS_USAGE.md`); set `KB_WORKING_DIR` or pass
`working_dir` per call. An agent planning a migration can now ask the archive
instead of re-reading the code, which is the whole point.

## Scaling: from shoebox to national museum

The adapter never touches back-end specifics; scale is a configuration change.
Recommended profiles (also listed in `config/mcp_servers_config.yaml`):

| Profile | Graph | Vectors | KV / status | Embeddings | Typical size |
|---|---|---|---|---|---|
| shoebox (laptop / CI) | `NetworkXStorage` | `NanoVectorDBStorage` | JSON files | sentence-transformers (local) | up to ~100k LOC, one user |
| team | `Neo4JStorage` | `PGVectorStorage` | `PGKVStorage` | OpenAI `text-embedding-3-large` | millions of LOC, several analysts, shared |
| national museum | `Neo4JStorage` | `QdrantVectorDBStorage` / `MilvusVectorDBStorage` | `RedisKVStorage` | OpenAI / self-hosted | many systems, one `workspace` each |

Set them via environment (`KB_GRAPH_STORAGE=Neo4JStorage`, `NEO4J_URI`,
`NEO4J_USERNAME` (falls back to `NEO4J_USER`), `NEO4J_PASSWORD`,
`POSTGRES_*`, `QDRANT_URL`, ...) or in the YAML section. Other scale levers:

- **Workspaces** — `--kb-workspace billing-core` keeps several analyzed systems
  apart inside one Neo4j/Postgres/Qdrant. One archive per site, one building.
- **Batching** — custom-KG inserts are streamed in batches of files, so a
  million-line codebase does not need to fit in one write.
- **Cost** — deterministic indexing is free of LLM tokens. `--kb-extract` is the
  only expensive step; cap it with `max_extract_files`, and LightRAG caches LLM
  responses so re-runs do not pay twice. Local embeddings via sentence-transformers
  or Ollama keep data on-premise, which matters when the code *is* the bank.
- **Offline** — `KB_TOKENIZER=bytes` and `KB_EMBEDDING_PROVIDER=hashing` run the
  whole pipeline without network access (this is what the test suite does). If
  the sentence-transformers model cannot be downloaded, the adapter falls back
  to hashing embeddings with a warning rather than dying in the trench.
- **Observability** — LightRAG calls go through the same Anthropic/OpenAI SDKs;
  the workflow node is a normal LangGraph node, so it shows up in LangSmith.

## Known gaps and the next season's dig plan

- AST entities are only available for tree-sitter-supported languages; COBOL,
  Fortran and Pascal contribute files, dependencies and stories until their
  grammars land (see the language matrix in the README).
- The dependency mapper still returns illustrative edges for some languages;
  the knowledge base faithfully indexes whatever it gets, so improving the
  mapper improves the graph automatically.
- Planned: incremental re-indexing keyed by file hash (LightRAG already tracks
  document ids), community summaries for very large systems, and feeding
  retrieved context back into the user-story prompt so stories are written
  with cross-file knowledge instead of one file at a time.
