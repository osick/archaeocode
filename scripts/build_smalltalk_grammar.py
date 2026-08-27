#!/usr/bin/env python3
"""
Build Tree-Sitter Smalltalk Grammar
====================================

This script clones and builds the tree-sitter-smalltalk grammar
for use with the AST analysis MCP server.

Supports both standard Smalltalk (Squeak) and Cincom Smalltalk variants.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path


def run_command(cmd: list[str], cwd: str = None):
    """Run a shell command and handle errors"""
    print(f"Running: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return False
    print(result.stdout)
    return True


def build_smalltalk_grammar():
    """Build the tree-sitter-smalltalk grammar"""

    # Project directories
    project_root = Path(__file__).parent.parent
    grammars_dir = project_root / "grammars"
    smalltalk_dir = grammars_dir / "tree-sitter-smalltalk"
    build_dir = project_root / "build" / "tree-sitter-smalltalk"

    print("=" * 80)
    print("Building Tree-Sitter Smalltalk Grammar")
    print("=" * 80)

    # Create directories
    grammars_dir.mkdir(exist_ok=True)
    build_dir.mkdir(parents=True, exist_ok=True)

    # Step 1: Clone tree-sitter-smalltalk if not exists
    if not smalltalk_dir.exists():
        print("\nStep 1: Cloning tree-sitter-smalltalk...")
        if not run_command([
            "git", "clone",
            "https://github.com/tom95/tree-sitter-smalltalk.git",
            str(smalltalk_dir)
        ]):
            print("✗ Failed to clone tree-sitter-smalltalk")
            return False
        print("✓ Cloned tree-sitter-smalltalk")
    else:
        print("\nStep 1: tree-sitter-smalltalk already cloned")
        # Update to latest
        print("Updating to latest version...")
        run_command(["git", "pull"], cwd=str(smalltalk_dir))

    # Step 2: Build the grammar using tree-sitter CLI (optional)
    print("\nStep 2: Checking tree-sitter CLI (optional)...")

    # Check if tree-sitter CLI is installed
    try:
        result = subprocess.run(
            ["tree-sitter", "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            # Generate parser if CLI is available
            print(f"✓ tree-sitter CLI found: {result.stdout.strip()}")
            print("Generating parser...")
            if run_command(["tree-sitter", "generate"], cwd=str(smalltalk_dir)):
                print("✓ Generated parser")
            else:
                print("⚠️  Parser generation failed, will use existing grammar")
        else:
            print("⚠️  tree-sitter CLI not working properly")
            print("The parser will be built directly from the grammar repository")
    except FileNotFoundError:
        print("⚠️  tree-sitter CLI not found (optional)")
        print("The parser will be built directly from the grammar repository")
        print("If you want to use tree-sitter CLI, install it with:")
        print("  npm install -g tree-sitter-cli")

    # Step 3: Build Python bindings using tree-sitter 0.21.3
    print("\nStep 3: Building Python bindings...")

    # Create build script
    build_script = f'''
import sys
from pathlib import Path
from tree_sitter import Language

# Path to the grammar
grammar_path = Path("{smalltalk_dir}")

# Output path for compiled language
output_path = Path("{build_dir}") / "smalltalk.so"
output_path.parent.mkdir(parents=True, exist_ok=True)

print(f"Building Smalltalk language from {{grammar_path}}")
print(f"Output: {{output_path}}")

try:
    Language.build_library(
        str(output_path),
        [str(grammar_path)]
    )
    print("✓ Successfully built Smalltalk language library")
    print(f"Library saved to: {{output_path}}")
    sys.exit(0)
except Exception as e:
    print(f"✗ Error building language: {{e}}")
    sys.exit(1)
'''

    build_script_path = build_dir / "build.py"
    with open(build_script_path, 'w') as f:
        f.write(build_script)

    # Run build script
    if not run_command([sys.executable, str(build_script_path)]):
        print("✗ Failed to build Python bindings")
        return False

    print("\n" + "=" * 80)
    print("✓ SMALLTALK GRAMMAR BUILD COMPLETE")
    print("=" * 80)
    print(f"\nCompiled library location: {build_dir / 'smalltalk.so'}")
    print("\nThe Smalltalk grammar is now ready to use!")
    print("\nNote: This grammar supports Squeak-style Smalltalk.")
    print("For Cincom Smalltalk, some syntax variations may require adjustments.")

    return True


def create_cincom_notes():
    """Create documentation about Cincom Smalltalk differences"""

    project_root = Path(__file__).parent.parent
    docs_dir = project_root / "docs"

    cincom_notes = """# Cincom Smalltalk Variant Support

## Overview

The tree-sitter-smalltalk grammar primarily targets **Squeak** Smalltalk syntax.
Cincom VisualWorks Smalltalk has some syntax differences that may require handling.

## Key Differences

### 1. Namespace Syntax

**Cincom VisualWorks:**
```smalltalk
Smalltalk.MyNamespace at: #MyClass
```

**Squeak/Standard:**
```smalltalk
MyClass
```

### 2. Class Definition

**Cincom VisualWorks:**
```smalltalk
Object subclass: #MyClass
    instanceVariableNames: 'var1 var2'
    classVariableNames: ''
    poolDictionaries: ''
    category: 'MyCategory'
```

**Standard (similar):**
Both use similar syntax for class definition.

### 3. Method Annotations

**Cincom VisualWorks:**
```smalltalk
method
    <primitive: 1>
    <category: 'accessing'>
    ^ self
```

Both support pragmas/annotations in similar ways.

## Current Support Status

- ✅ **Squeak Smalltalk:** Fully supported
- ⚠️ **Cincom VisualWorks:** Mostly supported, namespace syntax may need special handling
- ⚠️ **GNU Smalltalk:** Mostly supported
- ⚠️ **Pharo:** Mostly supported (Pharo is Squeak-based)

## Handling Variants

The AST analysis server treats all Smalltalk code the same way initially.
If specific Cincom features are needed, you can:

1. Add a `smalltalk-cincom` language variant in the LANGUAGE_MAP
2. Create a separate entity extractor for Cincom-specific syntax
3. Use AST queries to detect and handle namespace syntax

## Testing

Test with both Squeak and Cincom code samples to identify any parsing issues.
The grammar should handle most standard Smalltalk syntax across variants.

## Recommendations

1. **Start with standard Smalltalk syntax** - Most features are common
2. **Use namespace-agnostic code when possible**
3. **Add Cincom-specific handling only if needed**
4. **Test with real Cincom code samples** to identify edge cases

## Future Enhancements

If Cincom-specific support is critical, consider:

1. Forking tree-sitter-smalltalk to add Cincom syntax
2. Creating a preprocessing step for namespace resolution
3. Adding variant detection in the entity extractor
"""

    with open(docs_dir / "SMALLTALK_VARIANTS.md", 'w') as f:
        f.write(cincom_notes)

    print(f"\n✓ Created Cincom Smalltalk documentation: {docs_dir / 'SMALLTALK_VARIANTS.md'}")


def main():
    """Main entry point"""
    print("\nTree-Sitter Smalltalk Grammar Builder")
    print("This will download and build tree-sitter-smalltalk")
    print()

    if build_smalltalk_grammar():
        create_cincom_notes()
        print("\n✓ Setup complete!")
        print("\nNext steps:")
        print("1. The Smalltalk grammar is now available")
        print("2. Update ast_analysis_server.py to use it")
        print("3. Test with Smalltalk code samples")
        return 0
    else:
        print("\n✗ Setup failed")
        print("Please check the errors above and try again")
        return 1


if __name__ == "__main__":
    sys.exit(main())
