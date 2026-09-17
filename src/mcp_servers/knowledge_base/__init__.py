"""
Knowledge Base MCP Server
=========================

Persistent, queryable knowledge about an analyzed legacy system, backed by
`LightRAG <https://github.com/HKUDS/LightRAG>`_ (graph + vector retrieval).

See ``knowledge_base.py`` for the adapter and ``knowledge_mcp_server.py`` for
the MCP tool surface.
"""

from .knowledge_base import (  # noqa: F401
    KnowledgeBase,
    KnowledgeBaseConfig,
    KnowledgeBaseError,
    build_custom_kg,
    is_available,
)
