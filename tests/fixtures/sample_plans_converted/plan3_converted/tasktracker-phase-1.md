# TaskTracker MVP Phase 1: Data Layer Foundation

**Status:** Pending
**Master Plan:** [TaskTracker MVP - Master Plan](tasktracker-MASTER_PLAN.md)
**Depends On:** None

---

## Process Wrapper (MANDATORY)
- [ ] Read previous notes: N/A (initial phase)
- [ ] **[IMPLEMENTATION - see Tasks below]**
- [ ] Pre-validation (ALL required):
  ```bash
  npm run lint --fix
  npm run type-check
  npm test -- tests/models/ tests/repositories/
  npm audit --audit-level=moderate
  ```
- [ ] Fix loop: repeat pre-validation until clean
- [ ] Write `notes/NOTES_tasktracker_phase_1.md` (REQUIRED)

## Gates (must pass before completion)

**ALL gates are BLOCKING.**

- lint: `npm run lint` returns 0 errors
- type-check: `npm run type-check` returns 0 errors
- tests: `npm test -- tests/models/ tests/repositories/` - all pass, >90% coverage
- security: `npm audit --audit-level=moderate` - no high severity issues

---

## Overview

This phase establishes the database foundation using MongoDB and Mongoose. Creates data models, schemas, repositories, and validation layer that all subsequent modules depend on. This is the critical foundation—quality and test coverage here enables rapid development of authentication and API layers.

## Dependencies
- Previous phase: None (initial phase)
- External: MongoDB (local or Atlas), Node.js 16+, npm

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| MongoDB connection issues in development | Low | Medium | Document setup clearly, provide docker-compose for local testing, robust connection handling |
| Mongoose schema design flaws | Low | High | Comprehensive schema tests, create detailed test data scenarios, validate with experienced MongoDB users |
| Repository pattern adds complexity | Medium | Low | Clear documentation with examples, simple CRUD pattern first, add query optimization later |
| Index strategy inadequate for performance | Medium | Medium | Add indexes upfront for userId, status, createdAt; benchmark queries; add composite indexes based on common patterns |

---

## Tasks

### 1. Project Setup & Dependencies
- [ ] 1.1: Initialize Node.js project with `npm init -y`
- [ ] 1.2: Install core dependencies: mongoose, dotenv, jest, @types/node
- [ ] 1.3: Create project structure: src/models/, src/repositories/, src/config/, src/validation/, tests/
- [ ] 1.4: Configure jest.config.js for Node.js testing
- [ ] 1.5: Setup .env.example with MongoDB connection strings

### 2. MongoDB Connection Management
- [ ] 2.1: Create src/config/database.js with Database class
- [ ] 2.2: Implement connect() method with connection pooling (min: 5, max: 10)
- [ ] 2.3: Implement disconnect() method with graceful shutdown
- [ ] 2.4: Add connection event handlers (connected, disconnected, error)
- [ ] 2.5: Create test database configuration separate from development
- [ ] 2.6: Write integration tests for connection management

### 3. User Schema & Model
- [ ] 3.1: Create src/models/User.js with Mongoose User schema
- [ ] 3.2: Implement required fields: email, username, passwordHash, createdAt, settings
- [ ] 3.3: Add validation: email format, username pattern (3-30 chars, alphanumeric+underscore)
- [ ] 3.4: Create indexes: email (unique), username (unique)
- [ ] 3.5: Implement toJSON() method to exclude passwordHash
- [ ] 3.6: Add static methods: findByEmail(), findByUsername(), exists()
- [ ] 3.7: Write unit tests for User model (>90% coverage)

### 4. Task Schema & Model
- [ ] 4.1: Create src/models/Task.js with Mongoose Task schema
- [ ] 4.2: Implement required fields: title, status, priority, userId, createdAt, updatedAt
- [ ] 4.3: Implement optional fields: description, dueDate, tags, completedAt
- [ ] 4.4: Add enum validation for status (todo, in_progress, done) and priority (low, medium, high)
- [ ] 4.5: Create indexes: userId, status, createdAt, compound (userId, status)
- [ ] 4.6: Add pre-save middleware to update updatedAt timestamp
- [ ] 4.7: Add pre-save middleware to set completedAt when status changes to done
- [ ] 4.8: Implement instance methods: markComplete(), isOverdue()
- [ ] 4.9: Implement static methods: findByUser(), findByStatus(), searchTasks()
- [ ] 4.10: Add virtual: daysUntilDue (calculated property)
- [ ] 4.11: Write unit tests for Task model (>90% coverage)

### 5. Data Validation Layer
- [ ] 5.1: Create src/validation/schemas.js with validation schemas
- [ ] 5.2: Define createUserSchema with email, username, password validation rules
- [ ] 5.3: Define createTaskSchema with title, description, status, priority, dueDate rules
- [ ] 5.4: Create validator utility functions for reuse across project
- [ ] 5.5: Write unit tests for all validation schemas

### 6. User Repository
- [ ] 6.1: Create src/repositories/UserRepository.js
- [ ] 6.2: Implement create() - insert user document
- [ ] 6.3: Implement findById() - retrieve by ObjectId
- [ ] 6.4: Implement findByEmail() - retrieve by email field
- [ ] 6.5: Implement findByUsername() - retrieve by username field
- [ ] 6.6: Implement update() - modify user document
- [ ] 6.7: Implement delete() - remove user document
- [ ] 6.8: Implement exists() - check if email or username already exists
- [ ] 6.9: Write integration tests for all UserRepository methods
- [ ] 6.10: Test error handling (not found, duplicate key, invalid ID)

### 7. Task Repository
- [ ] 7.1: Create src/repositories/TaskRepository.js
- [ ] 7.2: Implement create() - insert task document
- [ ] 7.3: Implement findById() - retrieve by ObjectId
- [ ] 7.4: Implement findByUser() with optional filters (status, priority, tags)
- [ ] 7.5: Implement update() - modify task document
- [ ] 7.6: Implement delete() - remove task document
- [ ] 7.7: Implement search() - find by title/description with user filter
- [ ] 7.8: Implement getStatsByUser() - count tasks by status/priority
- [ ] 7.9: Implement bulkUpdate() - update multiple tasks at once
- [ ] 7.10: Write integration tests for all TaskRepository methods
- [ ] 7.11: Test pagination and filtering with large datasets

### 8. Documentation & Examples
- [ ] 8.1: Create README.md with MongoDB setup instructions (macOS, Ubuntu, Windows)
- [ ] 8.2: Document MongoDB Atlas setup for cloud development
- [ ] 8.3: Create docs/SCHEMA.md with detailed schema documentation
- [ ] 8.4: Create docs/REPOSITORIES.md with repository method documentation
- [ ] 8.5: Create example seed data script in scripts/seed-data.js
- [ ] 8.6: Document environment configuration in .env.example
- [ ] 8.7: Create TESTING.md with test running instructions

---

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `package.json` | Create | Project metadata, dependencies, scripts |
| `jest.config.js` | Create | Jest test configuration |
| `.env.example` | Create | Environment variable template |
| `src/config/database.js` | Create | MongoDB connection manager |
| `src/models/User.js` | Create | Mongoose User schema and model |
| `src/models/Task.js` | Create | Mongoose Task schema and model |
| `src/validation/schemas.js` | Create | Standalone validation schemas |
| `src/repositories/UserRepository.js` | Create | User data access layer |
| `src/repositories/TaskRepository.js` | Create | Task data access layer |
| `tests/models/User.test.js` | Create | Unit tests for User model |
| `tests/models/Task.test.js` | Create | Unit tests for Task model |
| `tests/repositories/UserRepository.test.js` | Create | Integration tests for UserRepository |
| `tests/repositories/TaskRepository.test.js` | Create | Integration tests for TaskRepository |
| `tests/config/database.test.js` | Create | Tests for database connection |
| `scripts/seed-data.js` | Create | Seed script for test data |
| `docs/SCHEMA.md` | Create | Schema documentation |
| `docs/REPOSITORIES.md` | Create | Repository API documentation |
| `README.md` | Create | Project setup and overview |

## Patterns to Follow

| Pattern | Reference | Usage |
|---------|-----------|-------|
| Repository Pattern | Data Layer section in source plan | Create repositories for all data access, never query directly in controllers |
| Mongoose Schema | User and Task schema specifications | Follow field types, validations, indexes as specified |
| Test Isolation | Jest best practices | Use separate test database, clean up after each test, mock external dependencies |
| Error Handling | Common Node.js patterns | Throw descriptive errors from repositories, let controllers handle HTTP responses |
| Index Strategy | MongoDB indexing guide | Index userId, status, createdAt; create compound indexes for common query patterns |

## Test Strategy

- [ ] **Unit Tests (Models):** Test schema validation, unique constraints, methods, virtuals, middleware
  - File: `tests/models/User.test.js` - >90% coverage
  - File: `tests/models/Task.test.js` - >90% coverage
  - Validate: All enum values, required fields, validation rules

- [ ] **Integration Tests (Repositories):** Test CRUD operations with test database
  - File: `tests/repositories/UserRepository.test.js` - >90% coverage
  - File: `tests/repositories/TaskRepository.test.js` - >90% coverage
  - Validate: Create, read, update, delete work correctly
  - Validate: Filters and search return correct results
  - Validate: Error handling for not found, duplicate key, invalid data

- [ ] **Connection Tests:** Test database connection management
  - File: `tests/config/database.test.js`
  - Validate: Connection succeeds/fails appropriately
  - Validate: Connection pooling works
  - Validate: Reconnection after disconnect works

- [ ] **Coverage Requirement:** Minimum 90% coverage for Phase 1
  - Run: `npm test -- --coverage`
  - Verify: All files in src/models and src/repositories have >90% coverage

## Acceptance Criteria

**ALL must pass:**

- [ ] All 8 task groups completed
- [ ] All gates passing (lint, type-check, tests, security)
- [ ] >90% test coverage for models and repositories
- [ ] No hardcoded credentials in code or examples
- [ ] All error messages are helpful and security-conscious
- [ ] Database indexes created for all query patterns
- [ ] Documentation complete and accurate
- [ ] Code follows consistent style (use `npm run lint --fix`)
- [ ] No npm audit vulnerabilities at moderate or higher level

## Rollback Plan

If issues arise during Phase 1:

1. **Schema Changes:** MongoDB supports schema evolution. If a schema change breaks tests:
   - Use `db.getCollection('users').drop()` to clear test collection
   - Delete and recreate test database: `mongo tasktracker_test --eval "db.dropDatabase()"`
   - Re-run migrations/seeds

2. **Dependency Issues:** If npm dependency conflicts arise:
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   npm test
   ```

3. **Connection Issues:** If MongoDB connection fails:
   - Verify MongoDB is running: `mongosh` command
   - Check connection string in .env matches your setup
   - For MongoDB Atlas: verify IP whitelist and database user credentials
   - Use test database separate from development

4. **Revert to Previous State:**
   ```bash
   git stash                  # Discard uncommitted changes
   git reset --hard HEAD~1   # Revert to previous commit
   ```

---

## Implementation Notes

**Architecture Decisions:**
- Use Repository Pattern for data access to decouple models from business logic
- Create separate test database configuration to avoid data pollution
- Index strategy focuses on userId (all queries filter by user), status (common filter), and createdAt (sorting)
- Compound index on (userId, status) for very common query pattern in Phase 3

**Mongoose Configuration:**
- Use timestamps: true for automatic createdAt/updatedAt
- Use sparse indexes for optional unique fields
- Validate email format and username pattern at schema level
- Pre-save hooks handle completedAt timestamp and updatedAt updates

**Testing Approach:**
- Mock database connection in unit tests, use real connection in integration tests
- Create test utilities for document creation/cleanup
- Test both happy path and error cases
- Verify indexes exist after model creation

**Performance Considerations (for Phase 3):**
- Indexes on userId ensure user task queries are efficient
- Compound index (userId, status) optimizes the very common "get user's todo tasks" query
- Pagination implemented in Phase 3 will rely on indexes for sorted, limited results