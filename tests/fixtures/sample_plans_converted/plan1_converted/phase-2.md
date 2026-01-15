# TaskTracker Phase 2: Backend API Development

**Status:** Pending
**Master Plan:** [TaskTracker-MASTER_PLAN.md](MASTER_PLAN.md)
**Depends On:** [Phase 1: Database and Models](phase-1.md)

---

## Process Wrapper (MANDATORY)
- [ ] Read previous notes: `notes/NOTES_tasktracker_phase_1.md`
- [ ] **[IMPLEMENTATION - see Tasks below]**
- [ ] Pre-validation (ALL required):
  ```bash
  # Python linting and type checking
  uv run ruff format . && uv run ruff check --fix .
  uv run pyright backend/
  uv run pytest backend/tests/ -v
  ```
- [ ] Fix loop: repeat pre-validation until clean
- [ ] Write `notes/NOTES_tasktracker_phase_2.md` (REQUIRED)

## Gates (must pass before completion)

**ALL gates are BLOCKING.**

- command: `uv run ruff check .` ➜ 0 errors
- command: `uv run pyright backend/` ➜ 0 errors
- command: `uv run pytest backend/tests/ -v` ➜ All tests pass
- command: `uv run bandit -r backend/` ➜ No high severity issues

---

## Overview

Phase 2 builds the Flask REST API with JWT authentication, CRUD endpoints for tasks, comprehensive input validation, and error handling. This phase creates all backend functionality needed for the frontend to interact with the database. A robust API with proper authentication and validation is critical for application security and reliability.

## Dependencies
- Previous phase: [Phase 1: Database and Models](phase-1.md) - requires working models and database
- External: Flask, Flask-JWT-Extended, Flask-CORS, Marshmallow for serialization

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| JWT token expiration edge cases | Medium | Medium | Implement refresh tokens, test token expiration flows, handle expired token responses |
| Database connection pooling issues under load | Low | Medium | Configure SQLAlchemy pool size, implement connection error handling |
| CORS misconfiguration blocking frontend requests | Medium | Medium | Test CORS with frontend origin, document allowed origins |
| Input validation bypass vulnerabilities | Low | High | Use Marshmallow schemas for all inputs, test injection attacks in unit tests |

---

## Tasks

### 1. Flask App Setup & Configuration
- [ ] 1.1: Create Flask application factory function
- [ ] 1.2: Configure Flask settings (debug, testing, database URL)
- [ ] 1.3: Set up Flask-SQLAlchemy with the database
- [ ] 1.4: Configure CORS for frontend integration
- [ ] 1.5: Set up logging configuration
- [ ] 1.6: Create error handlers for common HTTP errors (400, 404, 500)

### 2. JWT Authentication Implementation
- [ ] 2.1: Set up Flask-JWT-Extended configuration
- [ ] 2.2: Create JWT token generation on login
- [ ] 2.3: Implement refresh token logic
- [ ] 2.4: Create JWT authentication decorator for protected routes
- [ ] 2.5: Add token expiration handling
- [ ] 2.6: Test JWT token creation, validation, and expiration

### 3. User Authentication Endpoints
- [ ] 3.1: Create POST `/api/auth/register` endpoint with validation
- [ ] 3.2: Create POST `/api/auth/login` endpoint returning access token
- [ ] 3.3: Create POST `/api/auth/refresh` endpoint for token refresh
- [ ] 3.4: Create POST `/api/auth/logout` endpoint
- [ ] 3.5: Create GET `/api/users/me` endpoint for current user
- [ ] 3.6: Implement Marshmallow schemas for request/response validation

### 4. Task CRUD Endpoints
- [ ] 4.1: Create POST `/api/tasks` endpoint (create task for authenticated user)
- [ ] 4.2: Create GET `/api/tasks` endpoint (list all tasks with pagination)
- [ ] 4.3: Create GET `/api/tasks/{id}` endpoint (get single task)
- [ ] 4.4: Create PUT `/api/tasks/{id}` endpoint (update task)
- [ ] 4.5: Create DELETE `/api/tasks/{id}` endpoint (delete task)
- [ ] 4.6: Implement filtering by status and category
- [ ] 4.7: Implement sorting by due_date, created_at, priority

### 5. Category Endpoints
- [ ] 5.1: Create POST `/api/categories` endpoint (create category)
- [ ] 5.2: Create GET `/api/categories` endpoint (list user's categories)
- [ ] 5.3: Create PUT `/api/categories/{id}` endpoint (update category)
- [ ] 5.4: Create DELETE `/api/categories/{id}` endpoint (delete category)

### 6. Input Validation & Error Handling
- [ ] 6.1: Create Marshmallow schemas for all request bodies
- [ ] 6.2: Implement field validation (required fields, length constraints, enums)
- [ ] 6.3: Create custom error responses with meaningful messages
- [ ] 6.4: Implement HTTP status codes (201 created, 204 no content, 400 bad request, 401 unauthorized, 403 forbidden, 404 not found)
- [ ] 6.5: Add validation for user authorization (users can only modify their own data)

### 7. API Documentation & Testing
- [ ] 7.1: Create API documentation (endpoints, request/response examples)
- [ ] 7.2: Write unit tests for all endpoints (happy path and error cases)
- [ ] 7.3: Write integration tests for authentication flows
- [ ] 7.4: Write tests for pagination and filtering
- [ ] 7.5: Write security tests (unauthorized access, CSRF, SQL injection attempts)
- [ ] 7.6: Achieve 70%+ test coverage for API

---

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `backend/app.py` | Create | Flask application factory |
| `backend/config.py` | Modify | Add JWT and CORS configuration |
| `backend/auth.py` | Create | JWT token generation and validation |
| `backend/api/__init__.py` | Create | API blueprint initialization |
| `backend/api/auth.py` | Create | Authentication endpoints |
| `backend/api/tasks.py` | Create | Task CRUD endpoints |
| `backend/api/categories.py` | Create | Category endpoints |
| `backend/schemas.py` | Create | Marshmallow schemas for validation |
| `backend/tests/test_auth.py` | Create | Authentication endpoint tests |
| `backend/tests/test_tasks.py` | Create | Task endpoint tests |
| `backend/tests/test_categories.py` | Create | Category endpoint tests |
| `backend/tests/test_api.py` | Create | Integration and security tests |
| `backend/API_DOCS.md` | Create | API documentation and examples |

## Patterns to Follow

| Pattern | Reference | Usage |
|---------|-----------|-------|
| Flask Blueprints | Flask docs | Organize endpoints into api module |
| JWT Tokens | Flask-JWT-Extended | Use access + refresh tokens, 15min access token TTL |
| Marshmallow Schemas | Marshmallow docs | Use for request validation and response serialization |
| HTTP Status Codes | RFC 7231 | Return appropriate 2xx/4xx status codes |
| Error Responses | REST conventions | Return JSON error with message and code |
| Pagination | REST conventions | Use limit/offset query params, return total count |
| Authorization | OAuth2 patterns | Check user_id matches resource owner |

## Test Strategy

- [ ] Unit tests for authentication functions (token creation, validation)
- [ ] Unit tests for endpoint handlers (request parsing, response formatting)
- [ ] Integration tests for full authentication flow (register → login → access)
- [ ] Integration tests for task CRUD operations
- [ ] Security tests (unauthorized access, SQL injection, CSRF)
- [ ] Error handling tests (invalid input, missing fields, constraint violations)
- [ ] Pagination and filtering tests

## Acceptance Criteria

**ALL must pass:**

- [ ] All tasks completed
- [ ] All gates passing (lint, type-check, tests, security)
- [ ] User registration and login working end-to-end
- [ ] JWT tokens generated and validated correctly
- [ ] All CRUD endpoints working for tasks and categories
- [ ] Input validation catching malformed requests
- [ ] Unauthorized access properly blocked (401/403)
- [ ] Pagination working with limit/offset
- [ ] Filtering by status, category, and sorting by priority/due date working
- [ ] API documentation complete and accurate
- [ ] Test coverage >= 70%
- [ ] No security vulnerabilities

## Rollback Plan

If Phase 2 must be rolled back:

1. Delete API files: `rm -rf backend/api/ backend/auth.py backend/schemas.py backend/API_DOCS.md`
2. Remove API blueprint registration from `backend/app.py`
3. Remove JWT configuration from `backend/config.py`
4. Delete API tests: `rm -rf backend/tests/test_auth.py backend/tests/test_tasks.py backend/tests/test_categories.py backend/tests/test_api.py`
5. Git reset to previous phase: `git reset --hard <commit>`

---

## Implementation Notes

{Space for additional notes, architectural decisions, or important context discovered during implementation}