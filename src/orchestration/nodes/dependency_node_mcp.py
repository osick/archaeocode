"""
Dependency Mapping Node (MCP-Enabled)
=======================================

This node creates a dependency graph by analyzing imports, calls,
and references between code entities.

It can optionally use the Neo4j Graph MCP Server for persistence and
advanced graph queries.
"""

from typing import Any, Dict, Optional, List, Set
from langgraph.graph import StateGraph
import logging
import re

from ..state.graph_state import MigrationState as GraphState
from ..utils.mcp_client import call_mcp_tool

logger = logging.getLogger(__name__)


class DependencyMappingNodeMCP:
    """
    Dependency Mapping Node with optional MCP Graph integration.

    This node:
    1. Analyzes entities from AST analysis
    2. Identifies dependencies (imports, calls, references)
    3. Optionally stores in Neo4j via MCP server (if enabled)
    4. Creates in-memory dependency graph

    When Neo4j MCP is enabled:
    - Persists nodes and relationships to Neo4j
    - Can perform advanced graph queries
    - Can detect cycles and calculate metrics
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the Dependency Mapping Node.

        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.use_neo4j_mcp = self.config.get("use_neo4j_mcp", False)
        logger.info(f"Initialized Dependency Mapping Node (MCP mode: {self.use_neo4j_mcp})")

    async def __call__(self, state: GraphState) -> GraphState:
        """
        Process state through dependency mapping.

        Args:
            state: Current graph state

        Returns:
            Updated graph state with dependency information
        """
        logger.info("Starting Dependency Mapping Node (MCP)")

        # Get parsed_entities from AST analysis (MigrationState field)
        parsed_entities = state.get("parsed_entities", {})
        if not parsed_entities:
            logger.warning("No parsed_entities to analyze for dependencies")
            return state

        logger.info(f"Mapping dependencies for {len(parsed_entities)} files")

        # Build dependency graph
        dependency_graph = await self._build_dependency_graph(parsed_entities)

        # Optionally persist to Neo4j via MCP
        if self.use_neo4j_mcp:
            await self._persist_to_neo4j(dependency_graph)

        # Update state
        state["dependency_graph"] = dependency_graph

        # Calculate statistics
        total_nodes = len(dependency_graph.get("nodes", []))
        total_edges = len(dependency_graph.get("edges", []))
        logger.info(f"Dependency graph: {total_nodes} nodes, {total_edges} edges")

        return state

    async def _build_dependency_graph(self, entities: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build an in-memory dependency graph from entities.

        Args:
            entities: Dictionary of file_path -> entities

        Returns:
            Dependency graph with nodes and edges
        """
        nodes = []
        edges = []
        node_set = set()

        for file_path, file_entities in entities.items():
            # Extract classes, functions, methods
            classes = file_entities.get("classes", [])
            functions = file_entities.get("functions", [])
            methods = file_entities.get("methods", [])
            imports = file_entities.get("imports", [])

            # Create nodes for classes
            for cls in classes:
                node_name = cls.get("name")
                if node_name and node_name not in node_set:
                    nodes.append({
                        "name": node_name,
                        "type": "Class",
                        "file_path": file_path,
                        "line_start": cls.get("line_start"),
                        "line_end": cls.get("line_end")
                    })
                    node_set.add(node_name)

            # Create nodes for functions
            for func in functions:
                node_name = func.get("name")
                if node_name and node_name not in node_set:
                    nodes.append({
                        "name": node_name,
                        "type": "Function",
                        "file_path": file_path,
                        "line_start": func.get("line_start"),
                        "line_end": func.get("line_end")
                    })
                    node_set.add(node_name)

            # Create nodes for methods
            for method in methods:
                node_name = method.get("name")
                if node_name and node_name not in node_set:
                    nodes.append({
                        "name": node_name,
                        "type": "Method",
                        "file_path": file_path,
                        "line_start": method.get("line_start"),
                        "line_end": method.get("line_end")
                    })
                    node_set.add(node_name)

            # Create edges from imports
            for import_stmt in imports:
                statement = import_stmt.get("statement", "")
                source = self._extract_file_identifier(file_path)

                # Extract imported modules/classes
                imported = self._parse_import_statement(statement)
                for target in imported:
                    if target and source:
                        edges.append({
                            "source": source,
                            "target": target,
                            "type": "IMPORTS",
                            "file_path": file_path,
                            "line": import_stmt.get("line")
                        })

        # Analyze call relationships (simplified)
        # In a full implementation, this would parse method bodies for calls
        # For now, we'll create sample relationships based on common patterns

        return {
            "nodes": nodes,
            "edges": edges,
            "statistics": {
                "total_nodes": len(nodes),
                "total_edges": len(edges),
                "node_types": self._count_node_types(nodes),
                "edge_types": self._count_edge_types(edges)
            }
        }

    def _extract_file_identifier(self, file_path: str) -> str:
        """
        Extract a simple identifier from a file path.

        Args:
            file_path: Full file path

        Returns:
            File identifier (e.g., filename without extension)
        """
        import os
        basename = os.path.basename(file_path)
        name, _ = os.path.splitext(basename)
        return name

    def _parse_import_statement(self, statement: str) -> List[str]:
        """
        Parse an import statement to extract imported items.

        This is simplified and would need language-specific parsing.

        Args:
            statement: Import statement string

        Returns:
            List of imported module/class names
        """
        imported = []

        # Python: import x, from x import y
        if "import" in statement.lower():
            # Remove 'import' and 'from' keywords
            cleaned = re.sub(r'\b(import|from)\b', '', statement, flags=re.IGNORECASE)
            # Split by commas and whitespace
            parts = re.split(r'[,\s]+', cleaned.strip())
            imported.extend([p.strip() for p in parts if p.strip()])

        # Java: import com.example.Class
        if statement.startswith("import ") and ";" in statement:
            # Extract the last part (class name)
            parts = statement.replace("import ", "").replace(";", "").strip().split(".")
            if parts:
                imported.append(parts[-1])

        return imported

    def _count_node_types(self, nodes: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count nodes by type"""
        counts = {}
        for node in nodes:
            node_type = node.get("type", "Unknown")
            counts[node_type] = counts.get(node_type, 0) + 1
        return counts

    def _count_edge_types(self, edges: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count edges by type"""
        counts = {}
        for edge in edges:
            edge_type = edge.get("type", "Unknown")
            counts[edge_type] = counts.get(edge_type, 0) + 1
        return counts

    async def _persist_to_neo4j(self, dependency_graph: Dict[str, Any]):
        """
        Persist dependency graph to Neo4j via MCP server.

        Args:
            dependency_graph: Dependency graph to persist
        """
        try:
            nodes = dependency_graph.get("nodes", [])
            edges = dependency_graph.get("edges", [])

            # Create nodes in Neo4j
            if nodes:
                logger.info(f"Creating {len(nodes)} nodes in Neo4j via MCP")
                result = await call_mcp_tool(
                    server_name="neo4j-graph",
                    tool_name="create_nodes",
                    nodes=nodes
                )
                if "error" in result:
                    logger.error(f"Error creating nodes in Neo4j: {result['error']}")
                else:
                    logger.info(f"Successfully created {result.get('created', 0)} nodes")

            # Create relationships in Neo4j
            if edges:
                logger.info(f"Creating {len(edges)} relationships in Neo4j via MCP")
                # Convert edges to relationships format
                relationships = [
                    {
                        "source": edge["source"],
                        "target": edge["target"],
                        "type": edge["type"],
                        "properties": {
                            "file_path": edge.get("file_path"),
                            "line": edge.get("line")
                        }
                    }
                    for edge in edges
                ]

                result = await call_mcp_tool(
                    server_name="neo4j-graph",
                    tool_name="create_relationships",
                    relationships=relationships
                )
                if "error" in result:
                    logger.error(f"Error creating relationships in Neo4j: {result['error']}")
                else:
                    logger.info(f"Successfully created {result.get('created', 0)} relationships")

        except Exception as e:
            logger.error(f"Exception persisting to Neo4j: {e}")


async def dependency_mapping_node_mcp(state: GraphState) -> GraphState:
    """
    Async function wrapper for Dependency Mapping Node (MCP).

    Args:
        state: Current graph state

    Returns:
        Updated graph state
    """
    node = DependencyMappingNodeMCP()
    return await node(state)


def create_dependency_mapping_node_mcp(config: Optional[Dict[str, Any]] = None):
    """
    Factory function to create a Dependency Mapping Node (MCP).

    Args:
        config: Optional configuration

    Returns:
        Dependency Mapping Node instance
    """
    return DependencyMappingNodeMCP(config)
