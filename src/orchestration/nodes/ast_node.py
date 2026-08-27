"""
AST Analysis Node
=================

Parses code into Abstract Syntax Trees using tree-sitter.
"""

from typing import Dict, Any, List, Optional, Set
try:
    from tree_sitter_language_pack import get_parser
except ImportError:  # fallback for environments still on the legacy package
    from tree_sitter_languages import get_parser
from src.orchestration.state.graph_state import MigrationState, CodeArtifact, AnalysisPhase


class ASTAnalysisNode:
    """
    Node that parses code into AST representations using tree-sitter.

    Responsibilities:
    - Parse source files using tree-sitter
    - Extract structural entities (classes, functions, methods)
    - Calculate complexity metrics
    - Store AST for downstream processing
    """

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.parsers = {}
        self.supported_languages = set()
        self._initialize_parsers()

    def _initialize_parsers(self):
        """
        Initialize tree-sitter parsers for supported languages.

        Uses tree-sitter-languages package which provides pre-built
        parsers for common languages.
        """
        # Languages supported by tree-sitter-languages
        languages_to_try = [
            "java", "python", "javascript", "typescript",
            "c", "cpp", "go", "rust", "ruby", "php",
            "c_sharp", "bash", "html", "css", "json"
        ]

        for lang in languages_to_try:
            try:
                parser = get_parser(lang)
                self.parsers[lang] = parser
                self.supported_languages.add(lang)
            except Exception as e:
                # Language not available - skip silently
                pass

        print(f"  Initialized tree-sitter parsers for {len(self.supported_languages)} languages")

    def _map_language_name(self, language: str) -> Optional[str]:
        """
        Map our language names to tree-sitter language names.

        Args:
            language: Language name from our system

        Returns:
            tree-sitter language name or None if not supported
        """
        mapping = {
            "javascript": "javascript",
            "typescript": "typescript",
            "java": "java",
            "python": "python",
            "c": "c",
            "cpp": "cpp",
            "go": "go",
            "rust": "rust",
            "ruby": "ruby",
            "php": "php",
            "csharp": "c_sharp",
            "bash": "bash",
            "shell": "bash",
            "html": "html",
            "css": "css",
            "json": "json",
        }

        return mapping.get(language.lower())

    def parse_artifact(self, artifact: CodeArtifact) -> Optional[Dict[str, Any]]:
        """
        Parse a single code artifact into an AST.

        Args:
            artifact: CodeArtifact to parse

        Returns:
            AST representation or None if parsing fails
        """
        language = artifact["language"]
        ts_language = self._map_language_name(language)

        if not ts_language or ts_language not in self.parsers:
            # Language not supported by tree-sitter - return placeholder
            return {
                "type": "program",
                "language": language,
                "file_path": artifact["path"],
                "root_node": None,
                "supported": False,
                "metadata": {
                    "parsed": False,
                    "reason": "Language not supported by tree-sitter",
                }
            }

        try:
            parser = self.parsers[ts_language]
            tree = parser.parse(bytes(artifact["content"], "utf8"))

            return {
                "type": tree.root_node.type,
                "language": language,
                "file_path": artifact["path"],
                "root_node": tree.root_node,
                "supported": True,
                "metadata": {
                    "parsed": True,
                    "parser_version": "tree-sitter-0.21.3",
                    "node_count": self._count_nodes(tree.root_node),
                }
            }

        except Exception as e:
            return {
                "type": "error",
                "language": language,
                "file_path": artifact["path"],
                "root_node": None,
                "supported": False,
                "metadata": {
                    "parsed": False,
                    "error": str(e),
                }
            }

    def _count_nodes(self, node) -> int:
        """Count total nodes in AST"""
        count = 1
        for child in node.children:
            count += self._count_nodes(child)
        return count

    def extract_entities(self, ast: Dict[str, Any], language: str) -> Dict[str, List[Dict]]:
        """
        Extract high-level entities from AST.

        Args:
            ast: Parsed AST
            language: Source language

        Returns:
            Dictionary of entity types to entity lists
        """
        entities = {
            "classes": [],
            "functions": [],
            "methods": [],
            "imports": [],
            "variables": []
        }

        if not ast.get("supported") or not ast.get("root_node"):
            return entities

        root_node = ast["root_node"]

        # Language-specific entity extraction
        if language == "java":
            self._extract_java_entities(root_node, entities)
        elif language == "python":
            self._extract_python_entities(root_node, entities)
        elif language in ["javascript", "typescript"]:
            self._extract_javascript_entities(root_node, entities)
        elif language in ["c", "cpp"]:
            self._extract_c_entities(root_node, entities)
        else:
            # Generic extraction for other languages
            self._extract_generic_entities(root_node, entities)

        return entities

    def _extract_java_entities(self, node, entities: Dict):
        """Extract entities from Java AST"""
        def walk(n):
            if n.type == "class_declaration":
                class_name = None
                for child in n.children:
                    if child.type == "identifier":
                        class_name = child.text.decode('utf8')
                        break

                if class_name:
                    entities["classes"].append({
                        "name": class_name,
                        "line_start": n.start_point[0] + 1,
                        "line_end": n.end_point[0] + 1,
                        "type": "class"
                    })

            elif n.type == "method_declaration":
                method_name = None
                for child in n.children:
                    if child.type == "identifier":
                        method_name = child.text.decode('utf8')
                        break

                if method_name:
                    entities["methods"].append({
                        "name": method_name,
                        "line_start": n.start_point[0] + 1,
                        "line_end": n.end_point[0] + 1,
                        "type": "method"
                    })

            elif n.type == "import_declaration":
                import_text = n.text.decode('utf8').strip()
                entities["imports"].append({
                    "statement": import_text,
                    "line": n.start_point[0] + 1
                })

            for child in n.children:
                walk(child)

        walk(node)

    def _extract_python_entities(self, node, entities: Dict):
        """Extract entities from Python AST"""
        def walk(n):
            if n.type == "class_definition":
                class_name = None
                for child in n.children:
                    if child.type == "identifier":
                        class_name = child.text.decode('utf8')
                        break

                if class_name:
                    entities["classes"].append({
                        "name": class_name,
                        "line_start": n.start_point[0] + 1,
                        "line_end": n.end_point[0] + 1,
                        "type": "class"
                    })

            elif n.type == "function_definition":
                func_name = None
                for child in n.children:
                    if child.type == "identifier":
                        func_name = child.text.decode('utf8')
                        break

                if func_name:
                    entities["functions"].append({
                        "name": func_name,
                        "line_start": n.start_point[0] + 1,
                        "line_end": n.end_point[0] + 1,
                        "type": "function"
                    })

            elif n.type == "import_statement" or n.type == "import_from_statement":
                import_text = n.text.decode('utf8').strip()
                entities["imports"].append({
                    "statement": import_text,
                    "line": n.start_point[0] + 1
                })

            for child in n.children:
                walk(child)

        walk(node)

    def _extract_javascript_entities(self, node, entities: Dict):
        """Extract entities from JavaScript/TypeScript AST"""
        def walk(n):
            if n.type == "class_declaration":
                class_name = None
                for child in n.children:
                    if child.type == "identifier":
                        class_name = child.text.decode('utf8')
                        break

                if class_name:
                    entities["classes"].append({
                        "name": class_name,
                        "line_start": n.start_point[0] + 1,
                        "line_end": n.end_point[0] + 1,
                        "type": "class"
                    })

            elif n.type in ["function_declaration", "function"]:
                func_name = None
                for child in n.children:
                    if child.type == "identifier":
                        func_name = child.text.decode('utf8')
                        break

                if func_name:
                    entities["functions"].append({
                        "name": func_name,
                        "line_start": n.start_point[0] + 1,
                        "line_end": n.end_point[0] + 1,
                        "type": "function"
                    })

            elif n.type == "import_statement":
                import_text = n.text.decode('utf8').strip()
                entities["imports"].append({
                    "statement": import_text,
                    "line": n.start_point[0] + 1
                })

            for child in n.children:
                walk(child)

        walk(node)

    def _extract_c_entities(self, node, entities: Dict):
        """Extract entities from C/C++ AST"""
        def walk(n):
            if n.type == "function_definition":
                func_name = None
                for child in n.children:
                    if child.type == "function_declarator":
                        for subchild in child.children:
                            if subchild.type == "identifier":
                                func_name = subchild.text.decode('utf8')
                                break

                if func_name:
                    entities["functions"].append({
                        "name": func_name,
                        "line_start": n.start_point[0] + 1,
                        "line_end": n.end_point[0] + 1,
                        "type": "function"
                    })

            for child in n.children:
                walk(child)

        walk(node)

    def _extract_generic_entities(self, node, entities: Dict):
        """Generic entity extraction for unsupported languages"""
        # For unsupported languages, do a generic walk looking for common patterns
        def walk(n):
            node_type = n.type.lower()

            # Look for class-like structures
            if "class" in node_type and "declaration" in node_type:
                entities["classes"].append({
                    "name": f"class_at_line_{n.start_point[0] + 1}",
                    "line_start": n.start_point[0] + 1,
                    "line_end": n.end_point[0] + 1,
                    "type": "class"
                })

            # Look for function-like structures
            elif "function" in node_type or "method" in node_type:
                entities["functions"].append({
                    "name": f"function_at_line_{n.start_point[0] + 1}",
                    "line_start": n.start_point[0] + 1,
                    "line_end": n.end_point[0] + 1,
                    "type": "function"
                })

            for child in n.children:
                walk(child)

        walk(node)

    def calculate_complexity(self, ast: Dict[str, Any]) -> float:
        """
        Calculate cyclomatic complexity from AST.

        Args:
            ast: Parsed AST

        Returns:
            Complexity score (1.0 = simple, higher = more complex)
        """
        if not ast.get("supported") or not ast.get("root_node"):
            return 1.0

        root_node = ast["root_node"]

        # Count decision points
        decision_nodes = [
            "if_statement", "while_statement", "for_statement",
            "case_statement", "conditional_expression",
            "binary_expression",  # For && and ||
            "catch_clause", "except_clause"
        ]

        complexity = 1  # Base complexity

        def walk(node):
            nonlocal complexity

            # Count decision points
            if node.type in decision_nodes:
                complexity += 1

            # For binary expressions, check if it's a logical operator
            if node.type == "binary_expression":
                op_text = ""
                for child in node.children:
                    if child.type in ["&&", "||", "and", "or"]:
                        complexity += 1

            for child in node.children:
                walk(child)

        walk(root_node)

        return float(complexity)

    def __call__(self, state: MigrationState) -> MigrationState:
        """
        Execute the AST analysis node.

        Args:
            state: Current workflow state

        Returns:
            Updated state with AST analysis results
        """
        print(f"🌳 Analyzing AST for {len(state['code_artifacts'])} files...")

        ast_trees = {}
        parsed_entities = {
            "classes": [],
            "functions": [],
            "methods": [],
            "imports": [],
            "variables": []
        }

        parsed_count = 0
        skipped_count = 0

        for i, artifact in enumerate(state["code_artifacts"]):
            if i % 10 == 0 and i > 0:
                print(f"  Progress: {i}/{len(state['code_artifacts'])}")

            try:
                # Parse artifact
                ast = self.parse_artifact(artifact)

                if ast:
                    if ast.get("supported"):
                        parsed_count += 1

                        # Extract entities
                        entities = self.extract_entities(ast, artifact["language"])
                        for entity_type, entity_list in entities.items():
                            parsed_entities[entity_type].extend(entity_list)

                        # Calculate complexity
                        complexity = self.calculate_complexity(ast)
                        artifact["complexity_score"] = complexity
                        artifact["ast_representation"] = {
                            "type": ast["type"],
                            "supported": True,
                            "node_count": ast["metadata"].get("node_count", 0)
                        }

                        # Remove non-serializable tree-sitter Node from ast before storing
                        ast_for_storage = {
                            "type": ast["type"],
                            "language": ast["language"],
                            "file_path": ast["file_path"],
                            "supported": ast["supported"],
                            "metadata": ast["metadata"]
                        }
                        ast_trees[artifact["path"]] = ast_for_storage
                    else:
                        skipped_count += 1
                        artifact["complexity_score"] = 1.0
                        artifact["ast_representation"] = {
                            "type": "unsupported",
                            "supported": False,
                            "reason": ast["metadata"].get("reason", "Unknown")
                        }

                        # Store serializable version for unsupported languages
                        ast_trees[artifact["path"]] = {
                            "type": ast["type"],
                            "language": ast["language"],
                            "file_path": ast["file_path"],
                            "supported": False,
                            "metadata": ast["metadata"]
                        }

            except Exception as e:
                state["warnings"].append(f"Failed to parse {artifact['path']}: {str(e)}")
                skipped_count += 1

        # Update state
        state["ast_trees"] = ast_trees
        state["parsed_entities"] = parsed_entities
        state["phase"] = AnalysisPhase.DEPENDENCY_MAPPING

        total_entities = sum(len(v) for v in parsed_entities.values())

        print(f"✅ Parsed {parsed_count} files ({skipped_count} unsupported)")
        print(f"📊 Found: {total_entities} entities ({len(parsed_entities['classes'])} classes, {len(parsed_entities['functions'])} functions)")

        return state
