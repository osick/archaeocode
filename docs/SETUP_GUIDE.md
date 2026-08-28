# LangGraph Migration System - Setup Guide

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Infrastructure Setup](#infrastructure-setup)
3. [Application Setup](#application-setup)
4. [Configuration](#configuration)
5. [Verification](#verification)
6. [Troubleshooting](#troubleshooting)

## Prerequisites

### Software Requirements

- **Python**: 3.11 or higher
- **PostgreSQL**: 15 or higher
- **Neo4j**: 5.0 or higher
- **Qdrant**: Latest version
- **Docker** (recommended) and Docker Compose
- **Git**

### API Keys Required

- **Anthropic API Key** (for Claude) OR **OpenAI API Key** (for GPT)
- **LangSmith API Key** (for observability)

Get API keys:
- Anthropic: https://console.anthropic.com/
- OpenAI: https://platform.openai.com/api-keys
- LangSmith: https://smith.langchain.com/settings

## Infrastructure Setup

### Option 1: Docker Compose (Recommended)

Create `docker-compose.yml`:

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: langgraph_state
      POSTGRES_USER: langgraph
      POSTGRES_PASSWORD: langgraph_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data

  neo4j:
    image: neo4j:5.24
    environment:
      NEO4J_AUTH: neo4j/neo4j_password
      NEO4J_PLUGINS: '["apoc", "graph-data-science"]'
    ports:
      - "7474:7474"  # HTTP
      - "7687:7687"  # Bolt
    volumes:
      - neo4j_data:/data

  qdrant:
    image: qdrant/qdrant:latest
    ports:
      - "6333:6333"
      - "6334:6334"
    volumes:
      - qdrant_data:/qdrant/storage

volumes:
  postgres_data:
  neo4j_data:
  qdrant_data:
```

Start infrastructure:

```bash
docker-compose up -d
```

### Option 2: Manual Installation

#### PostgreSQL

**macOS**:
```bash
brew install postgresql@16
brew services start postgresql@16
createdb langgraph_state
```

**Ubuntu/Debian**:
```bash
sudo apt update
sudo apt install postgresql-16
sudo systemctl start postgresql
sudo -u postgres createdb langgraph_state
```

#### Neo4j

**macOS**:
```bash
brew install neo4j
neo4j start
```

**Ubuntu/Debian**:
```bash
wget -O - https://debian.neo4j.com/neotechnology.gpg.key | sudo apt-key add -
echo 'deb https://debian.neo4j.com stable latest' | sudo tee /etc/apt/sources.list.d/neo4j.list
sudo apt update
sudo apt install neo4j
sudo systemctl start neo4j
```

Access Neo4j browser: http://localhost:7474
Default credentials: neo4j/neo4j (change on first login)

#### Qdrant

**macOS**:
```bash
docker run -p 6333:6333 qdrant/qdrant
```

**Ubuntu/Debian**:
```bash
docker run -p 6333:6333 qdrant/qdrant
```

Or download binary from: https://github.com/qdrant/qdrant/releases

## Application Setup

### 1. Clone Repository

```bash
git clone https://github.com/your-org/archaeocode.git
cd archaeocode
```

### 2. Create Virtual Environment

```bash
# Using venv
python3.11 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Or using conda
conda create -n langgraph python=3.11
conda activate langgraph
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Install Tree-sitter Grammars

```bash
# Create grammars directory
mkdir -p parsers/tree-sitter-grammars
cd parsers/tree-sitter-grammars

# Clone grammar repositories
git clone https://github.com/tree-sitter/tree-sitter-java
git clone https://github.com/tree-sitter/tree-sitter-python
git clone https://github.com/yutaro-sakamoto/tree-sitter-cobol
git clone https://github.com/tom95/tree-sitter-smalltalk

# Build grammars (if needed)
# This is usually automatic with tree-sitter-languages package

cd ../..
```

## Configuration

### 1. Environment Variables

```bash
cp .env.example .env
```

Edit `.env`:

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-...
LANGSMITH_API_KEY=ls__...
LANGSMITH_PROJECT=legacy-code-migration

# Database credentials (match docker-compose or manual setup)
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=langgraph_state
POSTGRES_USER=langgraph
POSTGRES_PASSWORD=langgraph_password

NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=neo4j_password

QDRANT_HOST=localhost
QDRANT_PORT=6333
```

### 2. LangGraph Configuration

Review and customize `config/langgraph_config.yaml`:

```yaml
langsmith:
  enabled: true
  deployment: "cloud"  # or "eu_cloud" for EU
  project_name: "legacy-code-migration"

orchestration:
  max_iterations: 100
  timeout_seconds: 3600

llm:
  provider: "anthropic"  # or "openai"
  model: "claude-sonnet-4"
  temperature: 0.1
```

### 3. MCP Server Configuration

Review `config/mcp_servers_config.yaml`:

```yaml
static_analysis:
  tree_sitter:
    enabled: true
    languages: [java, cobol, python, javascript]

rag_pipeline:
  vector_store:
    provider: "qdrant"
    qdrant:
      host: "localhost"
      port: 6333

graph_db:
  provider: "neo4j"
  neo4j:
    uri: "bolt://localhost:7687"
```

## Verification

### 1. Test Database Connections

```python
# test_connections.py
import psycopg2
from neo4j import GraphDatabase
from qdrant_client import QdrantClient

# PostgreSQL
conn = psycopg2.connect(
    host="localhost",
    port=5432,
    database="langgraph_state",
    user="langgraph",
    password="langgraph_password"
)
print("✓ PostgreSQL connected")
conn.close()

# Neo4j
driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "neo4j_password")
)
driver.verify_connectivity()
print("✓ Neo4j connected")
driver.close()

# Qdrant
client = QdrantClient(host="localhost", port=6333)
print(f"✓ Qdrant connected: {client.get_collections()}")
```

Run:
```bash
python test_connections.py
```

### 2. Test LangGraph Import

```python
# test_import.py
from langgraph.graph import create_graph
from langgraph.state.graph_state import create_initial_state

print("✓ LangGraph imports successful")

# Create graph
graph = create_graph()
print("✓ Graph created")
```

Run:
```bash
python test_import.py
```

### 3. Run Example Workflow

```python
# example_run.py
from langgraph.graph import create_graph
import os

# Ensure API keys are set
assert os.getenv("ANTHROPIC_API_KEY"), "Set ANTHROPIC_API_KEY"
assert os.getenv("LANGSMITH_API_KEY"), "Set LANGSMITH_API_KEY"

# Create test directory
os.makedirs("sample_code", exist_ok=True)
with open("sample_code/test.py", "w") as f:
    f.write("def hello():\n    print('Hello, World!')")

# Run workflow
graph = create_graph()
result = graph.run(
    source_language="python",
    target_language="java",
    source_path="./sample_code"
)

print(f"✓ Workflow completed")
print(f"  Files processed: {result['total_files']}")
print(f"  Total lines: {result['total_lines']}")
```

Run:
```bash
python example_run.py
```

### 4. Check LangSmith

Visit https://smith.langchain.com and verify:
- Project "legacy-code-migration" exists
- Traces are being recorded
- No errors in traces

## Troubleshooting

### PostgreSQL Connection Error

**Error**: `psycopg2.OperationalError: could not connect to server`

**Solution**:
```bash
# Check if PostgreSQL is running
docker ps | grep postgres
# or
pg_isready

# Restart if needed
docker-compose restart postgres
```

### Neo4j Authentication Error

**Error**: `AuthError: The client is unauthorized`

**Solution**:
```bash
# Reset Neo4j password
docker exec -it <neo4j-container> cypher-shell
# Change password in Neo4j browser: http://localhost:7474
```

### Qdrant Connection Refused

**Error**: `ConnectionRefusedError: [Errno 111] Connection refused`

**Solution**:
```bash
# Check if Qdrant is running
docker ps | grep qdrant
curl http://localhost:6333/collections

# Restart if needed
docker-compose restart qdrant
```

### Tree-sitter Import Error

**Error**: `ImportError: tree_sitter_languages not found`

**Solution**:
```bash
pip install tree-sitter-languages
```

### LangSmith API Key Error

**Error**: `AuthenticationError: Invalid API key`

**Solution**:
- Verify API key at https://smith.langchain.com/settings
- Check `.env` file has correct key
- Reload environment: `source venv/bin/activate`

### Out of Memory

**Error**: `MemoryError` during large codebase analysis

**Solution**:
- Increase Docker memory limits
- Process codebase in batches
- Use pagination in `langgraph_config.yaml`:
  ```yaml
  orchestration:
    batch_size: 100  # Process 100 files at a time
  ```

## Next Steps

1. **Run Tests**: `pytest tests/`
2. **Read Documentation**: See `docs/LANGGRAPH_WIREFRAME.md`
3. **Explore Examples**: Check `examples/` directory
4. **Review Architecture**: Read `docs/LANGGRAPH_WIREFRAME.md`

## Support

- **Issues**: https://github.com/your-org/archaeocode/issues
- **Discussions**: https://github.com/your-org/archaeocode/discussions
- **Documentation**: https://your-docs-site.com

---

**Last Updated**: 2025-11-02
