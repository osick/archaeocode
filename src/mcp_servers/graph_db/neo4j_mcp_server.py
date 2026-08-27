"""
Neo4j Graph Database MCP Server
================================

MCP server for dependency graph operations using Neo4j and the official Anthropic MCP SDK.

This server exposes tools for:
- Creating nodes (classes, functions, modules, etc.)
- Creating relationships (CALLS, IMPORTS, EXTENDS, DEPENDS_ON, etc.)
- Querying the graph with Cypher
- Finding dependencies and dependents
- Detecting circular dependencies
- Calculating graph metrics
"""

from typing import Any, Optional
try:  # mcp >= 2.0
    from mcp.server import MCPServer
except ImportError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP as MCPServer
from mcp import types
import json


# Create MCP server instance
server = MCPServer("neo4j-graph")


# Node and relationship type definitions (from config)
NODE_TYPES = ["Class", "Method", "Function", "Module", "Package", "Database", "Table"]
RELATIONSHIP_TYPES = ["CALLS", "IMPORTS", "EXTENDS", "IMPLEMENTS", "DEPENDS_ON", "REFERENCES", "ACCESSES"]


def validate_node(node: dict[str, Any]) -> bool:
    """Validate node structure"""
    return "name" in node and "type" in node


def validate_relationship(rel: dict[str, Any]) -> bool:
    """Validate relationship structure"""
    return all(key in rel for key in ["source", "target", "type"])


# MCP Tool: create_nodes
@server.tool()
async def create_nodes(nodes: list[dict[str, Any]]) -> list[types.TextContent]:
    """
    Create nodes in the dependency graph.

    This is a placeholder. In production, it would:
    - Connect to Neo4j database
    - Execute CREATE Cypher queries
    - Handle transactions and error recovery

    Args:
        nodes: List of node definitions, each with:
            - name: Node identifier
            - type: Node type (Class, Function, Module, etc.)
            - properties: Optional dict of additional properties
                - file_path: Source file path
                - line_start: Starting line number
                - line_end: Ending line number
                - language: Programming language
                - complexity: Complexity score

    Returns:
        Creation statistics

    Example:
        nodes = [
            {
                "name": "UserService",
                "type": "Class",
                "properties": {
                    "file_path": "/src/services/user_service.py",
                    "line_start": 10,
                    "line_end": 150,
                    "language": "python"
                }
            }
        ]
    """
    try:
        # Validate nodes
        invalid_nodes = [i for i, n in enumerate(nodes) if not validate_node(n)]
        if invalid_nodes:
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Invalid nodes at indices: {invalid_nodes}",
                    "required_fields": ["name", "type"]
                }, indent=2)
            )]

        # In production, execute Cypher:
        # with driver.session() as session:
        #     for node in nodes:
        #         cypher = f"""
        #         CREATE (n:{node['type']} {{name: $name}})
        #         SET n += $properties
        #         """
        #         session.run(cypher, name=node['name'], properties=node.get('properties', {}))

        created_count = len(nodes)

        result = {
            "success": True,
            "created": created_count,
            "node_types": list(set(n["type"] for n in nodes)),
            "nodes": [
                {
                    "name": n["name"],
                    "type": n["type"],
                    "properties_count": len(n.get("properties", {}))
                }
                for n in nodes
            ],
            "status": "mock - not persisted to Neo4j"
        }

        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    except Exception as e:
        return [types.TextContent(
            type="text",
            text=json.dumps({"error": str(e)}, indent=2)
        )]


# MCP Tool: create_relationships
@server.tool()
async def create_relationships(
    relationships: list[dict[str, Any]]
) -> list[types.TextContent]:
    """
    Create relationships between nodes in the dependency graph.

    This is a placeholder. In production, it would:
    - Connect to Neo4j database
    - Match source and target nodes
    - Create relationships with properties

    Args:
        relationships: List of relationship definitions, each with:
            - source: Source node name
            - target: Target node name
            - type: Relationship type (CALLS, IMPORTS, DEPENDS_ON, etc.)
            - properties: Optional dict of additional properties

    Returns:
        Creation statistics

    Example:
        relationships = [
            {
                "source": "UserService",
                "target": "DatabaseConnection",
                "type": "DEPENDS_ON",
                "properties": {
                    "file_path": "/src/services/user_service.py",
                    "line_number": 25
                }
            }
        ]
    """
    try:
        # Validate relationships
        invalid_rels = [i for i, r in enumerate(relationships) if not validate_relationship(r)]
        if invalid_rels:
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "error": f"Invalid relationships at indices: {invalid_rels}",
                    "required_fields": ["source", "target", "type"]
                }, indent=2)
            )]

        # In production, execute Cypher:
        # with driver.session() as session:
        #     for rel in relationships:
        #         cypher = f"""
        #         MATCH (a {{name: $source}})
        #         MATCH (b {{name: $target}})
        #         CREATE (a)-[r:{rel['type']}]->(b)
        #         SET r += $properties
        #         """
        #         session.run(cypher, source=rel['source'], target=rel['target'],
        #                     properties=rel.get('properties', {}))

        created_count = len(relationships)

        result = {
            "success": True,
            "created": created_count,
            "relationship_types": list(set(r["type"] for r in relationships)),
            "relationships": [
                {
                    "source": r["source"],
                    "target": r["target"],
                    "type": r["type"]
                }
                for r in relationships
            ],
            "status": "mock - not persisted to Neo4j"
        }

        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    except Exception as e:
        return [types.TextContent(
            type="text",
            text=json.dumps({"error": str(e)}, indent=2)
        )]


# MCP Tool: query_graph
@server.tool()
async def query_graph(
    cypher: str,
    parameters: Optional[dict[str, Any]] = None
) -> list[types.TextContent]:
    """
    Execute a Cypher query against the graph database.

    This is a placeholder. In production, it would:
    - Execute the Cypher query
    - Return results as list of records

    Args:
        cypher: Cypher query string
        parameters: Optional query parameters (for parameterized queries)

    Returns:
        Query results

    Example:
        cypher = "MATCH (n:Class)-[:DEPENDS_ON]->(m) WHERE n.name = $name RETURN m"
        parameters = {"name": "UserService"}
    """
    try:
        parameters = parameters or {}

        # In production:
        # with driver.session() as session:
        #     result = session.run(cypher, parameters)
        #     return [record.data() for record in result]

        # Mock result
        mock_results = []

        result = {
            "success": True,
            "query": cypher,
            "parameters": parameters,
            "results": mock_results,
            "result_count": len(mock_results),
            "status": "mock - no real Neo4j connection"
        }

        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    except Exception as e:
        return [types.TextContent(
            type="text",
            text=json.dumps({"error": str(e)}, indent=2)
        )]


# MCP Tool: find_dependencies
@server.tool()
async def find_dependencies(
    node_name: str,
    depth: Optional[int] = None,
    relationship_type: Optional[str] = None
) -> list[types.TextContent]:
    """
    Find all dependencies of a node.

    This traverses outgoing relationships to find what a node depends on.

    Args:
        node_name: Name of the node to analyze
        depth: Maximum traversal depth (default: 1, use -1 for unlimited)
        relationship_type: Filter by relationship type (default: all types)

    Returns:
        List of dependent nodes with distance information

    Example Cypher (for depth=2):
        MATCH (n {name: $node_name})-[:DEPENDS_ON*1..2]->(dep)
        RETURN dep, length(path) as distance
    """
    try:
        depth = depth or 1
        depth_str = str(depth) if depth > 0 else ""

        # In production:
        # cypher = f"""
        # MATCH path = (n {{name: $node_name}})-[:{relationship_type or ''}*1..{depth_str}]->(dep)
        # RETURN dep, length(path) as distance
        # ORDER BY distance
        # """

        # Mock results
        mock_dependencies = [
            {
                "name": "DatabaseConnection",
                "type": "Class",
                "distance": 1,
                "relationship": "DEPENDS_ON"
            },
            {
                "name": "Logger",
                "type": "Module",
                "distance": 1,
                "relationship": "IMPORTS"
            }
        ]

        # Filter by relationship type if specified
        if relationship_type:
            mock_dependencies = [
                d for d in mock_dependencies
                if d["relationship"] == relationship_type
            ]

        result = {
            "success": True,
            "node_name": node_name,
            "depth": depth,
            "relationship_type": relationship_type,
            "dependencies": mock_dependencies,
            "total_dependencies": len(mock_dependencies),
            "status": "mock results"
        }

        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    except Exception as e:
        return [types.TextContent(
            type="text",
            text=json.dumps({"error": str(e)}, indent=2)
        )]


# MCP Tool: find_dependents
@server.tool()
async def find_dependents(
    node_name: str,
    depth: Optional[int] = None,
    relationship_type: Optional[str] = None
) -> list[types.TextContent]:
    """
    Find all nodes that depend on this node.

    This traverses incoming relationships to find what depends on a node.

    Args:
        node_name: Name of the node to analyze
        depth: Maximum traversal depth (default: 1, use -1 for unlimited)
        relationship_type: Filter by relationship type (default: all types)

    Returns:
        List of dependent nodes with distance information

    Example Cypher:
        MATCH (n {name: $node_name})<-[:DEPENDS_ON*1..2]-(dependent)
        RETURN dependent, length(path) as distance
    """
    try:
        depth = depth or 1

        # Mock results
        mock_dependents = [
            {
                "name": "UserController",
                "type": "Class",
                "distance": 1,
                "relationship": "DEPENDS_ON"
            },
            {
                "name": "AdminService",
                "type": "Class",
                "distance": 1,
                "relationship": "DEPENDS_ON"
            }
        ]

        # Filter by relationship type if specified
        if relationship_type:
            mock_dependents = [
                d for d in mock_dependents
                if d["relationship"] == relationship_type
            ]

        result = {
            "success": True,
            "node_name": node_name,
            "depth": depth,
            "relationship_type": relationship_type,
            "dependents": mock_dependents,
            "total_dependents": len(mock_dependents),
            "status": "mock results"
        }

        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    except Exception as e:
        return [types.TextContent(
            type="text",
            text=json.dumps({"error": str(e)}, indent=2)
        )]


# MCP Tool: shortest_path
@server.tool()
async def shortest_path(
    source: str,
    target: str,
    max_depth: Optional[int] = None
) -> list[types.TextContent]:
    """
    Find the shortest path between two nodes in the dependency graph.

    Args:
        source: Source node name
        target: Target node name
        max_depth: Maximum path length to search (default: unlimited)

    Returns:
        Shortest path as list of node names, or null if no path exists

    Example Cypher:
        MATCH path = shortestPath((a {name: $source})-[*]-(b {name: $target}))
        RETURN [node in nodes(path) | node.name] as path
    """
    try:
        # In production, execute shortest path algorithm in Neo4j
        # This would use Neo4j's built-in shortestPath function

        # Mock result
        mock_path = [source, "IntermediateClass", target]

        result = {
            "success": True,
            "source": source,
            "target": target,
            "path": mock_path,
            "path_length": len(mock_path) - 1,
            "status": "mock result"
        }

        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    except Exception as e:
        return [types.TextContent(
            type="text",
            text=json.dumps({"error": str(e)}, indent=2)
        )]


# MCP Tool: detect_cycles
@server.tool()
async def detect_cycles(
    max_cycles: Optional[int] = None
) -> list[types.TextContent]:
    """
    Detect circular dependencies in the graph.

    This is crucial for identifying architectural issues in codebases.

    Args:
        max_cycles: Maximum number of cycles to return (default: all)

    Returns:
        List of cycles, each represented as a list of node names

    Example Cypher:
        MATCH (n)-[r:DEPENDS_ON*]->(n)
        RETURN [node in nodes(r) | node.name] as cycle
    """
    try:
        max_cycles = max_cycles or 10

        # In production, execute cycle detection in Neo4j
        # This would find all paths where a node depends on itself

        # Mock results
        mock_cycles = [
            ["ClassA", "ClassB", "ClassC", "ClassA"],
            ["ModuleX", "ModuleY", "ModuleX"]
        ]

        # Limit to max_cycles
        mock_cycles = mock_cycles[:max_cycles]

        result = {
            "success": True,
            "cycles": mock_cycles,
            "total_cycles": len(mock_cycles),
            "max_cycles": max_cycles,
            "status": "mock results - no real cycle detection performed"
        }

        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    except Exception as e:
        return [types.TextContent(
            type="text",
            text=json.dumps({"error": str(e)}, indent=2)
        )]


# MCP Tool: get_graph_metrics
@server.tool()
async def get_graph_metrics() -> list[types.TextContent]:
    """
    Calculate graph metrics and statistics.

    Returns:
        Dictionary of metrics including:
        - total_nodes: Total number of nodes
        - total_relationships: Total number of relationships
        - node_types_distribution: Count of each node type
        - relationship_types_distribution: Count of each relationship type
        - density: Graph density
        - average_degree: Average node degree

    Example Cypher:
        MATCH (n) RETURN count(n) as total_nodes
        MATCH ()-[r]->() RETURN count(r) as total_relationships
    """
    try:
        # In production, query Neo4j for real statistics
        # Would execute multiple aggregation queries

        # Mock metrics
        metrics = {
            "success": True,
            "total_nodes": 150,
            "total_relationships": 320,
            "node_types_distribution": {
                "Class": 45,
                "Function": 80,
                "Module": 20,
                "Package": 5
            },
            "relationship_types_distribution": {
                "CALLS": 180,
                "IMPORTS": 85,
                "DEPENDS_ON": 40,
                "EXTENDS": 15
            },
            "density": 0.029,
            "average_degree": 4.27,
            "status": "mock metrics - no real graph analyzed"
        }

        return [types.TextContent(
            type="text",
            text=json.dumps(metrics, indent=2)
        )]

    except Exception as e:
        return [types.TextContent(
            type="text",
            text=json.dumps({"error": str(e)}, indent=2)
        )]


# MCP Tool: clear_graph
@server.tool()
async def clear_graph(confirm: bool = False) -> list[types.TextContent]:
    """
    Clear all nodes and relationships from the graph database.

    WARNING: This is a destructive operation!

    Args:
        confirm: Must be True to proceed with deletion

    Returns:
        Deletion statistics

    Example Cypher:
        MATCH (n) DETACH DELETE n
    """
    try:
        if not confirm:
            return [types.TextContent(
                type="text",
                text=json.dumps({
                    "error": "Confirmation required",
                    "message": "Set confirm=True to proceed with graph deletion"
                }, indent=2)
            )]

        # In production:
        # with driver.session() as session:
        #     result = session.run("MATCH (n) DETACH DELETE n")

        result = {
            "success": True,
            "deleted_nodes": 0,
            "deleted_relationships": 0,
            "status": "mock - no actual deletion performed"
        }

        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    except Exception as e:
        return [types.TextContent(
            type="text",
            text=json.dumps({"error": str(e)}, indent=2)
        )]


# Main entry point for running the server (stdio transport)
if __name__ == "__main__":
    server.run()
