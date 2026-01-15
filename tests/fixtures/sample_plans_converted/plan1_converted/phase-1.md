# TaskTracker Phase 1: Database and Models

**Status:** Pending
**Master Plan:** [TaskTracker-MASTER_PLAN.md](MASTER_PLAN.md)
**Depends On:** N/A

---

## Process Wrapper (MANDATORY)
- [ ] Read previous notes: `notes/NOTES_tasktracker_phase_1.md` (if available)
- [ ] **[IMPLEMENTATION - see Tasks below]**
- [ ] Pre-validation (ALL required):
  ```bash
  # Python linting and type checking
  uv run ruff format . && uv run ruff check --fix .
  uv run pyright backend/
  uv run pytest backend/tests/ -v
  ```
- [ ] Fix loop: repeat pre-validation until clean
- [ ] Write `notes/NOTES_tasktracker_phase_1.md` (REQUIRED)

## Gates (must pass before completion)

**ALL gates are BLOCKING.**

- command: `uv run ruff check .` ➜ 0 errors
- command: `uv run pyright backend/` ➜ 0 errors
- command: `uv run pytest backend/tests/ -v` ➜ All tests pass
- command: `uv run bandit -r backend/` ➜ No high severity issues

---

## Overview

Phase 1 establishes the data layer foundation for TaskTracker by designing and implementing the PostgreSQL database schema and SQLAlchemy models. This phase creates the data structures needed for users, tasks, categories, and temporal tracking. A solid data model is essential before building the API layer in Phase 2.

## Dependencies
- Previous phase: N/A (first phase)
- External: PostgreSQL database, SQLAlchemy ORM library, Flask-SQLAlchemy

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Schema design issues requiring rework | Low | Medium | Review schema against requirements, implement migrations incrementally |
| Password hashing implementation flaws | Low | High | Use bcrypt/argon2 via werkzeug.security, comprehensive unit tests |
| Relationship complexity in models | Medium | Low | Keep relationships simple, use eager/lazy loading strategically |
| Migration script errors | Low | High | Test migrations in development, version control all migration files |

---

## Tasks

### 1. Database Configuration & Setup
- [ ] 1.1: Create database configuration module (database URL, connection pooling)
- [ ] 1.2: Set up SQLAlchemy engine and session factory
- [ ] 1.3: Create database initialization script
- [ ] 1.4: Set up Alembic for database migrations

### 2. User Model Implementation
- [ ] 2.1: Define User model with id, username, email, password_hash fields
- [ ] 2.2: Implement password hashing using werkzeug.security
- [ ] 2.3: Add password verification method
- [ ] 2.4: Add validation for username (uniqueness, length constraints)
- [ ] 2.5: Add validation for email (format and uniqueness)
- [ ] 2.6: Create unit tests for User model (password hashing, validation)

### 3. Task & Category Models
- [ ] 3.1: Define Category model (id, name, user_id, description)
- [ ] 3.2: Define Task model (id, title, description, status, priority, user_id, category_id, created_at, updated_at, due_date)
- [ ] 3.3: Add relationships between User, Task, and Category models
- [ ] 3.4: Implement enum for Task status (todo, in_progress, done)
- [ ] 3.5: Implement enum for Task priority (low, medium, high)
- [ ] 3.6: Create unit tests for Task and Category models (relationships, validations)

### 4. Database Migrations
- [ ] 4.1: Create initial migration with all tables (users, categories, tasks)
- [ ] 4.2: Test migration script runs without errors
- [ ] 4.3: Verify schema matches model definitions
- [ ] 4.4: Create seed data script for development testing
- [ ] 4.5: Document migration process in README

### 5. Testing & Validation
- [ ] 5.1: Write integration tests for database connection
- [ ] 5.2: Write tests for model relationships (cascading deletes, foreign keys)
- [ ] 5.3: Write tests for uniqueness constraints
- [ ] 5.4: Write tests for timestamp fields (auto-updated)
- [ ] 5.5: Achieve 60%+ test coverage for models

---

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `backend/config.py` | Create | Database connection configuration and settings |
| `backend/models.py` | Create | SQLAlchemy models (User, Task, Category) |
| `backend/models/user.py` | Create | User model with password hashing |
| `backend/models/task.py` | Create | Task model with relationships |
| `backend/models/category.py` | Create | Category model |
| `backend/database.py` | Create | Database engine and session factory |
| `backend/alembic/versions/` | Create | Migration scripts directory |
| `backend/tests/test_models.py` | Create | Unit tests for all models |
| `backend/tests/test_database.py` | Create | Integration tests for database |
| `backend/.env.example` | Create | Example environment variables (DATABASE_URL) |
| `backend/requirements.txt` | Create | Python dependencies (sqlalchemy, psycopg2, alembic, etc.) |

## Patterns to Follow

| Pattern | Reference | Usage |
|---------|-----------|-------|
| Model Definition | SQLAlchemy docs | Use declarative base, type hints, column constraints |
| Password Security | werkzeug.security | Use `generate_password_hash()` and `check_password_hash()` |
| Timestamps | SQLAlchemy datetime | Use `default=datetime.utcnow, onupdate=datetime.utcnow` |
| Relationships | SQLAlchemy relationships | Use backref for bi-directional access, cascade for cleanup |
| Enums | Python enum | Use IntEnum or string Enum for status/priority fields |
| Validation | Pydantic or SQLAlchemy validators | Validate at model layer before persistence |

## Test Strategy

- [ ] Unit tests for each model (instantiation, field validation, methods)
- [ ] Integration tests for database operations (CRUD, relationships)
- [ ] Migration tests (forward and rollback migrations work)
- [ ] Constraint tests (unique constraints, foreign keys, not-null)
- [ ] Timestamp tests (auto-update on modification, defaults on creation)

## Acceptance Criteria

**ALL must pass:**

- [ ] All tasks completed
- [ ] All gates passing (lint, type-check, tests, security)
- [ ] User model with password hashing tested
- [ ] Task and Category models with relationships tested
- [ ] Database migrations run successfully
- [ ] No security vulnerabilities in password handling
- [ ] Test coverage >= 60%
- [ ] Schema documentation in notes

## Rollback Plan

If Phase 1 must be rolled back:

1. Drop all tables: `DROP TABLE IF EXISTS tasks, categories, users;`
2. Remove migration files in `backend/alembic/versions/`
3. Git reset to previous commit: `git reset --hard <commit>`
4. Remove `.env` file if created
5. Delete `backend/models.py` and related files

---

## Implementation Notes

{Space for additional notes, architectural decisions, or important context discovered during implementation}