# Architecture Tests

## Purpose

Architecture tests validate that the DDD structure is maintained and no
forbidden imports or cross-domain leakage occurs.

## Test Categories

### 1. Import Direction Tests

Verify that dependencies flow in the correct direction:

```python
# ✅ Allowed: presentation → application
# ✅ Allowed: application → domain
# ❌ Forbidden: domain → infrastructure
# ❌ Forbidden: domain → presentation
# ❌ Forbidden: application → infrastructure
```

### 2. Context Boundary Tests

Verify that bounded contexts don't import from each other's infrastructure:

```python
# ❌ Forbidden: jobs.infrastructure → companies.infrastructure
# ❌ Forbidden: skills.application → career.infrastructure
```

### 3. Shared Kernel Tests

Verify that shared kernel doesn't import from bounded contexts:

```python
# ❌ Forbidden: shared.* → jobs.*
# ❌ Forbidden: shared.* → companies.*
```

### 4. Domain Purity Tests

Verify that domain layer has no framework dependencies:

```python
# ❌ Forbidden in domain: from fastapi import ...
# ❌ Forbidden in domain: from sqlalchemy import ...
# ❌ Forbidden in domain: from pydantic import ...
```

## Running Tests

```bash
# Run all architecture tests
pytest tests/unit/test_architecture.py -v

# Run specific test categories
pytest tests/unit/test_architecture.py -k "import_direction" -v
pytest tests/unit/test_architecture.py -k "context_boundary" -v
pytest tests/unit/test_architecture.py -k "domain_purity" -v
```

## Adding New Tests

When adding new bounded contexts or modules:

1. Add import direction tests for the new context
2. Add context boundary tests to prevent cross-domain imports
3. Add domain purity tests if the context has a domain layer
4. Update this documentation

## Compliance

All code must pass architecture tests before merging. Violations should
be fixed by restructuring code, not by disabling tests.
