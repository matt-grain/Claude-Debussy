# TaskTracker MVP - Modular Implementation Plan

## Executive Summary

TaskTracker MVP is a lightweight task management application focused on individual productivity. This implementation plan takes a modular approach, building the application in self-contained modules that can be developed and tested independently.

**Target Launch**: 6 weeks from start
**Primary User**: Individual contributors and freelancers
**Core Value Prop**: Simple, fast task tracking without the complexity of team features

## Architecture Overview

```
┌─────────────────────────────────────────┐
│          Web Frontend (React)           │
│  - Task UI  - Auth UI  - Settings UI   │
└─────────────────┬───────────────────────┘
                  │ REST API
┌─────────────────▼───────────────────────┐
│       Backend API Layer (Node.js)       │
│  - Routes  - Controllers  - Middleware  │
└─────────────────┬───────────────────────┘
                  │
┌─────────────────▼───────────────────────┐
│      Data Layer (MongoDB + Mongoose)    │
│  - Models  - Schemas  - Validation      │
└─────────────────────────────────────────┘
```

## Technology Choices

**Backend**:
- Node.js with Express (fast iteration, JS full-stack)
- MongoDB for flexible schema (rapid prototyping)
- JWT for stateless authentication
- Jest for testing

**Frontend**:
- React with hooks (widely known, good ecosystem)
- Material-UI for components (quick development)
- React Query for data fetching (simplifies state)
- Vite for build tooling (faster than CRA)

**Infrastructure**:
- Vercel for frontend hosting (easy deployment)
- MongoDB Atlas for database (managed service)
- GitHub Actions for CI (free for public repos)

## Module Breakdown

The project is divided into four independent modules that build upon each other:

1. **Data Module** - Database models and data access layer
2. **Authentication Module** - User registration and login system
3. **API Module** - REST endpoints for task operations
4. **Interface Module** - React frontend application

Each module has clear inputs/outputs and can be validated independently.

---

## Module 1: Data Layer

**Objective**: Create MongoDB schemas and data access layer

See `module_1_data.md` for complete specification

---

## Module 2: Authentication

**Objective**: Implement user registration, login, and JWT-based auth

See `module_2_auth.md` for complete specification

---

## Module 3: Task API

**Objective**: Build REST API for task CRUD operations

See `module_3_api.md` for complete specification

---

## Module 4: User Interface

**Objective**: Create React frontend with Material-UI

See `module_4_interface.md` for complete specification

---

## Integration Testing

After all modules are complete, perform integration testing:

1. **End-to-End User Flows**
   - New user registration → create first task → mark complete
   - Login → view tasks → edit task → delete task
   - Filter and search tasks → update multiple tasks

2. **Cross-Module Validation**
   - Frontend auth flows work with backend JWT
   - Task operations trigger correct database queries
   - Error handling propagates through all layers

3. **Performance Testing**
   - API endpoints respond within 100ms
   - Frontend loads within 1.5s on 4G
   - Database queries are optimized with indexes

## Deployment Strategy

### Development Environment
- Local MongoDB instance
- Node server on localhost:3000
- React dev server on localhost:5173
- Environment variables in .env.local

### Staging Environment
- MongoDB Atlas free tier
- Backend on Vercel serverless functions
- Frontend on Vercel preview deployment
- Test with production-like data

### Production Environment
- MongoDB Atlas M2 cluster
- Backend on Vercel production
- Frontend on Vercel production with custom domain
- Environment secrets in Vercel dashboard
- Monitoring with Vercel Analytics

## Success Criteria

The MVP is considered complete when:

- [ ] Users can register and log in
- [ ] Users can create, view, edit, and delete tasks
- [ ] Tasks can be filtered by status and priority
- [ ] Search finds tasks by title and description
- [ ] Application works on mobile and desktop
- [ ] All API endpoints have >80% test coverage
- [ ] No critical security vulnerabilities (npm audit)
- [ ] Application deployed to production
- [ ] Performance metrics meet targets

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|-----------|
| MongoDB schema changes break compatibility | High | Use Mongoose migrations, version schemas |
| JWT token security issues | High | Use short expiry, HTTPS only, secure storage |
| Frontend state complexity | Medium | Use React Query for server state, keep local state minimal |
| API performance with large datasets | Medium | Add pagination early, implement database indexes |
| Third-party dependency vulnerabilities | Low | Regular npm audit, automated Dependabot PRs |

## Timeline

| Module | Duration | Dependencies |
|--------|----------|--------------|
| Data Layer | 3 days | None |
| Authentication | 4 days | Data Layer |
| Task API | 5 days | Data Layer, Authentication |
| User Interface | 10 days | All backend modules |
| Integration & Testing | 4 days | All modules |
| Deployment & Polish | 4 days | Integration complete |

**Total**: ~30 days (6 weeks)

## Future Enhancements (Post-MVP)

Ideas for v2:
- Recurring tasks
- Task categories/tags
- Due date reminders via email
- Data export (CSV, JSON)
- Mobile apps (React Native)
- Collaboration features (share tasks)
- Calendar view
- Task attachments
# Module 1: Data Layer

**Duration**: 3 days
**Dependencies**: None
**Validation Agent**: python-task-validator (for any Python utilities)

## Overview

Build the database foundation using MongoDB and Mongoose. This module establishes the data models, schemas, and basic data access patterns that all other modules will depend on.

## Setup

### MongoDB Installation

For local development:
```bash
# macOS
brew install mongodb-community

# Ubuntu
sudo apt-get install mongodb

# Windows
# Download installer from mongodb.com
```

### MongoDB Atlas Setup

For shared dev/staging:
1. Create account at mongodb.com/cloud/atlas
2. Create free M0 cluster
3. Add IP whitelist (0.0.0.0/0 for dev)
4. Create database user
5. Get connection string

### Project Initialization

```bash
npm init -y
npm install mongoose dotenv
npm install --save-dev jest @types/node
```

## Data Models

### User Schema

Location: `src/models/User.js`

```javascript
{
  email: {
    type: String,
    required: true,
    unique: true,
    lowercase: true,
    trim: true,
    validate: email validator
  },
  username: {
    type: String,
    required: true,
    unique: true,
    minlength: 3,
    maxlength: 30,
    trim: true
  },
  passwordHash: {
    type: String,
    required: true
  },
  createdAt: {
    type: Date,
    default: Date.now
  },
  settings: {
    theme: { type: String, default: 'light' },
    notifications: { type: Boolean, default: true }
  }
}
```

**Indexes**:
- email (unique)
- username (unique)

**Methods**:
- `toJSON()` - Remove passwordHash from output

**Statics**:
- `findByEmail(email)` - Find user by email
- `findByUsername(username)` - Find user by username

### Task Schema

Location: `src/models/Task.js`

```javascript
{
  title: {
    type: String,
    required: true,
    trim: true,
    maxlength: 200
  },
  description: {
    type: String,
    trim: true,
    maxlength: 2000
  },
  status: {
    type: String,
    enum: ['todo', 'in_progress', 'done'],
    default: 'todo'
  },
  priority: {
    type: String,
    enum: ['low', 'medium', 'high'],
    default: 'medium'
  },
  dueDate: {
    type: Date,
    default: null
  },
  userId: {
    type: mongoose.Schema.Types.ObjectId,
    ref: 'User',
    required: true,
    index: true
  },
  tags: [{
    type: String,
    trim: true,
    lowercase: true
  }],
  createdAt: {
    type: Date,
    default: Date.now,
    index: true
  },
  updatedAt: {
    type: Date,
    default: Date.now
  },
  completedAt: {
    type: Date,
    default: null
  }
}
```

**Indexes**:
- userId (for efficient user task queries)
- status (for filtering)
- createdAt (for sorting)
- Compound index on (userId, status) for common query pattern

**Middleware**:
- Pre-save hook to update `updatedAt`
- Pre-save hook to set `completedAt` when status changes to 'done'

**Methods**:
- `markComplete()` - Set status to done and timestamp
- `isOverdue()` - Check if task is past due date

**Statics**:
- `findByUser(userId)` - Get all tasks for user
- `findByStatus(userId, status)` - Get tasks by status
- `searchTasks(userId, query)` - Search by title/description

**Virtuals**:
- `daysUntilDue` - Calculate days remaining until due date

## Database Connection

Location: `src/config/database.js`

Create database connection manager:

```javascript
class Database {
  constructor() {
    this.connection = null;
  }

  async connect(uri) {
    // Connect to MongoDB
    // Handle connection events
    // Retry logic for failed connections
  }

  async disconnect() {
    // Gracefully close connection
  }

  getConnection() {
    return this.connection;
  }
}
```

**Configuration Options**:
- Connection pooling (min: 5, max: 10)
- Socket timeout: 30s
- Server selection timeout: 5s
- Auto-reconnect enabled

**Event Handlers**:
- Log on successful connection
- Log on disconnection
- Handle connection errors
- Emit custom events for monitoring

## Data Access Layer

Location: `src/repositories/`

Create repository pattern for data access:

### UserRepository

```javascript
class UserRepository {
  async create(userData) { }
  async findById(id) { }
  async findByEmail(email) { }
  async findByUsername(username) { }
  async update(id, updates) { }
  async delete(id) { }
  async exists(email, username) { }
}
```

### TaskRepository

```javascript
class TaskRepository {
  async create(taskData) { }
  async findById(id) { }
  async findByUser(userId, filters = {}) { }
  async update(id, updates) { }
  async delete(id) { }
  async search(userId, query) { }
  async getStatsByUser(userId) { }
  async bulkUpdate(taskIds, updates) { }
}
```

**Benefits of Repository Pattern**:
- Abstracts database operations
- Easier to mock in tests
- Centralized query logic
- Can switch databases with less code change

## Validation

Location: `src/validation/schemas.js`

Create validation schemas separate from Mongoose:

```javascript
const createUserSchema = {
  email: {
    required: true,
    type: 'email',
    maxLength: 100
  },
  username: {
    required: true,
    type: 'string',
    minLength: 3,
    maxLength: 30,
    pattern: /^[a-zA-Z0-9_]+$/
  },
  password: {
    required: true,
    type: 'string',
    minLength: 8,
    maxLength: 100
  }
}

const createTaskSchema = {
  title: {
    required: true,
    type: 'string',
    minLength: 1,
    maxLength: 200
  },
  description: {
    type: 'string',
    maxLength: 2000
  },
  status: {
    type: 'enum',
    values: ['todo', 'in_progress', 'done']
  },
  priority: {
    type: 'enum',
    values: ['low', 'medium', 'high']
  },
  dueDate: {
    type: 'date'
  }
}
```

## Testing

Location: `tests/models/`

### Unit Tests for Models

Test User model:
- Schema validation works correctly
- Unique constraints are enforced
- Email validation catches invalid emails
- toJSON removes sensitive fields
- Static methods return correct results

Test Task model:
- Required fields are enforced
- Enum validation works for status and priority
- Timestamps update correctly
- Middleware sets completedAt when marking done
- Virtuals calculate correctly
- Search functionality finds relevant tasks

### Integration Tests for Repositories

Test with test database:
- Create operations return valid documents
- Read operations find correct data
- Update operations modify documents
- Delete operations remove documents
- Search returns relevant results
- Filters work correctly

### Database Connection Tests

- Connection succeeds with valid URI
- Connection fails gracefully with invalid URI
- Reconnection works after disconnect
- Connection pooling limits connections

## Environment Configuration

Location: `.env.example`

```
# Database
MONGODB_URI=mongodb://localhost:27017/tasktracker_dev
MONGODB_TEST_URI=mongodb://localhost:27017/tasktracker_test

# Environment
NODE_ENV=development
```

## Module Validation Criteria

This module is complete when:

1. **Schema Validation**
   - All Mongoose models are defined with proper types
   - Indexes are created for frequently queried fields
   - Validation rules prevent invalid data
   - Relationships between models work correctly

2. **Repository Validation**
   - CRUD operations work for all models
   - Search and filtering return correct results
   - Repository methods handle errors gracefully
   - Repositories can be mocked for testing

3. **Testing Validation**
   - Unit tests pass for all models (>90% coverage)
   - Integration tests pass for repositories
   - Tests use isolated test database
   - Tests clean up data after execution

4. **Documentation**
   - README explains database setup
   - Schema documentation is complete
   - Repository methods are documented
   - Example usage provided for each model

5. **Code Quality**
   - ESLint passes with no errors
   - Code follows consistent style
   - No hardcoded credentials
   - Error messages are helpful

## Deliverables

- [ ] Mongoose User model with validation
- [ ] Mongoose Task model with validation
- [ ] Database connection manager
- [ ] UserRepository with CRUD operations
- [ ] TaskRepository with CRUD and search
- [ ] Validation schemas
- [ ] Unit tests for models (>90% coverage)
- [ ] Integration tests for repositories
- [ ] Database setup documentation
- [ ] Example seed data script
- [ ] Environment configuration examples

## Next Steps

Once this module is validated:
1. Tag release as `v0.1.0-data`
2. Document any lessons learned
3. Begin Module 2 (Authentication)
4. Use repositories from this module in auth controllers
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
# Module 3: Task API

**Duration**: 5 days
**Dependencies**: Module 1 (Data Layer), Module 2 (Authentication)
**Validation Agent**: python-task-validator

## Overview

Build the REST API for task management operations. This module provides endpoints for creating, reading, updating, and deleting tasks, with filtering, search, and statistics.

## Express Application Setup

Location: `src/app.js`

Configure Express application:

```javascript
const express = require('express');
const cors = require('cors');
const helmet = require('helmet');
const morgan = require('morgan');

const app = express();

// Security middleware
app.use(helmet());
app.use(cors({
  origin: process.env.FRONTEND_URL || 'http://localhost:5173',
  credentials: true
}));

// Logging
app.use(morgan('combined'));

// Body parsing
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Routes
app.use('/api/auth', authRoutes);
app.use('/api/tasks', taskRoutes);

// Health check
app.get('/health', (req, res) => {
  res.json({ status: 'ok', timestamp: new Date() });
});

// 404 handler
app.use((req, res) => {
  res.status(404).json({ error: 'Not found' });
});

// Error handler
app.use(errorHandler);

module.exports = app;
```

## Task Controller

Location: `src/controllers/TaskController.js`

Implement task operations:

```javascript
class TaskController {
  /**
   * Create new task
   * POST /api/tasks
   */
  async create(req, res) {
    // 1. Validate input
    // 2. Extract task data from request body
    // 3. Add userId from authenticated user
    // 4. Create task via TaskRepository
    // 5. Return created task with 201 status
  }

  /**
   * Get all tasks for user with filtering
   * GET /api/tasks?status=todo&priority=high&sort=dueDate
   */
  async list(req, res) {
    // 1. Extract query parameters
    // 2. Build filter object
    // 3. Apply sorting
    // 4. Paginate results
    // 5. Return tasks with pagination metadata
  }

  /**
   * Get single task by ID
   * GET /api/tasks/:id
   */
  async getById(req, res) {
    // 1. Extract task ID from params
    // 2. Find task in database
    // 3. Verify task belongs to authenticated user
    // 4. Return task or 404
  }

  /**
   * Update task
   * PUT /api/tasks/:id
   */
  async update(req, res) {
    // 1. Extract task ID and updates
    // 2. Find task and verify ownership
    // 3. Validate update data
    // 4. Update task in database
    // 5. Return updated task
  }

  /**
   * Delete task
   * DELETE /api/tasks/:id
   */
  async delete(req, res) {
    // 1. Extract task ID
    // 2. Find task and verify ownership
    // 3. Delete from database
    // 4. Return 204 No Content
  }

  /**
   * Search tasks
   * GET /api/tasks/search?q=meeting
   */
  async search(req, res) {
    // 1. Extract search query
    // 2. Search title and description
    // 3. Apply user filter
    // 4. Return matching tasks
  }

  /**
   * Get task statistics
   * GET /api/tasks/stats
   */
  async getStats(req, res) {
    // 1. Get authenticated user
    // 2. Calculate task counts by status
    // 3. Calculate task counts by priority
    // 4. Get overdue count
    // 5. Return statistics object
  }

  /**
   * Bulk update tasks
   * PATCH /api/tasks/bulk
   */
  async bulkUpdate(req, res) {
    // 1. Extract task IDs and updates
    // 2. Verify all tasks belong to user
    // 3. Update all tasks
    // 4. Return updated count
  }

  /**
   * Mark task as complete
   * POST /api/tasks/:id/complete
   */
  async markComplete(req, res) {
    // 1. Find task and verify ownership
    // 2. Set status to 'done'
    // 3. Set completedAt timestamp
    // 4. Save and return task
  }
}
```

## Task Routes

Location: `src/routes/tasks.js`

Define task API routes:

```javascript
const express = require('express');
const router = express.Router();
const TaskController = require('../controllers/TaskController');
const { authenticate } = require('../middleware/auth');
const { validateTask, validateTaskUpdate } = require('../middleware/validation');

// All task routes require authentication
router.use(authenticate);

// Main CRUD routes
router.post('/', validateTask, TaskController.create);
router.get('/', TaskController.list);
router.get('/stats', TaskController.getStats);
router.get('/search', TaskController.search);
router.get('/:id', TaskController.getById);
router.put('/:id', validateTaskUpdate, TaskController.update);
router.delete('/:id', TaskController.delete);

// Bulk operations
router.patch('/bulk', TaskController.bulkUpdate);

// Special actions
router.post('/:id/complete', TaskController.markComplete);

module.exports = router;
```

## Query Parameters & Filtering

### List Endpoint Query Params

- `status` - Filter by status (todo, in_progress, done)
- `priority` - Filter by priority (low, medium, high)
- `tags` - Filter by tags (comma-separated)
- `overdue` - Filter overdue tasks (true/false)
- `search` - Search in title and description
- `sort` - Sort field (createdAt, dueDate, priority, title)
- `order` - Sort order (asc, desc)
- `page` - Page number (default: 1)
- `limit` - Items per page (default: 20, max: 100)

### Example Queries

```
GET /api/tasks?status=todo&priority=high
GET /api/tasks?overdue=true&sort=dueDate&order=asc
GET /api/tasks?tags=work,urgent&page=2&limit=10
GET /api/tasks?search=meeting&sort=createdAt&order=desc
```

## Response Formats

### Success Response

```json
{
  "success": true,
  "data": { /* task object */ },
  "message": "Task created successfully"
}
```

### List Response

```json
{
  "success": true,
  "data": [
    { /* task object */ }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 45,
    "totalPages": 3,
    "hasNext": true,
    "hasPrev": false
  }
}
```

### Error Response

```json
{
  "success": false,
  "error": "Task not found",
  "statusCode": 404
}
```

## Validation Middleware

Location: `src/middleware/validation.js`

Add task validation:

```javascript
function validateTask(req, res, next) {
  const { title, description, status, priority, dueDate, tags } = req.body;

  const errors = [];

  // Title is required
  if (!title || title.trim().length === 0) {
    errors.push('Title is required');
  }
  if (title && title.length > 200) {
    errors.push('Title must be 200 characters or less');
  }

  // Description is optional but limited
  if (description && description.length > 2000) {
    errors.push('Description must be 2000 characters or less');
  }

  // Status must be valid enum value
  if (status && !['todo', 'in_progress', 'done'].includes(status)) {
    errors.push('Invalid status value');
  }

  // Priority must be valid enum value
  if (priority && !['low', 'medium', 'high'].includes(priority)) {
    errors.push('Invalid priority value');
  }

  // Due date must be valid date
  if (dueDate && isNaN(Date.parse(dueDate))) {
    errors.push('Invalid due date');
  }

  // Tags must be array
  if (tags && !Array.isArray(tags)) {
    errors.push('Tags must be an array');
  }

  if (errors.length > 0) {
    return res.status(400).json({ success: false, errors });
  }

  next();
}

function validateTaskUpdate(req, res, next) {
  // Similar to validateTask but all fields optional
  // At least one field must be provided
}
```

## Authorization Checks

Location: `src/middleware/taskAuth.js`

Ensure users can only access their own tasks:

```javascript
async function ensureTaskOwnership(req, res, next) {
  const taskId = req.params.id;
  const userId = req.user._id;

  const task = await TaskRepository.findById(taskId);

  if (!task) {
    return res.status(404).json({
      success: false,
      error: 'Task not found'
    });
  }

  if (task.userId.toString() !== userId.toString()) {
    return res.status(403).json({
      success: false,
      error: 'You do not have permission to access this task'
    });
  }

  req.task = task;
  next();
}
```

Use in routes:
```javascript
router.get('/:id', ensureTaskOwnership, TaskController.getById);
router.put('/:id', ensureTaskOwnership, validateTaskUpdate, TaskController.update);
router.delete('/:id', ensureTaskOwnership, TaskController.delete);
```

## Pagination Helper

Location: `src/utils/pagination.js`

Create pagination utility:

```javascript
function paginate(page = 1, limit = 20) {
  const maxLimit = 100;
  const sanitizedLimit = Math.min(Math.max(limit, 1), maxLimit);
  const sanitizedPage = Math.max(page, 1);
  const skip = (sanitizedPage - 1) * sanitizedLimit;

  return {
    skip,
    limit: sanitizedLimit,
    page: sanitizedPage
  };
}

function paginationMetadata(total, page, limit) {
  const totalPages = Math.ceil(total / limit);

  return {
    page,
    limit,
    total,
    totalPages,
    hasNext: page < totalPages,
    hasPrev: page > 1
  };
}
```

## Testing

Location: `tests/api/`

### Integration Tests

Test task creation:
- Valid task creation returns 201
- Created task has correct data
- Missing title returns 400
- Unauthenticated request returns 401

Test task listing:
- Returns user's tasks only
- Filters work correctly
- Pagination works correctly
- Sort order is correct

Test task retrieval:
- Valid ID returns task
- Invalid ID returns 404
- Other user's task returns 403

Test task update:
- Valid update modifies task
- Invalid data returns 400
- Other user's task returns 403
- Partial update works

Test task deletion:
- Valid delete removes task
- Deleted task cannot be retrieved
- Other user's task returns 403

Test search:
- Finds tasks by title
- Finds tasks by description
- Returns empty array if no matches
- Search is case-insensitive

Test statistics:
- Returns correct counts by status
- Returns correct counts by priority
- Includes overdue count

### Edge Cases

- Empty result sets
- Very long task titles/descriptions
- Special characters in search
- Invalid ObjectId format
- Concurrent updates to same task

## API Documentation

Location: `docs/api.md`

Document all endpoints with:
- HTTP method and path
- Authentication requirements
- Request parameters
- Request body schema
- Response schema
- Error responses
- Example requests and responses

Consider using Swagger/OpenAPI for interactive documentation.

## Module Validation Criteria

This module is complete when:

1. **Functionality Validation**
   - All CRUD operations work correctly
   - Filtering and sorting return expected results
   - Search finds relevant tasks
   - Pagination works with large datasets
   - Statistics calculations are accurate
   - Use `python-task-validator` to verify controller code

2. **Security Validation**
   - Users can only access their own tasks
   - Authentication is required for all endpoints
   - Input validation prevents injection attacks
   - Error messages don't leak sensitive info

3. **Testing Validation**
   - Integration tests pass (>85% coverage)
   - Edge cases are handled correctly
   - Tests use isolated test database
   - Performance is acceptable (< 100ms response)

4. **Code Quality**
   - ESLint passes with no errors
   - Code is well organized and documented
   - Error handling is consistent
   - Validation agent confirms quality

## Deliverables

- [ ] Express application setup
- [ ] TaskController with all operations
- [ ] Task routes configuration
- [ ] Input validation middleware
- [ ] Authorization checks for task ownership
- [ ] Pagination helper utilities
- [ ] Integration tests for all endpoints
- [ ] API documentation with examples
- [ ] Postman collection for manual testing
- [ ] Performance benchmarks

## Next Steps

Once this module is validated:
1. Tag release as `v0.3.0-api`
2. Test all endpoints with Postman collection
3. Begin Module 4 (User Interface)
4. Frontend will consume these API endpoints
# Module 4: User Interface

**Duration**: 10 days
**Dependencies**: Module 1, 2, 3 (Complete backend)

## Overview

Build the React frontend application with Material-UI components. This module creates a responsive, intuitive interface for task management with real-time feedback and smooth interactions.

## Project Setup

### Initialize React Project

```bash
npm create vite@latest tasktracker-ui -- --template react
cd tasktracker-ui
npm install
```

### Install Dependencies

```bash
# UI Framework
npm install @mui/material @mui/icons-material @emotion/react @emotion/styled

# State & Data Fetching
npm install @tanstack/react-query axios zustand

# Routing
npm install react-router-dom

# Forms
npm install react-hook-form

# Date handling
npm install date-fns

# Dev dependencies
npm install --save-dev @testing-library/react @testing-library/jest-dom vitest
```

### Project Structure

```
src/
├── components/
│   ├── auth/
│   │   ├── LoginForm.jsx
│   │   ├── RegisterForm.jsx
│   │   └── PrivateRoute.jsx
│   ├── tasks/
│   │   ├── TaskList.jsx
│   │   ├── TaskCard.jsx
│   │   ├── TaskForm.jsx
│   │   ├── TaskFilters.jsx
│   │   └── TaskStats.jsx
│   ├── layout/
│   │   ├── AppBar.jsx
│   │   ├── Sidebar.jsx
│   │   └── Layout.jsx
│   └── common/
│       ├── Loading.jsx
│       ├── ErrorMessage.jsx
│       └── ConfirmDialog.jsx
├── pages/
│   ├── Login.jsx
│   ├── Register.jsx
│   ├── Dashboard.jsx
│   └── NotFound.jsx
├── services/
│   ├── api.js
│   ├── auth.js
│   └── tasks.js
├── hooks/
│   ├── useAuth.js
│   └── useTasks.js
├── store/
│   └── authStore.js
├── utils/
│   └── formatters.js
├── App.jsx
└── main.jsx
```

## API Service Layer

Location: `src/services/api.js`

Create Axios instance with interceptors:

```javascript
import axios from 'axios';

const api = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:3000/api',
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json'
  }
});

// Request interceptor - add auth token
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Response interceptor - handle errors
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      // Token expired or invalid - logout
      localStorage.removeItem('authToken');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default api;
```

## Authentication Service

Location: `src/services/auth.js`

```javascript
import api from './api';

export const authService = {
  async register(email, username, password) {
    const response = await api.post('/auth/register', {
      email,
      username,
      password
    });
    return response.data;
  },

  async login(email, password) {
    const response = await api.post('/auth/login', {
      email,
      password
    });
    // Store token
    if (response.data.token) {
      localStorage.setItem('authToken', response.data.token);
    }
    return response.data;
  },

  async getCurrentUser() {
    const response = await api.get('/auth/me');
    return response.data;
  },

  logout() {
    localStorage.removeItem('authToken');
  },

  isAuthenticated() {
    return !!localStorage.getItem('authToken');
  }
};
```

## Task Service

Location: `src/services/tasks.js`

```javascript
import api from './api';

export const taskService = {
  async getTasks(filters = {}) {
    const params = new URLSearchParams();
    Object.entries(filters).forEach(([key, value]) => {
      if (value !== null && value !== undefined && value !== '') {
        params.append(key, value);
      }
    });

    const response = await api.get(`/tasks?${params}`);
    return response.data;
  },

  async getTask(id) {
    const response = await api.get(`/tasks/${id}`);
    return response.data;
  },

  async createTask(taskData) {
    const response = await api.post('/tasks', taskData);
    return response.data;
  },

  async updateTask(id, updates) {
    const response = await api.put(`/tasks/${id}`, updates);
    return response.data;
  },

  async deleteTask(id) {
    await api.delete(`/tasks/${id}`);
  },

  async markComplete(id) {
    const response = await api.post(`/tasks/${id}/complete`);
    return response.data;
  },

  async getStats() {
    const response = await api.get('/tasks/stats');
    return response.data;
  },

  async searchTasks(query) {
    const response = await api.get(`/tasks/search?q=${encodeURIComponent(query)}`);
    return response.data;
  }
};
```

## Authentication Pages

### Login Page

Location: `src/pages/Login.jsx`

```jsx
import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import {
  Container, Paper, TextField, Button,
  Typography, Alert, Box
} from '@mui/material';
import { authService } from '../services/auth';

export default function Login() {
  const navigate = useNavigate();
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const { register, handleSubmit, formState: { errors } } = useForm();

  const onSubmit = async (data) => {
    setLoading(true);
    setError('');
    try {
      await authService.login(data.email, data.password);
      navigate('/dashboard');
    } catch (err) {
      setError(err.response?.data?.error || 'Login failed');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Container maxWidth="sm">
      <Box sx={{ mt: 8 }}>
        <Paper elevation={3} sx={{ p: 4 }}>
          <Typography variant="h4" gutterBottom>
            Login to TaskTracker
          </Typography>

          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}

          <form onSubmit={handleSubmit(onSubmit)}>
            <TextField
              fullWidth
              label="Email"
              type="email"
              margin="normal"
              {...register('email', { required: 'Email is required' })}
              error={!!errors.email}
              helperText={errors.email?.message}
            />

            <TextField
              fullWidth
              label="Password"
              type="password"
              margin="normal"
              {...register('password', { required: 'Password is required' })}
              error={!!errors.password}
              helperText={errors.password?.message}
            />

            <Button
              fullWidth
              variant="contained"
              type="submit"
              disabled={loading}
              sx={{ mt: 3 }}
            >
              {loading ? 'Logging in...' : 'Login'}
            </Button>
          </form>

          <Typography variant="body2" sx={{ mt: 2, textAlign: 'center' }}>
            Don't have an account? <Link to="/register">Register</Link>
          </Typography>
        </Paper>
      </Box>
    </Container>
  );
}
```

### Register Page

Similar structure to Login but with additional fields (username, password confirmation).

## Dashboard Layout

Location: `src/components/layout/Layout.jsx`

```jsx
import { Box, AppBar, Toolbar, Typography, IconButton, Drawer } from '@mui/material';
import { Menu, Logout } from '@mui/icons-material';
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { authService } from '../../services/auth';

export default function Layout({ children }) {
  const [drawerOpen, setDrawerOpen] = useState(false);
  const navigate = useNavigate();

  const handleLogout = () => {
    authService.logout();
    navigate('/login');
  };

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar position="fixed">
        <Toolbar>
          <IconButton
            edge="start"
            color="inherit"
            onClick={() => setDrawerOpen(true)}
            sx={{ mr: 2 }}
          >
            <Menu />
          </IconButton>
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            TaskTracker
          </Typography>
          <IconButton color="inherit" onClick={handleLogout}>
            <Logout />
          </IconButton>
        </Toolbar>
      </AppBar>

      <Drawer
        anchor="left"
        open={drawerOpen}
        onClose={() => setDrawerOpen(false)}
      >
        {/* Sidebar content - filters, stats, etc. */}
      </Drawer>

      <Box component="main" sx={{ flexGrow: 1, p: 3, mt: 8 }}>
        {children}
      </Box>
    </Box>
  );
}
```

## Task List Component

Location: `src/components/tasks/TaskList.jsx`

```jsx
import { useQuery } from '@tanstack/react-query';
import { Grid, Box, Typography } from '@mui/material';
import { taskService } from '../../services/tasks';
import TaskCard from './TaskCard';
import Loading from '../common/Loading';
import ErrorMessage from '../common/ErrorMessage';

export default function TaskList({ filters }) {
  const { data, isLoading, error, refetch } = useQuery({
    queryKey: ['tasks', filters],
    queryFn: () => taskService.getTasks(filters)
  });

  if (isLoading) return <Loading />;
  if (error) return <ErrorMessage error={error} />;

  const tasks = data?.data || [];

  if (tasks.length === 0) {
    return (
      <Box sx={{ textAlign: 'center', py: 8 }}>
        <Typography variant="h6" color="text.secondary">
          No tasks found
        </Typography>
      </Box>
    );
  }

  return (
    <Grid container spacing={2}>
      {tasks.map(task => (
        <Grid item xs={12} sm={6} md={4} key={task._id}>
          <TaskCard task={task} onUpdate={refetch} />
        </Grid>
      ))}
    </Grid>
  );
}
```

## Task Card Component

Location: `src/components/tasks/TaskCard.jsx`

```jsx
import {
  Card, CardContent, CardActions,
  Typography, Chip, IconButton, Box
} from '@mui/material';
import { Edit, Delete, CheckCircle } from '@mui/icons-material';
import { format } from 'date-fns';

const priorityColors = {
  low: 'success',
  medium: 'warning',
  high: 'error'
};

const statusLabels = {
  todo: 'To Do',
  in_progress: 'In Progress',
  done: 'Done'
};

export default function TaskCard({ task, onUpdate }) {
  const handleComplete = async () => {
    await taskService.markComplete(task._id);
    onUpdate();
  };

  const handleEdit = () => {
    // Open edit dialog
  };

  const handleDelete = async () => {
    if (confirm('Delete this task?')) {
      await taskService.deleteTask(task._id);
      onUpdate();
    }
  };

  return (
    <Card>
      <CardContent>
        <Typography variant="h6" gutterBottom>
          {task.title}
        </Typography>

        {task.description && (
          <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
            {task.description}
          </Typography>
        )}

        <Box sx={{ display: 'flex', gap: 1, mb: 1 }}>
          <Chip
            label={statusLabels[task.status]}
            size="small"
            color={task.status === 'done' ? 'success' : 'default'}
          />
          <Chip
            label={task.priority}
            size="small"
            color={priorityColors[task.priority]}
          />
        </Box>

        {task.dueDate && (
          <Typography variant="caption" color="text.secondary">
            Due: {format(new Date(task.dueDate), 'MMM d, yyyy')}
          </Typography>
        )}
      </CardContent>

      <CardActions>
        {task.status !== 'done' && (
          <IconButton size="small" onClick={handleComplete}>
            <CheckCircle />
          </IconButton>
        )}
        <IconButton size="small" onClick={handleEdit}>
          <Edit />
        </IconButton>
        <IconButton size="small" onClick={handleDelete}>
          <Delete />
        </IconButton>
      </CardActions>
    </Card>
  );
}
```

## Task Form Component

Location: `src/components/tasks/TaskForm.jsx`

Create/edit task modal with:
- Title input (required)
- Description textarea
- Status select
- Priority select
- Due date picker
- Tags input
- Save/cancel buttons

## Task Filters Component

Location: `src/components/tasks/TaskFilters.jsx`

Filter panel with:
- Status checkboxes
- Priority checkboxes
- Search input
- Sort dropdown
- Clear filters button

## React Query Setup

Location: `src/App.jsx`

```jsx
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider, createTheme, CssBaseline } from '@mui/material';

import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import PrivateRoute from './components/auth/PrivateRoute';

const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1
    }
  }
});

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2'
    }
  }
});

export default function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <BrowserRouter>
          <Routes>
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            <Route
              path="/dashboard"
              element={
                <PrivateRoute>
                  <Dashboard />
                </PrivateRoute>
              }
            />
            <Route path="/" element={<Navigate to="/dashboard" />} />
          </Routes>
        </BrowserRouter>
      </ThemeProvider>
    </QueryClientProvider>
  );
}
```

## Responsive Design

### Breakpoints

- **Mobile** (xs): < 600px
  - Single column layout
  - Full-width cards
  - Bottom drawer for filters
  - Simplified navigation

- **Tablet** (sm, md): 600px - 1200px
  - Two column grid
  - Collapsible sidebar
  - Medium-sized cards

- **Desktop** (lg, xl): > 1200px
  - Three column grid
  - Persistent sidebar
  - Large cards with more details

## Loading States

Show skeleton screens while data loads:
- Skeleton cards during task loading
- Skeleton sidebar during stats loading
- Loading spinner for actions (complete, delete)

## Error Handling

Display user-friendly errors:
- Network errors: "Connection lost. Retrying..."
- 404: "Task not found"
- 403: "Permission denied"
- 500: "Server error. Please try again"

## Offline Support

Basic offline handling:
- Detect offline state
- Show offline banner
- Queue mutations for when back online
- Use React Query caching

## Testing

Location: `tests/`

### Component Tests

- Login form validates inputs
- Task card displays correct data
- Task filters update query
- Create task form submits correctly

### Integration Tests

- Login flow end-to-end
- Create task and see in list
- Edit task updates UI
- Delete task removes from list
- Filters update displayed tasks

## Module Validation Criteria

This module is complete when:

1. **Functionality Validation**
   - Users can log in and register
   - Dashboard displays user's tasks
   - Tasks can be created via form
   - Tasks can be edited and deleted
   - Filters update task display
   - Search finds tasks

2. **UX Validation**
   - Responsive on mobile, tablet, desktop
   - Loading states during async operations
   - Error messages are helpful
   - Smooth transitions and animations
   - Keyboard navigation works

3. **Integration Validation**
   - Frontend successfully calls all API endpoints
   - Authentication tokens work correctly
   - Error responses are handled
   - Pagination works with large datasets

4. **Code Quality**
   - ESLint passes with no errors
   - Components are properly organized
   - Code is well documented
   - Tests achieve >70% coverage

## Deliverables

- [ ] React application with Vite
- [ ] Material-UI theme and components
- [ ] Authentication pages (login, register)
- [ ] Dashboard with task list
- [ ] Task CRUD operations
- [ ] Filters and search
- [ ] Responsive layout
- [ ] API service layer with error handling
- [ ] React Query integration
- [ ] Component tests
- [ ] User guide documentation

## Next Steps

Once this module is validated:
1. Tag release as `v1.0.0`
2. Deploy to Vercel
3. Gather user feedback
4. Plan next iteration features
