"""
Knowledge Base MCP Server
=========================

Exposes the archaeocode knowledge base (LightRAG-backed GraphRAG) as MCP tools,
so any MCP-capable agent — Claude Desktop, Claude Code, an IDE, or the
archaeocode workflow itself — can ask questions about an analyzed legacy
system, walk its knowledge graph, add documents, and export a Markdown wiki.

Tools:
- kb_query          natural-language question → LLM-synthesized answer with citations
- kb_retrieve       structured retrieval (entities, relations, chunks) without an LLM
- kb_context        the prompt-ready context block for a question
- kb_graph          neighbourhood of an entity (or the whole graph)
- kb_stats          size and configuration of the knowledge base
- kb_add_documents  ingest additional documents (design docs, tickets, runbooks)
- kb_export_wiki    write an Obsidian-compatible Markdown wiki

Run standalone (stdio transport):
    python src/mcp_servers/knowledge_base/knowledge_mcp_server.py
"""

from __future__ import annotations

import asyncio
import json
import os
import sys
from typing import Any, Optional

try:  # mcp >= 2.0
    from mcp.server import MCPServer
except ImportError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP as MCPServer
from mcp import types

# Allow running the server file directly from a source checkout
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

from src.mcp_servers.knowledge_base.knowledge_base import (  # noqa: E402
    KnowledgeBase,
    KnowledgeBaseConfig,
    KnowledgeBaseError,
)

server = MCPServer("knowledge-base")

# One knowledge base per (working_dir, workspace, event loop). LightRAG binds
# its storages to the loop that opened them, so a different loop gets a fresh
# instance.
_instances: dict[tuple, KnowledgeBase] = {}


async def get_knowledge_base(working_dir: Optional[str] = None, workspace: Optional[str] = None) -> KnowledgeBase:
    """Return an initialized knowledge base for the given location (cached)."""
    config = KnowledgeBaseConfig.from_env(working_dir=working_dir, workspace=workspace)
    key = (config.working_dir, config.workspace, id(asyncio.get_running_loop()))
    kb = _instances.get(key)
    if kb is None:
        kb = KnowledgeBase(config)
        await kb.initialize()
        _instances[key] = kb
    return kb


def _ok(payload: dict[str, Any]) -> list[types.TextContent]:
    payload.setdefault("success", True)
    return [types.TextContent(type="text", text=json.dumps(payload, indent=2, default=str))]


def _fail(exc: Exception, **context: Any) -> list[types.TextContent]:
    payload = {"success": False, "error": f"{type(exc).__name__}: {exc}", **context}
    return [types.TextContent(type="text", text=json.dumps(payload, indent=2, default=str))]


@server.tool()
async def kb_query(
    question: str,
    mode: Optional[str] = None,
    response_type: Optional[str] = None,
    working_dir: Optional[str] = None,
    workspace: Optional[str] = None,
) -> list[types.TextContent]:
    """
    Ask the knowledge base a question and get an LLM-synthesized answer.

    Args:
        question: Natural-language question about the analyzed system
        mode: Retrieval mode — local (entity-centric), global (relation/theme-centric),
              hybrid, naive (chunks only) or mix (graph + chunks; default)
        response_type: Free-text answer format hint, e.g. "Bullet Points", "Single Paragraph"
        working_dir: Knowledge base directory (default: KB_WORKING_DIR or data/knowledge_base)
        workspace: Logical partition inside shared back-ends (default: KB_WORKSPACE)

    Returns:
        The answer text plus the retrieval mode used
    """
    try:
        kb = await get_knowledge_base(working_dir, workspace)
        answer = await kb.query(question, mode=mode, response_type=response_type or "Multiple Paragraphs")
        return _ok({"question": question, "mode": mode or kb.config.default_query_mode, "answer": answer})
    except Exception as exc:
        return _fail(exc, question=question)


@server.tool()
async def kb_retrieve(
    question: str,
    mode: Optional[str] = None,
    top_k: Optional[int] = None,
    chunk_top_k: Optional[int] = None,
    working_dir: Optional[str] = None,
    workspace: Optional[str] = None,
) -> list[types.TextContent]:
    """
    Structured retrieval without answer synthesis (no LLM required).

    Args:
        question: Search query (natural language, identifier, file name, ...)
        mode: local / global / hybrid / naive / mix (default from config)
        top_k: Maximum entities/relations to retrieve
        chunk_top_k: Maximum text chunks to retrieve
        working_dir: Knowledge base directory
        workspace: Logical partition inside shared back-ends

    Returns:
        Matching entities, relationships, text chunks and references
    """
    try:
        kb = await get_knowledge_base(working_dir, workspace)
        result = await kb.retrieve(question, mode=mode, top_k=top_k, chunk_top_k=chunk_top_k)
        return _ok(result)
    except Exception as exc:
        return _fail(exc, question=question)


@server.tool()
async def kb_context(
    question: str,
    mode: Optional[str] = None,
    working_dir: Optional[str] = None,
    workspace: Optional[str] = None,
) -> list[types.TextContent]:
    """
    Return the prompt-ready context block the knowledge base would give an LLM.

    Useful for agents that want to reason over the evidence themselves.
    """
    try:
        kb = await get_knowledge_base(working_dir, workspace)
        context = await kb.context(question, mode=mode)
        return _ok({"question": question, "mode": mode or kb.config.default_query_mode, "context": context})
    except Exception as exc:
        return _fail(exc, question=question)


@server.tool()
async def kb_graph(
    label: str = "*",
    max_depth: int = 2,
    max_nodes: Optional[int] = None,
    working_dir: Optional[str] = None,
    workspace: Optional[str] = None,
) -> list[types.TextContent]:
    """
    Get the neighbourhood of an entity in the knowledge graph.

    Args:
        label: Entity name (file path, "path::Function", "Story: ...") or "*" for everything
        max_depth: Traversal depth from the entity
        max_nodes: Cap on returned nodes
    """
    try:
        kb = await get_knowledge_base(working_dir, workspace)
        return _ok(await kb.graph(label, max_depth=max_depth, max_nodes=max_nodes))
    except Exception as exc:
        return _fail(exc, label=label)


@server.tool()
async def kb_stats(
    working_dir: Optional[str] = None,
    workspace: Optional[str] = None,
) -> list[types.TextContent]:
    """Size, entity-type breakdown and configuration of the knowledge base."""
    try:
        kb = await get_knowledge_base(working_dir, workspace)
        return _ok(await kb.stats())
    except Exception as exc:
        return _fail(exc)


@server.tool()
async def kb_add_documents(
    documents: list[dict[str, Any]],
    extract: Optional[bool] = None,
    working_dir: Optional[str] = None,
    workspace: Optional[str] = None,
) -> list[types.TextContent]:
    """
    Add documents (design docs, tickets, runbooks, interview notes) to the knowledge base.

    Args:
        documents: List of {"path": str, "content": str} objects
        extract: Run LLM entity/relation extraction (needs an LLM); default from config
    """
    try:
        kb = await get_knowledge_base(working_dir, workspace)
        return _ok(await kb.add_documents(documents, extract=extract))
    except Exception as exc:
        return _fail(exc)


@server.tool()
async def kb_export_wiki(
    output_dir: str,
    max_nodes: Optional[int] = None,
    working_dir: Optional[str] = None,
    workspace: Optional[str] = None,
) -> list[types.TextContent]:
    """
    Export the knowledge graph as an Obsidian-compatible Markdown wiki.

    Args:
        output_dir: Directory to write index.md and entities/*.md into
        max_nodes: Cap on exported entities
    """
    try:
        kb = await get_knowledge_base(working_dir, workspace)
        return _ok(await kb.export_wiki(output_dir, max_nodes=max_nodes))
    except Exception as exc:
        return _fail(exc, output_dir=output_dir)


if __name__ == "__main__":
    try:
        server.run()
    except KnowledgeBaseError as exc:  # pragma: no cover
        print(f"Knowledge base error: {exc}", file=sys.stderr)
        sys.exit(1)
