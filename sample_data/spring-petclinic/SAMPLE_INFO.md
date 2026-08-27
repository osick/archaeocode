# Spring PetClinic Sample Dataset

**Source:** https://github.com/spring-projects/spring-petclinic
**License:** Apache License 2.0
**Purpose:** Large-scale reverse engineering demonstration

---

## Overview

This is a curated sample from the official Spring PetClinic project - a reference implementation demonstrating Spring Boot best practices.

**What it demonstrates:**
- Real-world Spring Boot application architecture
- JPA/Hibernate entity relationships
- Spring MVC controllers
- Service layer patterns
- Repository patterns
- Comprehensive test coverage

---

## Dataset Statistics

```
Total Java Files: 47
Total Lines of Code: 3,678 LOC

Breakdown:
- Source (src/main/java): 30 files, ~1,793 LOC
- Tests (src/test/java): 17 files, ~1,885 LOC
```

---

## Project Structure

```
src/
├── main/
│   ├── java/org/springframework/samples/petclinic/
│   │   ├── model/           # Domain model (entities)
│   │   │   ├── BaseEntity.java
│   │   │   ├── NamedEntity.java
│   │   │   ├── Person.java
│   │   │   ├── Pet.java
│   │   │   ├── PetType.java
│   │   │   ├── Specialty.java
│   │   │   ├── Vet.java
│   │   │   └── Visit.java
│   │   ├── owner/           # Owner domain & controllers
│   │   │   ├── Owner.java
│   │   │   ├── OwnerController.java
│   │   │   ├── OwnerRepository.java
│   │   │   ├── PetController.java
│   │   │   ├── PetRepository.java
│   │   │   ├── PetValidator.java
│   │   │   ├── VisitController.java
│   │   │   └── VisitRepository.java
│   │   ├── vet/             # Veterinarian domain & controllers
│   │   │   ├── Vet.java
│   │   │   ├── VetController.java
│   │   │   └── VetRepository.java
│   │   ├── system/          # System controllers (welcome, error)
│   │   │   ├── WelcomeController.java
│   │   │   └── CrashController.java
│   │   └── PetClinicApplication.java  # Main application entry point
│   └── resources/
│       └── (configuration files)
└── test/
    └── java/org/springframework/samples/petclinic/
        ├── model/           # Model tests
        ├── owner/           # Owner tests
        ├── vet/             # Vet tests
        ├── service/         # Service layer tests
        ├── system/          # System tests
        └── *IntegrationTests.java  # Integration tests
```

---

## Domain Model

### Core Entities

**Owner** (Person)
- First name, last name
- Address, city, telephone
- Has many Pets

**Pet** (NamedEntity)
- Name, birth date
- Belongs to Owner
- Has PetType
- Has many Visits

**Vet** (Person)
- First name, last name
- Has many Specialties

**Visit** (BaseEntity)
- Visit date, description
- Associated with Pet

**PetType** (NamedEntity)
- Name (cat, dog, bird, etc.)

**Specialty** (NamedEntity)
- Name (radiology, surgery, dentistry, etc.)

### Relationships

```
Owner 1---* Pet *---1 PetType
              |
              1
              |
              *
            Visit

Vet *---* Specialty
```

---

## Technologies Used

- **Framework:** Spring Boot 3.x
- **Persistence:** Spring Data JPA / Hibernate
- **Database:** H2 (in-memory), MySQL, PostgreSQL support
- **Web:** Spring MVC, Thymeleaf
- **Testing:** JUnit 5, Spring Test, Mockito
- **Build:** Maven
- **Java Version:** 17+

---

## Key Patterns & Concepts

### Design Patterns
1. **Repository Pattern** - Data access abstraction
2. **Service Layer** - Business logic separation
3. **DTO Pattern** - Data transfer objects
4. **Validator Pattern** - Input validation
5. **MVC Pattern** - Model-View-Controller

### Spring Features
1. **Dependency Injection** - Constructor & field injection
2. **JPA Annotations** - @Entity, @ManyToOne, @OneToMany
3. **Validation** - @NotBlank, @Digits, custom validators
4. **Spring Data** - Automatic repository implementation
5. **Exception Handling** - @ExceptionHandler
6. **Transaction Management** - @Transactional

---

## Complexity Analysis

### Expected Metrics (from reverse engineering)

**Cyclomatic Complexity:**
- Simple methods: 1-5 (getters, setters, simple CRUD)
- Moderate methods: 6-10 (validation, business logic)
- Complex methods: 11-20 (complex queries, multi-step processing)

**Entity Extraction:**
- ~40 classes (entities, controllers, repositories, tests)
- ~200+ methods
- ~50+ imports
- ~100+ dependencies

**Dependency Graph:**
- Controller → Service → Repository pattern
- Circular references in bidirectional relationships (Owner↔Pet)
- Test dependencies on production code

---

## Use Cases for Reverse Engineering

### 1. Architecture Understanding
- Identify layered architecture (Controller → Service → Repository)
- Map domain model relationships
- Understand Spring Boot project structure

### 2. Migration Planning
- Identify dependencies for gradual migration
- Find tightly coupled components
- Discover integration points

### 3. Code Quality Assessment
- Measure complexity metrics
- Find code smells
- Identify test coverage gaps

### 4. Documentation Generation
- Auto-generate entity relationship diagrams
- Extract API documentation from controllers
- Create user stories from controllers

### 5. Refactoring Candidates
- Identify high-complexity methods
- Find duplicated code patterns
- Discover unused code

---

## Running the Sample

### Prerequisites
- Java 17 or higher
- Maven 3.x (or use included mvnw wrapper)

### Build & Run
```bash
cd sample_data/spring-petclinic

# Build
./mvnw package

# Run
java -jar target/spring-petclinic-*.jar

# Access
http://localhost:8080
```

### Test
```bash
# Run all tests
./mvnw test

# Run specific test
./mvnw test -Dtest=OwnerControllerTests
```

---

## Reverse Engineering with Our Tool

### Basic Analysis
```bash
# Analyze with MCP-enabled workflow
python src/langgraph/graph_mcp.py sample_data/spring-petclinic/src/main/java java

# Or use LangServe API
curl -X POST http://localhost:8000/reverse-engineer/invoke \
  -H "Content-Type: application/json" \
  -d '{"source_directory": "sample_data/spring-petclinic/src/main/java", "language": "java"}'
```

### Expected Results
- **Files Discovered:** 30 Java files
- **AST Nodes:** ~15,000+ nodes
- **Entities Extracted:** 40+ classes, 200+ methods
- **Dependencies:** 100+ imports, relationships
- **Complexity:** Average 3-5 per method
- **User Stories:** 20-30 generated from controllers

---

## Test Scenarios

### Scenario 1: Entity Extraction
**Test:** Parse and extract all JPA entities
**Expected:** Find Owner, Pet, Vet, Visit, PetType, Specialty

### Scenario 2: Relationship Mapping
**Test:** Build dependency graph
**Expected:** Discover Owner→Pet, Pet→Visit, Vet→Specialty relationships

### Scenario 3: Controller Analysis
**Test:** Extract REST endpoints
**Expected:** Find all @GetMapping, @PostMapping methods

### Scenario 4: Test Coverage
**Test:** Map tests to production code
**Expected:** 17 test files covering 30 source files

### Scenario 5: Quality Metrics
**Test:** Calculate complexity scores
**Expected:** Identify high-complexity methods for refactoring

---

## Comparison with Small Samples

| Metric | Small Sample (CustomerService.java) | Large Sample (PetClinic) |
|--------|-------------------------------------|--------------------------|
| Files | 1 | 47 |
| LOC | 35 | 3,678 |
| Classes | 1 | 40+ |
| Methods | 2 | 200+ |
| Dependencies | 3 | 100+ |
| Test Coverage | None | Comprehensive |
| Complexity | Low | Medium |

**Advantages of Large Sample:**
- Realistic codebase structure
- Multiple layers (controller, service, repository)
- Complex relationships and dependencies
- Real-world patterns and practices
- Comprehensive test suite

---

## License

This sample is from the Spring PetClinic project:

```
Copyright 2012-2025 the original author or authors.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
```

Full license: https://www.apache.org/licenses/LICENSE-2.0

---

## Credits

**Original Project:** Spring PetClinic
**Maintainer:** Spring Team
**Contributors:** 124+ contributors
**Repository:** https://github.com/spring-projects/spring-petclinic

This sample dataset is included for educational and testing purposes to demonstrate reverse engineering capabilities with a realistic, production-quality Spring Boot application.
