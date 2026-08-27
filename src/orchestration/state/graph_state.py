"""
LangGraph State Management
===========================

Defines the state schema for the reverse engineering workflow.
"""

from typing import TypedDict, List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class AnalysisPhase(Enum):
    """Workflow phases"""
    DISCOVERY = "discovery"
    AST_ANALYSIS = "ast_analysis"
    DEPENDENCY_MAPPING = "dependency_mapping"
    SECURITY_SCAN = "security_scan"
    CODE_GENERATION = "code_generation"
    VALIDATION = "validation"
    COMPLETE = "complete"


class CodeArtifact(TypedDict):
    """Represents a code artifact (file, class, function)"""
    id: str
    type: str  # "file", "class", "function", "module"
    path: str
    language: str
    content: str
    metadata: Dict[str, Any]
    ast_representation: Optional[Dict[str, Any]]
    dependencies: List[str]
    complexity_score: Optional[float]


class DependencyNode(TypedDict):
    """Represents a dependency in the graph"""
    source: str
    target: str
    relationship_type: str  # "calls", "imports", "extends", etc.
    metadata: Dict[str, Any]


class SecurityFinding(TypedDict):
    """Security scan result"""
    severity: str  # "ERROR", "WARNING", "INFO"
    rule_id: str
    message: str
    file_path: str
    line_number: int
    recommendation: str


class MigrationState(TypedDict):
    """
    Main state object for the LangGraph workflow.

    This state is passed between nodes and updated throughout the workflow.
    """
    # Workflow metadata
    workflow_id: str
    phase: AnalysisPhase
    timestamp: datetime

    # Input configuration
    source_language: str  # "cobol", "smalltalk", "java", etc.
    target_language: str  # "java", "kotlin", "python", etc.
    source_path: str

    # Discovered artifacts
    code_artifacts: List[CodeArtifact]
    total_files: int
    total_lines: int

    # AST analysis results
    ast_trees: Dict[str, Any]  # file_path -> AST
    parsed_entities: Dict[str, List[Dict]]  # type -> entities

    # Dependency mapping
    dependency_graph: List[DependencyNode]
    circular_dependencies: List[List[str]]
    dependency_layers: List[List[str]]

    # Security and quality
    security_findings: List[SecurityFinding]
    code_smells: List[Dict[str, Any]]
    quality_metrics: Dict[str, float]

    # RAG context
    embedded_chunks: List[Dict[str, Any]]
    vector_store_ids: List[str]

    # Graph database
    graph_db_populated: bool
    graph_query_results: Dict[str, Any]

    # Generated code
    generated_artifacts: List[CodeArtifact]
    migration_plan: Optional[Dict[str, Any]]

    # User stories
    user_stories: List[Dict[str, Any]]

    # Human-in-the-loop
    pending_approvals: List[Dict[str, Any]]
    human_feedback: List[Dict[str, Any]]

    # Errors and warnings
    errors: List[str]
    warnings: List[str]

    # Checkpoint
    last_checkpoint: Optional[str]
    can_resume: bool


class ReducerState(TypedDict):
    """
    State with reducer functions for merging updates.
    Used for parallel execution.
    """
    artifacts: List[CodeArtifact]  # Append-only
    findings: List[SecurityFinding]  # Append-only
    errors: List[str]  # Append-only


def merge_artifacts(left: List[CodeArtifact], right: List[CodeArtifact]) -> List[CodeArtifact]:
    """Merge two lists of artifacts, avoiding duplicates"""
    seen_ids = {artifact["id"] for artifact in left}
    merged = left.copy()
    for artifact in right:
        if artifact["id"] not in seen_ids:
            merged.append(artifact)
    return merged


def merge_findings(left: List[SecurityFinding], right: List[SecurityFinding]) -> List[SecurityFinding]:
    """Merge two lists of security findings"""
    # Simple append for findings
    return left + right


def create_initial_state(
    source_language: str,
    target_language: str,
    source_path: str,
    workflow_id: Optional[str] = None
) -> MigrationState:
    """Create initial state for a new workflow"""
    import uuid

    return MigrationState(
        workflow_id=workflow_id or str(uuid.uuid4()),
        phase=AnalysisPhase.DISCOVERY,
        timestamp=datetime.now(),
        source_language=source_language,
        target_language=target_language,
        source_path=source_path,
        code_artifacts=[],
        total_files=0,
        total_lines=0,
        ast_trees={},
        parsed_entities={},
        dependency_graph=[],
        circular_dependencies=[],
        dependency_layers=[],
        security_findings=[],
        code_smells=[],
        quality_metrics={},
        embedded_chunks=[],
        vector_store_ids=[],
        graph_db_populated=False,
        graph_query_results={},
        generated_artifacts=[],
        migration_plan=None,
        user_stories=[],
        pending_approvals=[],
        human_feedback=[],
        errors=[],
        warnings=[],
        last_checkpoint=None,
        can_resume=True
    )
