# TaskTracker Phase 2: Backend API Development

**Status:** Pending
**Master Plan:** [TaskTracker-MASTER_PLAN.md](MASTER_PLAN.md)
**Depends On:** [Phase 1: Database and Models](tasktracker-phase-1.md)

---

## Process Wrapper (MANDATORY)

- [ ] Read previous notes: `notes/NOTES_tasktracker_phase_1.md`
- [ ] **[IMPLEMENTATION - see Tasks below]**
- [ ] Pre-validation (ALL required):
  ```bash
  # Python code quality
  uv run ruff format . && uv run ruff check --fix .
  uv run pyright src/ backend/
  uv run pytest tests/ -v --cov=backend
  uv run bandit -r backend/
  ```
- [ ] Fix loop: repeat pre-validation until clean
- [ ] Write `notes/NOTES_tasktracker_phase_2.md` (REQUIRED)

## Gates (must pass before completion)

**ALL gates are BLOCKING.**

- **lint**: 0 errors (command: `uv run ruff check backend/`)
- **type-check**: 0 errors (command: `uv run pyright backend/`)
- **tests**: All tests pass (command: `uv run pytest tests/ -v`)
- **security**: No high severity issues (command: `uv run bandit -r backend/`)

---

## Overview

Phase 2 develops the Flask backend REST API for TaskTracker. This phase implements all CRUD endpoints for tasks and categories, user authentication with JWT tokens, middleware for authorization, comprehensive input validation, error handling, and API documentation. The backend will be fully tested and secured before Phase 3 begins.

## Dependencies

- Previous phase: [Phase 1: Database and Models](tasktracker-phase-1.md) - requires fully functional models and migrations
- External: Flask, Flask-JWT-Extended, Marshmallow for validation, pytest for testing

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| JWT token management complexity | Medium | High | Implement token refresh endpoint in early tasks, test expiration edge cases, add rate limiting |
| Input validation gaps allowing injection | Medium | High | Use Marshmallow schemas for all inputs, add unit tests for validation, security review before phase end |
| Authentication bypass vulnerabilities | Low | High | Implement proper middleware, test auth on all protected endpoints, add integration tests for unauthorized access |
| Database transaction consistency issues | Medium | Medium | Use transactions for multi-step operations, test rollback scenarios, add constraint validation |
| API versioning challenges later | Medium | Medium | Plan for versioning now (URL prefix /api/v1/), document breaking change policy |

---

## Tasks

### 1. Flask Application Setup
- [ ] 1.1: Create Flask app factory pattern in `backend/app.py`
- [ ] 1.2: Configure CORS for frontend origin (development and production)
- [ ] 1.3: Set up Flask blueprints for modular endpoint organization (auth, tasks, categories)
- [ ] 1.4: Add request/response logging middleware
- [ ] 1.5: Configure error handlers for common HTTP errors (400, 401, 403, 404, 500)

### 2. JWT Authentication System
- [ ] 2.1: Install and configure Flask-JWT-Extended
- [ ] 2.2: Create JWT token generation on user login
- [ ] 2.3: Implement JWT token refresh endpoint (returns new access token)
- [ ] 2.4: Add JWT_SECRET_KEY to environment configuration
- [ ] 2.5: Create @jwt_required() decorator for protected endpoints
- [ ] 2.6: Test token expiration and refresh flow

### 3. User Endpoints
- [ ] 3.1: Implement POST /api/v1/auth/register (user registration)
- [ ] 3.2: Implement POST /api/v1/auth/login (user login, returns JWT)
- [ ] 3.3: Implement POST /api/v1/auth/refresh (refresh access token)
- [ ] 3.4: Implement POST /api/v1/auth/logout (invalidate session)
- [ ] 3.5: Add password strength validation (min 8 chars, uppercase, number, symbol)
- [ ] 3.6: Add email uniqueness validation on registration

### 4. Task CRUD Endpoints
- [ ] 4.1: Implement GET /api/v1/tasks (list all user's tasks with pagination)
- [ ] 4.2: Implement GET /api/v1/tasks/:id (retrieve single task)
- [ ] 4.3: Implement POST /api/v1/tasks (create new task)
- [ ] 4.4: Implement PUT /api/v1/tasks/:id (update task)
- [ ] 4.5: Implement DELETE /api/v1/tasks/:id (delete task)
- [ ] 4.6: Add filtering (by status, category, due date)
- [ ] 4.7: Add sorting (by created_at, due_date, priority)
- [ ] 4.8: Implement pagination (limit, offset parameters)

### 5. Category CRUD Endpoints
- [ ] 5.1: Implement GET /api/v1/categories (list all user's categories)
- [ ] 5.2: Implement GET /api/v1/categories/:id (retrieve single category)
- [ ] 5.3: Implement POST /api/v1/categories (create new category)
- [ ] 5.4: Implement PUT /api/v1/categories/:id (update category)
- [ ] 5.5: Implement DELETE /api/v1/categories/:id (delete category)

### 6. Input Validation and Error Handling
- [ ] 6.1: Create Marshmallow schemas for all input validation (UserSchema, TaskSchema, CategorySchema)
- [ ] 6.2: Add validation for required fields, data types, string lengths
- [ ] 6.3: Implement error response format (consistent JSON error structure)
- [ ] 6.4: Add validation for enum fields (task status, priority)
- [ ] 6.5: Create custom error handlers that return proper HTTP status codes
- [ ] 6.6: Test all validation rules with edge cases

### 7. Authorization and Access Control
- [ ] 7.1: Ensure users can only access their own tasks (add user_id checks)
- [ ] 7.2: Ensure users can only access their own categories
- [ ] 7.3: Test that unauthorized users cannot access others' data
- [ ] 7.4: Add 401 responses for unauthenticated requests
- [ ] 7.5: Add 403 responses for unauthorized access attempts

### 8. API Documentation and Testing
- [ ] 8.1: Create comprehensive API documentation (endpoints, request/response examples)
- [ ] 8.2: Write unit tests for each endpoint (success and error cases)
- [ ] 8.3: Write integration tests for complete workflows (register -> login -> create task -> update -> delete)
- [ ] 8.4: Add edge case tests (empty lists, null values, invalid IDs)
- [ ] 8.5: Test all authentication flows (login, token refresh, logout)
- [ ] 8.6: Achieve 80%+ code coverage for backend

---

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `backend/app.py` | Create | Flask application factory and configuration |
| `backend/auth.py` | Create | JWT authentication logic and token management |
| `backend/routes/auth.py` | Create | User registration, login, refresh, logout endpoints |
| `backend/routes/tasks.py` | Create | Task CRUD endpoints with filtering, sorting, pagination |
| `backend/routes/categories.py` | Create | Category CRUD endpoints |
| `backend/schemas.py` | Create | Marshmallow schemas for request validation |
| `backend/errors.py` | Create | Custom error classes and error handlers |
| `backend/middleware.py` | Create | CORS, logging, and request/response middleware |
| `requirements.txt` | Modify | Add Flask, Flask-JWT-Extended, Marshmallow, pytest |
| `tests/test_auth.py` | Create | Tests for authentication endpoints |
| `tests/test_tasks.py` | Create | Tests for task endpoints |
| `tests/test_categories.py` | Create | Tests for category endpoints |
| `tests/test_validation.py` | Create | Tests for input validation and error handling |
| `docs/API_DOCUMENTATION.md` | Create | Complete API endpoint documentation |

## Patterns to Follow

| Pattern | Reference | Usage |
|---------|-----------|-------|
| Flask blueprints | Flask documentation | Organize endpoints into logical groups (auth, tasks, categories) |
| JWT tokens | JWT.io | Use Bearer token in Authorization header, implement refresh flow |
| Marshmallow schemas | Marshmallow documentation | Validate all inputs, serialize responses consistently |
| Error responses | REST best practices | Return consistent JSON error format with status code and message |
| Database transactions | SQLAlchemy docs | Wrap multi-step operations in transactions for consistency |
| Pagination | REST API design | Use limit/offset for list endpoints, include total count in response |
| Status codes | HTTP specification | 200 OK, 201 Created, 204 No Content, 400 Bad Request, 401 Unauthorized, 403 Forbidden, 404 Not Found, 500 Server Error |

## Test Strategy

- [ ] Unit tests for authentication logic (token generation, validation, refresh)
- [ ] Unit tests for each endpoint (request parsing, response format)
- [ ] Integration tests for complete user workflows (register -> login -> task CRUD)
- [ ] Validation tests (invalid inputs, missing fields, type mismatches)
- [ ] Authorization tests (cross-user access attempts, unauthenticated requests)
- [ ] Edge case tests (empty lists, pagination boundaries, concurrent updates)
- [ ] Error handling tests (database errors, network errors, timeout scenarios)
- [ ] Target 80%+ code coverage for all backend modules

## Validation

Use `python-task-validator` to verify:
- All endpoints follow REST conventions
- Input validation is comprehensive and secure
- JWT implementation follows security best practices
- No SQL injection or authorization bypass vulnerabilities
- Error handling is consistent and informative
- Type hints are complete and correct
- Database transactions are properly managed

## Acceptance Criteria

**ALL must pass:**

- [ ] All 8 user/task/category endpoints implemented and working
- [ ] JWT authentication middleware protecting all protected endpoints
- [ ] Input validation using Marshmallow schemas on all endpoints
- [ ] Error responses return proper HTTP status codes and JSON format
- [ ] Users can only access their own data (authorization checks working)
- [ ] Token refresh endpoint working and tested
- [ ] All endpoints tested (unit and integration tests)
- [ ] 80%+ code coverage achieved
- [ ] All gates passing (lint, type-check, tests, security)
- [ ] API documentation complete with examples
- [ ] No SQL injection or authorization vulnerabilities
- [ ] Pagination working on list endpoints

## Rollback Plan

If critical issues occur:

1. **Code Revert**: `git checkout backend/routes/ backend/auth.py` to revert to previous endpoint implementations
2. **Database State**: Re-run Phase 1 migrations if schema changes were made: `alembic upgrade head`
3. **Dependencies**: Revert requirements.txt and reinstall: `pip install -r requirements.txt`
4. **Test Failures**: Review failed tests with `pytest tests/ -v`, fix one test at a time
5. **Git Revert**: If entire phase needs rollback: `git revert HEAD~N` where N is number of commits to revert

---

## Implementation Notes

Phase 2 is the API backbone. All endpoints must be thoroughly tested and secured before Phase 3 frontend development begins. Key architectural decisions:
- Use Blueprint pattern for modular organization
- Implement JWT refresh token flow for security (short-lived access tokens)
- Validate ALL inputs with Marshmallow schemas (never trust client data)
- Always check user_id on data access (prevent cross-user access)
- Use database transactions for multi-step operations
- Keep endpoints REST-compliant (resources, HTTP verbs, status codes)
- Document API thoroughly with examples for frontend team