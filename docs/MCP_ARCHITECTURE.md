# Model Context Protocol (MCP) Server Architecture

## 📖 What is MCP?

**Model Context Protocol (MCP)** is an open protocol developed by Anthropic that standardizes how AI applications connect to external data sources and tools.

### Key Concepts

```
┌─────────────┐
│  LangGraph  │  ← Your orchestration layer (brain)
│    Nodes    │
└──────┬──────┘
       │ Uses MCP tools
       ↓
┌─────────────┐
│ MCP Servers │  ← Tool providers (hands)
├─────────────┤
│ • Static    │  - Expose specific capabilities
│   Analysis  │  - Modular and replaceable
│ • RAG       │  - Standard interface
│ • Graph DB  │  - Easy to test
└─────────────┘
```

### Why MCP?

**Without MCP:**
```python
# Tightly coupled - hard to maintain
from tree_sitter import Parser
from neo4j import GraphDatabase
from qdrant_client import QdrantClient

# Code mixed with infrastructure
parser = Parser()
db = GraphDatabase.driver(...)
vector_store = QdrantClient(...)

# Hard to test, hard to swap implementations
```

**With MCP:**
```python
# Loosely coupled - easy to maintain
mcp_client = MCPClient()

# Simple, standard interface
result = mcp_client.call_tool("parse_file", {
    "file_path": "CustomerService.java",
    "language": "java"
})

# Easy to mock, easy to swap providers
```

---

## 🏗️ Our MCP Architecture

We're implementing **3 MCP servers** for our reverse engineering system:

```
┌──────────────────────────────────────────────────────────────┐
│                    LangGraph Workflow                        │
│                                                              │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐   │
│  │Discovery │→→│   AST    │→→│Dependencies│→│Generation│   │
│  └────┬─────┘  └────┬─────┘  └─────┬──────┘  └─────┬────┘   │
│       │             │              │               │         │
└───────┼─────────────┼──────────────┼───────────────┼─────────┘
        ↓             ↓              ↓               ↓
┌──────────────────────────────────────────────────────────────┐
│                    MCP Tool Layer                            │
│                                                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │   Static     │  │     RAG      │  │   Graph DB   │      │
│  │   Analysis   │  │   Pipeline   │  │   (Neo4j)    │      │
│  │ MCP Server   │  │  MCP Server  │  │  MCP Server  │      │
│  └──────────────┘  └──────────────┘  └──────────────┘      │
└──────────────────────────────────────────────────────────────┘
```

---

## 🔧 MCP Server #1: Static Analysis

### Purpose
Parse code, extract entities, analyze structure

### Tools Exposed

| Tool | Description | Input | Output |
|------|-------------|-------|--------|
| `parse_file` | Parse source file into AST | `file_path`, `language` | AST tree |
| `query_ast` | Query AST with tree-sitter queries | `ast`, `query` | Matching nodes |
| `extract_symbols` | Extract classes, functions, etc. | `ast`, `language` | Symbol list |

### Example Usage

```python
# From LangGraph node
static_analysis = mcp_client.get_server("static_analysis")

# Parse a Java file
result = static_analysis.call_tool("parse_file", {
    "file_path": "./CustomerService.java",
    "language": "java"
})

# AST is returned as structured data
ast = result["ast"]

# Query the AST
functions = static_analysis.call_tool("query_ast", {
    "ast": ast,
    "query": "(method_declaration name: (identifier) @name)"
})

# Functions: ["processPayment", "calculateTotal", ...]
```

### Technology Stack
- **tree-sitter**: Real AST parsing
- **tree-sitter-languages**: Pre-built grammars (15 languages)
- **Custom queries**: Language-specific patterns

### Use Cases
- ✅ Parse code in AST node (we're already doing this)
- ✅ Extract entities for dependency analysis
- ✅ Find security patterns (unused variables, SQL injection points)
- ✅ Generate documentation from code structure

---

## 🔧 MCP Server #2: RAG Pipeline

### Purpose
Semantic code search using vector embeddings

### Tools Exposed

| Tool | Description | Input | Output |
|------|-------------|-------|--------|
| `chunk_document` | Split code into semantic chunks | `content`, `language` | Chunks |
| `embed_code` | Generate vector embeddings | `chunks` | Embeddings |
| `index_codebase` | Index entire codebase | `code_artifacts` | Stats |
| `semantic_search` | Search by meaning | `query`, `top_k` | Results |

### Example Usage

```python
# From LangGraph node
rag = mcp_client.get_server("rag_pipeline")

# Index the codebase
result = rag.call_tool("index_codebase", {
    "code_artifacts": state["code_artifacts"],
    "collection_name": "my_project"
})

# Later: Search for similar code
results = rag.call_tool("semantic_search", {
    "query": "payment processing logic",
    "top_k": 5,
    "filter_language": "java"
})

# Results:
# [
#   {
#     "text": "public void processPayment(Payment p) {...}",
#     "file_path": "PaymentService.java",
#     "score": 0.95
#   },
#   ...
# ]
```

### Technology Stack
- **Qdrant**: Vector database (or Chroma/Weaviate)
- **OpenAI Embeddings**: text-embedding-3-large (3072 dimensions)
- **LangChain**: Text splitters, document loaders
- **Semantic chunking**: Function-aware splitting

### Use Cases
- ✅ Find similar code patterns across projects
- ✅ Search by functionality ("find all payment processing code")
- ✅ Duplicate code detection
- ✅ Example-based code generation ("generate code like this example")
- ✅ Technical debt analysis (find outdated patterns)

### How It Works

```
1. Code File (Java)
   ↓
2. Chunk (function-aware)
   ↓
3. Embed (OpenAI)
   ↓
4. Store in Qdrant
   [0.123, 0.456, ..., 0.789]  (3072 dimensions)
   ↓
5. Query: "payment validation"
   ↓
6. Return similar chunks (cosine similarity)
```

---

## 🔧 MCP Server #3: Graph Database (Neo4j)

### Purpose
Map dependencies, detect cycles, analyze call graphs

### Tools Exposed

| Tool | Description | Input | Output |
|------|-------------|-------|--------|
| `create_nodes` | Create nodes (classes, functions) | `nodes` | Stats |
| `create_relationships` | Link dependencies | `relationships` | Stats |
| `query_graph` | Execute Cypher queries | `cypher`, `params` | Results |
| `find_dependencies` | Get all dependencies | `node_name`, `depth` | Node list |
| `find_dependents` | Who depends on this? | `node_name`, `depth` | Node list |
| `shortest_path` | Path between nodes | `source`, `target` | Path |
| `detect_cycles` | Find circular dependencies | - | Cycle list |

### Example Usage

```python
# From LangGraph dependency node
graph_db = mcp_client.get_server("graph_db")

# Create nodes for classes
graph_db.call_tool("create_nodes", {
    "nodes": [
        {"label": "Class", "name": "CustomerService", "file": "CustomerService.java"},
        {"label": "Class", "name": "PaymentService", "file": "PaymentService.java"},
        {"label": "Class", "name": "Database", "file": "Database.java"}
    ]
})

# Create dependency relationships
graph_db.call_tool("create_relationships", {
    "relationships": [
        {"source": "CustomerService", "target": "PaymentService", "type": "DEPENDS_ON"},
        {"source": "CustomerService", "target": "Database", "type": "DEPENDS_ON"},
        {"source": "PaymentService", "target": "Database", "type": "DEPENDS_ON"}
    ]
})

# Find all dependencies of CustomerService
deps = graph_db.call_tool("find_dependencies", {
    "node_name": "CustomerService",
    "depth": 10  # Traverse up to 10 levels
})

# deps = ["PaymentService", "Database"]

# Detect circular dependencies
cycles = graph_db.call_tool("detect_cycles", {})

# cycles = [["OrderService", "InventoryService", "OrderService"]]
```

### Technology Stack
- **Neo4j**: Graph database
- **Cypher**: Query language
- **Graph algorithms**: Path finding, cycle detection, centrality

### Use Cases
- ✅ Visualize code dependencies
- ✅ Detect circular dependencies (causes compilation issues)
- ✅ Impact analysis ("what breaks if I change this?")
- ✅ Migration planning (order modules by dependency layers)
- ✅ Dead code detection (nodes with no incoming edges)
- ✅ Hotspot detection (nodes with many dependencies)

### Graph Example

```
Neo4j Graph:

┌──────────────┐
│CustomerService│
└───────┬──────┘
        │ DEPENDS_ON
        ↓
┌──────────────┐     ┌──────────┐
│PaymentService│────→│ Database │
└──────────────┘     └──────────┘
      DEPENDS_ON
```

**Cypher Query:**
```cypher
MATCH (c:Class {name: "CustomerService"})-[:DEPENDS_ON*]->(dep)
RETURN dep.name, dep.file
ORDER BY dep.name
```

---

## 🔄 Integration with LangGraph

### Current Workflow (Phase 4)
```python
# In ast_node.py
def __call__(self, state):
    # Direct tree-sitter usage
    from tree_sitter_languages import get_parser
    parser = get_parser('java')
    tree = parser.parse(code)

    # Extract entities ourselves
    entities = self.extract_entities(tree, 'java')

    return state
```

### Future Workflow (Phase 5 with MCP)
```python
# In ast_node.py
def __call__(self, state):
    # Use MCP tool
    mcp = self.mcp_client.get_server("static_analysis")

    result = mcp.call_tool("parse_file", {
        "file_path": artifact["path"],
        "language": artifact["language"]
    })

    ast = result["ast"]

    # Extract entities via MCP
    entities = mcp.call_tool("extract_symbols", {
        "ast": ast,
        "language": artifact["language"]
    })

    return state
```

### Benefits of MCP Integration

1. **Modularity**
   - Swap tree-sitter for Universal CTags without changing nodes
   - Use different vector stores (Qdrant → Weaviate) via config
   - Test with mock MCP servers

2. **Scalability**
   - MCP servers can run on separate machines
   - Distribute parsing across multiple servers
   - Cache results at MCP layer

3. **Testability**
   ```python
   # Easy to mock
   mock_mcp = MockMCPServer()
   mock_mcp.register_response("parse_file", {
       "ast": {"type": "program", "children": [...]}
   })

   # Test node without real tree-sitter
   node = ASTNode(mcp_client=mock_mcp)
   ```

4. **Composability**
   ```python
   # Combine multiple MCP tools
   ast = static_analysis.parse_file(...)
   chunks = rag.chunk_document(ast_to_text(ast))
   rag.index_codebase(chunks)

   # Now you can search the AST!
   results = rag.semantic_search("complex payment logic")
   ```

---

## 📦 Implementation Plan

### Phase 5A: Static Analysis MCP Server
**Time**: 1-2 hours

**Tasks**:
1. Remove placeholders from `tree_sitter_server.py`
2. Integrate real tree-sitter (we already have this!)
3. Implement tree-sitter queries for pattern matching
4. Add MCP protocol methods (`list_tools`, `call_tool`)
5. Test with Java/Python samples

**Benefit**: Modular AST parsing, queryable code structure

### Phase 5B: RAG Pipeline MCP Server
**Time**: 2-3 hours

**Tasks**:
1. Install Qdrant (Docker or embedded)
2. Setup OpenAI embeddings
3. Implement chunking strategy (function-aware)
4. Index sample codebase
5. Test semantic search

**Benefit**: Semantic code search, find similar patterns

### Phase 5C: Graph Database MCP Server
**Time**: 2-3 hours

**Tasks**:
1. Install Neo4j (Docker)
2. Design graph schema (Classes, Methods, Dependencies)
3. Implement Cypher queries
4. Build dependency graph from artifacts
5. Detect circular dependencies

**Benefit**: Dependency visualization, impact analysis

### Phase 5D: Integration
**Time**: 1 hour

**Tasks**:
1. Create MCP client wrapper
2. Update nodes to use MCP tools
3. Add configuration for MCP servers
4. End-to-end testing

---

## 🎯 Use Case Examples

### Example 1: Find All Payment-Related Code
```python
# 1. Index codebase
rag.index_codebase(code_artifacts)

# 2. Search semantically
results = rag.semantic_search("payment processing logic", top_k=10)

# 3. Get dependencies
for result in results:
    deps = graph_db.find_dependencies(result["function_name"])
    print(f"{result['function_name']} depends on: {deps}")
```

### Example 2: Detect Circular Dependencies Before Migration
```python
# 1. Build dependency graph
graph_db.create_nodes(classes)
graph_db.create_relationships(dependencies)

# 2. Detect cycles
cycles = graph_db.detect_cycles()

# 3. Report
if cycles:
    print("⚠️  Circular dependencies detected!")
    for cycle in cycles:
        print(f"  Cycle: {' → '.join(cycle)}")
    print("  Fix these before migration!")
```

### Example 3: Find Security Vulnerabilities
```python
# 1. Parse all files
asts = [static_analysis.parse_file(f.path, f.lang) for f in files]

# 2. Query for SQL injection patterns
vulnerable = []
for ast in asts:
    results = static_analysis.query_ast(ast,
        query="(string_literal) @sql WHERE @sql MATCHES '.*SELECT.*'")
    if results:
        vulnerable.append(ast["file_path"])

# 3. Report
print(f"Found {len(vulnerable)} files with potential SQL injection")
```

---

## 💡 Key Advantages

### 1. **Separation of Concerns**
- **LangGraph**: Orchestration logic
- **MCP Servers**: Tool implementations
- **Clear boundaries**: Easy to understand and maintain

### 2. **Technology Flexibility**
- Swap Qdrant for Pinecone: Change config, not code
- Use Semgrep instead of tree-sitter: New MCP server, same interface
- Try different embedding models: Config change only

### 3. **Independent Scaling**
```
┌──────────────┐
│   LangGraph  │  (1 instance)
└──────┬───────┘
       │
       ├───→ Static Analysis MCP (3 instances - load balanced)
       ├───→ RAG MCP (2 instances)
       └───→ Graph DB MCP (1 instance)
```

### 4. **Easy Testing**
```python
# Test without real infrastructure
def test_dependency_node():
    mock_mcp = MockMCPClient()
    mock_mcp.register_tool("find_dependencies",
        lambda **args: ["ServiceA", "ServiceB"])

    node = DependencyNode(mcp_client=mock_mcp)
    result = node(state)

    assert len(result["dependencies"]) == 2
```

---

## 📊 Comparison: With vs Without MCP

| Aspect | Without MCP | With MCP |
|--------|-------------|----------|
| **Coupling** | Tight (nodes import libraries directly) | Loose (nodes call tools) |
| **Testing** | Hard (need real DB, tree-sitter, etc.) | Easy (mock MCP responses) |
| **Flexibility** | Low (changing tools = rewriting nodes) | High (swap MCP servers) |
| **Scalability** | Limited (everything in one process) | High (distribute servers) |
| **Debugging** | Mixed concerns | Clear boundaries |
| **Maintainability** | Complex (infrastructure + logic) | Simple (logic only in nodes) |

---

## 🚀 Next Steps

### Option 1: Full Implementation (Phase 5)
Implement all 3 MCP servers end-to-end

**Pros**: Complete architecture, maximum benefits
**Cons**: 6-8 hours total

### Option 2: Incremental (Start with Static Analysis)
Implement just the Static Analysis MCP server first

**Pros**: Quick win, demonstrates concept, 1-2 hours
**Cons**: Partial benefits

### Option 3: Skip for Now
Continue with current direct integration

**Pros**: Faster to Phase 6
**Cons**: Miss architecture benefits

---

## ❓ Questions to Consider

1. **Do we need independent scalability?**
   - If yes → MCP servers on separate infrastructure
   - If no → MCP servers still useful for modularity

2. **Will we swap implementations?**
   - If yes → MCP makes this trivial
   - If no → MCP still helps with testing

3. **How important is testing?**
   - Very → MCP enables easy mocking
   - Somewhat → MCP still beneficial but less critical

4. **Time budget?**
   - 6-8 hours → Full implementation (all 3 servers)
   - 2-3 hours → One server (Static Analysis)
   - 0 hours → Skip to Phase 6

---

## 📝 Summary

**MCP Servers** provide a standardized way to integrate tools into your LangGraph workflow:

- **3 servers planned**: Static Analysis, RAG, Graph DB
- **Modular architecture**: Swap implementations easily
- **Easy testing**: Mock MCP responses
- **Scalable**: Run servers independently
- **Clean code**: Nodes focus on logic, not infrastructure

**Ready to implement?** We can start with the Static Analysis MCP server (quickest win) or go for the full implementation.

What would you like to do?
