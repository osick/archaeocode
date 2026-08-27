# Pascal Test Samples

Legacy Pascal code samples for testing reverse engineering workflow.

## Files

### inventory.pas
- **Type**: Turbo Pascal
- **Domain**: Business / Retail
- **Purpose**: Warehouse inventory management system
- **Features**:
  - Records and arrays
  - Procedures and functions
  - Menu-driven interface
  - Data validation
  - Reorder level alerts
- **Lines of Code**: ~310
- **Typical Migration**: Java (Spring Boot) or Python (Django)

### payroll.pas
- **Type**: Standard Pascal
- **Domain**: Human Resources / Payroll
- **Purpose**: Employee payroll calculation with taxes and deductions
- **Features**:
  - Enumerated types
  - Record structures
  - Tax calculations
  - Multi-type employee handling (Hourly, Salaried, Contract)
  - Report generation
- **Lines of Code**: ~340
- **Typical Migration**: Java (enterprise HR systems) or C# (.NET)

## Legacy Characteristics

These samples represent typical Pascal code found in:
- Educational institutions (teaching systems from 1980s-1990s)
- Small business applications
- Early PC-based business software
- Banking and finance systems

### Common Patterns
- Strong typing with records
- Procedural programming
- Uses Crt unit for console manipulation
- Menu-driven text interfaces
- Fixed-size arrays
- Case statements for flow control
- Pass-by-reference (var parameters)

## Testing Use Cases

These files are useful for testing:
1. AST parsing of Pascal syntax
2. Record/struct type analysis
3. Procedure/function extraction
4. Business logic identification
5. User story generation from business domain code
6. Control flow analysis (case statements, loops)
7. Data structure migration planning
8. UI modernization (console → web)
