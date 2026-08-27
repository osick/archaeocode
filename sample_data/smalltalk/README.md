# Smalltalk Sample Code

This directory contains sample Smalltalk code for testing the tree-sitter-smalltalk parser integration.

## Files

### Counter.st
**Type:** Standard Smalltalk (Squeak/Pharo style)
**Description:** A simple counter class demonstrating basic Smalltalk syntax

**Features:**
- Class definition with instance variables
- Multiple method categories (initialization, accessing, operations, testing, printing)
- Instance methods and class methods
- Basic arithmetic operations
- Boolean testing methods

**Entity Counts:**
- Classes: 1 (Counter)
- Methods: 13 (11 instance + 2 class methods)
- Method categories: 5

### BankAccount.st
**Type:** Cincom VisualWorks style Smalltalk
**Description:** A bank account class with namespace syntax

**Features:**
- Namespace-style class definition (`Smalltalk.Examples`)
- Multiple method categories
- Block closures
- Error handling (`ifTrue:`, `error:`)
- Collection operations (OrderedCollection, Dictionary)
- Control flow (conditionals, blocks)

**Entity Counts:**
- Classes: 1 (BankAccount)
- Methods: 16 (13 instance + 3 class methods)
- Method categories: 6
- Blocks: ~15 (closures)

## Language Variants

### Standard Smalltalk (Squeak/Pharo/GNU)
Use language code: `smalltalk`, `squeak`, or `pharo`

```python
from src.langgraph.graph_mcp import ReverseEngineeringWorkflowMCP

workflow = ReverseEngineeringWorkflowMCP()
result = await workflow.run(
    source_directory="sample_data/smalltalk",
    language="smalltalk"
)
```

### Cincom VisualWorks
Use language code: `smalltalk-cincom`, `cincom`, or `visualworks`

```python
workflow = ReverseEngineeringWorkflowMCP()
result = await workflow.run(
    source_directory="sample_data/smalltalk",
    language="smalltalk-cincom"  # Enables Cincom-specific parsing
)
```

## Testing

### Quick Test

```bash
# Build the grammar first (one-time setup)
python scripts/build_smalltalk_grammar.py

# Test parsing directly
python -c "
from src.mcp_servers.static_analysis import custom_languages
parser = custom_languages.get_parser('smalltalk')
code = open('sample_data/smalltalk/Counter.st', 'rb').read()
tree = parser.parse(code)
print(f'Parsed successfully: {tree.root_node.type}')
print(f'Node count: {tree.root_node.end_byte - tree.root_node.start_byte} bytes')
"
```

### Full Workflow Test

```bash
# Test with MCP workflow
python tests/test_workflow_mcp.py --language smalltalk --directory sample_data/smalltalk
```

## Expected Results

### Counter.st Analysis
```
Files: 1
Methods: 13
  - initialize
  - count, count:
  - increment, decrement, incrementBy:, reset
  - isZero, isPositive, isNegative
  - printOn:
  - Class methods: new, startingAt:
```

### BankAccount.st Analysis
```
Files: 1
Methods: 16
  - initialize
  - accountNumber, balance, owner, owner:, transactionHistory
  - deposit:, withdraw:, transferTo:amount:
  - canWithdraw:, hasPositiveBalance, isOverdrawn
  - printStatementOn:, printTransactionsOn:
  - Class methods: new, forOwner:, forOwner:withInitialDeposit:, generateAccountNumber
Blocks: ~15 (closures/blocks)
```

## Smalltalk Syntax Notes

### Class Definition
```smalltalk
Object subclass: #ClassName
    instanceVariableNames: 'var1 var2'
    classVariableNames: ''
    poolDictionaries: ''
    category: 'Category'
```

### Method Definition
```smalltalk
!ClassName methodsFor: 'category'!

methodName
    "Method comment"
    ^ self doSomething
! !
```

### Message Sends
- **Unary:** `object message`
- **Binary:** `a + b`, `x <= y`
- **Keyword:** `object keyword1: arg1 keyword2: arg2`

### Blocks (Closures)
```smalltalk
[ :arg | arg + 1 ]  "Block with argument"
[ self doSomething ]  "Block without arguments"
```

### Control Flow
```smalltalk
condition ifTrue: [ action ].
condition ifFalse: [ alternative ] ifTrue: [ action ].
collection do: [ :each | each process ].
```

## Key Differences: Standard vs Cincom

| Feature | Standard (Squeak) | Cincom VisualWorks |
|---------|-------------------|---------------------|
| Class definition | `Object subclass: #Name` | `Smalltalk.Namespace defineClass: #Name` |
| Namespace | Implicit | Explicit (`#{Core.Object}`) |
| Imports | N/A | `imports: ''` clause |
| Method syntax | Same | Same |
| Blocks | Same | Same |

## AST Node Types

The tree-sitter-smalltalk grammar produces these key node types:

- `method` - Method definitions
- `unary_selector`, `binary_selector`, `keyword_selector` - Method names
- `keyword_message` - Keyword message sends (including class definitions)
- `unary_message`, `binary_message` - Simpler message sends
- `block` - Block closures `[ ... ]`
- `symbol` - Symbols like `#ClassName`
- `identifier` - Variable and method names
- `string`, `number` - Literals

## Troubleshooting

### Grammar Not Found
```
Error: Smalltalk grammar not built
Solution: Run python scripts/build_smalltalk_grammar.py
```

### Parse Errors
- Check file encoding (should be UTF-8)
- Verify Smalltalk syntax is valid
- Some Cincom-specific syntax may need the `smalltalk-cincom` language variant

### No Entities Extracted
- Ensure methods are in the correct format with `!` delimiters
- Check that the grammar was built successfully
- Verify file extension is `.st`

## References

- **Tree-sitter-smalltalk:** https://github.com/tom95/tree-sitter-smalltalk
- **Squeak Smalltalk:** https://squeak.org/
- **Pharo Smalltalk:** https://pharo.org/
- **Cincom VisualWorks:** https://www.cincomsmalltalk.com/main/products/visualworks/
- **GNU Smalltalk:** https://www.gnu.org/software/smalltalk/

## License

Sample code is provided for testing purposes under the project's license.
Smalltalk implementations have their own licenses:
- Squeak/Pharo: MIT License
- Cincom VisualWorks: Commercial (free non-commercial version available)
- GNU Smalltalk: GPL
