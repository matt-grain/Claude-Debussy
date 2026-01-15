# TaskTracker MVP Phase 2: Authentication System

**Status:** Pending
**Master Plan:** [TaskTracker MVP - Master Plan](tasktracker-MASTER_PLAN.md)
**Depends On:** [Phase 1: Data Layer Foundation](tasktracker-phase-1.md)

---

## Process Wrapper (MANDATORY)
- [ ] Read previous notes: `notes/NOTES_tasktracker_phase_1.md`
- [ ] **[IMPLEMENTATION - see Tasks below]**
- [ ] Pre-validation (ALL required):
  ```bash
  npm run lint --fix
  npm run type-check
  npm test -- tests/auth/ tests/services/
  npm audit --audit-level=moderate
  # Verify no passwords or secrets in logs or responses
  grep -r "password" tests/auth/*.js | grep -v "hash" | grep -v "secur" || echo "OK"
  ```
- [ ] Fix loop: repeat pre-validation until clean
- [ ] Write `notes/NOTES_tasktracker_phase_2.md` (REQUIRED)

## Gates (must pass before completion)

**ALL gates are BLOCKING.**

- lint: `npm run lint` returns 0 errors
- type-check: `npm run type-check` returns 0 errors
- tests: `npm test -- tests/auth/` - all pass, >85% coverage
- security: `npm audit --audit-level=moderate` - no high severity issues
- secrets: No passwords or JWT secrets hardcoded in code

---

## Overview

This phase implements user registration, login, and JWT-based authentication. Builds on the User model from Phase 1 and creates the security foundation for protecting task endpoints in Phase 3. Focuses on industry-standard security practices: bcrypt password hashing, JWT token management, and input validation.

## Dependencies
- Previous phase: Phase 1 Data Layer (User model, UserRepository)
- External: bcryptjs, jsonwebtoken packages, Node.js crypto for secret generation

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Password security insufficient | Low | High | Use bcryptjs with >=10 salt rounds, enforce password complexity, no plain-text storage |
| JWT token vulnerabilities | Low | High | Use short expiry (7d), verify signature always, store securely, use HTTPS only in production |
| Duplicate email/username not caught | Low | Medium | Database unique indexes from Phase 1, exists() check before creation, catch duplicate key errors |
| Token expiry handling unclear | Medium | Low | Clear error messages for expired tokens, refresh token strategy in Phase 5 (if needed), test expiry edge cases |

---

## Tasks

### 1. Security Configuration
- [ ] 1.1: Create src/config/auth.js with security constants
- [ ] 1.2: Define JWT configuration (secret via environment variable, 7d expiry, HS256 algorithm)
- [ ] 1.3: Define bcrypt configuration (10+ salt rounds)
- [ ] 1.4: Define password requirements (min 8 chars, uppercase, lowercase, number)
- [ ] 1.5: Add common password blacklist (top 1000 passwords)

### 2. Password Service
- [ ] 2.1: Create src/services/PasswordService.js
- [ ] 2.2: Implement hash() - bcryptjs password hashing
- [ ] 2.3: Implement compare() - verify password against hash
- [ ] 2.4: Implement validate() - check password meets complexity requirements
- [ ] 2.5: Add password strength validation (uppercase, lowercase, number)
- [ ] 2.6: Write unit tests for PasswordService (>90% coverage)
- [ ] 2.7: Test that hashing produces different output for same input (salt)
- [ ] 2.8: Test common passwords fail validation

### 3. Token Service
- [ ] 3.1: Create src/services/TokenService.js
- [ ] 3.2: Implement generate() - create JWT token with userId and email
- [ ] 3.3: Implement verify() - validate token signature and expiry
- [ ] 3.4: Implement decode() - extract payload without verification (debug only)
- [ ] 3.5: Add error handling for invalid/expired tokens
- [ ] 3.6: Write unit tests for TokenService (>90% coverage)
- [ ] 3.7: Test expired token detection
- [ ] 3.8: Test invalid signature rejection

### 4. Authentication Controller
- [ ] 4.1: Create src/controllers/AuthController.js
- [ ] 4.2: Implement register() endpoint - user creation with validation
  - Validate email, username, password
  - Check for duplicates
  - Hash password
  - Create user via UserRepository
  - Generate JWT token
  - Return user (without password) and token
- [ ] 4.3: Implement login() endpoint
  - Validate email and password input
  - Find user by email
  - Compare password with hash
  - Generate JWT token
  - Return user and token
- [ ] 4.4: Implement getCurrentUser() endpoint - return authenticated user data
- [ ] 4.5: Implement changePassword() endpoint
  - Verify current password correct
  - Validate new password
  - Hash new password
  - Update user record
- [ ] 4.6: Write integration tests for AuthController (>85% coverage)
- [ ] 4.7: Test all error cases (invalid input, user not found, duplicate email)

### 5. Authentication Middleware
- [ ] 5.1: Create src/middleware/auth.js
- [ ] 5.2: Implement authenticate() middleware
  - Extract token from Authorization header
  - Verify token signature and expiry
  - Load user from database
  - Attach to req.user
  - Return 401 if invalid
- [ ] 5.3: Implement optionalAuth() middleware (don't fail if no token)
- [ ] 5.4: Add error handling for malformed headers
- [ ] 5.5: Write unit tests for middleware

### 6. Input Validation Middleware
- [ ] 6.1: Create src/middleware/validation.js (extend from Phase 1 if exists)
- [ ] 6.2: Implement validateRegistration() middleware
  - Validate email format
  - Validate username (3-30 chars, alphanumeric+underscore)
  - Validate password strength
  - Validate no duplicate fields
- [ ] 6.3: Implement validateLogin() middleware
  - Validate email and password presence
- [ ] 6.4: Implement validateChangePassword() middleware
  - Validate current password and new password presence
  - Validate new password strength
- [ ] 6.5: Write tests for validation middleware

### 7. Error Handling
- [ ] 7.1: Create src/middleware/errorHandler.js (extend if exists from Phase 1)
- [ ] 7.2: Implement custom AuthError class
- [ ] 7.3: Implement centralized error handler middleware
- [ ] 7.4: Define error status codes: 400 (bad input), 401 (invalid auth), 409 (conflict), 500 (server error)
- [ ] 7.5: Ensure no password hashes or tokens in error messages
- [ ] 7.6: Write tests for error handling

### 8. Routes Configuration
- [ ] 8.1: Create src/routes/auth.js with all auth endpoints
- [ ] 8.2: POST /api/auth/register - public route for registration
- [ ] 8.3: POST /api/auth/login - public route for login
- [ ] 8.4: GET /api/auth/me - protected route, requires authenticate middleware
- [ ] 8.5: POST /api/auth/change-password - protected route
- [ ] 8.6: Write integration tests for all routes

### 9. Testing & Security
- [ ] 9.1: Create comprehensive test suite for registration flow
- [ ] 9.2: Create comprehensive test suite for login flow
- [ ] 9.3: Create test suite for protected routes
- [ ] 9.4: Test that passwords are hashed (never stored plain text)
- [ ] 9.5: Test that JWT secrets are not hardcoded
- [ ] 9.6: Test that sensitive data not in logs or responses
- [ ] 9.7: Test SQL injection/NoSQL injection prevention in validation
- [ ] 9.8: Verify bcrypt salt rounds >= 10 in tests

### 10. Documentation
- [ ] 10.1: Create docs/AUTH.md with authentication flow diagram
- [ ] 10.2: Document all endpoints with request/response schemas
- [ ] 10.3: Document error responses and status codes
- [ ] 10.4: Create example API calls (curl or Postman)
- [ ] 10.5: Document JWT token format and claims
- [ ] 10.6: Document password requirements and validation rules
- [ ] 10.7: Update environment variable documentation
- [ ] 10.8: Create SECURITY.md with password and token handling best practices

---

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `src/config/auth.js` | Create | Authentication security configuration |
| `src/services/PasswordService.js` | Create | Password hashing and validation |
| `src/services/TokenService.js` | Create | JWT token generation and verification |
| `src/controllers/AuthController.js` | Create | Registration, login, user endpoints |
| `src/middleware/auth.js` | Create/Modify | Authentication middleware for protected routes |
| `src/middleware/validation.js` | Modify | Add auth-specific validation |
| `src/middleware/errorHandler.js` | Create/Modify | Centralized error handling |
| `src/routes/auth.js` | Create | Auth endpoint routes |
| `tests/services/PasswordService.test.js` | Create | Unit tests for password hashing |
| `tests/services/TokenService.test.js` | Create | Unit tests for JWT tokens |
| `tests/auth/AuthController.test.js` | Create | Integration tests for auth endpoints |
| `tests/middleware/auth.test.js` | Create | Tests for authentication middleware |
| `docs/AUTH.md` | Create | Authentication API documentation |
| `docs/SECURITY.md` | Create | Security best practices and guidelines |
| `.env.example` | Modify | Add JWT_SECRET, BCRYPT_SALT_ROUNDS variables |
| `package.json` | Modify | Add bcryptjs, jsonwebtoken dependencies |

## Patterns to Follow

| Pattern | Reference | Usage |
|---------|-----------|-------|
| Service Layer | PasswordService, TokenService | Centralize security logic away from controllers |
| Middleware Chain | Express middleware pattern | Validation → Authentication → Authorization → Handler |
| Error Handling | Custom AuthError class | Throw errors from services, catch in controller or middleware |
| Configuration | src/config/auth.js | Never hardcode secrets, all from environment variables |
| Password Hashing | bcryptjs with >=10 salt rounds | Never use crypto.pbkdf2 or simple hashing |
| JWT Claims | userId and email only | Minimal payload, re-verify on protected routes |

## Test Strategy

- [ ] **Unit Tests (Services):** Test password and token operations in isolation
  - File: `tests/services/PasswordService.test.js` - >90% coverage
    - Valid password hashing and comparison
    - Password validation with various inputs
    - Weak password rejection
  - File: `tests/services/TokenService.test.js` - >90% coverage
    - Token generation and verification
    - Expired token rejection
    - Invalid signature rejection
    - Payload integrity

- [ ] **Integration Tests (Controller & Routes):** Test full auth flows with database
  - File: `tests/auth/AuthController.test.js` - >85% coverage
    - Valid registration creates user and returns token
    - Duplicate email returns 409 error
    - Invalid password returns 400 error
    - Valid login returns token
    - Invalid credentials return 401 error
    - Token can access protected routes
    - Change password works correctly
    - Invalid current password rejected

- [ ] **Middleware Tests:** Test authentication and validation
  - File: `tests/middleware/auth.test.js`
    - Valid token allows access
    - Missing token returns 401
    - Invalid token returns 401
    - Expired token returns 401
    - User attached to request

- [ ] **Security Tests:** Verify no sensitive data exposure
  - No password hashes in responses
  - No JWT secrets in code
  - No plain-text passwords in database
  - Bcrypt salt rounds sufficient (>=10)
  - Error messages don't leak information

- [ ] **Coverage Requirement:** Minimum 85% coverage for Phase 2
  - Run: `npm test -- tests/auth/ tests/services/ --coverage`

## Acceptance Criteria

**ALL must pass:**

- [ ] All 10 task groups completed
- [ ] All gates passing (lint, type-check, tests, security, no hardcoded secrets)
- [ ] >85% test coverage for auth module
- [ ] Registration and login endpoints working
- [ ] JWT tokens generated and verified correctly
- [ ] Protected routes require authentication
- [ ] No passwords stored plain-text in database
- [ ] No secrets hardcoded in source code
- [ ] All error messages user-friendly and security-conscious
- [ ] Documentation complete and accurate

## Rollback Plan

If authentication issues arise:

1. **JWT Secret Exposure:** If JWT_SECRET accidentally committed:
   ```bash
   # Rotate the secret immediately
   # Generate new secret: openssl rand -base64 32
   # Update .env with new secret
   # Force users to re-authenticate with new token secret
   git rm --cached .env
   git add .gitignore
   git commit -m "Remove .env from tracking"
   ```

2. **Password Hash Issues:** If bcrypt configuration changed mid-phase:
   ```bash
   # Drop test database and reseed
   mongo tasktracker_test --eval "db.dropDatabase()"
   npm run test:db:seed
   ```

3. **Test Failures:** Isolate and fix test database
   ```bash
   rm -rf tests/.db
   npm test -- tests/auth/ --forceExit
   ```

4. **Dependency Conflicts:** Roll back to working state
   ```bash
   rm -rf node_modules package-lock.json
   git checkout package.json
   npm install
   npm test
   ```

5. **Complete Revert:**
   ```bash
   git stash
   git reset --hard HEAD~1
   ```

---

## Implementation Notes

**Security Architecture:**
- Passwords never stored or transmitted plain-text
- JWT tokens use HTTPS-only storage (localStorage, secure cookies in Phase 4)
- Token expiry is short (7 days) to limit compromise window
- Password hashing uses bcryptjs with >=10 salt rounds (computationally expensive, resists brute force)
- No sensitive data in error messages (generic "Invalid credentials" instead of "Email not found")

**Token Management:**
- JWT payload contains only userId and email (minimal surface area)
- Token verified on every protected request (re-verify pattern)
- Expiry enforced by JWT library with timestamp comparison
- No refresh token in MVP (Phase 5 can add if needed)

**Password Validation:**
- Enforces minimum 8 characters for length
- Requires uppercase, lowercase, number (entropy requirement)
- Optional: block common passwords (top 1000 list)
- User-friendly error messages guide password creation

**Error Handling Philosophy:**
- 400: Invalid input (validation failed)
- 401: Authentication failed (invalid credentials or token)
- 409: Conflict (duplicate email or username)
- 500: Server error (unexpected exception)
- Never reveal whether email exists in system (prevent user enumeration)

**Testing Strategy:**
- Isolated test database prevents production data access
- Mock UserRepository in unit tests, use real repository in integration tests
- Test both happy path and all error cases
- Security tests verify no leakage of sensitive data