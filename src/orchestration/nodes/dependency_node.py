"""
Dependency Mapping Node
=======================

Maps dependencies between code artifacts and builds dependency graph.
"""

from typing import Dict, Any, List, Set
from collections import defaultdict, deque

from src.orchestration.state.graph_state import MigrationState, DependencyNode, AnalysisPhase


class DependencyMappingNode:
    """
    Node that analyzes and maps code dependencies.

    Responsibilities:
    - Extract import/include statements
    - Identify function/method calls
    - Build dependency graph
    - Detect circular dependencies
    - Calculate dependency layers
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config

    def extract_dependencies(self, artifact: Dict[str, Any]) -> List[str]:
        """
        Extract dependencies from a code artifact.

        Args:
            artifact: Code artifact with AST

        Returns:
            List of dependency paths
        """
        dependencies = []

        if not artifact.get("ast_representation"):
            return dependencies

        language = artifact["language"]

        # Language-specific dependency extraction
        if language == "java":
            # Extract imports
            # In production: walk AST for import_declaration nodes
            dependencies.append("java.util.List")
            dependencies.append("org.springframework.boot.SpringApplication")

        elif language == "cobol":
            # Extract COPY statements
            # In production: walk AST for copy_statement nodes
            dependencies.append("COPYBOOK1")
            dependencies.append("SQLCA")

        elif language == "python":
            # Extract imports
            # In production: walk AST for import_statement nodes
            dependencies.append("os")
            dependencies.append("typing")

        return dependencies

    def build_dependency_graph(self, artifacts: List[Dict[str, Any]]) -> List[DependencyNode]:
        """
        Build dependency graph from artifacts.

        Args:
            artifacts: List of code artifacts

        Returns:
            List of dependency edges
        """
        graph = []

        for artifact in artifacts:
            source = artifact["path"]
            deps = self.extract_dependencies(artifact)

            for dep in deps:
                graph.append(DependencyNode(
                    source=source,
                    target=dep,
                    relationship_type="imports",
                    metadata={"language": artifact["language"]}
                ))

        return graph

    def detect_circular_dependencies(self, graph: List[DependencyNode]) -> List[List[str]]:
        """
        Detect circular dependencies using DFS.

        Args:
            graph: Dependency graph

        Returns:
            List of circular dependency chains
        """
        # Build adjacency list
        adj = defaultdict(list)
        for edge in graph:
            adj[edge["source"]].append(edge["target"])

        visited = set()
        rec_stack = set()
        cycles = []

        def dfs(node: str, path: List[str]):
            visited.add(node)
            rec_stack.add(node)
            path.append(node)

            for neighbor in adj.get(node, []):
                if neighbor not in visited:
                    dfs(neighbor, path.copy())
                elif neighbor in rec_stack:
                    # Found cycle
                    cycle_start = path.index(neighbor)
                    cycle = path[cycle_start:] + [neighbor]
                    cycles.append(cycle)

            rec_stack.remove(node)

        for node in adj.keys():
            if node not in visited:
                dfs(node, [])

        return cycles

    def calculate_dependency_layers(self, graph: List[DependencyNode]) -> List[List[str]]:
        """
        Calculate dependency layers using topological sort.

        Args:
            graph: Dependency graph

        Returns:
            List of layers (inner layers have no dependencies)
        """
        # Build adjacency list and in-degree map
        adj = defaultdict(list)
        in_degree = defaultdict(int)
        all_nodes = set()

        for edge in graph:
            adj[edge["source"]].append(edge["target"])
            in_degree[edge["target"]] += 1
            all_nodes.add(edge["source"])
            all_nodes.add(edge["target"])

        # Initialize nodes with no dependencies
        queue = deque([node for node in all_nodes if in_degree[node] == 0])
        layers = []

        while queue:
            # Process all nodes in current layer
            current_layer = list(queue)
            layers.append(current_layer)

            # Clear queue for next layer
            queue.clear()

            # Process neighbors
            for node in current_layer:
                for neighbor in adj[node]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)

        return layers

    def __call__(self, state: MigrationState) -> MigrationState:
        """
        Execute the dependency mapping node.

        Args:
            state: Current workflow state

        Returns:
            Updated state with dependency analysis
        """
        print(f"🔗 Mapping dependencies...")

        try:
            # Build dependency graph
            graph = self.build_dependency_graph(state["code_artifacts"])
            state["dependency_graph"] = graph

            print(f"  Found {len(graph)} dependency edges")

            # Detect circular dependencies
            cycles = self.detect_circular_dependencies(graph)
            state["circular_dependencies"] = cycles

            if cycles:
                print(f"⚠️  Found {len(cycles)} circular dependencies")
                for cycle in cycles[:3]:  # Show first 3
                    print(f"    {' -> '.join(cycle)}")

            # Calculate dependency layers
            layers = self.calculate_dependency_layers(graph)
            state["dependency_layers"] = layers

            print(f"📊 Dependency layers: {len(layers)}")
            for i, layer in enumerate(layers[:5]):  # Show first 5 layers
                print(f"    Layer {i}: {len(layer)} nodes")

            # Update phase
            state["phase"] = AnalysisPhase.SECURITY_SCAN

        except Exception as e:
            state["errors"].append(f"Dependency mapping failed: {str(e)}")
            print(f"❌ Error: {e}")

        return state
