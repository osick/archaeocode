# End-to-End Workflow Roadmap

## Goal
Get a working end-to-end workflow that can:
1. Discover code files in a directory
2. Parse them with AST analysis
3. Build dependency graphs
4. Extract user stories (bonus)
5. Generate reports/output

## Current Status

### ✅ What Works
- Directory structure is clean and organized
- Graph orchestration framework is solid
- State management is well-defined
- Discovery node is fully implemented
- AST and Dependency nodes have placeholder implementations
- Configuration files exist

### ⚠️ What Needs Fixing
1. **Import paths** - Still using old paths (need `src.` prefix)
2. **No entry point** - No CLI to run the workflow
3. **No test data** - Need sample code to test with
4. **Tree-sitter not implemented** - AST parsing is stubbed out
5. **Missing nodes** - Security, RAG, Generation nodes not implemented

## Phased Approach

---

## 🎯 Phase 1: Minimal Working Example (1-2 hours)
**Goal**: Get a simple end-to-end workflow running with placeholder implementations

### Tasks
1. ✅ Fix all import paths to use `src.` prefix
2. ✅ Create CLI entry point (`run_workflow.py`)
3. ✅ Create sample test data directory with example files
4. ✅ Test basic workflow: Discovery → AST (stub) → Dependency (stub) → Report
5. ✅ Add simple output/reporting

### Success Criteria
- Can run: `python run_workflow.py --source ./sample_data --language cobol`
- Workflow completes without errors
- Outputs a summary report

---

## 🎯 Phase 2: Real AST Parsing (2-3 hours)
**Goal**: Implement actual tree-sitter parsing

### Tasks
1. Install tree-sitter language packs
2. Implement real AST parsing in `ast_node.py`
3. Extract actual entities (classes, functions, imports)
4. Calculate real complexity metrics
5. Test with real COBOL/Java files

### Success Criteria
- AST node parses real code (not placeholders)
- Extracts actual classes/functions
- Shows real complexity scores

---

## 🎯 Phase 3: User Story Extraction (2-3 hours)
**Goal**: Add user story extraction to workflow

### Tasks
1. Create `user_story_node.py`
2. Integrate user story agent from `src/orchestration/agents/user_story_agent.py`
3. Add to graph workflow
4. Configure LLM (Claude/GPT)
5. Test user story generation

### Success Criteria
- Workflow includes user story extraction
- Generates markdown user stories from code
- Stories follow INVEST format

---

## 🎯 Phase 4: Observability & Tracing (1-2 hours)
**Goal**: Add LangSmith tracing for debugging

### Tasks
1. Configure LangSmith API keys
2. Add tracing decorators
3. Setup project in LangSmith
4. Verify trace data appears

### Success Criteria
- Can view workflow traces in LangSmith UI
- Can see token usage and costs
- Can debug failures

---

## 🎯 Phase 5: MCP Server Integration (3-4 hours)
**Goal**: Implement MCP servers for tools

### Tasks
1. Implement tree-sitter MCP server
2. Implement RAG pipeline MCP server
3. Implement Neo4j graph DB MCP server
4. Update nodes to use MCP tools
5. Test integration

### Success Criteria
- AST node uses tree-sitter MCP server
- Dependency node uses Neo4j MCP server
- All nodes communicate via MCP protocol

---

## 🎯 Phase 6: Code Generation (Advanced)
**Goal**: Add code generation capability

### Tasks
1. Create `generation_node.py`
2. Implement code templates (COBOL→Java, Smalltalk→Java)
3. Add migration planning
4. Test generation

### Success Criteria
- Can generate target code from source
- Maintains business logic
- Includes tests

---

## Quick Wins (Next 30 minutes)

Let's start with Phase 1 right now:

### Immediate Actions
1. ✅ Fix import paths
2. ✅ Create `run_workflow.py` entry point
3. ✅ Create sample COBOL file in `sample_data/`
4. ✅ Run first end-to-end test

### Expected Output
```bash
$ python run_workflow.py --source ./sample_data

🚀 Starting migration workflow: abc-123
   Source: cobol -> Target: java
   Path: ./sample_data

🔍 Discovering code in: ./sample_data
✅ Discovered 3 files (250 lines)
📊 Language breakdown: {'cobol': 2, 'java': 1}

✓ Completed: discovery

🌳 Analyzing AST for 3 files...
  Progress: 0/3
✅ Parsed 3 files
📊 Found: 5 entities

✓ Completed: ast_analysis

🔗 Mapping dependencies...
  Found 8 dependency edges
📊 Dependency layers: 2
    Layer 0: 2 nodes
    Layer 1: 1 nodes

✓ Completed: dependency_mapping

============================================================
WORKFLOW COMPLETE
============================================================
Processed 3 files
Total lines: 250
Errors: 0
Warnings: 0
```

---

## Priority Order

1. **Phase 1** - Do this NOW (gets you running)
2. **Phase 2** - Do next (real parsing)
3. **Phase 3** - High value (user stories are unique)
4. **Phase 4** - Important for debugging
5. **Phase 5** - Can defer (nice architecture but not critical)
6. **Phase 6** - Advanced feature

---

## Recommended Next Step

**Start Phase 1 immediately**. I can help you:

1. Fix all import paths
2. Create `run_workflow.py`
3. Create sample test data
4. Run your first end-to-end workflow

This will give you a working foundation to build on.

Shall I proceed with Phase 1?
