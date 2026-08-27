"""
MCP Client Integration Layer
==============================

This module provides a client wrapper for calling MCP servers from within LangGraph nodes.

It allows nodes to invoke MCP tools asynchronously and handle responses properly.
"""

import asyncio
import json
import subprocess
from typing import Any, Optional, Dict, List
from dataclasses import dataclass
import os
import logging

logger = logging.getLogger(__name__)


@dataclass
class MCPServerConfig:
    """Configuration for an MCP server"""
    name: str
    command: str
    args: List[str]
    enabled: bool = True


class MCPClient:
    """
    Client for communicating with MCP servers.

    This client can:
    - Start MCP servers as subprocesses
    - Send tool call requests via stdio
    - Receive and parse responses
    - Handle multiple concurrent servers
    """

    def __init__(self, server_config: MCPServerConfig):
        """
        Initialize MCP client for a specific server.

        Args:
            server_config: Server configuration
        """
        self.config = server_config
        self.process: Optional[subprocess.Popen] = None
        self.request_id = 0

    async def start(self):
        """Start the MCP server subprocess"""
        if not self.config.enabled:
            logger.warning(f"MCP server {self.config.name} is disabled")
            return

        try:
            # For now, we'll use direct imports instead of subprocess
            # This is more efficient for servers running in the same process
            logger.info(f"MCP server {self.config.name} ready (in-process mode)")
        except Exception as e:
            logger.error(f"Failed to start MCP server {self.config.name}: {e}")
            raise

    async def stop(self):
        """Stop the MCP server subprocess"""
        if self.process:
            self.process.terminate()
            self.process.wait()
            self.process = None

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call an MCP tool and return the result.

        Args:
            tool_name: Name of the tool to call
            arguments: Tool arguments as a dictionary

        Returns:
            Tool response as a dictionary
        """
        if not self.config.enabled:
            return {"error": f"MCP server {self.config.name} is disabled"}

        try:
            # Import the appropriate server module based on config
            result = await self._invoke_tool_direct(tool_name, arguments)
            return result
        except Exception as e:
            logger.error(f"Error calling MCP tool {tool_name}: {e}")
            return {"error": str(e)}

    async def _invoke_tool_direct(self, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Invoke an MCP tool directly by importing the server module.

        This is more efficient than subprocess communication for servers
        running in the same Python process.
        """
        # Import based on server name
        if self.config.name == "ast-analysis":
            from src.mcp_servers.static_analysis.ast_analysis_server import (
                parse_file, extract_entities, get_complexity, list_supported_languages
            )

            tool_map = {
                "parse_file": parse_file,
                "extract_entities": extract_entities,
                "get_complexity": get_complexity,
                "list_supported_languages": list_supported_languages
            }

        elif self.config.name == "rag-pipeline":
            from src.mcp_servers.rag_pipeline.rag_mcp_server import (
                chunk_document, embed_code, index_codebase, semantic_search, get_collection_stats
            )

            tool_map = {
                "chunk_document": chunk_document,
                "embed_code": embed_code,
                "index_codebase": index_codebase,
                "semantic_search": semantic_search,
                "get_collection_stats": get_collection_stats
            }

        elif self.config.name == "neo4j-graph":
            from src.mcp_servers.graph_db.neo4j_mcp_server import (
                create_nodes, create_relationships, query_graph,
                find_dependencies, find_dependents, shortest_path,
                detect_cycles, get_graph_metrics, clear_graph
            )

            tool_map = {
                "create_nodes": create_nodes,
                "create_relationships": create_relationships,
                "query_graph": query_graph,
                "find_dependencies": find_dependencies,
                "find_dependents": find_dependents,
                "shortest_path": shortest_path,
                "detect_cycles": detect_cycles,
                "get_graph_metrics": get_graph_metrics,
                "clear_graph": clear_graph
            }
        else:
            raise ValueError(f"Unknown MCP server: {self.config.name}")

        # Get the tool function
        if tool_name not in tool_map:
            raise ValueError(f"Unknown tool: {tool_name} for server {self.config.name}")

        tool_func = tool_map[tool_name]

        # Call the tool with unpacked arguments
        result = await tool_func(**arguments)

        # Parse the result (MCP tools return list[TextContent])
        if result and len(result) > 0:
            text_content = result[0].text
            return json.loads(text_content)

        return {"error": "No response from tool"}


class MCPClientManager:
    """
    Manager for multiple MCP clients.

    This allows nodes to access different MCP servers through a unified interface.
    """

    def __init__(self):
        """Initialize the MCP client manager"""
        self.clients: Dict[str, MCPClient] = {}
        self._initialized = False

    def configure_from_dict(self, config: Dict[str, Any]):
        """
        Configure MCP servers from a dictionary.

        Args:
            config: Configuration dictionary with server definitions
        """
        mcp_config = config.get("mcp_servers", {})

        for server_name, server_info in mcp_config.items():
            if server_info.get("enabled", True):
                server_config = MCPServerConfig(
                    name=server_name,
                    command=server_info.get("command", "python"),
                    args=server_info.get("args", []),
                    enabled=server_info.get("enabled", True)
                )
                self.clients[server_name] = MCPClient(server_config)

    async def initialize(self):
        """Initialize all configured MCP servers"""
        if self._initialized:
            return

        for client in self.clients.values():
            await client.start()

        self._initialized = True
        logger.info(f"Initialized {len(self.clients)} MCP servers")

    async def shutdown(self):
        """Shutdown all MCP servers"""
        for client in self.clients.values():
            await client.stop()

        self._initialized = False
        logger.info("Shutdown all MCP servers")

    def get_client(self, server_name: str) -> Optional[MCPClient]:
        """
        Get an MCP client by server name.

        Args:
            server_name: Name of the server

        Returns:
            MCPClient instance or None if not found
        """
        return self.clients.get(server_name)

    async def call_tool(self, server_name: str, tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
        """
        Call an MCP tool on a specific server.

        Args:
            server_name: Name of the MCP server
            tool_name: Name of the tool to call
            arguments: Tool arguments

        Returns:
            Tool response as a dictionary
        """
        client = self.get_client(server_name)
        if not client:
            return {"error": f"MCP server not found: {server_name}"}

        return await client.call_tool(tool_name, arguments)


# Global MCP client manager instance
_mcp_manager: Optional[MCPClientManager] = None


def get_mcp_manager() -> MCPClientManager:
    """
    Get the global MCP client manager instance.

    Returns:
        Global MCPClientManager instance
    """
    global _mcp_manager
    if _mcp_manager is None:
        _mcp_manager = MCPClientManager()
    return _mcp_manager


def configure_mcp_manager(config: Dict[str, Any]):
    """
    Configure the global MCP manager from a configuration dictionary.

    Args:
        config: Configuration dictionary
    """
    manager = get_mcp_manager()
    manager.configure_from_dict(config)


async def initialize_mcp_servers():
    """Initialize all configured MCP servers"""
    manager = get_mcp_manager()
    await manager.initialize()


async def shutdown_mcp_servers():
    """Shutdown all MCP servers"""
    manager = get_mcp_manager()
    await manager.shutdown()


async def call_mcp_tool(server_name: str, tool_name: str, **kwargs) -> Dict[str, Any]:
    """
    Convenience function to call an MCP tool.

    Args:
        server_name: Name of the MCP server
        tool_name: Name of the tool to call
        **kwargs: Tool arguments

    Returns:
        Tool response as a dictionary

    Example:
        result = await call_mcp_tool(
            "ast-analysis",
            "parse_file",
            file_path="/path/to/file.py",
            language="python"
        )
    """
    manager = get_mcp_manager()

    # Initialize if not already initialized
    if not manager._initialized:
        await manager.initialize()

    return await manager.call_tool(server_name, tool_name, kwargs)
