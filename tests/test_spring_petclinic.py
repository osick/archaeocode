#!/usr/bin/env python3
"""
Test Spring PetClinic Sample
=============================

Production-scale test using the Spring PetClinic sample dataset.
"""

import asyncio
import sys
import os

# Add project root to path
project_root = os.path.join(os.path.dirname(__file__), '..')
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.orchestration.graph_mcp import ReverseEngineeringWorkflowMCP


async def test_spring_petclinic():
    """Test workflow with Spring PetClinic sample (production scale)"""
    print("\n" + "=" * 80)
    print("Testing Spring PetClinic Sample (Production Scale)")
    print("=" * 80)

    # Path to Spring PetClinic Java sources
    petclinic_dir = "sample_data/spring-petclinic/src/main/java"

    if not os.path.exists(petclinic_dir):
        print(f"\n✗ Spring PetClinic sample not found at {petclinic_dir}")
        print("Please ensure the sample dataset is properly downloaded.")
        return False

    try:
        # Create workflow
        workflow = ReverseEngineeringWorkflowMCP()

        print(f"\nAnalyzing: {petclinic_dir}")
        print("-" * 80)

        # Run workflow
        result = await workflow.run(
            source_directory=petclinic_dir,
            language="java"
        )

        # Extract results
        artifacts = result.get("code_artifacts", [])
        ast_trees = result.get("ast_trees", {})
        entities = result.get("parsed_entities", {})
        dependency_graph = result.get("dependency_graph", {})
        user_stories = result.get("user_stories", [])
        quality_metrics = result.get("quality_metrics", {})
        complexity_scores = quality_metrics.get("complexity_scores", {})

        # Display summary
        print("\n" + "=" * 80)
        print("ANALYSIS RESULTS")
        print("=" * 80)

        print(f"\n📁 Files Discovered: {len(artifacts)}")
        print(f"🌲 AST Trees Parsed: {len(ast_trees)}")
        print(f"📊 Files with Entities: {len(entities)}")
        print(f"📈 Complexity Scores: {len(complexity_scores)}")

        # Count total AST nodes
        total_nodes = sum(
            tree.get("node_count", 0)
            for tree in ast_trees.values()
        )
        print(f"🔢 Total AST Nodes: {total_nodes:,}")

        # Count total entities
        total_classes = 0
        total_methods = 0
        total_imports = 0

        for file_entities in entities.values():
            total_classes += len(file_entities.get("classes", []))
            total_methods += len(file_entities.get("methods", []))
            total_imports += len(file_entities.get("imports", []))

        print(f"\n📦 Entity Statistics:")
        print(f"   - Classes: {total_classes}")
        print(f"   - Methods: {total_methods}")
        print(f"   - Imports: {total_imports}")
        print(f"   - Total Entities: {total_classes + total_methods + total_imports}")

        # Dependency graph
        nodes = dependency_graph.get("nodes", [])
        edges = dependency_graph.get("edges", [])
        stats = dependency_graph.get("statistics", {})

        print(f"\n🔗 Dependency Graph:")
        print(f"   - Nodes: {len(nodes)}")
        print(f"   - Edges: {len(edges)}")
        print(f"   - Node Types: {stats.get('node_types', {})}")
        print(f"   - Edge Types: {stats.get('edge_types', {})}")

        # User stories
        print(f"\n📖 User Stories: {len(user_stories)}")
        if user_stories:
            print("\n   Sample Stories:")
            for i, story in enumerate(user_stories[:5], 1):
                title = story.get("title", "N/A")
                print(f"   {i}. {title[:70]}...")

        # Sample file details
        if entities:
            print(f"\n📄 Sample File Analysis:")
            # Find a controller file for detailed display
            controller_files = [
                (path, ents) for path, ents in entities.items()
                if "Controller" in path
            ]

            if controller_files:
                sample_path, sample_entities = controller_files[0]
                print(f"\n   File: {os.path.basename(sample_path)}")
                print(f"   Classes: {len(sample_entities.get('classes', []))}")
                print(f"   Methods: {len(sample_entities.get('methods', []))}")

                # Show class details
                for cls in sample_entities.get("classes", [])[:2]:
                    print(f"\n   • Class: {cls.get('name')}")
                    print(f"     Lines: {cls.get('line_start')}-{cls.get('line_end')}")
                    print(f"     Annotations: {', '.join(cls.get('annotations', []))}")

        # Validation
        print("\n" + "=" * 80)
        print("VALIDATION")
        print("=" * 80)

        checks = []

        # Check 1: Files discovered
        if len(artifacts) > 25:  # Expected ~30 Java files
            checks.append("✓ Files discovered (>25)")
        else:
            checks.append(f"✗ Files discovered ({len(artifacts)} < 25)")

        # Check 2: AST nodes parsed
        if total_nodes > 8000:  # Expected ~9,800 for main/java only
            checks.append(f"✓ AST nodes parsed ({total_nodes:,} > 8,000)")
        else:
            checks.append(f"✗ AST nodes parsed ({total_nodes:,} < 8,000)")

        # Check 3: Entities extracted
        total_entities = total_classes + total_methods + total_imports
        if total_entities > 200:  # Expected ~280
            checks.append(f"✓ Entities extracted ({total_entities} > 200)")
        else:
            checks.append(f"✗ Entities extracted ({total_entities} < 200)")

        # Check 4: Dependency graph
        if len(nodes) > 50:  # Expected ~156
            checks.append(f"✓ Dependency nodes ({len(nodes)} > 50)")
        else:
            checks.append(f"✗ Dependency nodes ({len(nodes)} < 50)")

        # Display checks
        for check in checks:
            print(f"  {check}")

        # Overall result
        passed = all("✓" in check for check in checks)

        print("\n" + "=" * 80)
        if passed:
            print("✓ SPRING PETCLINIC TEST PASSED")
            print("\nProduction-scale analysis is working correctly!")
            print("The workflow successfully analyzed 3,600+ LOC with comprehensive")
            print("entity extraction, dependency mapping, and complexity analysis.")
        else:
            print("⚠ SPRING PETCLINIC TEST PARTIAL SUCCESS")
            print("\nSome validation checks failed. Review the results above.")
        print("=" * 80 + "\n")

        return passed

    except Exception as e:
        print(f"\n✗ Spring PetClinic Test FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False


async def main():
    """Run Spring PetClinic test"""
    result = await test_spring_petclinic()
    return 0 if result else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
