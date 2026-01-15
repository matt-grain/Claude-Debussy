# TaskTracker Pro Phase 1: Foundation Sprint - Core Backend

**Status:** Pending
**Master Plan:** [TaskTracker Pro - MASTER_PLAN.md](MASTER_PLAN.md)
**Depends On:** N/A (initial phase)

---

## Process Wrapper (MANDATORY)
- [ ] Read previous notes: `notes/NOTES_phase0_plan.md`
- [ ] **[IMPLEMENTATION - see Tasks below]**
- [ ] Pre-validation (ALL required):
  ```bash
  # Python/Django quality checks
  uv run ruff format . && uv run ruff check --fix .
  uv run pyright src/backend/
  uv run pytest tests/ -v --cov=backend --cov-report=term-missing
  ```
- [ ] Fix loop: repeat pre-validation until clean
- [ ] Write `notes/NOTES_phase1_backend.md` (REQUIRED)

## Gates (must pass before completion)

**ALL gates are BLOCKING.**

- lint: `uv run ruff check backend/` → 0 errors
- type-check: `uv run pyright backend/` → 0 errors
- tests: `uv run pytest tests/ -v` → All tests pass, coverage ≥ 60%
- security: No high severity vulnerabilities in dependencies

---

## Overview

Phase 1 establishes the foundational backend infrastructure for TaskTracker Pro. This sprint focuses on building Django REST Framework setup, PostgreSQL database models, authentication system, and core API endpoints for task management. Success in this phase enables Phase 2 to build the frontend with confidence.

## Dependencies
- Previous phase: N/A (initial phase)
- External: Python 3.9+, PostgreSQL 12+, Redis 6+, Django 4.2+, Django REST Framework 3.14+

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Django ORM performance with complex queries | Low | Medium | Design models with proper indexes and relationships upfront; use select_related/prefetch_related |
| Authentication system security vulnerabilities | Low | High | Use Django's built-in security features, JWT with django-rest-framework-simplejwt, regular security audits |
| Database migration issues in later phases | Low | Medium | Write reversible migrations, test migrations in isolation, document all schema changes |
| Redis caching implementation complexity | Low | Medium | Use django-redis for transparent caching, start simple with basic TTL strategy |

---

## Tasks

### 1. Project Setup & Infrastructure
- [ ] 1.1: Initialize Django project structure with proper app organization (accounts, tasks, core)
- [ ] 1.2: Configure PostgreSQL database connection and settings for development/staging/production
- [ ] 1.3: Set up Redis configuration for caching and session management
- [ ] 1.4: Configure Django REST Framework with appropriate default settings (pagination, authentication, permissions)
- [ ] 1.5: Set up environment variable management (.env files, python-dotenv)
- [ ] 1.6: Create Docker setup for local development (docker-compose.yml for PostgreSQL, Redis)

### 2. Database Models & Schema
- [ ] 2.1: Design and implement User model extending Django's AbstractUser (with team associations)
- [ ] 2.2: Create Task model with fields: title, description, status, priority, assigned_to, due_date, created_at, updated_at
- [ ] 2.3: Create Project model for task grouping (name, description, owner, members)
- [ ] 2.4: Implement TaskTag model for tagging and filtering capabilities
- [ ] 2.5: Create database indexes on frequently queried fields (status, assigned_to, project_id)
- [ ] 2.6: Write and test Django migrations for all models

### 3. Authentication & Authorization
- [ ] 3.1: Implement JWT token-based authentication using django-rest-framework-simplejwt
- [ ] 3.2: Create custom user serializer with proper password hashing validation
- [ ] 3.3: Implement login endpoint returning access and refresh tokens
- [ ] 3.4: Create logout endpoint that invalidates tokens (token blacklist with Redis)
- [ ] 3.5: Implement custom permission classes for task ownership and project membership
- [ ] 3.6: Add password reset functionality with email verification

### 4. Core API Endpoints
- [ ] 4.1: Create Task ViewSet with list, create, retrieve, update, delete endpoints
- [ ] 4.2: Implement filtering by status, priority, assigned_to, project_id using django-filter
- [ ] 4.3: Create Project ViewSet for project CRUD operations
- [ ] 4.4: Implement TaskTag ViewSet for tag management
- [ ] 4.5: Create User profile endpoint for retrieving current user and team membership
- [ ] 4.6: Implement proper pagination (20 items per page default)

### 5. Testing & Validation
- [ ] 5.1: Write unit tests for User model and authentication flow
- [ ] 5.2: Write unit tests for Task and Project models with validation rules
- [ ] 5.3: Write API tests for all endpoints using pytest-django
- [ ] 5.4: Create fixtures for test data (users, projects, tasks)
- [ ] 5.5: Achieve minimum 60% code coverage for backend code
- [ ] 5.6: Set up CI/CD pipeline to run tests on each commit

### 6. Documentation & Deployment Prep
- [ ] 6.1: Document all API endpoints with request/response examples (using drf-spectacular for OpenAPI)
- [ ] 6.2: Create API documentation in Swagger/OpenAPI format
- [ ] 6.3: Write deployment guide for local development setup
- [ ] 6.4: Create database migration documentation
- [ ] 6.5: Document authentication flow and JWT token handling

---

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `backend/manage.py` | Create | Django project management entry point |
| `backend/settings.py` | Create | Django configuration with PostgreSQL, Redis, JWT auth |
| `backend/accounts/models.py` | Create | User model extending AbstractUser |
| `backend/tasks/models.py` | Create | Task, Project, TaskTag models with relationships |
| `backend/accounts/serializers.py` | Create | User and authentication serializers |
| `backend/tasks/serializers.py` | Create | Task, Project, TaskTag serializers |
| `backend/accounts/views.py` | Create | Authentication ViewSets and endpoints |
| `backend/tasks/views.py` | Create | Task, Project, TaskTag ViewSets |
| `backend/urls.py` | Create | URL routing with nested routes |
| `docker-compose.yml` | Create | PostgreSQL, Redis, Django service definitions |
| `.env.example` | Create | Environment variable template |
| `tests/test_models.py` | Create | Unit tests for all models |
| `tests/test_api.py` | Create | Integration tests for API endpoints |
| `requirements.txt` or `pyproject.toml` | Create | Python dependencies (Django, DRF, simplejwt, django-filter, django-redis, etc.) |

## Patterns to Follow

| Pattern | Reference | Usage |
|---------|-----------|-------|
| DRY principle for serializers | DRF documentation | Use nested serializers, HyperlinkedIdentityField for relationships |
| Model best practices | Django documentation | Use descriptive field names, add help_text, use validators |
| API versioning | DRF documentation | Include version in API URLs (e.g., /api/v1/tasks/) |
| Error handling | DRF documentation | Use appropriate HTTP status codes and error response formats |

## Test Strategy

- [ ] Unit tests for all models with validation and constraints
- [ ] Integration tests for all API endpoints (authentication, CRUD operations)
- [ ] Test authentication flow (login, token refresh, logout)
- [ ] Test permission enforcement (users can only access their own tasks and projects)
- [ ] Test filtering and pagination on list endpoints
- [ ] Test database migrations with actual schema changes
- [ ] Load testing for API endpoints to establish performance baseline

## Acceptance Criteria

**ALL must pass:**

- [ ] All tasks completed
- [ ] All gates passing (lint, type-check, tests with 60%+ coverage, security)
- [ ] Tests written and passing (minimum 60% code coverage)
- [ ] Documentation complete (API docs, deployment guide, database docs)
- [ ] No security vulnerabilities in dependencies (check with `safety` or `bandit`)
- [ ] Docker setup runs locally without errors
- [ ] Swagger/OpenAPI documentation generated and accessible

## Rollback Plan

If critical issues arise during Phase 1:

1. **Code rollback**: Use `git revert` to undo problematic commits; preserve main branch integrity
2. **Database rollback**: Use Django migrations in reverse: `python manage.py migrate [app_name] [migration_number]`
3. **Dependency issues**: Maintain `requirements.txt.lock` or use `poetry.lock` for reproducible environments; use `pip install -r requirements.txt --no-cache-dir` to restore known good state
4. **Complete restart**: Remove all local containers (`docker-compose down -v`) and restart from fresh database state
5. **Communication**: Document what went wrong in notes for Phase 2 team

---

## Implementation Notes

{Space for discoveries, architectural decisions, and lessons learned during implementation}

---

## Validation

- Use `python-task-validator` to verify all Python code meets quality standards during implementation