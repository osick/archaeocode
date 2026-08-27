# Fortran Test Samples

Legacy Fortran code samples for testing reverse engineering workflow.

## Files

### TRAJECTORY.f90
- **Type**: Fortran 90/95
- **Domain**: Scientific computing / Aerospace
- **Purpose**: Calculates projectile trajectory with atmospheric drag
- **Features**:
  - Physics simulation with differential equations
  - File I/O operations
  - Iterative calculations
  - Subroutines for atmospheric modeling
- **Lines of Code**: ~115
- **Typical Migration**: Python (NumPy/SciPy) or Java (Apache Commons Math)

### LOANPAY.f
- **Type**: FORTRAN 77
- **Domain**: Financial / Banking
- **Purpose**: Calculates loan amortization schedules
- **Features**:
  - Fixed-format FORTRAN 77 syntax (columns 1-72)
  - DO loops with labels
  - FORMAT statements for output
  - Input validation
- **Lines of Code**: ~120
- **Typical Migration**: Java (financial libraries) or Python (pandas)

## Legacy Characteristics

These samples represent typical Fortran code found in:
- Scientific computing systems (NASA, research labs)
- Financial institutions (banking systems from 1970s-1980s)
- Engineering firms (simulation software)

### Common Patterns
- Implicit variable typing
- GOTO statements and labeled loops
- Column-based formatting (FORTRAN 77)
- Extensive use of COMMON blocks (not shown here)
- Fixed-precision arithmetic
- Procedural programming style

## Testing Use Cases

These files are useful for testing:
1. AST parsing of Fortran syntax
2. Control flow analysis (DO loops, IF-THEN)
3. Mathematical expression extraction
4. User story generation from scientific/financial code
5. Dependency analysis between subroutines
6. Legacy-to-modern language migration
