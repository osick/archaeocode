"""
Code Discovery Node
===================

Discovers and catalogs all source code files in the target directory.
"""

import os
from pathlib import Path
from typing import Dict, Any
from datetime import datetime

from src.orchestration.state.graph_state import MigrationState, CodeArtifact, AnalysisPhase


class CodeDiscoveryNode:
    """
    Node that discovers and catalogs source code files.

    Responsibilities:
    - Traverse directory structure
    - Identify code files by extension
    - Calculate basic metrics (LOC, file count)
    - Create initial CodeArtifact objects
    """

    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.supported_extensions = self._get_supported_extensions()

    def _get_supported_extensions(self) -> Dict[str, str]:
        """Map file extensions to language types"""
        return {
            # COBOL
            ".cob": "cobol",
            ".cbl": "cobol",
            ".COB": "cobol",
            ".CBL": "cobol",

            # Java
            ".java": "java",

            # Smalltalk
            ".st": "smalltalk",
            ".cs": "smalltalk",  # Cincom VisualWorks

            # Python
            ".py": "python",

            # SQL
            ".sql": "sql",

            # TAL (HP NonStop)
            ".tal": "tal",

            # JavaScript/TypeScript
            ".js": "javascript",
            ".ts": "typescript",
            ".jsx": "javascript",
            ".tsx": "typescript",

            # Fortran
            ".f": "fortran",
            ".f90": "fortran",
            ".f95": "fortran",
            ".f03": "fortran",
            ".F": "fortran",
            ".F90": "fortran",

            # Pascal
            ".pas": "pascal",
            ".pp": "pascal",
            ".p": "pascal",
            ".PAS": "pascal",
        }

    def _count_lines(self, file_path: str) -> int:
        """Count non-empty lines in a file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return sum(1 for line in f if line.strip())
        except Exception as e:
            print(f"Error reading {file_path}: {e}")
            return 0

    def _create_artifact(self, file_path: Path, language: str) -> CodeArtifact:
        """Create a CodeArtifact from a file"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            content = f"# Error reading file: {e}"

        stat = file_path.stat()

        return CodeArtifact(
            id=str(file_path),
            type="file",
            path=str(file_path),
            language=language,
            content=content,
            metadata={
                "size_bytes": stat.st_size,
                "modified_time": datetime.fromtimestamp(stat.st_mtime).isoformat(),
                "line_count": self._count_lines(str(file_path)),
                "extension": file_path.suffix,
            },
            ast_representation=None,
            dependencies=[],
            complexity_score=None
        )

    def discover(self, source_path: str, max_files: int = 10000) -> tuple[list[CodeArtifact], int, int]:
        """
        Discover all code files in the source path.

        Args:
            source_path: Root directory to search
            max_files: Maximum number of files to process

        Returns:
            Tuple of (artifacts, total_files, total_lines)
        """
        artifacts = []
        total_lines = 0
        file_count = 0

        source = Path(source_path)

        if not source.exists():
            raise ValueError(f"Source path does not exist: {source_path}")

        # Walk directory tree
        for root, dirs, files in os.walk(source):
            # Skip common non-source directories
            dirs[:] = [d for d in dirs if d not in {'.git', '.svn', 'node_modules', '__pycache__', 'build', 'dist'}]

            for file in files:
                if file_count >= max_files:
                    break

                file_path = Path(root) / file
                extension = file_path.suffix

                if extension in self.supported_extensions:
                    language = self.supported_extensions[extension]
                    artifact = self._create_artifact(file_path, language)
                    artifacts.append(artifact)
                    total_lines += artifact["metadata"]["line_count"]
                    file_count += 1

        return artifacts, file_count, total_lines

    def __call__(self, state: MigrationState) -> MigrationState:
        """
        Execute the discovery node.

        Args:
            state: Current workflow state

        Returns:
            Updated state with discovered artifacts
        """
        print(f"🔍 Discovering code in: {state['source_path']}")

        try:
            artifacts, file_count, total_lines = self.discover(state["source_path"])

            # Update state
            state["code_artifacts"] = artifacts
            state["total_files"] = file_count
            state["total_lines"] = total_lines
            state["phase"] = AnalysisPhase.AST_ANALYSIS

            print(f"✅ Discovered {file_count} files ({total_lines:,} lines)")

            # Log language breakdown
            language_counts = {}
            for artifact in artifacts:
                lang = artifact["language"]
                language_counts[lang] = language_counts.get(lang, 0) + 1

            print(f"📊 Language breakdown: {language_counts}")

        except Exception as e:
            state["errors"].append(f"Discovery failed: {str(e)}")
            print(f"❌ Discovery error: {e}")

        return state


# Wrapper function for discovery node
def discovery_node(state):
    """Wrapper function for DiscoveryNode class"""
    node = CodeDiscoveryNode()
    return node(state)

