"""
LangSmith Tracing Utilities
============================

Helper functions for adding rich tracing metadata to workflow nodes.
"""

import os
from typing import Dict, Any, Optional, Callable
from functools import wraps


def is_tracing_enabled() -> bool:
    """Check if LangSmith tracing is currently enabled"""
    return os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"


def get_project_name() -> str:
    """Get the current LangSmith project name"""
    return os.getenv("LANGCHAIN_PROJECT", "archaeocode")


def add_node_metadata(node_name: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add metadata for a node execution.

    Args:
        node_name: Name of the node
        metadata: Additional metadata to include

    Returns:
        Dictionary with combined metadata
    """
    return {
        "node": node_name,
        "tracing_enabled": is_tracing_enabled(),
        "project": get_project_name(),
        **metadata
    }


def trace_node(node_name: str, description: Optional[str] = None):
    """
    Decorator to add tracing metadata to node execution functions.

    Args:
        node_name: Name of the node being traced
        description: Optional description of what the node does

    Usage:
        @trace_node("discovery", "Discovers code files in source directory")
        def __call__(self, state):
            # Node logic here
            pass
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Add tracing context if enabled
            if is_tracing_enabled():
                # Could add langsmith.traceable decorator here
                # For now, we rely on LangGraph's built-in tracing
                pass

            # Execute the function
            result = func(*args, **kwargs)

            return result

        # Store metadata on the function
        wrapper._trace_metadata = {
            "node_name": node_name,
            "description": description
        }

        return wrapper
    return decorator


def log_trace_event(event_type: str, data: Dict[str, Any]):
    """
    Log a trace event (only if tracing is enabled).

    Args:
        event_type: Type of event (e.g., "node_start", "node_complete")
        data: Event data to log
    """
    if is_tracing_enabled():
        print(f"[TRACE] {event_type}: {data}")


def create_run_metadata(
    workflow_id: str,
    source_language: str,
    target_language: str,
    additional: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create metadata for a workflow run.

    Args:
        workflow_id: Unique workflow identifier
        source_language: Source code language
        target_language: Target language
        additional: Additional metadata

    Returns:
        Dictionary with run metadata
    """
    metadata = {
        "workflow_id": workflow_id,
        "source_language": source_language,
        "target_language": target_language,
        "tracing_enabled": is_tracing_enabled(),
        "project": get_project_name()
    }

    if additional:
        metadata.update(additional)

    return metadata


def create_run_tags(
    source_language: str,
    target_language: str,
    additional_tags: Optional[list] = None
) -> list:
    """
    Create tags for a workflow run.

    Args:
        source_language: Source code language
        target_language: Target language
        additional_tags: Additional tags to include

    Returns:
        List of tags
    """
    tags = [
        f"source:{source_language}",
        f"target:{target_language}",
        "reverse-engineering",
        "migration"
    ]

    if additional_tags:
        tags.extend(additional_tags)

    return tags


# Example usage in nodes:
"""
from src.orchestration.utils.tracing import trace_node, add_node_metadata

class CodeDiscoveryNode:
    @trace_node("discovery", "Discovers code files in source directory")
    def __call__(self, state: MigrationState) -> MigrationState:
        # Node logic...

        # Add metadata for this execution
        metadata = add_node_metadata("discovery", {
            "files_discovered": len(files),
            "total_lines": total_lines
        })

        return state
"""
