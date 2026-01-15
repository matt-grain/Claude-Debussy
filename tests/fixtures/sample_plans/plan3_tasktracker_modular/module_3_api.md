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
