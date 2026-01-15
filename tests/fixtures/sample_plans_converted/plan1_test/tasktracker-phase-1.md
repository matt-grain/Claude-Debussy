# TaskTracker Phase 1: Database and Models

**Status:** Pending
**Master Plan:** [TaskTracker-MASTER_PLAN.md](MASTER_PLAN.md)
**Depends On:** N/A (initial phase)

---

## Process Wrapper (MANDATORY)

- [ ] Read previous notes: `notes/NOTES_tasktracker_phase_0.md` (N/A for phase 1)
- [ ] **[IMPLEMENTATION - see Tasks below]**
- [ ] Pre-validation (ALL required):
  ```bash
  # Python code quality
  uv run ruff format . && uv run ruff check --fix .
  uv run pyright src/ backend/
  uv run pytest tests/ -v --cov=backend
  ```
- [ ] Fix loop: repeat pre-validation until clean
- [ ] Write `notes/NOTES_tasktracker_phase_1.md` (REQUIRED)

## Gates (must pass before completion)

**ALL gates are BLOCKING.**

- **lint**: 0 errors (command: `uv run ruff check backend/`)
- **type-check**: 0 errors (command: `uv run pyright backend/`)
- **tests**: All tests pass (command: `uv run pytest tests/ -v`)
- **security**: No high severity issues (command: `uv run bandit -r backend/`)

---

## Overview

Phase 1 establishes the database foundation for TaskTracker. This phase involves designing and implementing the PostgreSQL schema, creating SQLAlchemy ORM models for users, tasks, and categories, and setting up database migration scripts. All models will be properly typed, validated, and tested before Phase 2 begins.

## Dependencies

- Previous phase: None (initial phase)
- External: PostgreSQL server, SQLAlchemy library, Alembic for migrations

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Schema design changes after Phase 2 starts | Medium | High | Perform thorough design review and testing before phase completion, create comprehensive test suite |
| Password hashing library vulnerabilities | Low | High | Use well-maintained bcrypt library, follow OWASP guidelines, add security tests |
| Database migration failures in production | Medium | Medium | Test all migrations thoroughly in phase, maintain rollback scripts, document migration strategy |
| Relationship complexity between models | Medium | Medium | Create detailed ER diagram, test all relationships with multiple test cases |

---

## Tasks

### 1. Database Setup and Configuration
- [ ] 1.1: Create PostgreSQL database configuration module with connection pooling
- [ ] 1.2: Set up SQLAlchemy session factory and engine
- [ ] 1.3: Configure database environment variables (.env, .env.example)
- [ ] 1.4: Create requirements.txt with SQLAlchemy, Alembic, psycopg2 dependencies

### 2. User Model Implementation
- [ ] 2.1: Define User model with id, username, email, password_hash fields
- [ ] 2.2: Implement password hashing using bcrypt with salt generation
- [ ] 2.3: Add email validation and uniqueness constraints
- [ ] 2.4: Add created_at and updated_at timestamp fields with defaults
- [ ] 2.5: Create User model tests (creation, validation, password hashing)

### 3. Task Model Implementation
- [ ] 3.1: Define Task model with id, title, description, status fields
- [ ] 3.2: Add due_date, priority, category_id foreign key fields
- [ ] 3.3: Add user_id foreign key with cascade delete
- [ ] 3.4: Add created_at and updated_at timestamp fields
- [ ] 3.5: Define task status enum (pending, in_progress, completed)
- [ ] 3.6: Create Task model tests (creation, relationships, status transitions)

### 4. Category Model Implementation
- [ ] 4.1: Define Category model with id, name, user_id fields
- [ ] 4.2: Add color field for UI categorization
- [ ] 4.3: Add user_id foreign key with cascade delete
- [ ] 4.4: Create Category model tests (creation, user relationships)

### 5. Model Relationships and Constraints
- [ ] 5.1: Establish User -> Tasks one-to-many relationship
- [ ] 5.2: Establish User -> Categories one-to-many relationship
- [ ] 5.3: Establish Task -> Category many-to-one relationship
- [ ] 5.4: Add database constraints (NOT NULL, UNIQUE, FOREIGN KEY)
- [ ] 5.5: Create comprehensive relationship tests

### 6. Database Migrations
- [ ] 6.1: Initialize Alembic migration environment
- [ ] 6.2: Create initial migration with all tables (users, tasks, categories)
- [ ] 6.3: Test migration up and down operations
- [ ] 6.4: Document migration procedures

---

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `backend/config.py` | Create | Database configuration, connection pooling settings |
| `backend/models.py` | Create | SQLAlchemy ORM model definitions (User, Task, Category) |
| `backend/database.py` | Create | Session factory and database utilities |
| `requirements.txt` | Create | Python dependencies (SQLAlchemy, Alembic, psycopg2, bcrypt) |
| `.env.example` | Create | Template for environment variables |
| `alembic/versions/001_initial_schema.py` | Create | Initial database migration |
| `tests/test_models.py` | Create | Comprehensive model unit tests |
| `tests/test_relationships.py` | Create | Model relationship integration tests |

## Patterns to Follow

| Pattern | Reference | Usage |
|---------|-----------|-------|
| SQLAlchemy ORM models | SQLAlchemy documentation | Define all models with type hints, relationships, and constraints |
| Password hashing | OWASP guidelines | Use bcrypt with salt, never store plain passwords |
| Database migrations | Alembic documentation | Create reversible migrations, test up/down operations |
| Environment variables | 12-factor app | Use .env file locally, document in .env.example |
| Model validation | Pydantic or dataclass validators | Validate data at ORM layer before persistence |
| Timestamp fields | Standard pattern | Use CURRENT_TIMESTAMP for created_at, updated_at triggers |

## Test Strategy

- [ ] Unit tests for each model class (creation, field validation, constraints)
- [ ] Password hashing tests (bcrypt salt generation, verification)
- [ ] Relationship tests (foreign keys, cascade operations, referential integrity)
- [ ] Migration tests (up, down, idempotency)
- [ ] Edge cases (null values, unique constraint violations, invalid enum values)
- [ ] Database connection and pooling tests

## Validation

Use `python-task-validator` to verify:
- Model definitions follow Python best practices
- Type hints are correct and complete
- Password hashing implementation is secure
- Database schema is properly normalized
- All migrations are tested and reversible

## Acceptance Criteria

**ALL must pass:**

- [ ] All 4 models created (User, Task, Category, Status enum)
- [ ] All fields properly typed with SQLAlchemy column definitions
- [ ] All relationships established and tested
- [ ] All constraints (NOT NULL, UNIQUE, FOREIGN KEY) implemented
- [ ] Password hashing uses bcrypt with salt
- [ ] All gates passing (lint, type-check, tests, security)
- [ ] Migration scripts created and tested (up and down)
- [ ] Database schema diagram created
- [ ] Comprehensive test suite written (70%+ coverage for models)
- [ ] Documentation updated with schema design decisions

## Rollback Plan

If critical issues occur:

1. **Migration Rollback**: `alembic downgrade -1` to revert to previous schema state
2. **Model Revert**: `git checkout backend/models.py` to revert to previous model definitions
3. **Database Reset**: Drop and recreate database if schema is corrupted: `DROP DATABASE tasktracker; CREATE DATABASE tasktracker;` then re-run migrations
4. **Dependency Issues**: Revert `requirements.txt` and reinstall: `pip install -r requirements.txt`
5. **All Else Fails**: Contact team lead and review git history for specific commit to revert to

---

## Implementation Notes

Phase 1 is the critical foundation. All subsequent phases depend on correct model design and migration strategy. Key decisions:
- Use SQLAlchemy ORM for type safety and query building (vs raw SQL)
- Implement proper timestamp fields with defaults for audit trail
- Use bcrypt for password hashing, never store plaintext
- Create comprehensive migration tests to catch issues early
- Document all schema design decisions for team reference