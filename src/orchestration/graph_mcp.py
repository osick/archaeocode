"""
Reverse Engineering LangGraph Workflow (MCP-Enabled)
======================================================

This is the MCP-enabled version of the reverse engineering workflow
that uses MCP servers for AST analysis and dependency mapping.

This demonstrates the integration pattern:
- LangGraph for orchestration
- MCP servers for specialized capabilities
- LangSmith for observability
"""

from typing import TypedDict, Annotated, Sequence
import operator
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

# PostgreSQL checkpointer is optional
try:
    from langgraph.checkpoint.postgres import PostgresSaver
    HAS_POSTGRES = True
except ImportError:
    PostgresSaver = None
    HAS_POSTGRES = False

import logging
import yaml
import os
import asyncio

from .state.graph_state import MigrationState as GraphState
from .nodes.discovery_node import discovery_node
from .nodes.ast_node_mcp import ast_analysis_node_mcp
from .nodes.dependency_node_mcp import dependency_mapping_node_mcp
from .nodes.user_story_node import user_story_extraction_node
from .utils.mcp_client import configure_mcp_manager, initialize_mcp_servers, shutdown_mcp_servers
from .utils.tracing import is_tracing_enabled, create_run_metadata

logger = logging.getLogger(__name__)


def load_config(config_path: str = "config/langgraph_config.yaml") -> dict:
    """
    Load configuration from YAML file.

    Args:
        config_path: Path to config file

    Returns:
        Configuration dictionary
    """
    try:
        with open(config_path, 'r') as f:
            config = yaml.safe_load(f)
        logger.info(f"Loaded configuration from {config_path}")
        return config
    except Exception as e:
        logger.error(f"Failed to load config: {e}")
        return {}


def create_checkpointer(config: dict):
    """
    Create appropriate checkpointer based on config.

    Args:
        config: Configuration dictionary

    Returns:
        Checkpointer instance
    """
    checkpoint_config = config.get("checkpoints", {})

    if not checkpoint_config.get("enabled", False):
        logger.info("Checkpointing disabled")
        return None

    backend = checkpoint_config.get("backend", "memory")

    if backend == "postgres":
        # PostgreSQL checkpointer
        if not HAS_POSTGRES:
            logger.warning("PostgreSQL checkpointer not available, falling back to memory")
            return MemorySaver()

        postgres_config = config.get("state", {}).get("postgres", {})
        connection_string = (
            f"postgresql://{os.getenv('POSTGRES_USER', 'postgres')}:"
            f"{os.getenv('POSTGRES_PASSWORD', 'postgres')}@"
            f"{postgres_config.get('host', 'localhost')}:"
            f"{postgres_config.get('port', 5432)}/"
            f"{postgres_config.get('database', 'langgraph_state')}"
        )
        logger.info("Using PostgreSQL checkpointer")
        return PostgresSaver(connection_string)
    else:
        # In-memory checkpointer
        logger.info("Using in-memory checkpointer")
        return MemorySaver()


class ReverseEngineeringWorkflowMCP:
    """
    MCP-enabled reverse engineering workflow using LangGraph.

    This workflow:
    1. Discovers source files
    2. Analyzes AST using MCP server
    3. Maps dependencies using MCP server (optional Neo4j)
    4. Extracts user stories
    """

    def __init__(self, config_path: str = "config/langgraph_config.yaml"):
        """
        Initialize the workflow.

        Args:
            config_path: Path to configuration file
        """
        self.config = load_config(config_path)
        self.checkpointer = create_checkpointer(self.config)
        self.graph = None
        self._setup_mcp()
        self._build_graph()

    def _setup_mcp(self):
        """Configure MCP servers from config"""
        logger.info("Configuring MCP servers")
        configure_mcp_manager(self.config)

    def _build_graph(self):
        """Build the LangGraph workflow"""
        logger.info("Building LangGraph workflow (MCP-enabled)")

        # Create graph
        workflow = StateGraph(GraphState)

        # Add nodes
        workflow.add_node("discovery", discovery_node)
        workflow.add_node("ast_analysis", ast_analysis_node_mcp)
        workflow.add_node("dependency_mapping", dependency_mapping_node_mcp)
        workflow.add_node("user_story_extraction", user_story_extraction_node)

        # Define edges
        workflow.set_entry_point("discovery")
        workflow.add_edge("discovery", "ast_analysis")
        workflow.add_edge("ast_analysis", "dependency_mapping")
        workflow.add_edge("dependency_mapping", "user_story_extraction")
        workflow.add_edge("user_story_extraction", END)

        # Compile graph
        self.graph = workflow.compile(checkpointer=self.checkpointer)
        logger.info("LangGraph workflow compiled successfully")

    async def run(self, source_directory: str, language: str = "java") -> dict:
        """
        Run the reverse engineering workflow.

        Args:
            source_directory: Directory containing source code
            language: Programming language (java, python, etc.)

        Returns:
            Final state dictionary
        """
        logger.info(f"Starting reverse engineering workflow for: {source_directory}")
        logger.info(f"Language: {language}")
        logger.info(f"MCP mode: enabled")

        # Initialize MCP servers
        await initialize_mcp_servers()

        try:
            # Create initial state matching MigrationState schema
            from datetime import datetime
            import uuid
            from .state.graph_state import AnalysisPhase

            initial_state = GraphState(
                workflow_id=str(uuid.uuid4()),
                phase=AnalysisPhase.DISCOVERY,
                timestamp=datetime.now(),
                source_language=language,
                target_language="python",  # Default target
                source_path=source_directory,
                code_artifacts=[],
                total_files=0,
                total_lines=0,
                ast_trees={},
                parsed_entities={},
                dependency_graph=[],
                circular_dependencies=[],
                dependency_layers=[],
                security_findings=[],
                quality_metrics={},
                generated_code=[],
                migration_plan={},
                test_cases=[],
                errors=[]
            )

            # Add LangSmith tracing metadata if enabled
            if is_tracing_enabled():
                initial_state["metadata"] = create_run_metadata(
                    source_directory=source_directory,
                    language=language,
                    workflow_type="mcp-enabled"
                )

            # Run the workflow
            config = {"configurable": {"thread_id": "reverse-engineering-mcp"}}
            final_state = await self.graph.ainvoke(initial_state, config)

            logger.info("Workflow completed successfully")
            return final_state

        except Exception as e:
            logger.error(f"Workflow failed: {e}")
            raise
        finally:
            # Shutdown MCP servers
            await shutdown_mcp_servers()

    def visualize(self, output_path: str = "docs/workflow_mcp.png"):
        """
        Generate a visual representation of the workflow.

        Args:
            output_path: Path to save the visualization
        """
        try:
            from IPython.display import Image
            import os

            # Generate Mermaid diagram
            mermaid = self.graph.get_graph().draw_mermaid()

            # Save to file
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            with open(output_path.replace(".png", ".mmd"), "w") as f:
                f.write(mermaid)

            logger.info(f"Workflow diagram saved to {output_path.replace('.png', '.mmd')}")
            return mermaid

        except Exception as e:
            logger.error(f"Failed to generate visualization: {e}")
            return None


async def run_reverse_engineering_mcp(
    source_directory: str,
    language: str = "java",
    config_path: str = "config/langgraph_config.yaml"
) -> dict:
    """
    Convenience function to run the reverse engineering workflow.

    Args:
        source_directory: Directory containing source code
        language: Programming language
        config_path: Path to configuration file

    Returns:
        Final state dictionary
    """
    workflow = ReverseEngineeringWorkflowMCP(config_path)
    return await workflow.run(source_directory, language)


def main():
    """Main entry point for testing"""
    import sys

    if len(sys.argv) < 2:
        print("Usage: python graph_mcp.py <source_directory> [language]")
        sys.exit(1)

    source_dir = sys.argv[1]
    language = sys.argv[2] if len(sys.argv) > 2 else "java"

    # Run the workflow
    result = asyncio.run(run_reverse_engineering_mcp(source_dir, language))

    # Print summary
    print("\n" + "=" * 60)
    print("Reverse Engineering Workflow Complete (MCP-Enabled)")
    print("=" * 60)
    print(f"Source directory: {source_dir}")
    print(f"Language: {language}")
    print(f"Files discovered: {len(result.get('artifacts', []))}")
    print(f"Files parsed: {len(result.get('ast_trees', {}))}")
    print(f"Entities extracted: {len(result.get('entities', {}))}")
    print(f"Dependency nodes: {len(result.get('dependency_graph', {}).get('nodes', []))}")
    print(f"Dependency edges: {len(result.get('dependency_graph', {}).get('edges', []))}")
    print(f"User stories: {len(result.get('user_stories', []))}")
    print("=" * 60)


if __name__ == "__main__":
    main()
