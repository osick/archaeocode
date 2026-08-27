# Cincom Smalltalk Variant Support

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
