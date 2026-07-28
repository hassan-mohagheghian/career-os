You are working on a Python backend project that has already been migrated to SQLAlchemy and Alembic.

Your task is to perform a complete cleanup and refactor of the codebase to ensure that there is no remaining raw SQL usage anywhere in the project, including tests.

Objectives:

1. Audit the entire repository:
   - Search for all raw SQL queries, SQL strings, manual table creation scripts, direct cursor usage, engine.execute usage, text() usage, and any database access patterns that bypass SQLAlchemy ORM/Core abstractions.
   - Include application code, infrastructure code, migration-related helpers, scripts, fixtures, and all test files.

2. Replace raw SQL usage:
   - Remove all direct SQL statements from the codebase.
   - Replace them with proper SQLAlchemy ORM or SQLAlchemy Core approaches.
   - Use the existing SQLAlchemy models, repositories, sessions, and patterns already established in the project.
   - Do not create unnecessary duplicate models or bypass the existing architecture.

3. Refactor tests:
   - Review all tests and fixtures.
   - Replace raw SQL used for:
     - inserting test data
     - cleaning databases
     - creating test records
     - querying assertions
     - setup/teardown logic
   - Use SQLAlchemy sessions and ORM models instead.
   - Create test data through the same domain/application layer when appropriate.
   - Ensure tests validate real application behavior instead of depending on database implementation details.

4. Maintain architectural principles:
   - Keep the existing DDD, Hexagonal Architecture, Clean Architecture, and SOLID principles.
   - Database access must remain behind repositories/interfaces where applicable.
   - Tests should not directly depend on database tables or SQL syntax.
   - Respect separation between:
     - Domain layer
     - Application layer
     - Infrastructure layer
     - Presentation layer

5. Database handling:
   - Keep Alembic as the only migration mechanism.
   - Do not introduce manual SQL migration files.
   - Ensure all database initialization and test database setup is handled through SQLAlchemy/Alembic.
   - Preserve existing PostgreSQL schema separation and application ownership boundaries.

6. Code quality requirements:
   - Follow Clean Code principles.
   - Apply SOLID principles.
   - Avoid unnecessary abstractions.
   - Prefer readable and maintainable SQLAlchemy patterns.
   - Remove dead code after replacing raw SQL.
   - Add comments only when the reasoning is not obvious.

7. Validation:
   - After refactoring:
     - Run the full test suite.
     - Verify migrations still work.
     - Verify database setup works from a clean environment.
     - Search again for raw SQL patterns and confirm there are no remaining usages.

Expected final state:
- The entire project uses SQLAlchemy for database interaction.
- Tests use SQLAlchemy ORM/models instead of raw SQL.
- No direct SQL queries remain in application code or tests.
- The architecture remains clean, modular, and ready for future scaling.

Before making changes:
1. Analyze the repository structure.
2. Identify all raw SQL usages and provide a short migration/refactor plan.
3. Then implement the changes step by step.
4. Do not perform a large destructive rewrite; preserve existing behavior.
