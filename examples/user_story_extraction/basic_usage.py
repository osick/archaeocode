"""
Basic usage example: run the full reverse-engineering workflow on the bundled
Java sample and print the extracted user stories.

Requires ANTHROPIC_API_KEY (or OPENAI_API_KEY) in your environment / .env file
for the user-story step; without a key the workflow still runs the discovery,
AST, and dependency phases.

Run from the project root:
    python examples/user_story_extraction/basic_usage.py
"""

import os
import sys

# Add project root to path
project_root = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, project_root)

from src.orchestration.graph import create_graph


def main():
    source_path = os.path.join(project_root, "sample_data", "java")

    graph = create_graph({"checkpoints": {"enabled": True}, "hitl": {"enabled": False}})

    result = graph.run(
        source_language="java",
        target_language="python",
        source_path=source_path,
    )

    print(f"\nProcessed {result['total_files']} files, {result['total_lines']} lines")
    print(f"Dependency edges: {len(result.get('dependency_graph', []))}")

    stories = result.get("user_stories", [])
    if not stories:
        print("\nNo user stories generated (is an LLM API key configured in .env?)")
        return

    print(f"\nExtracted {len(stories)} user stories:\n")
    for i, story in enumerate(stories, 1):
        print(f"{i}. {story.get('title', 'Untitled')} [{story.get('priority', 'Medium')}]")
        print(f"   As a {story.get('user_role', '?')}, I want to {story.get('capability', '?')}, "
              f"so that {story.get('benefit', '?')}\n")


if __name__ == "__main__":
    main()
