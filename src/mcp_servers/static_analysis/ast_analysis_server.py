"""
AST Analysis MCP Server
========================

MCP server for code parsing and analysis using tree-sitter.
Uses the official Anthropic MCP SDK.

This server exposes tools for:
- Parsing source code into AST
- Extracting entities (classes, functions, methods)
- Querying AST structure
- Calculating complexity metrics
"""

from typing import Any
try:  # mcp >= 2.0
    from mcp.server import MCPServer
except ImportError:  # mcp 1.x
    from mcp.server.fastmcp import FastMCP as MCPServer
from mcp import types
try:
    from tree_sitter_language_pack import get_parser as get_standard_parser
except ImportError:  # fallback for environments still on the legacy package
    from tree_sitter_languages import get_parser as get_standard_parser
import json

# Import custom language loader for Smalltalk support
try:
    from . import custom_languages
    CUSTOM_LANGUAGES_AVAILABLE = True
except ImportError:
    CUSTOM_LANGUAGES_AVAILABLE = False
    custom_languages = None


# Create MCP server instance
server = MCPServer("ast-analysis")


# Language mapping (from our existing code)
LANGUAGE_MAP = {
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
    # Smalltalk support (custom grammars)
    "smalltalk": "smalltalk",
    "squeak": "smalltalk",
    "pharo": "smalltalk",
    "smalltalk-cincom": "smalltalk-cincom",
    "cincom": "smalltalk-cincom",
    "visualworks": "smalltalk-cincom",
}


def get_tree_sitter_language(language: str) -> str | None:
    """Map language name to tree-sitter language"""
    return LANGUAGE_MAP.get(language.lower())


def get_parser(language: str):
    """
    Get parser for a language (standard or custom).

    Args:
        language: Tree-sitter language name

    Returns:
        Parser object

    Raises:
        Exception if language not supported
    """
    # Check if it's a custom language
    if CUSTOM_LANGUAGES_AVAILABLE and custom_languages.is_custom_language(language):
        parser = custom_languages.get_parser(language)
        if parser:
            return parser
        # If custom language is configured but not built, fall through to error

    # Try standard languages
    try:
        return get_standard_parser(language)
    except Exception:
        # If standard fails and it was supposed to be custom, give helpful error
        if language in ["smalltalk", "smalltalk-cincom"]:
            raise Exception(
                f"Smalltalk grammar not built. "
                f"Run: python scripts/build_smalltalk_grammar.py"
            )
        raise


def count_nodes(node) -> int:
    """Count total nodes in AST"""
    count = 1
    for child in node.children:
        count += count_nodes(child)
    return count


def extract_java_entities(node, entities: dict):
    """Extract entities from Java AST"""
    def walk(n):
        if n.type == "class_declaration":
            for child in n.children:
                if child.type == "identifier":
                    entities["classes"].append({
                        "name": child.text.decode('utf8'),
                        "line_start": n.start_point[0] + 1,
                        "line_end": n.end_point[0] + 1,
                    })
                    break

        elif n.type == "method_declaration":
            for child in n.children:
                if child.type == "identifier":
                    entities["methods"].append({
                        "name": child.text.decode('utf8'),
                        "line_start": n.start_point[0] + 1,
                        "line_end": n.end_point[0] + 1,
                    })
                    break

        elif n.type == "import_declaration":
            entities["imports"].append({
                "statement": n.text.decode('utf8').strip(),
                "line": n.start_point[0] + 1
            })

        for child in n.children:
            walk(child)

    walk(node)


def extract_python_entities(node, entities: dict):
    """Extract entities from Python AST"""
    def walk(n):
        if n.type == "class_definition":
            for child in n.children:
                if child.type == "identifier":
                    entities["classes"].append({
                        "name": child.text.decode('utf8'),
                        "line_start": n.start_point[0] + 1,
                        "line_end": n.end_point[0] + 1,
                    })
                    break

        elif n.type == "function_definition":
            for child in n.children:
                if child.type == "identifier":
                    entities["functions"].append({
                        "name": child.text.decode('utf8'),
                        "line_start": n.start_point[0] + 1,
                        "line_end": n.end_point[0] + 1,
                    })
                    break

        elif n.type in ["import_statement", "import_from_statement"]:
            entities["imports"].append({
                "statement": n.text.decode('utf8').strip(),
                "line": n.start_point[0] + 1
            })

        for child in n.children:
            walk(child)

    walk(node)


def extract_javascript_entities(node, entities: dict):
    """Extract entities from JavaScript/TypeScript AST"""
    def walk(n):
        if n.type == "class_declaration":
            for child in n.children:
                if child.type == "identifier":
                    entities["classes"].append({
                        "name": child.text.decode('utf8'),
                        "line_start": n.start_point[0] + 1,
                        "line_end": n.end_point[0] + 1,
                    })
                    break

        elif n.type in ["function_declaration", "function"]:
            for child in n.children:
                if child.type == "identifier":
                    entities["functions"].append({
                        "name": child.text.decode('utf8'),
                        "line_start": n.start_point[0] + 1,
                        "line_end": n.end_point[0] + 1,
                    })
                    break

        elif n.type == "import_statement":
            entities["imports"].append({
                "statement": n.text.decode('utf8').strip(),
                "line": n.start_point[0] + 1
            })

        for child in n.children:
            walk(child)

    walk(node)


def extract_smalltalk_entities(node, entities: dict, is_cincom: bool = False):
    """
    Extract entities from Smalltalk AST.

    In Smalltalk, methods are the primary code unit. Classes are typically
    defined via message sends (e.g., "Object subclass: #MyClass...").

    Args:
        node: Root AST node
        entities: Dict to populate with extracted entities
        is_cincom: Whether this is Cincom Smalltalk (for namespace handling)
    """
    def walk(n):
        # Method definitions
        if n.type == "method":
            # Extract method selector (name)
            for child in n.children:
                if child.type in ["unary_selector", "binary_selector", "keyword_selector"]:
                    method_name = child.text.decode('utf8').strip()
                    entities["methods"].append({
                        "name": method_name,
                        "line_start": n.start_point[0] + 1,
                        "line_end": n.end_point[0] + 1,
                        "type": "method"
                    })
                    break

        # Class definitions (via subclass: messages)
        # Pattern: "Object subclass: #ClassName"
        elif n.type == "keyword_message":
            # Check if this is a class definition message
            text = n.text.decode('utf8', errors='ignore')
            if "subclass:" in text:
                # Try to extract class name
                for child in n.children:
                    if child.type == "symbol":
                        class_name = child.text.decode('utf8').strip().lstrip('#')
                        entities["classes"].append({
                            "name": class_name,
                            "line_start": n.start_point[0] + 1,
                            "line_end": n.end_point[0] + 1,
                            "type": "class_definition"
                        })
                        break

        # Message sends (for imports/dependencies)
        # In Smalltalk, there are no explicit imports, but we track message sends
        elif n.type in ["unary_message", "binary_message", "keyword_message"]:
            # Record significant message patterns
            text = n.text.decode('utf8', errors='ignore').strip()

            # Track class/namespace references (Cincom style)
            if is_cincom and "." in text and text.count('.') <= 2:
                entities["imports"].append({
                    "statement": text,
                    "line": n.start_point[0] + 1,
                    "type": "namespace_reference"
                })

        # Blocks (closures) - important Smalltalk construct
        elif n.type == "block":
            # Count blocks as a metric (similar to functions)
            entities.setdefault("blocks", []).append({
                "line_start": n.start_point[0] + 1,
                "line_end": n.end_point[0] + 1,
            })

        # Recurse
        for child in n.children:
            walk(child)

    walk(node)

    # If no blocks key was created, ensure it exists
    entities.setdefault("blocks", [])


def calculate_complexity(node) -> float:
    """Calculate cyclomatic complexity from AST"""
    decision_nodes = [
        "if_statement", "while_statement", "for_statement",
        "case_statement", "conditional_expression",
        "catch_clause", "except_clause"
    ]

    complexity = 1  # Base complexity

    def walk(n):
        nonlocal complexity
        if n.type in decision_nodes:
            complexity += 1
        for child in n.children:
            walk(child)

    walk(node)
    return float(complexity)


# MCP Tool: parse_file
@server.tool()
async def parse_file(file_path: str, language: str) -> list[types.TextContent]:
    """
    Parse a source code file into an AST.

    Args:
        file_path: Path to the source file
        language: Programming language (java, python, javascript, etc.)

    Returns:
        AST structure with metadata
    """
    ts_language = get_tree_sitter_language(language)

    if not ts_language:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "error": f"Language not supported: {language}",
                "supported_languages": list(LANGUAGE_MAP.keys())
            }, indent=2)
        )]

    try:
        # Read file
        with open(file_path, 'rb') as f:
            source_code = f.read()

        # Parse with tree-sitter
        parser = get_parser(ts_language)
        tree = parser.parse(source_code)
        root = tree.root_node

        # Build result
        result = {
            "success": True,
            "file_path": file_path,
            "language": language,
            "ast": {
                "type": root.type,
                "start_point": {
                    "row": root.start_point[0],
                    "column": root.start_point[1]
                },
                "end_point": {
                    "row": root.end_point[0],
                    "column": root.end_point[1]
                },
                "byte_range": {
                    "start": root.start_byte,
                    "end": root.end_byte
                },
                "node_count": count_nodes(root),
                "has_error": root.has_error
            }
        }

        return [types.TextContent(
            type="text",
            text=json.dumps(result, indent=2)
        )]

    except Exception as e:
        return [types.TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "file_path": file_path,
                "language": language
            }, indent=2)
        )]


# MCP Tool: extract_entities
@server.tool()
async def extract_entities(file_path: str, language: str) -> list[types.TextContent]:
    """
    Extract entities (classes, functions, methods, imports) from code.

    Args:
        file_path: Path to the source file
        language: Programming language

    Returns:
        Dictionary of entity types to entity lists
    """
    ts_language = get_tree_sitter_language(language)

    if not ts_language:
        return [types.TextContent(
            type="text",
            text=json.dumps({"error": f"Language not supported: {language}"}, indent=2)
        )]

    try:
        # Read and parse
        with open(file_path, 'rb') as f:
            source_code = f.read()

        parser = get_parser(ts_language)
        tree = parser.parse(source_code)
        root = tree.root_node

        # Extract entities based on language
        entities = {
            "classes": [],
            "functions": [],
            "methods": [],
            "imports": []
        }

        if language == "java":
            extract_java_entities(root, entities)
        elif language == "python":
            extract_python_entities(root, entities)
        elif language in ["javascript", "typescript"]:
            extract_javascript_entities(root, entities)
        elif language in ["smalltalk", "squeak", "pharo"]:
            extract_smalltalk_entities(root, entities, is_cincom=False)
        elif language in ["smalltalk-cincom", "cincom", "visualworks"]:
            extract_smalltalk_entities(root, entities, is_cincom=True)

        result = {
            "success": True,
            "file_path": file_path,
            "language": language,
            "entities": entities,
            "summary": {
                "classes": len(entities["classes"]),
                "functions": len(entities["functions"]),
                "methods": len(entities["methods"]),
                "imports": len(entities["imports"]),
                "total": sum(len(v) for v in entities.values())
            }
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


# MCP Tool: calculate_complexity
@server.tool()
async def get_complexity(file_path: str, language: str) -> list[types.TextContent]:
    """
    Calculate cyclomatic complexity for a source file.

    Args:
        file_path: Path to the source file
        language: Programming language

    Returns:
        Complexity score and breakdown
    """
    ts_language = get_tree_sitter_language(language)

    if not ts_language:
        return [types.TextContent(
            type="text",
            text=json.dumps({"error": f"Language not supported: {language}"}, indent=2)
        )]

    try:
        # Read and parse
        with open(file_path, 'rb') as f:
            source_code = f.read()

        parser = get_parser(ts_language)
        tree = parser.parse(source_code)
        root = tree.root_node

        # Calculate complexity
        complexity = calculate_complexity(root)

        result = {
            "success": True,
            "file_path": file_path,
            "language": language,
            "complexity": complexity,
            "interpretation": (
                "Simple" if complexity <= 5 else
                "Moderate" if complexity <= 10 else
                "Complex" if complexity <= 20 else
                "Very Complex"
            )
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


# MCP Tool: list_supported_languages
@server.tool()
async def list_supported_languages() -> list[types.TextContent]:
    """
    List all programming languages supported by this MCP server.

    Returns:
        List of supported language names
    """
    result = {
        "supported_languages": list(LANGUAGE_MAP.keys()),
        "total": len(LANGUAGE_MAP)
    }

    return [types.TextContent(
        type="text",
        text=json.dumps(result, indent=2)
    )]


# Main entry point for running the server (stdio transport)
if __name__ == "__main__":
    server.run()
