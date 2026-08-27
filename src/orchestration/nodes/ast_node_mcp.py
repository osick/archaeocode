"""
AST Analysis Node (MCP-Enabled)
=================================

This is the MCP-enabled version of the AST Analysis node that uses the
AST Analysis MCP Server instead of direct tree-sitter calls.

This demonstrates the integration between LangGraph nodes and MCP servers.
"""

from typing import Any, Dict, Optional, List
from langgraph.graph import StateGraph
from langgraph.checkpoint.base import BaseCheckpointSaver
import logging
import asyncio
import os

from ..state.graph_state import MigrationState as GraphState
from ..utils.mcp_client import call_mcp_tool

logger = logging.getLogger(__name__)


class ASTAnalysisNodeMCP:
    """
    AST Analysis Node using MCP Server.

    This node delegates all AST parsing, entity extraction, and complexity
    calculation to the AST Analysis MCP Server.

    Benefits:
    - Modular: AST logic is in a separate MCP server
    - Reusable: Same MCP server can be used by other applications
    - Scalable: MCP server can run on a different machine
    - Testable: Easy to mock MCP calls for testing
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the AST Analysis Node.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        logger.info("Initialized AST Analysis Node (MCP-enabled)")

    async def __call__(self, state: GraphState) -> GraphState:
        """
        Process state through AST analysis using MCP server.

        This is the main entry point for the node.

        Args:
            state: Current graph state

        Returns:
            Updated graph state with AST analysis results
        """
        logger.info("Starting AST Analysis Node (MCP)")

        # Get discovered artifacts from MigrationState
        code_artifacts = state.get("code_artifacts", [])
        if not code_artifacts:
            logger.warning("No code_artifacts to analyze")
            return state

        logger.info(f"Analyzing {len(code_artifacts)} artifacts using MCP server")

        # Process each artifact
        ast_trees = {}
        parsed_entities = {}  # Changed from 'entities' to match MigrationState
        complexity_scores = {}

        for artifact in code_artifacts:
            file_path = artifact.get("path")
            language = artifact.get("language", "unknown")

            if language == "unknown":
                logger.warning(f"Skipping {file_path}: unknown language")
                continue

            # Parse the file using MCP
            ast_result = await self._parse_file_mcp(file_path, language)
            if ast_result:
                ast_trees[file_path] = ast_result

            # Extract entities using MCP
            entities_result = await self._extract_entities_mcp(file_path, language)
            if entities_result:
                parsed_entities[file_path] = entities_result

            # Calculate complexity using MCP
            complexity_result = await self._get_complexity_mcp(file_path, language)
            if complexity_result:
                complexity_scores[file_path] = complexity_result.get("complexity", 0.0)

        # Update state using MigrationState field names
        state["ast_trees"] = ast_trees
        state["parsed_entities"] = parsed_entities  # Using correct field name

        # Store complexity scores in quality_metrics (MigrationState field)
        quality_metrics = state.get("quality_metrics", {})
        quality_metrics["complexity_scores"] = complexity_scores
        state["quality_metrics"] = quality_metrics

        logger.info(
            f"AST Analysis complete: {len(ast_trees)} files parsed, "
            f"{len(parsed_entities)} files with entities, "
            f"{len(complexity_scores)} complexity scores"
        )

        return state

    async def _parse_file_mcp(self, file_path: str, language: str) -> Optional[Dict[str, Any]]:
        """
        Parse a file using the AST Analysis MCP Server.

        Args:
            file_path: Path to the source file
            language: Programming language

        Returns:
            Parsed AST or None if parsing failed
        """
        try:
            result = await call_mcp_tool(
                server_name="ast-analysis",
                tool_name="parse_file",
                file_path=file_path,
                language=language
            )

            if "error" in result:
                logger.error(f"MCP parse_file error for {file_path}: {result['error']}")
                return None

            if result.get("success"):
                return result.get("ast")

            return None

        except Exception as e:
            logger.error(f"Exception calling MCP parse_file for {file_path}: {e}")
            return None

    async def _extract_entities_mcp(self, file_path: str, language: str) -> Optional[Dict[str, Any]]:
        """
        Extract entities using the AST Analysis MCP Server.

        Args:
            file_path: Path to the source file
            language: Programming language

        Returns:
            Extracted entities or None if extraction failed
        """
        try:
            result = await call_mcp_tool(
                server_name="ast-analysis",
                tool_name="extract_entities",
                file_path=file_path,
                language=language
            )

            if "error" in result:
                logger.error(f"MCP extract_entities error for {file_path}: {result['error']}")
                return None

            if result.get("success"):
                return result.get("entities")

            return None

        except Exception as e:
            logger.error(f"Exception calling MCP extract_entities for {file_path}: {e}")
            return None

    async def _get_complexity_mcp(self, file_path: str, language: str) -> Optional[Dict[str, Any]]:
        """
        Calculate complexity using the AST Analysis MCP Server.

        Args:
            file_path: Path to the source file
            language: Programming language

        Returns:
            Complexity result or None if calculation failed
        """
        try:
            result = await call_mcp_tool(
                server_name="ast-analysis",
                tool_name="get_complexity",
                file_path=file_path,
                language=language
            )

            if "error" in result:
                logger.error(f"MCP get_complexity error for {file_path}: {result['error']}")
                return None

            if result.get("success"):
                return result

            return None

        except Exception as e:
            logger.error(f"Exception calling MCP get_complexity for {file_path}: {e}")
            return None


async def ast_analysis_node_mcp(state: GraphState) -> GraphState:
    """
    Async function wrapper for AST Analysis Node (MCP).

    This is the node function that gets added to the LangGraph.

    Args:
        state: Current graph state

    Returns:
        Updated graph state
    """
    node = ASTAnalysisNodeMCP()
    return await node(state)


def create_ast_analysis_node_mcp(config: Optional[Dict[str, Any]] = None):
    """
    Factory function to create an AST Analysis Node (MCP).

    Args:
        config: Optional configuration

    Returns:
        AST Analysis Node instance
    """
    return ASTAnalysisNodeMCP(config)
