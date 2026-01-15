# TaskTracker Pro Phase 1: Foundation Sprint - Core Backend

**Status:** Pending
**Master Plan:** [TaskTracker Pro - Master Plan](MASTER_PLAN.md)
**Depends On:** None (initial phase)

---

## Process Wrapper (MANDATORY)

- [ ] Read previous notes: None (first phase)
- [ ] **[IMPLEMENTATION - see Tasks below]**
- [ ] Pre-validation (ALL required):
  ```bash
  # Python backend linting and type checking
  ruff format . && ruff check --fix .
  pyright src/
  
  # Run all tests with coverage
  pytest tests/ -v --cov=src/ --cov-report=html
  
  # Security scanning
  bandit -r src/ -ll
  ```
- [ ] Fix loop: repeat pre-validation until clean
- [ ] Write `notes/NOTES_tasktracker_phase_1.md` (REQUIRED)

## Gates (must pass before completion)

**ALL gates are BLOCKING.**

- **lint**: 0 errors from ruff format and ruff check
- **type-check**: 0 errors from pyright
- **tests**: All tests pass with >60% coverage
- **security**: No high severity issues from bandit

---

## Overview

Phase 1 establishes the foundational backend infrastructure for TaskTracker Pro. This phase focuses on building Django models for tasks, teams, and users; implementing JWT-based authentication; setting up PostgreSQL and Redis integration; and creating basic REST API endpoints for core functionality. By the end of Phase 1, we'll have a working backend that can handle user registration, team creation, and task management operations.

## Dependencies

- **Previous phase:** None (first phase)
- **External:** Python 3.10+, PostgreSQL 13+, Redis 6+, Docker

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Model schema changes in Phase 2 | Medium | Medium | Design schema carefully with team input, use Django migrations for flexibility |
| Authentication complexity | Low | Medium | Use Django REST Framework's built-in auth systems and well-tested JWT libraries |
| Database connection pooling issues | Low | Medium | Implement connection pooling from the start, test under load |
| Redis cache invalidation | Medium | Low | Keep cache logic simple in Phase 1, refine in Phase 2 |

---

## Tasks

### 1. Project Setup & Infrastructure

- [ ] 1.1: Initialize Django project with REST Framework and Channels dependencies
- [ ] 1.2: Configure PostgreSQL database connection with environment variables
- [ ] 1.3: Set up Redis for caching and session management
- [ ] 1.4: Create Docker Compose file for local development (Django, PostgreSQL, Redis)
- [ ] 1.5: Implement database connection pooling with django-db-pool or similar
- [ ] 1.6: Create initial Django apps: users, teams, tasks, auth

### 2. User & Authentication Models

- [ ] 2.1: Create User model extending Django's AbstractUser with additional fields (profile, preferences)
- [ ] 2.2: Create UserProfile model for extended user information
- [ ] 2.3: Implement JWT token generation and refresh token strategy
- [ ] 2.4: Create authentication serializers for login/registration/token refresh
- [ ] 2.5: Set up JWT middleware for request authentication
- [ ] 2.6: Implement password hashing and validation
- [ ] 2.7: Create API endpoints: /auth/register, /auth/login, /auth/refresh, /auth/logout

### 3. Team & Organization Models

- [ ] 3.1: Create Team model with name, description, owner, and metadata
- [ ] 3.2: Create TeamMember model for team membership with roles (admin, member, viewer)
- [ ] 3.3: Create role-based permission system for team access levels
- [ ] 3.4: Implement team creation and member invitation logic
- [ ] 3.5: Create API endpoints: /teams (CRUD), /teams/{id}/members (list/add/remove)
- [ ] 3.6: Add team filtering to user API responses

### 4. Task & Board Models

- [ ] 4.1: Create Task model with title, description, status, priority, assigned user, due date, and timestamps
- [ ] 4.2: Create Board model representing task collections (e.g., "To Do", "In Progress", "Done")
- [ ] 4.3: Create TaskList model linking tasks to boards with ordering
- [ ] 4.4: Implement task status transitions with validation
- [ ] 4.5: Add audit fields (created_by, created_at, updated_at) to all models
- [ ] 4.6: Create API endpoints: /tasks (CRUD), /boards (CRUD), /tasks?filter=status,priority,assigned_to

### 5. REST API Endpoints

- [ ] 5.1: Implement serializers for all models with nested relationships
- [ ] 5.2: Create ViewSets with proper permissions and filtering for all resources
- [ ] 5.3: Implement pagination (default 20 items, max 100)
- [ ] 5.4: Add ordering support (by created_at, due_date, priority)
- [ ] 5.5: Implement soft delete for tasks (mark deleted rather than remove)
- [ ] 5.6: Add request/response logging middleware
- [ ] 5.7: Create API documentation endpoint (/api/docs)

### 6. Caching & Performance

- [ ] 6.1: Implement Redis caching for frequently accessed resources (user profiles, team info)
- [ ] 6.2: Add cache invalidation on model updates
- [ ] 6.3: Create cache key strategies to prevent collisions
- [ ] 6.4: Add database query optimization (select_related, prefetch_related)
- [ ] 6.5: Monitor and log slow queries (>100ms threshold)

### 7. Testing & Documentation

- [ ] 7.1: Write unit tests for all models (fixtures, validation, relationships)
- [ ] 7.2: Write unit tests for authentication (login, token refresh, logout)
- [ ] 7.3: Write API integration tests for all endpoints (success paths, error cases)
- [ ] 7.4: Write permission/authorization tests (team membership, role-based access)
- [ ] 7.5: Create API documentation (endpoints, request/response examples, auth)
- [ ] 7.6: Write setup instructions for local development

---

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `manage.py` | Create | Django project management script |
| `settings.py` | Create | Django configuration with DRF, Channels, PostgreSQL, Redis settings |
| `docker-compose.yml` | Create | Local development environment (Django, PostgreSQL, Redis) |
| `.env.example` | Create | Environment variables template |
| `users/models.py` | Create | User and UserProfile models |
| `users/serializers.py` | Create | User serializers for API |
| `users/views.py` | Create | User ViewSets and authentication endpoints |
| `teams/models.py` | Create | Team and TeamMember models |
| `teams/serializers.py` | Create | Team serializers |
| `teams/views.py` | Create | Team ViewSets |
| `tasks/models.py` | Create | Task, Board, TaskList models |
| `tasks/serializers.py` | Create | Task serializers with filtering |
| `tasks/views.py` | Create | Task ViewSets with permissions |
| `auth/authentication.py` | Create | JWT authentication backend |
| `auth/permissions.py` | Create | Role-based permission classes |
| `tests/test_models.py` | Create | Unit tests for all models |
| `tests/test_auth.py` | Create | Authentication tests |
| `tests/test_api.py` | Create | API endpoint integration tests |
| `requirements.txt` or `pyproject.toml` | Create | Python dependencies |

## Patterns to Follow

| Pattern | Reference | Usage |
|---------|-----------|-------|
| Django Models | Django docs: Models | Use abstract base models for timestamps, implement __str__ methods |
| DRF Serializers | DRF docs: Serializers | Nested serializers for relationships, validation in validate_* methods |
| ViewSets & Routers | DRF docs: ViewSets | Generic ViewSets with filtering, pagination, permissions |
| JWT Auth | djangorestframework-simplejwt | Token generation, refresh, blacklist strategies |
| Role-Based Access | DRF Permissions | Custom permission classes checking team membership and role |

## Test Strategy

- [ ] Unit tests for all model methods and validations (target: 70% coverage)
- [ ] Integration tests for API endpoints (success paths, 400/403/404/500 responses)
- [ ] Authentication flow tests (register, login, token refresh, logout)
- [ ] Permission tests (verify role-based access restrictions)
- [ ] Database migration tests (ensure migrations are reversible)
- [ ] Manual testing: use Django shell to verify model relationships

## Acceptance Criteria

**ALL must pass:**

- [ ] All tasks completed
- [ ] All gates passing (lint, type-check, tests, security)
- [ ] Django models properly normalized with correct relationships
- [ ] User authentication (register/login/refresh/logout) works end-to-end
- [ ] Team creation and membership management functional
- [ ] All REST endpoints respond with correct status codes and data formats
- [ ] Database queries optimized (no N+1 queries)
- [ ] At least 60% test coverage with no critical security issues
- [ ] API documentation generated and accessible
- [ ] No warnings from pyright type checker
- [ ] Code formatted and linted with ruff

## Rollback Plan

If Phase 1 encounters critical issues:

1. **Database rollback**: `python manage.py migrate {app} {target_migration}`
2. **Dependency rollback**: Revert `requirements.txt` or `pyproject.toml` and reinstall with `pip install -r requirements.txt`
3. **Code rollback**: Use git to revert commits: `git revert {commit_hash}`
4. **Docker cleanup**: Remove containers and volumes: `docker-compose down -v`
5. **Cache cleanup**: Clear Redis: `redis-cli FLUSHALL`
6. **Environment reset**: Start fresh with `docker-compose up` and migrate from scratch

---

## Implementation Notes

- Use Django's model meta options (unique_together, indexes) to enforce data integrity at the database level
- Implement soft deletes for tasks to preserve audit trails
- Keep serializers simple—complex logic belongs in model methods or services
- Use Django signals sparingly for cache invalidation
- Consider using django-filter for advanced filtering in Phase 2
- Plan for database migrations early—use meaningful migration names
- Test authentication thoroughly before Phase 2 (frontend will depend on it)