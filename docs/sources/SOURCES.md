# Source References for LangGraph Migration System

## Official Documentation

### LangGraph
- **LangGraph Documentation**: https://langchain-ai.github.io/langgraph/
- **LangGraph Tutorials**: https://langchain-ai.github.io/langgraph/tutorials/
- **State Management**: https://langchain-ai.github.io/langgraph/how-tos/state-model/
- **Checkpointing**: https://langchain-ai.github.io/langgraph/how-tos/persistence/
- **Human-in-the-Loop**: https://langchain-ai.github.io/langgraph/how-tos/human-in-the-loop/
- **GitHub Repository**: https://github.com/langchain-ai/langgraph

### LangSmith
- **LangSmith Platform**: https://smith.langchain.com
- **LangSmith Docs**: https://docs.smith.langchain.com
- **Tracing Guide**: https://docs.smith.langchain.com/tracing
- **Observability**: https://docs.smith.langchain.com/observability
- **Security & Compliance**: https://docs.smith.langchain.com/security
  - SOC 2 Type II (July 2024)
  - GDPR Compliance
  - HIPAA with BAAs

### Model Context Protocol (MCP)
- **MCP Specification**: https://modelcontextprotocol.io/
- **MCP Python SDK**: https://github.com/modelcontextprotocol/python-sdk
- **MCP Servers List**: https://github.com/modelcontextprotocol/servers
- **MCP TypeScript SDK**: https://github.com/modelcontextprotocol/typescript-sdk

### LangChain
- **LangChain Docs**: https://python.langchain.com/docs/
- **Document Loaders**: https://python.langchain.com/docs/integrations/document_loaders/
- **Text Splitters**: https://python.langchain.com/docs/modules/data_connection/document_transformers/
- **Embeddings**: https://python.langchain.com/docs/integrations/text_embedding/
- **Vector Stores**: https://python.langchain.com/docs/integrations/vectorstores/

## Static Analysis Tools

### Tree-Sitter
- **Main Repository**: https://github.com/tree-sitter/tree-sitter
- **Python Bindings**: https://github.com/tree-sitter/py-tree-sitter
- **Grammars**:
  - Java: https://github.com/tree-sitter/tree-sitter-java
  - Python: https://github.com/tree-sitter/tree-sitter-python
  - JavaScript: https://github.com/tree-sitter/tree-sitter-javascript
  - COBOL: https://github.com/yutaro-sakamoto/tree-sitter-cobol
  - Smalltalk: https://github.com/tom95/tree-sitter-smalltalk
- **Query Syntax**: https://tree-sitter.github.io/tree-sitter/using-parsers#pattern-matching-with-queries
- **Used By**: Aider, Continue.dev, GitHub CodeQL

### Semgrep
- **Main Site**: https://semgrep.dev
- **Documentation**: https://semgrep.dev/docs/
- **Rule Registry**: https://semgrep.dev/explore
  - 5,000+ security rules
  - OWASP Top 10 coverage
- **CLI Reference**: https://semgrep.dev/docs/cli-reference/
- **MCP Server**: https://github.com/modelcontextprotocol/servers/tree/main/src/semgrep
- **Python API**: https://semgrep.dev/docs/semgrep-ci/api/

### Universal Ctags
- **Repository**: https://github.com/universal-ctags/ctags
- **Documentation**: https://docs.ctags.io/en/latest/
- **Supported Languages**: 150+ languages
- **Output Formats**: JSON, CSV, Xref

### SonarQube
- **Main Site**: https://www.sonarsource.com/products/sonarqube/
- **Community Edition**: https://github.com/SonarSource/sonarqube
- **API Documentation**: https://docs.sonarqube.org/latest/extend/web-api/
- **Python Plugin**: https://docs.sonarqube.org/latest/analysis/languages/python/

## Graph Databases

### Neo4j
- **Main Site**: https://neo4j.com
- **Documentation**: https://neo4j.com/docs/
- **Cypher Query Language**: https://neo4j.com/docs/cypher-manual/current/
- **Python Driver**: https://neo4j.com/docs/python-manual/current/
- **Graph Data Science**: https://neo4j.com/docs/graph-data-science/current/
- **Community Edition**: https://github.com/neo4j/neo4j
- **Docker Image**: https://hub.docker.com/_/neo4j

### Memgraph
- **Main Site**: https://memgraph.com
- **Documentation**: https://memgraph.com/docs
- **Cypher Support**: Full Cypher compatibility
- **Python Client**: https://memgraph.com/docs/client-libraries/python
- **Docker Image**: https://hub.docker.com/r/memgraph/memgraph
- **Performance**: In-memory, optimized for OLTP

## Vector Databases

### Qdrant
- **Main Site**: https://qdrant.tech
- **Documentation**: https://qdrant.tech/documentation/
- **Python Client**: https://github.com/qdrant/qdrant-client
- **LangChain Integration**: https://python.langchain.com/docs/integrations/vectorstores/qdrant
- **Features**: Rust-based, high performance, filtering, hybrid search
- **Cloud Service**: https://cloud.qdrant.io
- **Docker Image**: https://hub.docker.com/r/qdrant/qdrant

### Weaviate
- **Main Site**: https://weaviate.io
- **Documentation**: https://weaviate.io/developers/weaviate
- **Python Client**: https://weaviate.io/developers/weaviate/client-libraries/python
- **LangChain Integration**: https://python.langchain.com/docs/integrations/vectorstores/weaviate
- **Features**: Hybrid search, multi-tenancy, GraphQL API

### Chroma
- **Main Site**: https://www.trychroma.com
- **GitHub**: https://github.com/chroma-core/chroma
- **Documentation**: https://docs.trychroma.com
- **LangChain Integration**: https://python.langchain.com/docs/integrations/vectorstores/chroma
- **Features**: Embedded option, simple API, open source

### Pinecone
- **Main Site**: https://www.pinecone.io
- **Documentation**: https://docs.pinecone.io
- **Python Client**: https://docs.pinecone.io/docs/python-client
- **LangChain Integration**: https://python.langchain.com/docs/integrations/vectorstores/pinecone
- **Features**: Managed service, serverless, enterprise ready

## Embedding Models

### OpenAI
- **Text Embeddings**: https://platform.openai.com/docs/guides/embeddings
- **Models**:
  - `text-embedding-3-large`: 3072 dimensions
  - `text-embedding-3-small`: 1536 dimensions
  - `text-embedding-ada-002`: 1536 dimensions (legacy)
- **Pricing**: https://openai.com/api/pricing/

### Cohere
- **Embed API**: https://docs.cohere.com/reference/embed
- **Models**:
  - `embed-english-v3.0`: 1024 dimensions
  - `embed-multilingual-v3.0`: 1024 dimensions
- **LangChain Integration**: https://python.langchain.com/docs/integrations/text_embedding/cohere

### HuggingFace
- **Sentence Transformers**: https://huggingface.co/sentence-transformers
- **Popular Models**:
  - `all-MiniLM-L6-v2`: Fast, 384 dimensions
  - `all-mpnet-base-v2`: High quality, 768 dimensions
- **LangChain Integration**: https://python.langchain.com/docs/integrations/text_embedding/huggingfacehub

## Legacy System Migration

### Research Papers

**2024**
- **Unraveling the Potential of Large Language Models in Code Translation**
  - ArXiv: https://arxiv.org/pdf/2410.09812v1
  - Focus: LLM-based code translation effectiveness
  - Key findings: Performance on COBOL, Java, Python

**2023**
- **Automated Code Translation with LLMs: A Survey**
  - Review of techniques and tools

**Pre-2020**
- **A-PART Framework: Porting from VisualWorks**
  - SlideShare: https://www.slideshare.net/slideshow/apart-framework-porting-from-visualworks/143194747
  - Focus: Smalltalk to Java migration
  - Technique: Automated refactoring and porting

### Migration Strategies

- **The 7 R's of Migration**:
  - Rehost, Replatform, Repurchase, Refactor, Rearchitect, Rebuild, Retire
  - Source: AWS Cloud Adoption Framework
  - URL: https://aws.amazon.com/cloud-migration/

- **Strangler Fig Pattern**:
  - Martin Fowler: https://martinfowler.com/bliki/StranglerFigApplication.html
  - Microsoft Docs: https://learn.microsoft.com/en-us/azure/architecture/patterns/strangler-fig

- **Legacy System Modernization**:
  - BitCot Guide: https://www.bitcot.com/legacy-system-modernization-and-migration/
  - Covers: Strategies, processes, services, costs

## Language-Specific Resources

### COBOL

**HP NonStop COBOL**
- **NonStop Development**: https://www.hpe.com/us/en/servers/nonstop.html
- **TMF (Transaction Management Facility)**: HP NonStop documentation
- **Pathway**: Screen management and transaction processing
- **Enscribe**: HP NonStop file system
- **TAL (Transaction Application Language)**: Low-level language

**COBOL Parsers**
- **tree-sitter-cobol**: https://github.com/yutaro-sakamoto/tree-sitter-cobol
- **COBOL Control Flow**: https://github.com/eclipse/che-che4z-lsp-for-cobol

**Migration Tools**
- **AWS Mainframe Modernization**: https://aws.amazon.com/mainframe-modernization/
- **Azure Mainframe Migration**: https://azure.microsoft.com/en-us/solutions/mainframe-modernization/

### Smalltalk

**Cincom VisualWorks**
- **Main Site**: https://www.cincomsmalltalk.com/main/products/visualworks/
- **Documentation**: Available with product
- **Image Format**: Proprietary binary format

**Pharo**
- **Main Site**: https://pharo.org
- **Documentation**: https://pharo.org/documentation
- **Image Tools**: https://github.com/pharo-project/pharo

**Smalltalk Parsers**
- **tree-sitter-smalltalk**: https://github.com/tom95/tree-sitter-smalltalk
- **SmaCC (Smalltalk Compiler Compiler)**: https://github.com/j-brant/SmaCC

**Type Inference**
- **Gradual Typing for Smalltalk**: Research papers
- **Pharo Type Checker**: https://github.com/guillep/pharo-type-checker

### Java / Spring Boot

- **Spring Boot**: https://spring.io/projects/spring-boot
- **Spring Initializr**: https://start.spring.io
- **Microservices Patterns**: https://microservices.io/patterns/
- **tree-sitter-java**: https://github.com/tree-sitter/tree-sitter-java

## AI/LLM Resources

### Anthropic Claude
- **API Documentation**: https://docs.anthropic.com/
- **Claude Models**: Sonnet, Opus, Haiku
- **Context Window**: 200k tokens
- **Function Calling**: https://docs.anthropic.com/claude/docs/tool-use

### OpenAI GPT
- **API Documentation**: https://platform.openai.com/docs/
- **GPT-4 Turbo**: Latest model
- **Function Calling**: https://platform.openai.com/docs/guides/function-calling

## Infrastructure

### Docker
- **Docker Compose**: For local development
- **Containers**:
  - Neo4j: `neo4j:latest`
  - Qdrant: `qdrant/qdrant:latest`
  - PostgreSQL: `postgres:16`

### Kubernetes
- **Helm Charts**:
  - Neo4j: https://github.com/neo4j-contrib/neo4j-helm
  - PostgreSQL: https://github.com/bitnami/charts/tree/main/bitnami/postgresql
  - Qdrant: https://github.com/qdrant/qdrant-helm

## Community Resources

### GitHub Repositories

**Similar Projects**
- **Aider**: https://github.com/paul-gauthier/aider
  - AI pair programming tool
  - Uses tree-sitter for code understanding

- **Continue.dev**: https://github.com/continuedev/continue
  - VSCode/JetBrains extension
  - Codebase indexing with embeddings

- **Sourcegraph Cody**: https://github.com/sourcegraph/cody
  - AI code assistant
  - Large-scale code search

**Code Translation Tools**
- **Code-Llama**: https://github.com/facebookresearch/codellama
- **StarCoder**: https://github.com/bigcode-project/starcoder

### Blogs and Tutorials

- **LangChain Blog**: https://blog.langchain.dev/
- **LangSmith Tutorials**: https://docs.smith.langchain.com/tutorials
- **Tree-sitter Tutorials**: https://tree-sitter.github.io/tree-sitter/

## Books

1. **"Working Effectively with Legacy Code"** by Michael Feathers
2. **"Refactoring: Improving the Design of Existing Code"** by Martin Fowler
3. **"Building Microservices"** by Sam Newman
4. **"Graph Databases"** by Ian Robinson, Jim Webber, Emil Eifrem (Neo4j)
5. **"Smalltalk Best Practice Patterns"** by Kent Beck

## Standards and Specifications

- **SCIP (Source Code Indexing Protocol)**: https://github.com/sourcegraph/scip
- **LSP (Language Server Protocol)**: https://microsoft.github.io/language-server-protocol/
- **SARIF (Static Analysis Results Interchange Format)**: https://sarifweb.azurewebsites.net/

## License Information

- **LangGraph**: MIT License
- **LangChain**: MIT License
- **Tree-sitter**: MIT License
- **Neo4j Community**: GPL v3
- **Qdrant**: Apache 2.0
- **Semgrep**: LGPL 2.1 (Community)

---

**Last Updated**: 2025-11-02
**Maintained By**: archaeocode project
**Related Documents**: See LANGGRAPH_WIREFRAME.md
