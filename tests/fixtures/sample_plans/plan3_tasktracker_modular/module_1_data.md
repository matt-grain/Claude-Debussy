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
