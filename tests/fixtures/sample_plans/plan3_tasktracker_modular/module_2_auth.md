# Module 2: Authentication

**Duration**: 4 days
**Dependencies**: Module 1 (Data Layer)
**Validation Agent**: python-task-validator (for Node.js code quality checks where applicable)

## Overview

Implement user registration, login, and JWT-based authentication. This module builds on the User model from Module 1 and provides the security foundation for the application.

## Setup

### Install Dependencies

```bash
npm install bcryptjs jsonwebtoken
npm install --save-dev supertest
```

### Security Configuration

Location: `src/config/auth.js`

```javascript
module.exports = {
  jwt: {
    secret: process.env.JWT_SECRET,
    expiresIn: '7d',
    algorithm: 'HS256'
  },
  bcrypt: {
    saltRounds: 10
  },
  password: {
    minLength: 8,
    maxLength: 100,
    requireUppercase: true,
    requireLowercase: true,
    requireNumber: true
  }
}
```

## Password Hashing

Location: `src/services/PasswordService.js`

Create service for password operations:

```javascript
class PasswordService {
  /**
   * Hash a plain text password
   * @param {string} password - Plain text password
   * @returns {Promise<string>} Hashed password
   */
  async hash(password) {
    // Validate password meets requirements
    // Hash using bcryptjs
  }

  /**
   * Compare password with hash
   * @param {string} password - Plain text password
   * @param {string} hash - Hashed password
   * @returns {Promise<boolean>} Match result
   */
  async compare(password, hash) {
    // Use bcryptjs compare
  }

  /**
   * Validate password meets complexity requirements
   * @param {string} password - Password to validate
   * @returns {object} Validation result
   */
  validate(password) {
    // Check length
    // Check for uppercase, lowercase, number
    // Return {valid: boolean, errors: string[]}
  }
}
```

**Password Requirements**:
- Minimum 8 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one number
- No common passwords (check against list)

## JWT Token Management

Location: `src/services/TokenService.js`

Create service for JWT operations:

```javascript
class TokenService {
  /**
   * Generate JWT token for user
   * @param {object} user - User object
   * @returns {string} JWT token
   */
  generate(user) {
    // Create payload with user id and email
    // Sign with secret and expiration
  }

  /**
   * Verify and decode JWT token
   * @param {string} token - JWT token
   * @returns {object} Decoded payload
   * @throws {Error} If token invalid or expired
   */
  verify(token) {
    // Verify token signature
    // Check expiration
    // Return decoded payload
  }

  /**
   * Decode token without verification (for debugging)
   * @param {string} token - JWT token
   * @returns {object} Decoded payload
   */
  decode(token) {
    // Return decoded payload without verification
  }
}
```

**Token Payload**:
```javascript
{
  userId: 'ObjectId',
  email: 'user@example.com',
  iat: 1234567890,  // Issued at
  exp: 1234567890   // Expiration
}
```

## Authentication Controller

Location: `src/controllers/AuthController.js`

Create controller for auth endpoints:

```javascript
class AuthController {
  /**
   * Register new user
   * POST /api/auth/register
   */
  async register(req, res) {
    // 1. Validate input (email, username, password)
    // 2. Check if user already exists
    // 3. Validate password complexity
    // 4. Hash password
    // 5. Create user in database
    // 6. Generate JWT token
    // 7. Return user data and token
  }

  /**
   * Login existing user
   * POST /api/auth/login
   */
  async login(req, res) {
    // 1. Validate input (email, password)
    // 2. Find user by email
    // 3. Compare password with hash
    // 4. Generate JWT token
    // 5. Return user data and token
  }

  /**
   * Get current user from token
   * GET /api/auth/me
   */
  async getCurrentUser(req, res) {
    // 1. User already attached by auth middleware
    // 2. Return user data (without password)
  }

  /**
   * Change password
   * POST /api/auth/change-password
   */
  async changePassword(req, res) {
    // 1. Verify current password
    // 2. Validate new password
    // 3. Hash new password
    // 4. Update user record
    // 5. Optionally invalidate old tokens
  }
}
```

## Authentication Middleware

Location: `src/middleware/auth.js`

Create middleware to protect routes:

```javascript
/**
 * Verify JWT token and attach user to request
 */
async function authenticate(req, res, next) {
  try {
    // 1. Extract token from Authorization header
    // 2. Verify token is valid
    // 3. Decode token to get user ID
    // 4. Load user from database
    // 5. Attach user to req.user
    // 6. Call next()
  } catch (error) {
    // Return 401 Unauthorized if token invalid
  }
}

/**
 * Optional authentication - attach user if token present
 */
async function optionalAuth(req, res, next) {
  // Same as authenticate but don't return error if no token
  // Just skip to next() without attaching user
}
```

**Header Format**:
```
Authorization: Bearer <jwt_token>
```

## Routes

Location: `src/routes/auth.js`

Define auth routes:

```javascript
const express = require('express');
const router = express.Router();
const AuthController = require('../controllers/AuthController');
const { authenticate } = require('../middleware/auth');

// Public routes
router.post('/register', AuthController.register);
router.post('/login', AuthController.login);

// Protected routes (require authentication)
router.get('/me', authenticate, AuthController.getCurrentUser);
router.post('/change-password', authenticate, AuthController.changePassword);

module.exports = router;
```

## Error Handling

Location: `src/middleware/errorHandler.js`

Create centralized error handler:

```javascript
class AuthError extends Error {
  constructor(message, statusCode = 401) {
    super(message);
    this.statusCode = statusCode;
    this.name = 'AuthError';
  }
}

function errorHandler(err, req, res, next) {
  // Log error for debugging
  console.error(err);

  // Determine status code and message
  const statusCode = err.statusCode || 500;
  const message = err.message || 'Internal server error';

  // Send error response
  res.status(statusCode).json({
    success: false,
    error: message,
    ...(process.env.NODE_ENV === 'development' && { stack: err.stack })
  });
}
```

**Error Types**:
- 400 Bad Request - Invalid input
- 401 Unauthorized - Invalid credentials or token
- 403 Forbidden - Valid token but insufficient permissions
- 409 Conflict - User already exists
- 500 Internal Server Error - Unexpected errors

## Input Validation

Location: `src/middleware/validation.js`

Create validation middleware:

```javascript
function validateRegistration(req, res, next) {
  const { email, username, password } = req.body;

  const errors = [];

  // Validate email
  if (!email || !isValidEmail(email)) {
    errors.push('Invalid email address');
  }

  // Validate username
  if (!username || username.length < 3 || username.length > 30) {
    errors.push('Username must be 3-30 characters');
  }
  if (!/^[a-zA-Z0-9_]+$/.test(username)) {
    errors.push('Username can only contain letters, numbers, and underscores');
  }

  // Validate password
  const passwordValidation = PasswordService.validate(password);
  if (!passwordValidation.valid) {
    errors.push(...passwordValidation.errors);
  }

  if (errors.length > 0) {
    return res.status(400).json({ success: false, errors });
  }

  next();
}
```

## Testing

Location: `tests/auth/`

### Unit Tests

Test PasswordService:
- Hashing produces different output for same input (salt)
- Compare correctly identifies matching passwords
- Validation catches weak passwords
- Strong passwords pass validation

Test TokenService:
- Generated tokens can be verified
- Expired tokens throw error
- Invalid tokens throw error
- Payload contains expected data

### Integration Tests

Test registration endpoint:
- Valid registration creates user and returns token
- Duplicate email returns 409 error
- Invalid email returns 400 error
- Weak password returns 400 error
- Password is hashed (not stored plain text)

Test login endpoint:
- Valid credentials return token
- Invalid email returns 401
- Invalid password returns 401
- Token can be used to access protected routes

Test authentication middleware:
- Valid token allows access
- Missing token returns 401
- Invalid token returns 401
- Expired token returns 401
- User is attached to request object

Test change password:
- Correct current password allows change
- Incorrect current password returns 401
- Weak new password returns 400
- Password is updated in database

### Security Tests

- Passwords are never logged
- Password hashes are never returned in responses
- JWT secret is not hardcoded
- Tokens expire as configured
- bcrypt salt rounds are sufficient (>= 10)

## Module Validation Criteria

This module is complete when:

1. **Functionality Validation**
   - Users can register with email, username, and password
   - Users can log in with email and password
   - JWT tokens are generated on successful auth
   - Protected routes require valid token
   - Password change works correctly

2. **Security Validation**
   - Passwords are hashed with bcrypt
   - JWT tokens use strong secret
   - Tokens expire after configured time
   - Password complexity requirements enforced
   - No sensitive data in responses or logs

3. **Testing Validation**
   - All unit tests pass (>85% coverage)
   - All integration tests pass
   - Security tests verify no vulnerabilities
   - Tests use isolated test database

4. **Code Quality**
   - ESLint passes with no errors
   - Code follows consistent style
   - Error messages are helpful
   - Functions are well documented
   - Use validation agent to check code quality

## Environment Variables

Add to `.env`:

```
JWT_SECRET=your-secret-key-change-in-production
JWT_EXPIRES_IN=7d
BCRYPT_SALT_ROUNDS=10
```

**Production Security**:
- Generate JWT_SECRET with: `openssl rand -base64 32`
- Never commit secrets to version control
- Use environment-specific secrets
- Rotate secrets periodically

## Deliverables

- [ ] PasswordService with hashing and validation
- [ ] TokenService with JWT generation and verification
- [ ] AuthController with register, login, getCurrentUser
- [ ] Authentication middleware
- [ ] Auth routes configuration
- [ ] Input validation middleware
- [ ] Error handling middleware
- [ ] Unit tests for services (>90% coverage)
- [ ] Integration tests for endpoints
- [ ] Security test suite
- [ ] API documentation for auth endpoints
- [ ] Environment variable documentation

## Next Steps

Once this module is validated:
1. Tag release as `v0.2.0-auth`
2. Test authentication flow manually with Postman
3. Begin Module 3 (Task API)
4. Use auth middleware to protect task endpoints
