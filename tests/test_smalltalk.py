#!/usr/bin/env python3
"""
Test Smalltalk Parser Integration
==================================

Tests the tree-sitter-smalltalk grammar integration with the AST MCP server.
"""

import asyncio
import sys
import os

import pytest

# Add project root to path
project_root = os.path.join(os.path.dirname(__file__), '..')
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.mcp_servers.static_analysis import custom_languages


def test_smalltalk_parser():
    """Test basic Smalltalk parsing"""
    print("\n" + "=" * 80)
    print("Testing Smalltalk Parser")
    print("=" * 80)

    # Check availability
    available = custom_languages.list_available()
    print(f"\nAvailable custom languages: {available}")

    if 'smalltalk' not in available:
        pytest.skip("Smalltalk grammar not built (run: python scripts/build_smalltalk_grammar.py)")

    # Test parser loading
    parser = custom_languages.get_parser('smalltalk')
    if not parser:
        print("✗ Failed to load Smalltalk parser")
        return False

    print("✓ Smalltalk parser loaded")

    # Test parsing Counter.st
    counter_file = "sample_data/smalltalk/Counter.st"
    if not os.path.exists(counter_file):
        print(f"✗ Sample file not found: {counter_file}")
        return False

    with open(counter_file, 'rb') as f:
        code = f.read()

    tree = parser.parse(code)
    root = tree.root_node

    print(f"\n✓ Parsed {counter_file}")
    print(f"  Root type: {root.type}")
    print(f"  Byte range: {root.start_byte}-{root.end_byte}")
    print(f"  Has errors: {root.has_error}")

    # Count nodes
    def count_nodes(node):
        count = 1
        for child in node.children:
            count += count_nodes(child)
        return count

    total = count_nodes(root)
    print(f"  Total nodes: {total}")

    # Count specific node types
    def count_types(node, type_name):
        count = 1 if node.type == type_name else 0
        for child in node.children:
            count += count_types(child, type_name)
        return count

    methods = count_types(root, "method")
    blocks = count_types(root, "block")
    messages = sum(count_types(root, t) for t in ["unary_message", "binary_message", "keyword_message"])

    print(f"\n  Methods: {methods}")
    print(f"  Blocks: {blocks}")
    print(f"  Message sends: {messages}")

    # Test BankAccount.st
    bank_file = "sample_data/smalltalk/BankAccount.st"
    if os.path.exists(bank_file):
        with open(bank_file, 'rb') as f:
            code = f.read()

        tree = parser.parse(code)
        root = tree.root_node

        print(f"\n✓ Parsed {bank_file}")
        print(f"  Total nodes: {count_nodes(root)}")
        print(f"  Methods: {count_types(root, 'method')}")
        print(f"  Blocks: {count_types(root, 'block')}")

    print("\n" + "=" * 80)
    print("✓ SMALLTALK PARSER TEST PASSED")
    print("=" * 80)

    return True


def test_entity_extraction():
    """Test entity extraction from Smalltalk code"""
    print("\n" + "=" * 80)
    print("Testing Smalltalk Entity Extraction")
    print("=" * 80)

    from src.mcp_servers.static_analysis.ast_analysis_server import (
        extract_smalltalk_entities,
        get_parser
    )

    if 'smalltalk' not in custom_languages.list_available():
        pytest.skip("Smalltalk grammar not built (run: python scripts/build_smalltalk_grammar.py)")

    # Parse Counter.st
    counter_file = "sample_data/smalltalk/Counter.st"
    with open(counter_file, 'rb') as f:
        code = f.read()

    parser = get_parser('smalltalk')
    tree = parser.parse(code)
    root = tree.root_node

    # Extract entities
    entities = {
        "classes": [],
        "functions": [],
        "methods": [],
        "imports": []
    }

    extract_smalltalk_entities(root, entities, is_cincom=False)

    print(f"\nExtracted from {counter_file}:")
    print(f"  Classes: {len(entities['classes'])}")
    for cls in entities['classes']:
        print(f"    - {cls['name']} (line {cls['line_start']}-{cls['line_end']})")

    print(f"  Methods: {len(entities['methods'])}")
    for method in entities['methods'][:5]:
        print(f"    - {method['name']} (line {method['line_start']}-{method['line_end']})")
    if len(entities['methods']) > 5:
        print(f"    ... and {len(entities['methods']) - 5} more")

    print(f"  Blocks: {len(entities.get('blocks', []))}")

    # Test Cincom variant
    print(f"\n--- Testing Cincom variant ---")
    bank_file = "sample_data/smalltalk/BankAccount.st"
    if os.path.exists(bank_file):
        with open(bank_file, 'rb') as f:
            code = f.read()

        parser = get_parser('smalltalk-cincom')
        tree = parser.parse(code)
        root = tree.root_node

        entities_cincom = {
            "classes": [],
            "functions": [],
            "methods": [],
            "imports": []
        }

        extract_smalltalk_entities(root, entities_cincom, is_cincom=True)

        print(f"\nExtracted from {bank_file} (Cincom mode):")
        print(f"  Classes: {len(entities_cincom['classes'])}")
        print(f"  Methods: {len(entities_cincom['methods'])}")
        print(f"  Imports/References: {len(entities_cincom['imports'])}")
        print(f"  Blocks: {len(entities_cincom.get('blocks', []))}")

    print("\n" + "=" * 80)
    print("✓ ENTITY EXTRACTION TEST PASSED")
    print("=" * 80)

    return True


def main():
    """Run all Smalltalk tests"""
    print("\nSmall Talk Parser Integration Tests")
    print("Reverse Engineering with MCP & Tree-Sitter")

    try:
        if not test_smalltalk_parser():
            return 1

        if not test_entity_extraction():
            return 1

        print("\n" + "=" * 80)
        print("✓ ALL SMALLTALK TESTS PASSED")
        print("=" * 80)
        print("\nNext steps:")
        print("1. Test with your own Smalltalk code")
        print("2. Integrate into the full workflow")
        print("3. Use with LangGraph Studio for visual debugging")

        return 0

    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
