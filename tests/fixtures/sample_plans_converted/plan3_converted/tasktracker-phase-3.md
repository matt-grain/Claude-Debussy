# TaskTracker MVP Phase 3: Task API Development

**Status:** Pending
**Master Plan:** [TaskTracker MVP - Master Plan](tasktracker-MASTER_PLAN.md)
**Depends On:** [Phase 2: Authentication System](tasktracker-phase-2.md)

---

## Process Wrapper (MANDATORY)
- [ ] Read previous notes: `notes/NOTES_tasktracker_phase_2.md`
- [ ] **[IMPLEMENTATION - see Tasks below]**
- [ ] Pre-validation (ALL required):
  ```bash
  npm run lint --fix
  npm run type-check
  npm test -- tests/api/
  npm audit --audit-level=moderate
  # Verify response times
  npm run test:performance 2>/dev/null || echo "Performance tests optional"
  ```
- [ ] Fix loop: repeat pre-validation until clean
- [ ] Write `notes/NOTES_tasktracker_phase_3.md` (REQUIRED)

## Gates (must pass before completion)

**ALL gates are BLOCKING.**

- lint: `npm run lint` returns 0 errors
- type-check: `npm run type-check` returns 0 errors
- tests: `npm test -- tests/api/` - all pass, >85% coverage
- security: `npm audit --audit-level=moderate` - no high severity issues
- performance: API endpoints respond in <100ms (median response time)

---

## Overview

This phase implements the REST API for task management. Provides endpoints for creating, reading, updating, and deleting tasks, with filtering, search, and statistics capabilities. Builds on Phases 1-2 and creates the backend layer that the frontend (Phase 4) will consume. Focus on robust error handling, pagination, and performance.

## Dependencies
- Previous phase: Phase 2 Authentication (authenticate middleware, UserRepository)
- External: cors, helmet, morgan packages; Express 4.x

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| N+1 query problems with large datasets | Medium | High | Implement pagination early, use indexes from Phase 1, load-test with realistic data |
| Authorization bypass (user accesses others' tasks) | Low | High | ensureTaskOwnership middleware on all task routes, unit tests verify ownership checks |
| Pagination edge cases (page 0, negative limit) | Low | Medium | Validate and sanitize page/limit params, write edge case tests |
| Large request bodies cause memory issues | Low | Medium | Set request size limit in Express, validate input lengths at controller |
| Missing or malformed query parameters | Medium | Low | Provide sensible defaults, validate before using, return helpful error messages |

---

## Tasks

### 1. Express Application Setup
- [ ] 1.1: Create src/app.js with Express application configuration
- [ ] 1.2: Add helmet middleware for security headers
- [ ] 1.3: Add cors middleware with configurable origin
- [ ] 1.4: Add morgan middleware for request logging
- [ ] 1.5: Add body parsing middleware (express.json)
- [ ] 1.6: Add health check endpoint (GET /health)
- [ ] 1.7: Add 404 handler for non-existent routes
- [ ] 1.8: Write tests for app initialization

### 2. Task Controller Implementation
- [ ] 2.1: Create src/controllers/TaskController.js
- [ ] 2.2: Implement create() - POST /api/tasks
  - Validate input
  - Add userId from authenticated user
  - Create via TaskRepository
  - Return 201 with created task
- [ ] 2.3: Implement list() - GET /api/tasks with filtering
  - Extract query parameters (status, priority, tags, search, sort, order, page, limit)
  - Build filter object
  - Apply sorting
  - Paginate results
  - Return tasks with pagination metadata
- [ ] 2.4: Implement getById() - GET /api/tasks/:id
  - Find task by ID
  - Verify ownership (user can only access own tasks)
  - Return task or 404
- [ ] 2.5: Implement update() - PUT /api/tasks/:id
  - Find and verify ownership
  - Validate update data
  - Update via TaskRepository
  - Return updated task
- [ ] 2.6: Implement delete() - DELETE /api/tasks/:id
  - Find and verify ownership
  - Delete via TaskRepository
  - Return 204 No Content
- [ ] 2.7: Implement search() - GET /api/tasks/search?q=query
  - Extract search query
  - Search title and description
  - Filter by user
  - Return matching tasks
- [ ] 2.8: Implement getStats() - GET /api/tasks/stats
  - Count tasks by status
  - Count tasks by priority
  - Count overdue tasks
  - Return statistics object
- [ ] 2.9: Implement bulkUpdate() - PATCH /api/tasks/bulk
  - Extract task IDs and updates
  - Verify all tasks belong to user
  - Update all via TaskRepository
  - Return updated count
- [ ] 2.10: Implement markComplete() - POST /api/tasks/:id/complete
  - Find and verify ownership
  - Set status to done
  - Set completedAt timestamp
  - Return updated task

### 3. Task Routes Configuration
- [ ] 3.1: Create src/routes/tasks.js
- [ ] 3.2: Apply authenticate middleware to all task routes
- [ ] 3.3: POST / - create task (validateTask middleware)
- [ ] 3.4: GET / - list tasks with filters
- [ ] 3.5: GET /stats - get statistics
- [ ] 3.6: GET /search - search tasks
- [ ] 3.7: GET /:id - get single task (ensureTaskOwnership middleware)
- [ ] 3.8: PUT /:id - update task (ensureTaskOwnership, validateTaskUpdate middleware)
- [ ] 3.9: DELETE /:id - delete task (ensureTaskOwnership middleware)
- [ ] 3.10: PATCH /bulk - bulk update tasks
- [ ] 3.11: POST /:id/complete - mark complete (ensureTaskOwnership middleware)

### 4. Authorization Middleware
- [ ] 4.1: Create src/middleware/taskAuth.js
- [ ] 4.2: Implement ensureTaskOwnership() middleware
  - Extract task ID from params
  - Find task in database
  - Verify task.userId matches authenticated user
  - Return 403 if not owner
  - Attach task to req.task
- [ ] 4.3: Write unit tests for ensureTaskOwnership

### 5. Query Parameter Handling
- [ ] 5.1: Create src/utils/pagination.js
- [ ] 5.2: Implement paginate() - sanitize and limit page/limit parameters
  - Default: page=1, limit=20
  - Max limit: 100
  - Return {skip, limit, page}
- [ ] 5.3: Implement paginationMetadata() - calculate pagination info
  - Calculate totalPages, hasNext, hasPrev
- [ ] 5.4: Create src/utils/filtering.js
- [ ] 5.5: Implement buildTaskFilter() - create MongoDB filter from query params
  - Filter by status (single or array)
  - Filter by priority (single or array)
  - Filter by tags (match any tag)
  - Filter by overdue status
- [ ] 5.6: Implement buildSort() - parse sort and order parameters
  - Default: createdAt desc
  - Validate sort field against allowed fields
- [ ] 5.7: Write tests for pagination and filtering utilities

### 6. Input Validation Enhancement
- [ ] 6.1: Extend src/middleware/validation.js with task validation
- [ ] 6.2: Implement validateTask() - validate task creation data
  - Title required, max 200 chars
  - Description optional, max 2000 chars
  - Status must be valid enum
  - Priority must be valid enum
  - Due date must be valid date
  - Tags must be array of strings
- [ ] 6.3: Implement validateTaskUpdate() - validate partial updates
  - All fields optional
  - At least one field required
  - Validate data types and constraints
- [ ] 6.4: Implement validateBulkUpdate() - validate bulk operation
  - taskIds array required
  - updates object required
  - At least one field in updates
- [ ] 6.5: Write tests for all validation middleware

### 7. Response Formatting
- [ ] 7.1: Create src/utils/responses.js
- [ ] 7.2: Implement success() helper - format successful responses
  - {success: true, data, message}
- [ ] 7.3: Implement error() helper - format error responses
  - {success: false, error, statusCode}
- [ ] 7.4: Implement paginatedResponse() helper
  - {success: true, data: [], pagination: {}}
- [ ] 7.5: Update all controllers to use response formatters

### 8. Express Server Initialization
- [ ] 8.1: Create src/server.js
- [ ] 8.2: Initialize Express app from src/app.js
- [ ] 8.3: Connect to MongoDB database
- [ ] 8.4: Register auth routes
- [ ] 8.5: Register task routes
- [ ] 8.6: Start server on configured port
- [ ] 8.7: Add graceful shutdown handler

### 9. Testing - API Integration Tests
- [ ] 9.1: Create tests/api/tasks.test.js with comprehensive API tests
- [ ] 9.2: Test task creation (valid, missing title, invalid priority, unauthenticated)
- [ ] 9.3: Test task listing (filters, sorting, pagination, user isolation)
- [ ] 9.4: Test task retrieval (valid, not found, not owner)
- [ ] 9.5: Test task update (valid, partial, validation, not owner)
- [ ] 9.6: Test task deletion (valid, not owner, already deleted)
- [ ] 9.7: Test search functionality (title, description, case-insensitive)
- [ ] 9.8: Test statistics endpoint (correct counts, user isolation)
- [ ] 9.9: Test bulk update (multiple tasks, permission check)
- [ ] 9.10: Test mark complete (status change, completedAt timestamp)
- [ ] 9.11: Test edge cases (empty results, large datasets, special characters)
- [ ] 9.12: Achieve >85% coverage for API code

### 10. Testing - Performance & Load
- [ ] 10.1: Create tests/api/performance.test.js
- [ ] 10.2: Test list endpoint response time with 1000 tasks (<100ms)
- [ ] 10.3: Test search endpoint response time (<100ms)
- [ ] 10.4: Test pagination with large result sets
- [ ] 10.5: Verify indexes are used (explain plans show indexed queries)
- [ ] 10.6: Load test: concurrent requests from 10 users
- [ ] 10.7: Benchmark: measure response times before/after optimizations

### 11. Documentation
- [ ] 11.1: Create docs/API.md with OpenAPI/Swagger style documentation
- [ ] 11.2: Document all endpoints with method, path, authentication, parameters
- [ ] 11.3: Document request body schemas (JSON schema format)
- [ ] 11.4: Document response schemas with examples
- [ ] 11.5: Document all error responses and status codes
- [ ] 11.6: Create example curl requests for each endpoint
- [ ] 11.7: Create Postman collection in postman/TaskTracker.postman_collection.json
- [ ] 11.8: Document pagination and filtering with examples
- [ ] 11.9: Create PERFORMANCE.md with optimization notes

### 12. Error Handling & Logging
- [ ] 12.1: Ensure all endpoints catch errors and return appropriate status codes
- [ ] 12.2: Log all errors to console/file with context (user, endpoint, error)
- [ ] 12.3: Test error scenarios (db down, invalid input, auth failure)
- [ ] 12.4: Verify error messages don't leak sensitive information
- [ ] 12.5: Write tests for all error scenarios

---

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `src/app.js` | Modify | Add Express middleware and route registration |
| `src/server.js` | Create | Server initialization and startup |
| `src/controllers/TaskController.js` | Create | Task CRUD and statistics logic |
| `src/routes/tasks.js` | Create | Task API route definitions |
| `src/middleware/taskAuth.js` | Create | Task ownership authorization |
| `src/middleware/validation.js` | Modify | Add task-specific validation |
| `src/utils/pagination.js` | Create | Pagination helper functions |
| `src/utils/filtering.js` | Create | Filter and sort logic |
| `src/utils/responses.js` | Create | Consistent response formatting |
| `tests/api/tasks.test.js` | Create | Comprehensive API integration tests |
| `tests/api/performance.test.js` | Create | Performance and load tests |
| `docs/API.md` | Create | API endpoint documentation |
| `docs/PERFORMANCE.md` | Create | Performance optimization notes |
| `postman/TaskTracker.postman_collection.json` | Create | Postman collection for manual testing |
| `package.json` | Modify | Add cors, helmet, morgan, supertest |

## Patterns to Follow

| Pattern | Reference | Usage |
|---------|-----------|-------|
| REST Convention | HTTP verbs for CRUD operations | POST=create, GET=read, PUT=update, DELETE=delete |
| Pagination | Offset-limit pattern with metadata | Always include total, page, hasNext, hasPrev |
| Filtering | Query parameters for conditions | ?status=todo&priority=high |
| Sorting | query params: sort=field&order=asc/desc | Default: createdAt desc |
| Authorization | ensureTaskOwnership middleware | Verify user owns task before allowing operation |
| Error Responses | Consistent {success, error, statusCode} | Use provided response formatters |
| Response Status Codes | 201 created, 204 no content, 400 bad request, 401 unauthorized, 403 forbidden, 404 not found |

## Test Strategy

- [ ] **Unit Tests:** Test utilities and helpers in isolation
  - `tests/utils/pagination.test.js` - edge cases, bounds
  - `tests/utils/filtering.test.js` - filter combinations
  - `tests/middleware/taskAuth.test.js` - authorization logic

- [ ] **Integration Tests:** Test full API flows with database
  - `tests/api/tasks.test.js` - >85% coverage
    - CREATE: valid, invalid input, unauthenticated, missing fields
    - READ: valid ID, not found, not owner (403)
    - UPDATE: valid, partial, validation, not owner
    - DELETE: valid, not owner, idempotent
    - LIST: filters, sorting, pagination, user isolation
    - SEARCH: title, description, case-insensitive, empty results
    - STATS: correct counts, user isolation
    - BULK: multiple tasks, permission checks
    - COMPLETE: status change, completedAt timestamp

- [ ] **Performance Tests:** Verify response times and query efficiency
  - `tests/api/performance.test.js`
    - List 1000 tasks: <100ms median response
    - Search 1000 tasks: <100ms median response
    - Verify indexes used (MongoDB explain plans)
    - Concurrent load: 10 simultaneous users
    - Pagination: 50k tasks with various page sizes

- [ ] **Security Tests:** Authorization and input validation
  - User can only access own tasks
  - Input validation prevents injection attacks
  - Error messages don't leak sensitive data

- [ ] **Coverage Requirement:** Minimum 85% coverage for Phase 3
  - Run: `npm test -- tests/api/ --coverage`
  - Check: controllers, routes, utilities all >85%

## Acceptance Criteria

**ALL must pass:**

- [ ] All 12 task groups completed
- [ ] All gates passing (lint, type-check, tests, security, performance)
- [ ] >85% test coverage for API code
- [ ] All CRUD operations functional
- [ ] Filtering, sorting, pagination working correctly
- [ ] Search functionality finds relevant tasks
- [ ] Statistics calculations accurate
- [ ] All endpoints require authentication
- [ ] User can only access own tasks (authorization verified)
- [ ] API responds in <100ms for typical queries
- [ ] All error scenarios handled gracefully
- [ ] Documentation complete and accurate
- [ ] Postman collection functional

## Rollback Plan

If API issues arise:

1. **Query Performance Degradation:** If queries slow down
   ```bash
   # Verify indexes exist
   mongo tasktracker --eval "db.tasks.getIndexes()"
   # Rebuild indexes if needed
   mongo tasktracker --eval "db.tasks.dropIndex('userId_1'); db.tasks.createIndex({userId: 1})"
   ```

2. **Authorization Bypass:** If user can access other users' tasks
   ```bash
   # Immediately disable route (comment out in src/routes/tasks.js)
   # Run test suite to identify issue
   npm test -- tests/api/tasks.test.js
   # Verify ensureTaskOwnership middleware is applied
   ```

3. **Database Connection Issues:** If MongoDB unavailable during tests
   ```bash
   # Restart MongoDB
   brew services restart mongodb-community  # macOS
   # Clear test database
   mongo tasktracker_test --eval "db.dropDatabase()"
   ```

4. **Memory Leak in List Endpoint:** If handling large datasets causes issues
   ```bash
   # Check for missing pagination
   # Verify request.json limit is set
   # Add memory monitoring to tests
   ```

5. **Complete Revert:**
   ```bash
   git stash
   git reset --hard HEAD~1
   npm install
   npm test
   ```

---

## Implementation Notes

**Architecture Decisions:**
- TaskController handles all business logic, routes just delegate
- Middleware chain: authenticate → ensureTaskOwnership (if needed) → validate → controller → respond
- Pagination: offset-limit pattern (not cursor) for simplicity, supports traditional page numbers
- Filtering: separate filtering logic from controller for testability

**Performance Optimizations:**
- Indexes from Phase 1 support all common queries
- Pagination prevents loading entire dataset into memory
- Sort must use indexed fields (createdAt, dueDate, priority)
- Bulk update uses MongoDB updateMany for efficiency

**Error Handling Strategy:**
- Controllers catch errors from repositories
- Return consistent response format
- Generic error messages for security (don't reveal internal details)
- Log detailed errors server-side for debugging

**Testing Approach:**
- Isolated test database (separate from dev)
- Supertest for HTTP assertions
- Mock repository in unit tests, use real in integration tests
- Load tests with 1000+ tasks to find performance issues
- Test both happy path and all documented error cases

**API Design Principles:**
- RESTful: resources as URLs, HTTP verbs for operations
- Consistent response format: {success, data, error, pagination}
- Meaningful HTTP status codes (201 for created, 204 for deleted, 400 for bad input, etc.)
- Pagination metadata in every list response
- Filters as query parameters, sorting optional
- Authentication on all endpoints, authorization per-task