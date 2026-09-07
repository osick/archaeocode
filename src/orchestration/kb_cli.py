"""
archaeo-kb — query the knowledge base
=====================================

Companion CLI to ``archaeo``. After a run with ``--knowledge-base`` the
knowledge base lives on disk (or in Neo4j/Postgres/...); this tool asks it
questions, inspects the graph, adds documents, and exports a wiki.

Usage:
    archaeo-kb query "Which programs update the customer master file?"
    archaeo-kb retrieve "PAYMENT" --mode local --json
    archaeo-kb graph "CUSTMGMT.cob" --depth 2
    archaeo-kb stats
    archaeo-kb add docs/runbook.md docs/interview-notes.md
    archaeo-kb wiki ./wiki
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict

from src.mcp_servers.knowledge_base.knowledge_base import (
    QUERY_MODES,
    KnowledgeBase,
    KnowledgeBaseConfig,
    KnowledgeBaseError,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="archaeo-kb", description="Query the archaeocode knowledge base")
    parser.add_argument("--dir", "-d", help="Knowledge base directory (default: $KB_WORKING_DIR or data/knowledge_base)")
    parser.add_argument("--workspace", "-w", help="Workspace inside shared back-ends (default: $KB_WORKSPACE)")
    parser.add_argument("--embeddings", choices=["sentence-transformers", "openai", "ollama", "hashing"],
                        help="Embedding provider (must match the one used for indexing)")
    parser.add_argument("--llm", choices=["auto", "anthropic", "openai", "ollama", "none"], help="LLM provider")
    parser.add_argument("--json", action="store_true", help="Print raw JSON")
    parser.add_argument("--verbose", "-v", action="store_true")

    sub = parser.add_subparsers(dest="command", required=True)

    q = sub.add_parser("query", help="Ask a question (needs an LLM)")
    q.add_argument("question")
    q.add_argument("--mode", choices=QUERY_MODES)
    q.add_argument("--response-type", default="Multiple Paragraphs")

    r = sub.add_parser("retrieve", help="Structured retrieval without an LLM")
    r.add_argument("question")
    r.add_argument("--mode", choices=QUERY_MODES)
    r.add_argument("--top-k", type=int)
    r.add_argument("--chunk-top-k", type=int)

    c = sub.add_parser("context", help="Print the prompt-ready context for a question")
    c.add_argument("question")
    c.add_argument("--mode", choices=QUERY_MODES)

    g = sub.add_parser("graph", help="Show the neighbourhood of an entity")
    g.add_argument("label", nargs="?", default="*")
    g.add_argument("--depth", type=int, default=2)
    g.add_argument("--max-nodes", type=int)

    sub.add_parser("stats", help="Knowledge base statistics")

    a = sub.add_parser("add", help="Add documents (markdown, text, ...)")
    a.add_argument("files", nargs="+")
    a.add_argument("--extract", action="store_true", help="Run LLM entity extraction on the documents")

    w = sub.add_parser("wiki", help="Export an Obsidian-compatible Markdown wiki")
    w.add_argument("output_dir")
    w.add_argument("--max-nodes", type=int)

    return parser


def _config_from_args(args: argparse.Namespace) -> KnowledgeBaseConfig:
    return KnowledgeBaseConfig.from_env(
        working_dir=args.dir,
        workspace=args.workspace,
        embedding_provider=args.embeddings,
        llm_provider=args.llm,
        verbose=True if args.verbose else None,
    )


def _print_retrieval(result: Dict[str, Any]) -> None:
    print(f"\n🔎 {result['question']}  (mode: {result['mode']})")
    entities = result.get("entities", [])
    if entities:
        print(f"\nEntities ({len(entities)}):")
        for entity in entities[:20]:
            print(f"  - {entity.get('entity_name')} [{entity.get('entity_type')}]: {str(entity.get('description', ''))[:120]}")
    relations = result.get("relationships", [])
    if relations:
        print(f"\nRelations ({len(relations)}):")
        for rel in relations[:20]:
            print(f"  - {rel.get('src_id')} —{rel.get('keywords', '')}→ {rel.get('tgt_id')}")
    chunks = result.get("chunks", [])
    if chunks:
        print(f"\nChunks ({len(chunks)}):")
        for chunk in chunks[:10]:
            first_line = str(chunk.get("content", "")).strip().splitlines()[:1]
            print(f"  - {chunk.get('file_path')}: {first_line[0] if first_line else ''}")
    if not (entities or relations or chunks):
        print("  (nothing found)")


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = _config_from_args(args)
    except KnowledgeBaseError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 2

    async def run(kb: KnowledgeBase) -> Any:
        if args.command == "query":
            return {"question": args.question, "answer": await kb.query(args.question, mode=args.mode, response_type=args.response_type)}
        if args.command == "retrieve":
            return await kb.retrieve(args.question, mode=args.mode, top_k=args.top_k, chunk_top_k=args.chunk_top_k)
        if args.command == "context":
            return {"question": args.question, "context": await kb.context(args.question, mode=args.mode)}
        if args.command == "graph":
            return await kb.graph(args.label, max_depth=args.depth, max_nodes=args.max_nodes)
        if args.command == "stats":
            return await kb.stats()
        if args.command == "add":
            documents = []
            for file_name in args.files:
                path = Path(file_name)
                documents.append({"path": str(path), "content": path.read_text(encoding="utf-8", errors="ignore")})
            return await kb.add_documents(documents, extract=args.extract or None)
        if args.command == "wiki":
            return await kb.export_wiki(args.output_dir, max_nodes=args.max_nodes)
        raise KnowledgeBaseError(f"Unknown command {args.command}")

    try:
        result = KnowledgeBase.run_with(run, config)
    except KnowledgeBaseError as exc:
        print(f"❌ {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        return 130

    if args.json:
        print(json.dumps(result, indent=2, default=str))
        return 0

    if args.command == "query":
        print(f"\n❓ {result['question']}\n")
        print(result["answer"])
    elif args.command == "retrieve":
        _print_retrieval(result)
    elif args.command == "context":
        print(result["context"])
    elif args.command == "graph":
        print(f"\n🕸️  {result['label']}: {len(result['nodes'])} nodes, {len(result['edges'])} edges"
              + (" (truncated)" if result.get("is_truncated") else ""))
        for node in result["nodes"][:50]:
            print(f"  • {node['id']} [{node.get('entity_type', '?')}]")
        for edge in result["edges"][:50]:
            print(f"  {edge['source']} —{edge.get('keywords', '')}→ {edge['target']}")
    elif args.command == "stats":
        print("\n📚 Knowledge base")
        for key, value in result.items():
            print(f"  {key:16} {value}")
    elif args.command == "add":
        print(f"\n✓ Added {result.get('documents', 0)} document(s) ({result.get('mode')})")
    elif args.command == "wiki":
        print(f"\n✓ Wiki written to {result['output_dir']}: {result['pages']} pages, {result['relations']} relations")
        print(f"  Open {result['index']} (Obsidian-compatible)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
