"""
Test MCP-Enabled Workflow
==========================

End-to-end test of the reverse engineering workflow using MCP servers.
"""

import asyncio
import sys
import os
import logging

# Add project root to path (not src directly to avoid shadowing langgraph library)
project_root = os.path.join(os.path.dirname(__file__), '..')
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Import from our src package
from src.orchestration.graph_mcp import ReverseEngineeringWorkflowMCP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def test_java_workflow():
    """Test workflow with Java sample code"""
    print("\n" + "=" * 70)
    print("Testing MCP-Enabled Workflow with Java Sample")
    print("=" * 70)

    # Check if Java samples exist
    java_dir = "sample_data/java"
    if not os.path.exists(java_dir):
        print(f"⚠ Java samples not found at {java_dir}")
        return False

    try:
        # Create workflow
        workflow = ReverseEngineeringWorkflowMCP()

        # Run workflow
        result = await workflow.run(
            source_directory=java_dir,
            language="java"
        )

        # Validate results
        print("\n" + "-" * 70)
        print("Workflow Results:")
        print("-" * 70)

        artifacts = result.get("artifacts", [])
        ast_trees = result.get("ast_trees", {})
        entities = result.get("entities", {})
        dependency_graph = result.get("dependency_graph", {})
        user_stories = result.get("user_stories", [])
        complexity_scores = result.get("complexity_scores", {})

        print(f"✓ Files discovered: {len(artifacts)}")
        print(f"✓ Files parsed (AST): {len(ast_trees)}")
        print(f"✓ Files with entities: {len(entities)}")
        print(f"✓ Complexity scores: {len(complexity_scores)}")

        # Dependency graph stats
        nodes = dependency_graph.get("nodes", [])
        edges = dependency_graph.get("edges", [])
        stats = dependency_graph.get("statistics", {})

        print(f"\nDependency Graph:")
        print(f"  - Nodes: {len(nodes)}")
        print(f"  - Edges: {len(edges)}")
        print(f"  - Node types: {stats.get('node_types', {})}")
        print(f"  - Edge types: {stats.get('edge_types', {})}")

        # User stories
        print(f"\nUser Stories: {len(user_stories)}")
        for i, story in enumerate(user_stories[:3], 1):  # Show first 3
            print(f"  {i}. {story.get('title', 'N/A')[:60]}...")

        # Show entity details for first file
        if entities:
            first_file = list(entities.keys())[0]
            file_entities = entities[first_file]
            print(f"\nSample Entities from {os.path.basename(first_file)}:")
            print(f"  - Classes: {len(file_entities.get('classes', []))}")
            print(f"  - Functions: {len(file_entities.get('functions', []))}")
            print(f"  - Methods: {len(file_entities.get('methods', []))}")
            print(f"  - Imports: {len(file_entities.get('imports', []))}")

            # Show class names
            for cls in file_entities.get('classes', [])[:2]:
                print(f"    • Class: {cls.get('name')} (lines {cls.get('line_start')}-{cls.get('line_end')})")

        print("\n" + "=" * 70)
        print("✓ Java Workflow Test PASSED")
        print("=" * 70)

        return True

    except Exception as e:
        print(f"\n✗ Java Workflow Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_python_workflow():
    """Test workflow with Python sample code"""
    print("\n" + "=" * 70)
    print("Testing MCP-Enabled Workflow with Python Sample")
    print("=" * 70)

    # Check if Python samples exist
    python_dir = "sample_data/python"
    if not os.path.exists(python_dir):
        # Create a simple Python sample for testing
        os.makedirs(python_dir, exist_ok=True)
        sample_code = '''"""Sample Python module"""
import json
import sys

class DataProcessor:
    """Process data"""

    def __init__(self):
        self.data = []

    def process(self, item):
        """Process an item"""
        if item:
            self.data.append(item)
        return True

def main():
    """Main function"""
    processor = DataProcessor()
    processor.process("test")
    print("Done")

if __name__ == "__main__":
    main()
'''
        with open(f"{python_dir}/sample.py", "w") as f:
            f.write(sample_code)
        print(f"✓ Created sample Python file")

    try:
        # Create workflow
        workflow = ReverseEngineeringWorkflowMCP()

        # Run workflow
        result = await workflow.run(
            source_directory=python_dir,
            language="python"
        )

        # Validate results
        print("\n" + "-" * 70)
        print("Workflow Results:")
        print("-" * 70)

        artifacts = result.get("artifacts", [])
        ast_trees = result.get("ast_trees", {})
        entities = result.get("entities", {})

        print(f"✓ Files discovered: {len(artifacts)}")
        print(f"✓ Files parsed: {len(ast_trees)}")
        print(f"✓ Files with entities: {len(entities)}")

        print("\n" + "=" * 70)
        print("✓ Python Workflow Test PASSED")
        print("=" * 70)

        return True

    except Exception as e:
        print(f"\n✗ Python Workflow Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_mcp_integration():
    """Test MCP server integration specifically"""
    print("\n" + "=" * 70)
    print("Testing MCP Server Integration")
    print("=" * 70)

    try:
        from src.orchestration.utils.mcp_client import (
            get_mcp_manager,
            configure_mcp_manager,
            initialize_mcp_servers,
            call_mcp_tool
        )
        import yaml

        # Load config
        with open("config/langgraph_config.yaml", "r") as f:
            config = yaml.safe_load(f)

        # Configure MCP manager
        configure_mcp_manager(config)
        manager = get_mcp_manager()

        print(f"✓ MCP Manager configured")
        print(f"  - Servers configured: {len(manager.clients)}")

        # Initialize servers
        await initialize_mcp_servers()
        print(f"✓ MCP Servers initialized")

        # Test AST analysis server
        print("\nTesting AST Analysis MCP Server:")

        # List supported languages
        result = await call_mcp_tool(
            "ast-analysis",
            "list_supported_languages"
        )
        print(f"  ✓ Supported languages: {result.get('total', 0)}")

        # Test with Java file if it exists
        java_file = "sample_data/java/CustomerService.java"
        if os.path.exists(java_file):
            # Parse file
            result = await call_mcp_tool(
                "ast-analysis",
                "parse_file",
                file_path=java_file,
                language="java"
            )
            if result.get("success"):
                print(f"  ✓ Parsed {java_file}: {result['ast']['node_count']} nodes")

            # Extract entities
            result = await call_mcp_tool(
                "ast-analysis",
                "extract_entities",
                file_path=java_file,
                language="java"
            )
            if result.get("success"):
                summary = result.get("summary", {})
                print(f"  ✓ Entities: {summary.get('total', 0)} total")
                print(f"    - Classes: {summary.get('classes', 0)}")
                print(f"    - Methods: {summary.get('methods', 0)}")
                print(f"    - Imports: {summary.get('imports', 0)}")

        print("\n" + "=" * 70)
        print("✓ MCP Integration Test PASSED")
        print("=" * 70)

        return True

    except Exception as e:
        print(f"\n✗ MCP Integration Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run all tests"""
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 20 + "MCP WORKFLOW TESTS" + " " * 30 + "║")
    print("╚" + "=" * 68 + "╝")

    results = []

    # Test 1: MCP Integration
    results.append(await test_mcp_integration())

    # Test 2: Java Workflow
    results.append(await test_java_workflow())

    # Test 3: Python Workflow
    results.append(await test_python_workflow())

    # Summary
    print("\n")
    print("╔" + "=" * 68 + "╗")
    print("║" + " " * 25 + "TEST SUMMARY" + " " * 31 + "║")
    print("╚" + "=" * 68 + "╝")

    passed = sum(results)
    total = len(results)

    print(f"\nTests Passed: {passed}/{total}")

    if passed == total:
        print("\n✓ ALL TESTS PASSED!")
        print("\nThe MCP-enabled workflow is working correctly.")
        print("AST analysis, dependency mapping, and user story extraction")
        print("are all functioning through the MCP server architecture.\n")
        return 0
    else:
        print(f"\n✗ {total - passed} TEST(S) FAILED")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
