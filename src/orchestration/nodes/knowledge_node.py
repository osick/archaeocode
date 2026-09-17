"""
Knowledge Base Node
===================

Final workflow step: persist everything the run has learned (files, AST
entities, dependency graph, user stories) into the knowledge base so it can be
queried later — by people, by the ``archaeo-kb`` CLI, or by agents through the
knowledge-base MCP server.

The node is opt-in (``config["knowledge_base"]["enabled"]``). Deterministic
indexing needs no LLM; LLM-based entity extraction is a separate switch
(``extract_entities``) because it costs tokens proportional to the codebase.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from src.orchestration.state.graph_state import MigrationState, AnalysisPhase
from src.mcp_servers.knowledge_base.knowledge_base import (
    KnowledgeBase,
    KnowledgeBaseConfig,
    KnowledgeBaseError,
    is_available,
)


class KnowledgeBaseNode:
    """Index the workflow state into the LightRAG-backed knowledge base."""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.kb_settings: Dict[str, Any] = dict(self.config.get("knowledge_base") or {})
        self.enabled = bool(self.kb_settings.pop("enabled", False))
        self.wiki_dir: Optional[str] = self.kb_settings.pop("wiki_dir", None)
        self.kb_settings.setdefault("verbose", bool(self.config.get("verbose", False)))
        self.kb_config: Optional[KnowledgeBaseConfig] = None
        if self.enabled:
            self.kb_config = KnowledgeBaseConfig.from_env(**self.kb_settings)

    def __call__(self, state: MigrationState) -> MigrationState:
        if not self.enabled:
            return state

        print("\n🧠 Building knowledge base...")

        if not is_available():
            message = "Knowledge base requested but LightRAG is not installed (pip install lightrag-hku)"
            print(f"  ❌ {message}")
            state["errors"].append(message)
            state["phase"] = AnalysisPhase.COMPLETE
            return state

        async def _job(kb: KnowledgeBase) -> Dict[str, Any]:
            print(f"  Storage:    {kb.config.graph_storage} / {kb.config.vector_storage}")
            print(f"  Embeddings: {kb.embedding_description}")
            print(f"  LLM:        {kb.llm_description}")
            if kb.config.extract_entities and not kb.llm_available:
                print("  ⚠️  extract_entities requested but no LLM configured — deterministic indexing only")
            stats = await kb.index_state(state)
            if self.wiki_dir:
                stats["wiki"] = await kb.export_wiki(self.wiki_dir)
            return stats

        try:
            stats = KnowledgeBase.run_with(_job, self.kb_config)
            state["knowledge_base"] = stats
            print(
                f"  ✓ Indexed {stats['files']} files, {stats['chunks']} chunks, "
                f"{stats['entities']} entities, {stats['relationships']} relations "
                f"(LLM extraction: {stats['extraction']})"
            )
            if "wiki" in stats:
                print(f"  ✓ Wiki exported to {stats['wiki']['output_dir']} ({stats['wiki']['pages']} pages)")
            print(f"  📚 Knowledge base: {stats['working_dir']}")
        except KnowledgeBaseError as exc:
            state["errors"].append(f"Knowledge base failed: {exc}")
            print(f"  ❌ {exc}")
        except Exception as exc:  # keep the analysis results even if indexing dies
            state["errors"].append(f"Knowledge base failed: {type(exc).__name__}: {exc}")
            print(f"  ❌ {type(exc).__name__}: {exc}")

        state["phase"] = AnalysisPhase.COMPLETE
        return state


def knowledge_base_node(state: MigrationState, config: Optional[Dict[str, Any]] = None) -> MigrationState:
    """Function wrapper around :class:`KnowledgeBaseNode`."""
    return KnowledgeBaseNode(config)(state)
