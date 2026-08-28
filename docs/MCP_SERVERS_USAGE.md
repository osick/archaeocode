# MCP Servers Usage Guide

This document explains how to use the MCP (Model Context Protocol) servers implemented in this project.

## Overview

The project implements **three MCP servers** using the official [Anthropic MCP SDK](https://github.com/anthropics/mcp):

1. **AST Analysis Server** - Code parsing and static analysis using tree-sitter
2. **RAG Pipeline Server** - Code chunking, embeddings, and semantic search
3. **Neo4j Graph Database Server** - Dependency graph operations

All servers follow the official MCP protocol and can be used standalone or integrated with Claude Desktop, IDEs, or custom applications.

---

## 1. AST Analysis MCP Server

**Location:** `src/mcp_servers/static_analysis/ast_analysis_server.py`

### Available Tools

#### `parse_file`
Parse a source code file into an Abstract Syntax Tree (AST).

**Parameters:**
- `file_path` (string, required): Path to the source file
- `language` (string, required): Programming language (java, python, javascript, etc.)

**Returns:**
```json
{
  "success": true,
  "file_path": "/path/to/file.java",
  "language": "java",
  "ast": {
    "type": "program",
    "start_point": {"row": 0, "column": 0},
    "end_point": {"row": 150, "column": 1},
    "byte_range": {"start": 0, "end": 4500},
    "node_count": 333,
    "has_error": false
  }
}
```

#### `extract_entities`
Extract code entities (classes, functions, methods, imports) from a file.

**Parameters:**
- `file_path` (string, required): Path to the source file
- `language` (string, required): Programming language

**Returns:**
```json
{
  "success": true,
  "file_path": "/path/to/file.py",
  "language": "python",
  "entities": {
    "classes": [
      {"name": "DataProcessor", "line_start": 10, "line_end": 150}
    ],
    "functions": [
      {"name": "process_data", "line_start": 5, "line_end": 8}
    ],
    "methods": [],
    "imports": [
      {"statement": "import json", "line": 1}
    ]
  },
  "summary": {
    "classes": 1,
    "functions": 1,
    "methods": 0,
    "imports": 1,
    "total": 3
  }
}
```

#### `get_complexity`
Calculate cyclomatic complexity for a source file.

**Parameters:**
- `file_path` (string, required): Path to the source file
- `language` (string, required): Programming language

**Returns:**
```json
{
  "success": true,
  "file_path": "/path/to/file.py",
  "language": "python",
  "complexity": 5.0,
  "interpretation": "Simple"
}
```

Complexity interpretations:
- **Simple**: ≤ 5
- **Moderate**: 6-10
- **Complex**: 11-20
- **Very Complex**: > 20

#### `list_supported_languages`
List all programming languages supported by the server.

**Parameters:** None

**Returns:**
```json
{
  "supported_languages": [
    "javascript", "typescript", "java", "python", "c", "cpp",
    "go", "rust", "ruby", "php", "csharp", "bash", "shell"
  ],
  "total": 13
}
```

### Running the AST Server

#### Standalone Mode

```bash
# Run the server
python src/mcp_servers/static_analysis/ast_analysis_server.py
```

The server communicates via stdio (standard input/output) following the MCP protocol.

#### Testing

```bash
# Run tests
python tests/test_mcp_servers.py
```

---

## 2. RAG Pipeline MCP Server

**Location:** `src/mcp_servers/rag_pipeline/rag_mcp_server.py`

### Available Tools

#### `chunk_document`
Split a code document into chunks for embedding.

**Parameters:**
- `content` (string, required): Source code content
- `language` (string, required): Programming language
- `chunk_size` (integer, optional): Maximum chunk size in characters (default: 1000)
- `chunk_overlap` (integer, optional): Overlap between chunks (default: 200)

**Returns:**
```json
{
  "success": true,
  "chunks": [
    {
      "text": "def example():\n    pass",
      "metadata": {
        "language": "python",
        "chunk_index": 0,
        "start_char": 0,
        "end_char": 100,
        "chunk_size": 100
      }
    }
  ],
  "summary": {
    "total_chunks": 3,
    "language": "python",
    "chunk_size": 1000,
    "chunk_overlap": 200,
    "total_characters": 2500
  }
}
```

#### `embed_code`
Generate embeddings for code chunks.

**Note:** This is currently a mock implementation. In production, it would call OpenAI's `text-embedding-3-large` or similar embedding models.

**Parameters:**
- `chunks` (array, required): List of text chunks to embed

**Returns:**
```json
{
  "success": true,
  "embedded_chunks": [
    {
      "text": "def example():\n    pass",
      "metadata": {...},
      "embedding": [0.1, 0.2, ...],  // 3072 dimensions
      "embedding_model": "text-embedding-3-large (mock)"
    }
  ],
  "summary": {
    "total_chunks": 2,
    "embedding_dimensions": 3072,
    "embedding_model": "text-embedding-3-large (mock)"
  }
}
```

#### `index_codebase`
Index an entire codebase into a vector store.

**Note:** This is currently a mock implementation. In production, it would connect to Qdrant, Weaviate, Chroma, or Pinecone.

**Parameters:**
- `files` (array, required): List of file objects with `content`, `path`, `language` keys
- `collection_name` (string, optional): Vector store collection name (default: "code_embeddings")

**Returns:**
```json
{
  "success": true,
  "total_files": 10,
  "total_chunks": 125,
  "collection_name": "code_embeddings",
  "processed_files": [
    {"path": "/src/main.py", "language": "python", "chunks": 15}
  ],
  "status": "indexed (mock - not persisted)"
}
```

#### `semantic_search`
Perform semantic search over indexed code.

**Note:** This is currently a mock implementation returning sample results.

**Parameters:**
- `query` (string, required): Search query (natural language or code)
- `top_k` (integer, optional): Number of results to return (default: 5)
- `filter_language` (string, optional): Filter by language (e.g., "python")
- `collection_name` (string, optional): Collection to search (default: "code_embeddings")

**Returns:**
```json
{
  "success": true,
  "query": "function to add numbers",
  "results": [
    {
      "text": "def add(a, b):\n    return a + b",
      "metadata": {
        "file_path": "/src/math_utils.py",
        "language": "python",
        "chunk_index": 0
      },
      "score": 0.95
    }
  ],
  "summary": {
    "total_results": 2,
    "top_k": 5,
    "filter_language": "python",
    "collection_name": "code_embeddings"
  }
}
```

#### `get_collection_stats`
Get statistics about a vector store collection.

**Parameters:**
- `collection_name` (string, optional): Collection name (default: "code_embeddings")

**Returns:**
```json
{
  "success": true,
  "collection_name": "code_embeddings",
  "total_documents": 0,
  "total_vectors": 0,
  "embedding_dimensions": 3072,
  "indexed_languages": []
}
```

### Running the RAG Server

```bash
# Run the server
python src/mcp_servers/rag_pipeline/rag_mcp_server.py
```

---

## 3. Neo4j Graph Database MCP Server

**Location:** `src/mcp_servers/graph_db/neo4j_mcp_server.py`

### Available Tools

#### `create_nodes`
Create nodes in the dependency graph.

**Parameters:**
- `nodes` (array, required): List of node definitions

**Node Structure:**
```json
{
  "name": "UserService",
  "type": "Class",
  "properties": {
    "file_path": "/src/services/user_service.py",
    "line_start": 10,
    "line_end": 150,
    "language": "python",
    "complexity": 8.0
  }
}
```

**Supported Node Types:**
- Class
- Method
- Function
- Module
- Package
- Database
- Table

**Returns:**
```json
{
  "success": true,
  "created": 2,
  "node_types": ["Class"],
  "nodes": [
    {"name": "UserService", "type": "Class", "properties_count": 4}
  ]
}
```

#### `create_relationships`
Create relationships between nodes.

**Parameters:**
- `relationships` (array, required): List of relationship definitions

**Relationship Structure:**
```json
{
  "source": "UserService",
  "target": "DatabaseConnection",
  "type": "DEPENDS_ON",
  "properties": {
    "file_path": "/src/services/user_service.py",
    "line_number": 25
  }
}
```

**Supported Relationship Types:**
- CALLS - Function/method calls
- IMPORTS - Module imports
- EXTENDS - Class inheritance
- IMPLEMENTS - Interface implementation
- DEPENDS_ON - General dependency
- REFERENCES - Variable/field reference
- ACCESSES - Database/resource access

**Returns:**
```json
{
  "success": true,
  "created": 1,
  "relationship_types": ["DEPENDS_ON"],
  "relationships": [
    {"source": "UserService", "target": "DatabaseConnection", "type": "DEPENDS_ON"}
  ]
}
```

#### `query_graph`
Execute a Cypher query against the graph database.

**Parameters:**
- `cypher` (string, required): Cypher query string
- `parameters` (object, optional): Query parameters

**Example:**
```json
{
  "cypher": "MATCH (n:Class)-[:DEPENDS_ON]->(m) WHERE n.name = $name RETURN m",
  "parameters": {"name": "UserService"}
}
```

**Returns:**
```json
{
  "success": true,
  "query": "MATCH (n:Class)...",
  "parameters": {"name": "UserService"},
  "results": [],
  "result_count": 0
}
```

#### `find_dependencies`
Find all dependencies of a node.

**Parameters:**
- `node_name` (string, required): Name of the node to analyze
- `depth` (integer, optional): Maximum traversal depth (default: 1, use -1 for unlimited)
- `relationship_type` (string, optional): Filter by relationship type

**Returns:**
```json
{
  "success": true,
  "node_name": "UserService",
  "depth": 2,
  "relationship_type": "DEPENDS_ON",
  "dependencies": [
    {
      "name": "DatabaseConnection",
      "type": "Class",
      "distance": 1,
      "relationship": "DEPENDS_ON"
    }
  ],
  "total_dependencies": 2
}
```

#### `find_dependents`
Find all nodes that depend on this node.

**Parameters:**
- `node_name` (string, required): Name of the node to analyze
- `depth` (integer, optional): Maximum traversal depth (default: 1)
- `relationship_type` (string, optional): Filter by relationship type

**Returns:**
```json
{
  "success": true,
  "node_name": "DatabaseConnection",
  "dependents": [
    {
      "name": "UserService",
      "type": "Class",
      "distance": 1,
      "relationship": "DEPENDS_ON"
    }
  ],
  "total_dependents": 3
}
```

#### `shortest_path`
Find the shortest path between two nodes.

**Parameters:**
- `source` (string, required): Source node name
- `target` (string, required): Target node name
- `max_depth` (integer, optional): Maximum path length to search

**Returns:**
```json
{
  "success": true,
  "source": "UserController",
  "target": "DatabaseConnection",
  "path": ["UserController", "UserService", "DatabaseConnection"],
  "path_length": 2
}
```

#### `detect_cycles`
Detect circular dependencies in the graph.

**Parameters:**
- `max_cycles` (integer, optional): Maximum number of cycles to return (default: 10)

**Returns:**
```json
{
  "success": true,
  "cycles": [
    ["ClassA", "ClassB", "ClassC", "ClassA"],
    ["ModuleX", "ModuleY", "ModuleX"]
  ],
  "total_cycles": 2,
  "max_cycles": 10
}
```

#### `get_graph_metrics`
Calculate graph metrics and statistics.

**Parameters:** None

**Returns:**
```json
{
  "success": true,
  "total_nodes": 150,
  "total_relationships": 320,
  "node_types_distribution": {
    "Class": 45,
    "Function": 80,
    "Module": 20,
    "Package": 5
  },
  "relationship_types_distribution": {
    "CALLS": 180,
    "IMPORTS": 85,
    "DEPENDS_ON": 40,
    "EXTENDS": 15
  },
  "density": 0.029,
  "average_degree": 4.27
}
```

#### `clear_graph`
Clear all nodes and relationships from the graph database.

**⚠️ WARNING: This is a destructive operation!**

**Parameters:**
- `confirm` (boolean, required): Must be `true` to proceed

**Returns:**
```json
{
  "success": true,
  "deleted_nodes": 150,
  "deleted_relationships": 320
}
```

### Running the Neo4j Server

```bash
# Run the server
python src/mcp_servers/graph_db/neo4j_mcp_server.py
```

---

## Integration with Claude Desktop

To use these MCP servers with Claude Desktop, add them to your Claude Desktop configuration file:

### macOS/Linux
Edit: `~/Library/Application Support/Claude/claude_desktop_config.json`

### Windows
Edit: `%APPDATA%\Claude\claude_desktop_config.json`

### Configuration Example

```json
{
  "mcpServers": {
    "ast-analysis": {
      "command": "python",
      "args": [
        "/path/to/archaeocode/src/mcp_servers/static_analysis/ast_analysis_server.py"
      ]
    },
    "rag-pipeline": {
      "command": "python",
      "args": [
        "/path/to/archaeocode/src/mcp_servers/rag_pipeline/rag_mcp_server.py"
      ]
    },
    "neo4j-graph": {
      "command": "python",
      "args": [
        "/path/to/archaeocode/src/mcp_servers/graph_db/neo4j_mcp_server.py"
      ]
    }
  }
}
```

After adding the configuration, restart Claude Desktop. The MCP servers will be available as tools in your conversations.

---

## Testing

Run the comprehensive test suite:

```bash
# Test all MCP servers
python tests/test_mcp_servers.py

# Expected output:
# ╔==========================================================╗
# ║               MCP SERVER TESTS                           ║
# ╚==========================================================╝
#
# Testing AST Analysis MCP Server...
# ✓ All tests passed
#
# Testing RAG Pipeline MCP Server...
# ✓ All tests passed
#
# Testing Neo4j Graph Database MCP Server...
# ✓ All tests passed
#
# ╔==========================================================╗
# ║          ALL TESTS COMPLETED SUCCESSFULLY                ║
# ╚==========================================================╝
```

---

## Production Deployment Notes

### AST Analysis Server
- **Ready for production**: Uses real tree-sitter parsing
- **Supported languages**: 13 languages (JavaScript, TypeScript, Java, Python, C, C++, Go, Rust, Ruby, PHP, C#, Bash, Shell)
- **Dependencies**: `tree-sitter==0.21.3`, `tree-sitter-languages==1.10.2`

### RAG Pipeline Server
- **Current status**: Mock implementation
- **Production requirements**:
  - OpenAI API key for embeddings (or Cohere/HuggingFace)
  - Vector store: Qdrant, Weaviate, Chroma, or Pinecone
  - Update `embed_code` to call real embedding API
  - Update `index_codebase` to connect to vector store
  - Update `semantic_search` to query vector store

### Neo4j Graph Database Server
- **Current status**: Mock implementation
- **Production requirements**:
  - Neo4j database running (bolt://localhost:7687)
  - Neo4j credentials (NEO4J_USER, NEO4J_PASSWORD)
  - Install `neo4j` Python driver: `pip install neo4j`
  - Update all methods to execute real Cypher queries

---

## Environment Variables

Create a `.env` file for production configuration:

```bash
# OpenAI (for RAG embeddings)
OPENAI_API_KEY=your-openai-key-here

# Neo4j (for graph database)
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password-here
NEO4J_DATABASE=code_dependency_graph

# Qdrant (for vector store)
QDRANT_HOST=localhost
QDRANT_PORT=6333
QDRANT_COLLECTION=code_embeddings
```

---

## Error Handling

All MCP tools return errors in a consistent format:

```json
{
  "error": "Error message here",
  "context": "Additional context if available"
}
```

Always check for the `error` key in responses before processing results.

---

## Next Steps

1. **For RAG Pipeline**: Integrate with OpenAI embeddings and Qdrant vector store
2. **For Neo4j Graph**: Connect to real Neo4j database and implement Cypher queries
3. **Integration**: Update LangGraph nodes to use MCP servers instead of direct implementations
4. **Monitoring**: Add LangSmith tracing to MCP server calls
5. **Performance**: Add caching and batch processing for large codebases

---

## Support

For issues or questions:
- Review the test suite: `tests/test_mcp_servers.py`
- Check the main documentation: `docs/MCP_ARCHITECTURE.md`
- Refer to the official MCP SDK: https://github.com/anthropics/mcp
