"""
LangGraph Orchestrator
======================

Main graph definition for the reverse engineering workflow.
"""

import os
from typing import Dict, Any
from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from src.orchestration.state.graph_state import MigrationState, create_initial_state, AnalysisPhase
from src.orchestration.nodes.discovery_node import CodeDiscoveryNode
from src.orchestration.nodes.ast_node import ASTAnalysisNode
from src.orchestration.nodes.dependency_node import DependencyMappingNode
from src.orchestration.nodes.user_story_node import UserStoryExtractionNode


def _setup_langsmith_tracing():
    """
    Setup LangSmith tracing if configured.

    Reads configuration from environment variables and enables tracing.
    """
    try:
        from dotenv import load_dotenv
        load_dotenv()

        # Check if LangSmith is enabled
        enable_langsmith = os.getenv("ENABLE_LANGSMITH", "false").lower() == "true"
        langsmith_key = os.getenv("LANGSMITH_API_KEY")

        if enable_langsmith and langsmith_key and langsmith_key != "your-langsmith-key-here":
            # Set LangSmith environment variables
            os.environ["LANGCHAIN_TRACING_V2"] = "true"
            os.environ["LANGCHAIN_PROJECT"] = os.getenv(
                "LANGSMITH_PROJECT",
                "archaeocode"
            )
            os.environ["LANGCHAIN_ENDPOINT"] = os.getenv(
                "LANGSMITH_ENDPOINT",
                "https://api.smith.langchain.com"
            )
            os.environ["LANGCHAIN_API_KEY"] = langsmith_key

            print("✅ LangSmith tracing enabled")
            print(f"   Project: {os.environ['LANGCHAIN_PROJECT']}")
            print(f"   Endpoint: {os.environ['LANGCHAIN_ENDPOINT']}")
            return True
        else:
            if enable_langsmith:
                print("⚠️  LangSmith enabled but no API key configured")
            return False

    except Exception as e:
        print(f"⚠️  Failed to setup LangSmith tracing: {e}")
        return False


class ReverseMigrationGraph:
    """
    Main orchestrator for the reverse engineering workflow.

    Graph structure:
    START -> Discovery -> AST Analysis -> Dependency Mapping -> User Story Extraction -> END
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.graph = None
        self.checkpointer = None
        self.langsmith_enabled = _setup_langsmith_tracing()
        self._build_graph()

    def _build_graph(self):
        """Build the LangGraph workflow"""

        # Initialize nodes
        discovery_node = CodeDiscoveryNode(self.config)
        ast_node = ASTAnalysisNode(self.config)
        dependency_node = DependencyMappingNode(self.config)
        user_story_node = UserStoryExtractionNode(self.config)

        # Create state graph
        workflow = StateGraph(MigrationState)

        # Add nodes
        workflow.add_node("discovery", discovery_node)
        workflow.add_node("ast_analysis", ast_node)
        workflow.add_node("dependency_mapping", dependency_node)
        workflow.add_node("user_story_extraction", user_story_node)

        # Define edges (workflow transitions)
        workflow.set_entry_point("discovery")
        workflow.add_edge("discovery", "ast_analysis")
        workflow.add_edge("ast_analysis", "dependency_mapping")
        workflow.add_edge("dependency_mapping", "user_story_extraction")
        workflow.add_edge("user_story_extraction", END)

        # Add conditional edges based on state
        # workflow.add_conditional_edges(
        #     "dependency_mapping",
        #     self._should_continue,
        #     {
        #         "security_scan": "security_scan",
        #         "end": END
        #     }
        # )

        # Setup checkpointing
        if self.config.get("checkpoints", {}).get("enabled", True):
            self.checkpointer = MemorySaver()
        else:
            self.checkpointer = None

        # Compile graph
        self.graph = workflow.compile(checkpointer=self.checkpointer)

    def _should_continue(self, state: MigrationState) -> str:
        """Conditional logic for workflow branching"""
        if state.get("errors"):
            return "end"
        if state["phase"] == AnalysisPhase.DEPENDENCY_MAPPING:
            return "security_scan"
        return "end"

    def run(
        self,
        source_language: str,
        target_language: str,
        source_path: str,
        workflow_id: str = None
    ) -> MigrationState:
        """
        Execute the reverse engineering workflow.

        Args:
            source_language: Source code language (e.g., "cobol", "smalltalk")
            target_language: Target language (e.g., "java", "kotlin")
            source_path: Path to source code directory
            workflow_id: Optional workflow ID for resuming

        Returns:
            Final workflow state
        """
        # Create initial state
        initial_state = create_initial_state(
            source_language=source_language,
            target_language=target_language,
            source_path=source_path,
            workflow_id=workflow_id
        )

        print(f"🚀 Starting migration workflow: {initial_state['workflow_id']}")
        print(f"   Source: {source_language} -> Target: {target_language}")
        print(f"   Path: {source_path}")
        if self.langsmith_enabled:
            print(f"   📊 LangSmith tracing: Active")
        print()

        # Execute graph with metadata for LangSmith
        config = {
            "configurable": {"thread_id": initial_state["workflow_id"]},
            "metadata": {
                "workflow_id": initial_state["workflow_id"],
                "source_language": source_language,
                "target_language": target_language,
                "source_path": source_path,
            },
            "tags": [
                f"source:{source_language}",
                f"target:{target_language}",
                "reverse-engineering",
                "migration"
            ]
        }

        final_state = None
        for output in self.graph.stream(initial_state, config):
            # Stream outputs node by node
            node_name = list(output.keys())[0]
            node_output = output[node_name]
            final_state = node_output

            print(f"✓ Completed: {node_name}")
            print()

        return final_state

    def resume(self, workflow_id: str, from_checkpoint: str = None) -> MigrationState:
        """
        Resume a workflow from a checkpoint.

        Args:
            workflow_id: Workflow ID to resume
            from_checkpoint: Optional specific checkpoint to resume from

        Returns:
            Final workflow state
        """
        if not self.checkpointer:
            raise ValueError("Checkpointing not enabled")

        config = {
            "configurable": {
                "thread_id": workflow_id,
                "checkpoint_id": from_checkpoint
            }
        }

        print(f"🔄 Resuming workflow: {workflow_id}")

        final_state = None
        for output in self.graph.stream(None, config):
            node_name = list(output.keys())[0]
            node_output = output[node_name]
            final_state = node_output

            print(f"✓ Completed: {node_name}")

        return final_state

    def visualize(self, output_path: str = "workflow_graph.png"):
        """
        Generate visual representation of the workflow graph.

        Args:
            output_path: Path to save the visualization
        """
        try:
            from IPython.display import Image, display

            # Get Mermaid diagram
            mermaid_diagram = self.graph.get_graph().draw_mermaid()

            print("Workflow Graph (Mermaid):")
            print(mermaid_diagram)

            # In Jupyter, could render as image
            # display(Image(self.graph.get_graph().draw_mermaid_png()))

        except ImportError:
            print("Install IPython for visualization support")


def create_graph(config: Dict[str, Any] = None) -> ReverseMigrationGraph:
    """
    Factory function to create the migration graph.

    Args:
        config: Configuration dictionary

    Returns:
        Configured ReverseMigrationGraph instance
    """
    if config is None:
        config = {
            "checkpoints": {"enabled": True},
            "hitl": {"enabled": True}
        }

    return ReverseMigrationGraph(config)


# Example usage
if __name__ == "__main__":
    # Create graph
    graph = create_graph()

    # Run workflow
    result = graph.run(
        source_language="cobol",
        target_language="java",
        source_path="./sample_code"
    )

    print("\n" + "="*60)
    print("WORKFLOW COMPLETE")
    print("="*60)
    print(f"Processed {result['total_files']} files")
    print(f"Total lines: {result['total_lines']:,}")
    print(f"Errors: {len(result['errors'])}")
    print(f"Warnings: {len(result['warnings'])}")
