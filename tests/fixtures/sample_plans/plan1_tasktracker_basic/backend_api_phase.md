# Backend API Development Phase

## Overview

Develop the Flask REST API with authentication, CRUD operations for tasks and categories, and comprehensive error handling.

## API Architecture

### Application Structure

```
app/
├── __init__.py          # Flask app factory
├── config.py            # Configuration settings
├── auth/
│   ├── __init__.py
│   ├── routes.py        # Auth endpoints
│   └── middleware.py    # JWT verification
├── tasks/
│   ├── __init__.py
│   ├── routes.py        # Task CRUD endpoints
│   └── validators.py    # Input validation
├── categories/
│   ├── __init__.py
│   └── routes.py        # Category endpoints
└── utils/
    ├── errors.py        # Error handlers
    └── responses.py     # Response helpers
```

## Authentication Endpoints

### POST /api/auth/register

Register a new user account.

**Request Body:**
```json
{
  "email": "user@example.com",
  "username": "johndoe",
  "password": "SecurePass123!"
}
```

**Response (201):**
```json
{
  "message": "User registered successfully",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "username": "johndoe"
  }
}
```

**Validation:**
- Email must be valid format and unique
- Username must be 3-30 characters and unique
- Password must be at least 8 characters

### POST /api/auth/login

Authenticate user and receive JWT token.

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "SecurePass123!"
}
```

**Response (200):**
```json
{
  "token": "jwt_token_here",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "username": "johndoe"
  }
}
```

### GET /api/auth/me

Get current authenticated user information.

**Headers:** `Authorization: Bearer <token>`

**Response (200):**
```json
{
  "id": "uuid",
  "email": "user@example.com",
  "username": "johndoe",
  "created_at": "2024-01-15T10:30:00Z"
}
```

## Task Endpoints

All task endpoints require authentication via JWT token in Authorization header.

### GET /api/tasks

Retrieve all tasks for the authenticated user.

**Query Parameters:**
- `status` (optional): Filter by status (pending, in_progress, completed)
- `category_id` (optional): Filter by category
- `sort` (optional): Sort field (due_date, created_at, priority)
- `order` (optional): Sort order (asc, desc)

**Response (200):**
```json
{
  "tasks": [
    {
      "id": "uuid",
      "title": "Complete project documentation",
      "description": "Write comprehensive API docs",
      "status": "in_progress",
      "priority": "high",
      "due_date": "2024-01-20T23:59:59Z",
      "category": {
        "id": "uuid",
        "name": "Work",
        "color": "#FF5733"
      },
      "created_at": "2024-01-15T10:00:00Z",
      "updated_at": "2024-01-15T14:30:00Z"
    }
  ],
  "total": 1
}
```

### POST /api/tasks

Create a new task.

**Request Body:**
```json
{
  "title": "New task title",
  "description": "Optional description",
  "status": "pending",
  "priority": "medium",
  "due_date": "2024-01-25T23:59:59Z",
  "category_id": "uuid"
}
```

**Response (201):** Created task object

### GET /api/tasks/:id

Retrieve a specific task by ID.

### PUT /api/tasks/:id

Update an existing task.

### DELETE /api/tasks/:id

Delete a task.

**Response (204):** No content

## Category Endpoints

### GET /api/categories

List all categories for the authenticated user.

### POST /api/categories

Create a new category.

**Request Body:**
```json
{
  "name": "Personal",
  "color": "#4CAF50"
}
```

### PUT /api/categories/:id

Update a category.

### DELETE /api/categories/:id

Delete a category (tasks will have category_id set to null).

## Middleware Implementation

### JWT Authentication

Create middleware to:
- Extract JWT token from Authorization header
- Verify token signature and expiration
- Load user from database
- Attach user to request context

### Error Handling

Implement global error handlers for:
- 400 Bad Request (validation errors)
- 401 Unauthorized (missing or invalid token)
- 403 Forbidden (insufficient permissions)
- 404 Not Found (resource doesn't exist)
- 500 Internal Server Error

## Input Validation

Use Marshmallow schemas to validate:
- Required fields are present
- Field types are correct
- String lengths are within limits
- Enum values are valid
- Dates are properly formatted

## Validation Criteria

The backend API phase is complete when:

1. **Endpoint Functionality**
   - All endpoints return correct status codes
   - Response data matches documented schemas
   - Authentication properly protects routes
   - Use `python-task-validator` to verify route implementations

2. **Security**
   - Passwords are hashed using bcrypt
   - JWT tokens expire after configured time
   - Users can only access their own data
   - SQL injection is prevented via ORM

3. **Error Handling**
   - All errors return consistent JSON format
   - Validation errors provide helpful messages
   - Uncaught exceptions don't expose sensitive info

4. **Testing**
   - Unit tests for all endpoints pass
   - Integration tests verify auth flow
   - Edge cases are handled (empty results, invalid IDs)

## Deliverables

- Flask application with all endpoints implemented
- JWT authentication middleware
- Input validation schemas
- Error handling and logging
- API documentation (Swagger/OpenAPI)
- Test suite with >80% coverage
- Postman collection for manual testing
