"""
archaeocode CLI
===============

Entry point for running the archaeocode analysis workflow.

Usage:
    archaeo --source ./sample_data --source-lang cobol --target-lang java
    archaeo --source ./legacy_code --source-lang smalltalk --target-lang kotlin
    archaeo --source ./legacy_code --source-lang cobol --knowledge-base --kb-wiki ./wiki
"""

import argparse
import sys
import json
from pathlib import Path
from datetime import datetime

from src.orchestration.graph import create_graph


def parse_args():
    """Parse command line arguments"""
    parser = argparse.ArgumentParser(
        description="Excavate user stories and dependency maps from legacy code"
    )

    parser.add_argument(
        "--source",
        "-s",
        required=True,
        help="Path to source code directory"
    )

    parser.add_argument(
        "--source-lang",
        "--sl",
        default="cobol",
        choices=["cobol", "smalltalk", "java", "python", "javascript", "fortran", "pascal"],
        help="Source code language (default: cobol)"
    )

    parser.add_argument(
        "--target-lang",
        "--tl",
        default="java",
        choices=["java", "kotlin", "python", "typescript"],
        help="Target language (default: java)"
    )

    parser.add_argument(
        "--workflow-id",
        "--id",
        help="Workflow ID (for resuming existing workflow)"
    )

    parser.add_argument(
        "--output",
        "-o",
        help="Output directory for generated artifacts"
    )

    parser.add_argument(
        "--report",
        "-r",
        default="workflow_report.json",
        help="Path to save workflow report (default: workflow_report.json)"
    )

    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output"
    )

    parser.add_argument(
        "--visualize",
        action="store_true",
        help="Generate workflow graph visualization"
    )

    kb = parser.add_argument_group(
        "knowledge base",
        "Persist the run into a queryable knowledge base (LightRAG GraphRAG). "
        "Query it afterwards with `archaeo-kb` or the knowledge-base MCP server."
    )
    kb.add_argument(
        "--knowledge-base",
        "--kb",
        action="store_true",
        help="Index files, entities, dependencies and user stories into the knowledge base"
    )
    kb.add_argument(
        "--kb-dir",
        help="Knowledge base directory (default: $KB_WORKING_DIR or data/knowledge_base)"
    )
    kb.add_argument(
        "--kb-workspace",
        help="Workspace name inside shared back-ends such as Neo4j (default: $KB_WORKSPACE)"
    )
    kb.add_argument(
        "--kb-extract",
        action="store_true",
        help="Also run LLM entity/relation extraction over the sources (needs an API key, costs tokens)"
    )
    kb.add_argument(
        "--kb-wiki",
        metavar="DIR",
        help="Export the knowledge graph as an Obsidian-compatible Markdown wiki into DIR"
    )
    kb.add_argument(
        "--kb-embeddings",
        choices=["sentence-transformers", "openai", "ollama", "hashing"],
        help="Embedding provider (default: $KB_EMBEDDING_PROVIDER or sentence-transformers)"
    )

    return parser.parse_args()


def save_report(state: dict, report_path: str):
    """Save workflow results to JSON report"""
    report = {
        "workflow_id": state["workflow_id"],
        "timestamp": state["timestamp"].isoformat() if isinstance(state["timestamp"], datetime) else str(state["timestamp"]),
        "source_language": state["source_language"],
        "target_language": state["target_language"],
        "source_path": state["source_path"],
        "phase": state["phase"].value if hasattr(state["phase"], 'value') else str(state["phase"]),
        "statistics": {
            "total_files": state["total_files"],
            "total_lines": state["total_lines"],
            "dependency_edges": len(state.get("dependency_graph", [])),
            "circular_dependencies": len(state.get("circular_dependencies", [])),
            "dependency_layers": len(state.get("dependency_layers", [])),
            "errors": len(state.get("errors", [])),
            "warnings": len(state.get("warnings", [])),
        },
        "language_breakdown": {},
        "errors": state.get("errors", []),
        "warnings": state.get("warnings", []),
    }

    # Calculate language breakdown
    for artifact in state.get("code_artifacts", []):
        lang = artifact["language"]
        report["language_breakdown"][lang] = report["language_breakdown"].get(lang, 0) + 1

    # Add user stories
    report["user_stories"] = state.get("user_stories", [])
    report["statistics"]["user_stories_generated"] = len(state.get("user_stories", []))

    # Knowledge base (only present when --knowledge-base was used)
    if state.get("knowledge_base"):
        report["knowledge_base"] = state["knowledge_base"]

    # Save to file
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)

    print(f"\n📄 Report saved to: {report_path}")


def print_summary(state: dict):
    """Print workflow summary"""
    print("\n" + "="*70)
    print("WORKFLOW COMPLETE")
    print("="*70)

    print(f"\n📊 Statistics:")
    print(f"   Workflow ID:       {state['workflow_id']}")
    print(f"   Source Language:   {state['source_language']}")
    print(f"   Target Language:   {state['target_language']}")
    print(f"   Files Processed:   {state['total_files']}")
    print(f"   Total Lines:       {state['total_lines']:,}")

    if state.get("dependency_graph"):
        print(f"\n🔗 Dependencies:")
        print(f"   Dependency Edges:  {len(state['dependency_graph'])}")
        print(f"   Circular Deps:     {len(state.get('circular_dependencies', []))}")
        print(f"   Dependency Layers: {len(state.get('dependency_layers', []))}")

    errors = state.get("errors", [])
    warnings = state.get("warnings", [])

    if errors:
        print(f"\n❌ Errors: {len(errors)}")
        for error in errors[:5]:
            print(f"   - {error}")
        if len(errors) > 5:
            print(f"   ... and {len(errors) - 5} more")

    if warnings:
        print(f"\n⚠️  Warnings: {len(warnings)}")
        for warning in warnings[:3]:
            print(f"   - {warning}")
        if len(warnings) > 3:
            print(f"   ... and {len(warnings) - 3} more")

    # Show user stories
    user_stories = state.get("user_stories", [])
    if user_stories:
        print(f"\n📖 User Stories: {len(user_stories)}")
        for i, story in enumerate(user_stories[:3], 1):
            print(f"   {i}. {story.get('title', 'Untitled')} ({story.get('priority', 'Medium')} priority)")
        if len(user_stories) > 3:
            print(f"   ... and {len(user_stories) - 3} more")

    kb = state.get("knowledge_base")
    if kb:
        print(f"\n🧠 Knowledge Base: {kb.get('working_dir')}")
        print(f"   Entities: {kb.get('entities')} | Relations: {kb.get('relationships')} | Chunks: {kb.get('chunks')}")
        print(f"   Storage:  {kb.get('graph_storage')} / {kb.get('vector_storage')} | LLM extraction: {kb.get('extraction')}")
        if kb.get("wiki"):
            print(f"   Wiki:     {kb['wiki'].get('output_dir')} ({kb['wiki'].get('pages')} pages)")
        print(f"   Query it: archaeo-kb --dir {kb.get('working_dir')} query \"<question>\"")

    print("\n" + "="*70 + "\n")


def main():
    """Main entry point"""
    args = parse_args()

    # Validate source path
    source_path = Path(args.source)
    if not source_path.exists():
        print(f"❌ Error: Source path does not exist: {args.source}")
        sys.exit(1)

    # Create configuration
    config = {
        "checkpoints": {"enabled": True},
        "hitl": {"enabled": False},  # Disable for now
        "verbose": args.verbose
    }

    if args.knowledge_base:
        kb_config = {"enabled": True, "extract_entities": bool(args.kb_extract)}
        if args.kb_dir:
            kb_config["working_dir"] = args.kb_dir
        if args.kb_workspace:
            kb_config["workspace"] = args.kb_workspace
        if args.kb_wiki:
            kb_config["wiki_dir"] = args.kb_wiki
        if args.kb_embeddings:
            kb_config["embedding_provider"] = args.kb_embeddings
        config["knowledge_base"] = kb_config

    try:
        # Create graph
        print("🔧 Initializing LangGraph workflow...\n")
        graph = create_graph(config)

        # Visualize if requested
        if args.visualize:
            graph.visualize()
            print()

        # Run workflow
        result = graph.run(
            source_language=args.source_lang,
            target_language=args.target_lang,
            source_path=str(source_path),
            workflow_id=args.workflow_id
        )

        # Print summary
        print_summary(result)

        # Save report
        save_report(result, args.report)

        # Exit with appropriate code
        if result.get("errors"):
            sys.exit(1)
        else:
            sys.exit(0)

    except KeyboardInterrupt:
        print("\n\n⚠️  Workflow interrupted by user")
        sys.exit(130)

    except Exception as e:
        print(f"\n\n❌ Workflow failed with error:")
        print(f"   {type(e).__name__}: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
