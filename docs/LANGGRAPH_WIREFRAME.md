# LangGraph Architecture Wireframe

## Overview

This document describes the LangGraph implementation structure for the reverse engineering and code migration system.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                   LangGraph Orchestration Layer                 │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │  Discovery   │→→│ AST Analysis │→→│  Dependency  │         │
│  │    Node      │  │     Node     │  │  Mapping     │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                             ↓                   │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │     Code     │←←│   Security   │←←│     RAG      │         │
│  │  Generation  │  │    Scan      │  │  Indexing    │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
│                                                                 │
│  State Management: PostgreSQL                                  │
│  Checkpointing: SQLite / PostgreSQL                            │
│  Human-in-the-Loop: Approval Gates                             │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                       MCP Tool Layer                            │
│                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐ │
│  │ Static Analysis  │  │  RAG Pipeline    │  │  Graph DB    │ │
│  ├──────────────────┤  ├──────────────────┤  ├──────────────┤ │
│  │ • tree-sitter    │  │ • Qdrant         │  │ • Neo4j      │ │
│  │ • Semgrep        │  │ • OpenAI Embed   │  │ • Cypher     │ │
│  │ • Universal Tags │  │ • LangChain      │  │ • Queries    │ │
│  │ • SonarQube      │  │ • Chunking       │  │ • Analytics  │ │
│  └──────────────────┘  └──────────────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│          Source Language Abstraction Layer (SLAB)               │
│                                                                 │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐      │
│  │  COBOL   │  │ Smalltalk│  │   Java   │  │  Python  │      │
│  │  Parser  │  │  Parser  │  │  Parser  │  │  Parser  │      │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘      │
│                                                                 │
│  Special Extensions:                                           │
│  • HP NonStop COBOL (TMF, Pathway, Enscribe, TAL)              │
│  • Cincom Smalltalk (Image extraction, Type inference)         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                   Data Storage Layer                            │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐         │
│  │ Vector Store │  │  Graph DB    │  │   Metadata   │         │
│  │  (Qdrant)    │  │  (Neo4j)     │  │ (PostgreSQL) │         │
│  └──────────────┘  └──────────────┘  └──────────────┘         │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    LangSmith Observability                      │
│                                                                 │
│  • Tracing: Every LLM call and node execution                  │
│  • Metrics: Token usage, latency, cost                         │
│  • Debugging: State inspection, error tracking                 │
│  • Compliance: SOC 2, GDPR, HIPAA                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

## Directory Structure

```
codelore/
│
├── src/                           # Main source code (Python package)
│   ├── __init__.py
│   │
│   ├── langgraph/                 # Core LangGraph orchestration
│   │   ├── __init__.py
│   │   ├── graph.py               # Main graph orchestrator
│   │   │
│   │   ├── state/
│   │   │   ├── __init__.py
│   │   │   └── graph_state.py     # State schema and management
│   │   │
│   │   ├── nodes/
│   │   │   ├── __init__.py
│   │   │   ├── discovery_node.py  # Code discovery
│   │   │   ├── ast_node.py        # AST parsing
│   │   │   ├── dependency_node.py # Dependency mapping
│   │   │   ├── security_node.py   # Security scanning
│   │   │   ├── rag_node.py        # RAG indexing
│   │   │   ├── generation_node.py # Code generation
│   │   │   └── user_story_node.py # User story extraction
│   │   │
│   │   ├── agents/
│   │   │   ├── __init__.py
│   │   │   ├── migration_agent.py # LLM-based migration agent
│   │   │   └── user_story_agent.py # User story extraction agent
│   │   │
│   │   ├── checkpoints/
│   │   │   ├── __init__.py
│   │   │   └── checkpoint_manager.py # Checkpoint handling
│   │   │
│   │   ├── tools/
│   │   │   ├── __init__.py
│   │   │   ├── mcp_tool_wrapper.py # MCP tool wrappers
│   │   │   ├── code_analyzer.py    # Code analysis tools
│   │   │   └── rag_retriever.py    # RAG retrieval tools
│   │   │
│   │   ├── models/
│   │   │   ├── __init__.py
│   │   │   ├── workflow_state.py   # Workflow state models
│   │   │   └── user_story_models.py # User story data models
│   │   │
│   │   ├── prompts/
│   │   │   ├── __init__.py
│   │   │   ├── migration_prompts.py
│   │   │   └── story_generation.py # User story prompts
│   │   │
│   │   └── utils/
│   │       ├── __init__.py
│   │       ├── config_loader.py   # Configuration utilities
│   │       └── logging_setup.py   # Logging configuration
│   │
│   ├── mcp_servers/
│   │   ├── __init__.py
│   │   │
│   │   ├── static_analysis/
│   │   │   ├── __init__.py
│   │   │   ├── tree_sitter_server.py # Tree-sitter MCP server
│   │   │   └── semgrep_server.py     # Semgrep MCP server
│   │   │
│   │   ├── rag_pipeline/
│   │   │   ├── __init__.py
│   │   │   ├── rag_server.py         # RAG pipeline MCP server
│   │   │   └── embeddings.py         # Embedding utilities
│   │   │
│   │   └── graph_db/
│   │       ├── __init__.py
│   │       ├── neo4j_server.py       # Neo4j MCP server
│   │       └── memgraph_server.py    # Memgraph alternative
│   │
│   └── parsers/
│       ├── __init__.py
│       │
│       ├── cobol/
│       │   ├── __init__.py
│       │   └── nonstop_extensions.py # HP NonStop COBOL extensions
│       │
│       ├── smalltalk/
│       │   ├── __init__.py
│       │   └── image_extractor.py    # Smalltalk image extraction
│       │
│       └── java/
│           ├── __init__.py
│           └── spring_analyzer.py    # Spring Boot analysis
│
├── config/
│   ├── langgraph_config.yaml      # LangGraph orchestration config
│   ├── mcp_servers_config.yaml    # MCP server configurations
│   └── .env.example               # Environment variables template
│
├── data/
│   ├── vector_store/              # Vector embeddings storage
│   ├── graph_db/                  # Graph database files
│   └── metadata/                  # Metadata cache
│
├── docs/
│   ├── LANGGRAPH_WIREFRAME.md     # This document
│   ├── USER_STORIES.md            # User story extraction documentation
│   ├── SETUP_GUIDE.md             # Setup instructions
│   └── sources/
│       └── SOURCES.md             # All reference sources
│
├── examples/                      # Usage examples
│   ├── cobol_migration/           # COBOL migration example
│   ├── smalltalk_migration/       # Smalltalk migration example
│   └── user_story_extraction/     # User story extraction examples
│
├── tests/
│   ├── __init__.py
│   ├── unit/                      # Unit tests
│   │   ├── test_nodes.py
│   │   ├── test_agents.py
│   │   └── test_user_story_agent.py
│   ├── integration/               # Integration tests
│   │   ├── test_workflow.py
│   │   └── test_mcp_servers.py
│   └── e2e/                       # End-to-end tests
│       └── test_migrations.py
│
├── requirements.txt               # Python dependencies
├── setup.py                       # Package setup
├── .env.example                   # Environment template
├── .gitignore
└── README.md                      # Project overview
```

## Workflow Phases

### 1. Discovery Phase
**Node**: `discovery_node.py`
- Traverse source directory
- Identify code files by extension
- Count lines of code
- Create initial CodeArtifact objects

**Output**: List of code artifacts, file counts, language breakdown

### 2. AST Analysis Phase
**Node**: `ast_node.py`
- Parse files using tree-sitter
- Extract structural entities (classes, functions, methods)
- Calculate complexity metrics
- Store AST representations

**Tools Used**: tree-sitter MCP server

**Output**: AST trees, parsed entities, complexity scores

### 3. Dependency Mapping Phase
**Node**: `dependency_node.py`
- Extract import/include statements
- Map function/method calls
- Build dependency graph
- Detect circular dependencies
- Calculate dependency layers

**Tools Used**: Graph DB MCP server (Neo4j)

**Output**: Dependency graph, circular dependencies, layering

### 4. Security Scan Phase
**Node**: `security_node.py` (to be created)
- Run Semgrep security rules
- Identify code smells
- Calculate quality metrics
- Generate security report

**Tools Used**: Semgrep MCP server

**Output**: Security findings, quality metrics

### 5. RAG Indexing Phase
**Node**: `rag_node.py` (to be created)
- Chunk code into embeddings
- Generate vector embeddings
- Index into vector store
- Populate graph database

**Tools Used**: RAG Pipeline MCP server, Graph DB server

**Output**: Embedded chunks, vector store IDs

### 6. Code Generation Phase
**Node**: `generation_node.py` (to be created)
- Generate migration plan
- Create target code
- Generate tests
- Generate documentation

**Tools Used**: LLM (Claude/GPT), RAG search for context

**Output**: Generated artifacts, migration plan

## State Management

The workflow uses a typed state object (`MigrationState`) that flows through all nodes:

```python
MigrationState = {
    "workflow_id": str,
    "phase": AnalysisPhase,
    "code_artifacts": List[CodeArtifact],
    "ast_trees": Dict[str, Any],
    "dependency_graph": List[DependencyNode],
    "security_findings": List[SecurityFinding],
    "generated_artifacts": List[CodeArtifact],
    # ... more fields
}
```

## Checkpointing

- Backend: PostgreSQL or SQLite
- Frequency: Every 10 nodes (configurable)
- Enables: Workflow resumption after failures
- Storage: State snapshots with timestamps

## Human-in-the-Loop

Approval gates for:
- Code generation
- Schema migration
- Deployment steps

Timeout: 24 hours (configurable)

## MCP Server Architecture

All tools are exposed via MCP (Model Context Protocol) servers:

1. **Static Analysis Server** (`tree_sitter_server.py`)
   - parse_file
   - query_ast
   - extract_symbols

2. **RAG Pipeline Server** (`rag_server.py`)
   - chunk_document
   - embed_code
   - semantic_search
   - index_codebase

3. **Graph DB Server** (`neo4j_server.py`)
   - create_nodes
   - create_relationships
   - query_graph
   - find_dependencies
   - detect_cycles

## LangSmith Integration

All workflow executions are traced in LangSmith:

- **Tracing**: Every node execution, LLM call
- **Metrics**: Token usage, cost, latency
- **Debugging**: State inspection, error tracking
- **Compliance**: SOC 2, GDPR, HIPAA ready

Deployment options:
- Cloud: `https://smith.langchain.com`
- EU: `https://eu.smith.langchain.com`
- Self-hosted: Kubernetes + Helm

## Next Steps

1. **Complete remaining nodes**:
   - security_node.py
   - rag_node.py
   - generation_node.py

2. **Implement MCP servers**:
   - semgrep_server.py
   - ctags_server.py
   - memgraph_server.py

3. **Add language parsers**:
   - COBOL NonStop extensions
   - Smalltalk image extractor
   - Java Spring analyzer

4. **Setup infrastructure**:
   - PostgreSQL for state
   - Neo4j for graphs
   - Qdrant for vectors

5. **Testing**:
   - Unit tests for nodes
   - Integration tests for workflow
   - End-to-end migration tests

6. **Documentation**:
   - API reference
   - Setup guide
   - Migration examples

## Configuration

See `config/langgraph_config.yaml` for:
- LangSmith settings
- Checkpoint configuration
- HITL settings
- LLM configuration
- Performance tuning

See `config/mcp_servers_config.yaml` for:
- Tool configurations
- Vector store settings
- Graph DB connection
- Parser settings
