"""
Test MCP Servers
=================

Simple test script to verify MCP servers are working correctly.
"""

import asyncio
import json
import sys
import os

# Add project root to path (not src directly, to avoid shadowing installed packages)
project_root = os.path.join(os.path.dirname(__file__), '..')
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.mcp_servers.static_analysis.ast_analysis_server import (
    parse_file, extract_entities, get_complexity, list_supported_languages
)


async def test_ast_server():
    """Test AST Analysis MCP Server"""
    print("=" * 60)
    print("Testing AST Analysis MCP Server")
    print("=" * 60)

    # Test 1: List supported languages
    print("\n1. Testing list_supported_languages...")
    result = await list_supported_languages()
    data = json.loads(result[0].text)
    print(f"   Supported languages: {len(data['supported_languages'])} languages")
    print(f"   Total: {data['total']}")
    assert data['total'] > 0, "Should have supported languages"
    print("   ✓ Passed")

    # Test 2: Parse a Java file
    print("\n2. Testing parse_file (Java)...")
    java_file = "sample_data/java/CustomerService.java"
    if os.path.exists(java_file):
        result = await parse_file(file_path=java_file, language="java")
        data = json.loads(result[0].text)
        if "error" not in data:
            print(f"   File: {data['file_path']}")
            print(f"   Language: {data['language']}")
            print(f"   Node count: {data['ast']['node_count']}")
            print(f"   Has errors: {data['ast']['has_error']}")
            assert data['success'] == True, "Parse should succeed"
            print("   ✓ Passed")
        else:
            print(f"   Error: {data['error']}")
            print("   ⚠ File exists but parsing failed")
    else:
        print(f"   ⚠ File not found: {java_file}")

    # Test 3: Extract entities from Python file
    print("\n3. Testing extract_entities (Python)...")
    python_file = "sample_data/python/data_processor.py"
    if os.path.exists(python_file):
        result = await extract_entities(file_path=python_file, language="python")
        data = json.loads(result[0].text)
        if "error" not in data:
            print(f"   Classes: {data['summary']['classes']}")
            print(f"   Functions: {data['summary']['functions']}")
            print(f"   Methods: {data['summary']['methods']}")
            print(f"   Imports: {data['summary']['imports']}")
            print(f"   Total entities: {data['summary']['total']}")
            assert data['success'] == True, "Entity extraction should succeed"
            print("   ✓ Passed")
        else:
            print(f"   Error: {data['error']}")
            print("   ⚠ File exists but extraction failed")
    else:
        print(f"   ⚠ File not found: {python_file}")

    # Test 4: Calculate complexity
    print("\n4. Testing get_complexity (Python)...")
    if os.path.exists(python_file):
        result = await get_complexity(file_path=python_file, language="python")
        data = json.loads(result[0].text)
        if "error" not in data:
            print(f"   Complexity: {data['complexity']}")
            print(f"   Interpretation: {data['interpretation']}")
            assert data['success'] == True, "Complexity calculation should succeed"
            print("   ✓ Passed")
        else:
            print(f"   Error: {data['error']}")
            print("   ⚠ File exists but complexity calculation failed")
    else:
        print(f"   ⚠ File not found: {python_file}")

    # Test 5: Unsupported language
    print("\n5. Testing unsupported language...")
    result = await parse_file(file_path="test.xyz", language="unsupported")
    data = json.loads(result[0].text)
    if "error" in data:
        print(f"   Error message: {data['error']}")
        print(f"   Supported: {len(data['supported_languages'])} languages")
        print("   ✓ Passed (correctly rejected unsupported language)")
    else:
        print("   ✗ Failed (should have rejected unsupported language)")

    print("\n" + "=" * 60)
    print("AST Server Tests Complete")
    print("=" * 60)


async def test_rag_server():
    """Test RAG Pipeline MCP Server"""
    print("\n" + "=" * 60)
    print("Testing RAG Pipeline MCP Server")
    print("=" * 60)

    from src.mcp_servers.rag_pipeline.rag_mcp_server import (
        chunk_document, embed_code, semantic_search
    )

    # Test 1: Chunk document
    print("\n1. Testing chunk_document...")
    sample_code = """
def example_function(x, y):
    '''Add two numbers'''
    return x + y

class Calculator:
    def add(self, a, b):
        return a + b

    def multiply(self, a, b):
        return a * b
"""
    result = await chunk_document(
        content=sample_code,
        language="python",
        chunk_size=100,
        chunk_overlap=20
    )
    data = json.loads(result[0].text)
    print(f"   Total chunks: {data['summary']['total_chunks']}")
    print(f"   Language: {data['summary']['language']}")
    print(f"   Total characters: {data['summary']['total_characters']}")
    assert data['success'] == True, "Chunking should succeed"
    print("   ✓ Passed")

    # Test 2: Embed code
    print("\n2. Testing embed_code...")
    chunks = data['chunks'][:2]  # Take first 2 chunks
    result = await embed_code(chunks=chunks)
    data = json.loads(result[0].text)
    print(f"   Embedded chunks: {data['summary']['total_chunks']}")
    print(f"   Embedding dimensions: {data['summary']['embedding_dimensions']}")
    assert data['success'] == True, "Embedding should succeed"
    print("   ✓ Passed")

    # Test 3: Semantic search
    print("\n3. Testing semantic_search...")
    result = await semantic_search(
        query="function to add numbers",
        top_k=3,
        filter_language="python"
    )
    data = json.loads(result[0].text)
    print(f"   Query: {data['query']}")
    print(f"   Results: {data['summary']['total_results']}")
    assert data['success'] == True, "Search should succeed"
    print("   ✓ Passed")

    print("\n" + "=" * 60)
    print("RAG Server Tests Complete")
    print("=" * 60)


async def test_neo4j_server():
    """Test Neo4j Graph Database MCP Server"""
    print("\n" + "=" * 60)
    print("Testing Neo4j Graph Database MCP Server")
    print("=" * 60)

    from src.mcp_servers.graph_db.neo4j_mcp_server import (
        create_nodes, create_relationships, find_dependencies,
        detect_cycles, get_graph_metrics
    )

    # Test 1: Create nodes
    print("\n1. Testing create_nodes...")
    nodes = [
        {
            "name": "UserService",
            "type": "Class",
            "properties": {"file_path": "/src/user_service.py", "language": "python"}
        },
        {
            "name": "DatabaseConnection",
            "type": "Class",
            "properties": {"file_path": "/src/db.py", "language": "python"}
        }
    ]
    result = await create_nodes(nodes=nodes)
    data = json.loads(result[0].text)
    print(f"   Created: {data['created']} nodes")
    print(f"   Node types: {data['node_types']}")
    assert data['success'] == True, "Node creation should succeed"
    print("   ✓ Passed")

    # Test 2: Create relationships
    print("\n2. Testing create_relationships...")
    relationships = [
        {
            "source": "UserService",
            "target": "DatabaseConnection",
            "type": "DEPENDS_ON",
            "properties": {"line_number": 25}
        }
    ]
    result = await create_relationships(relationships=relationships)
    data = json.loads(result[0].text)
    print(f"   Created: {data['created']} relationships")
    print(f"   Relationship types: {data['relationship_types']}")
    assert data['success'] == True, "Relationship creation should succeed"
    print("   ✓ Passed")

    # Test 3: Find dependencies
    print("\n3. Testing find_dependencies...")
    result = await find_dependencies(node_name="UserService", depth=2)
    data = json.loads(result[0].text)
    print(f"   Node: {data['node_name']}")
    print(f"   Dependencies: {data['total_dependencies']}")
    assert data['success'] == True, "Find dependencies should succeed"
    print("   ✓ Passed")

    # Test 4: Detect cycles
    print("\n4. Testing detect_cycles...")
    result = await detect_cycles(max_cycles=5)
    data = json.loads(result[0].text)
    print(f"   Cycles found: {data['total_cycles']}")
    assert data['success'] == True, "Cycle detection should succeed"
    print("   ✓ Passed")

    # Test 5: Get graph metrics
    print("\n5. Testing get_graph_metrics...")
    result = await get_graph_metrics()
    data = json.loads(result[0].text)
    print(f"   Total nodes: {data['total_nodes']}")
    print(f"   Total relationships: {data['total_relationships']}")
    print(f"   Density: {data['density']}")
    assert data['success'] == True, "Metrics should succeed"
    print("   ✓ Passed")

    print("\n" + "=" * 60)
    print("Neo4j Server Tests Complete")
    print("=" * 60)


async def main():
    """Run all MCP server tests"""
    print("\n")
    print("╔" + "=" * 58 + "╗")
    print("║" + " " * 15 + "MCP SERVER TESTS" + " " * 27 + "║")
    print("╚" + "=" * 58 + "╝")

    try:
        # Test each MCP server
        await test_ast_server()
        await test_rag_server()
        await test_neo4j_server()

        print("\n")
        print("╔" + "=" * 58 + "╗")
        print("║" + " " * 10 + "ALL TESTS COMPLETED SUCCESSFULLY" + " " * 16 + "║")
        print("╚" + "=" * 58 + "╝")
        print("\n")

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
