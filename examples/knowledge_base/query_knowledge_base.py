"""
Knowledge base example: analyze the bundled COBOL sample, persist the findings
into the LightRAG-backed knowledge base, then query it.

Runs fully offline (no API key needed) with local embeddings. With
ANTHROPIC_API_KEY (or OPENAI_API_KEY) set, the last step also asks the LLM a
question and you can pass --extract to let it mine business entities.

Run from the project root:
    python examples/knowledge_base/query_knowledge_base.py [--extract]
"""

import os
import sys

project_root = os.path.join(os.path.dirname(__file__), "..", "..")
sys.path.insert(0, project_root)

from src.orchestration.graph import create_graph  # noqa: E402
from src.mcp_servers.knowledge_base import KnowledgeBase, KnowledgeBaseConfig, KnowledgeBaseError  # noqa: E402


def main() -> None:
    extract = "--extract" in sys.argv
    kb_dir = os.path.join(project_root, "data", "knowledge_base", "example")

    graph = create_graph(
        {
            "checkpoints": {"enabled": False},
            "hitl": {"enabled": False},
            "knowledge_base": {
                "enabled": True,
                "working_dir": kb_dir,
                "extract_entities": extract,
                "wiki_dir": os.path.join(kb_dir, "wiki"),
            },
        }
    )
    result = graph.run(
        source_language="cobol",
        target_language="java",
        source_path=os.path.join(project_root, "sample_data", "cobol"),
    )
    stats = result["knowledge_base"]
    print(f"\nIndexed {stats['entities']} entities / {stats['relationships']} relations into {stats['working_dir']}")

    config = KnowledgeBaseConfig.from_env(working_dir=kb_dir)

    async def explore(kb: KnowledgeBase):
        hits = await kb.retrieve("customer payment", mode="hybrid")
        print("\nEntities matching 'customer payment':")
        for entity in hits["entities"][:5]:
            print(f"  - {entity['entity_name']} [{entity['entity_type']}]")

        neighbourhood = await kb.graph("PAYMENT.cob", max_depth=1)
        print("\nNeighbourhood of PAYMENT.cob:")
        for edge in neighbourhood["edges"]:
            print(f"  {edge['source']} —{edge['keywords']}→ {edge['target']}")

        if kb.llm_available:
            print("\nAsking the LLM...")
            print(await kb.query("What does the payment program do, and which other programs does it rely on?"))
        else:
            print("\n(no LLM key configured — skipping the natural-language answer)")

    try:
        KnowledgeBase.run_with(explore, config)
    except KnowledgeBaseError as exc:
        print(f"Knowledge base error: {exc}")

    print(f"\nWiki: {os.path.join(kb_dir, 'wiki', 'index.md')}")
    print(f"CLI:  archaeo-kb --dir {kb_dir} retrieve \"payment\"")


if __name__ == "__main__":
    main()
