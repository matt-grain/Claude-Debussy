# Sprint 1: Foundation - Core Backend

**Goal**: Establish the backend foundation with Django REST Framework, user authentication, and core data models.

## 1. Project Setup

Initialize the Django project with all necessary dependencies and configuration.

### 1.1 Django Project Initialization
- Create new Django project `tasktracker_pro`
- Install dependencies: djangorestframework, djangorestframework-simplejwt, django-cors-headers, psycopg2, redis, celery
- Set up project structure with apps: `users`, `tasks`, `teams`
- Configure settings for development and production environments

### 1.2 Database Configuration
- Set up PostgreSQL database
- Configure database connection with environment variables
- Create Redis connection for caching
- Set up database migration tracking

### 1.3 Docker Setup
- Create Dockerfile for Django application
- Create docker-compose.yml with services: app, postgres, redis
- Add environment variable files
- Document local development setup

**Validation**:
- Project runs successfully with `docker-compose up`
- Database migrations apply cleanly
- Python code follows Django best practices (verified by `python-task-validator`)

## 2. User Management

Implement user authentication and profile management.

### 2.1 Custom User Model
- Extend Django's AbstractUser
- Add fields: `avatar_url`, `bio`, `timezone`, `notification_preferences`
- Create user manager for custom user creation
- Add email verification fields

### 2.2 Authentication System
- Configure JWT authentication with djangorestframework-simplejwt
- Set token lifetime (access: 15min, refresh: 7 days)
- Create registration endpoint with email validation
- Create login endpoint returning JWT tokens
- Create token refresh endpoint
- Create password reset flow (email-based)

### 2.3 User Profile API
- GET /api/users/me - Retrieve current user profile
- PUT /api/users/me - Update user profile
- POST /api/users/avatar - Upload profile picture
- GET /api/users/:id - Get public profile (for team members)

**Validation**:
- All authentication flows work correctly
- JWT tokens expire and refresh properly
- Passwords are hashed securely
- Email validation prevents invalid addresses
- Use `python-task-validator` to verify authentication code

## 3. Task Models

Define the core data models for tasks and related entities.

### 3.1 Task Model

```python
class Task:
    id: UUID
    title: str (max 300 chars)
    description: TextField (optional)
    status: Enum [backlog, todo, in_progress, review, done]
    priority: Enum [none, low, medium, high, urgent]

    # Relationships
    created_by: ForeignKey(User)
    assigned_to: ForeignKey(User, null=True)
    team: ForeignKey(Team, null=True)
    parent_task: ForeignKey(Task, null=True)  # For subtasks

    # Metadata
    due_date: DateTime (optional)
    estimated_hours: DecimalField (optional)
    actual_hours: DecimalField (optional)
    tags: ManyToMany(Tag)

    # Tracking
    created_at: DateTime
    updated_at: DateTime
    completed_at: DateTime (optional)

    # Position for drag-and-drop ordering
    position: IntegerField
```

### 3.2 Team Model

```python
class Team:
    id: UUID
    name: str (max 100 chars)
    description: TextField
    owner: ForeignKey(User)
    members: ManyToMany(User, through=TeamMember)
    created_at: DateTime
    settings: JSONField  # Team preferences
```

### 3.3 TeamMember Model

```python
class TeamMember:
    team: ForeignKey(Team)
    user: ForeignKey(User)
    role: Enum [owner, admin, member, viewer]
    joined_at: DateTime
    invited_by: ForeignKey(User)
```

### 3.4 Tag Model

```python
class Tag:
    id: UUID
    name: str (max 50 chars)
    color: str (hex color)
    team: ForeignKey(Team, null=True)  # null for personal tags
    created_by: ForeignKey(User)
```

### 3.5 Comment Model

```python
class Comment:
    id: UUID
    task: ForeignKey(Task)
    author: ForeignKey(User)
    content: TextField
    created_at: DateTime
    updated_at: DateTime
    edited: BooleanField
```

**Validation**:
- All models have proper field types and constraints
- Foreign keys cascade correctly on delete
- Indexes are added for frequently queried fields
- Model methods (str, repr) are implemented
- Use `python-task-validator` to check model quality

## 4. Basic API Endpoints

Implement REST endpoints for task CRUD operations.

### 4.1 Task Endpoints

- POST /api/tasks - Create a new task
- GET /api/tasks - List tasks with filtering and pagination
  - Query params: `status`, `priority`, `assigned_to`, `team`, `search`, `page`, `page_size`
- GET /api/tasks/:id - Get task details with comments
- PUT /api/tasks/:id - Update task
- PATCH /api/tasks/:id - Partial update (e.g., status change)
- DELETE /api/tasks/:id - Delete task
- POST /api/tasks/:id/comments - Add comment to task

### 4.2 Tag Endpoints

- GET /api/tags - List all tags for user
- POST /api/tags - Create new tag
- PUT /api/tags/:id - Update tag
- DELETE /api/tags/:id - Delete tag

### 4.3 Serializers

Create DRF serializers for:
- UserSerializer (public profile)
- TaskSerializer (detailed)
- TaskListSerializer (lightweight for lists)
- CommentSerializer
- TagSerializer
- TeamSerializer

**Validation**:
- All endpoints return appropriate HTTP status codes
- Pagination works correctly
- Filtering and search return expected results
- Users can only access their own data or team data
- Validation errors provide clear messages
- Use `python-task-validator` to verify API implementation

## 5. Permissions & Authorization

Implement row-level permissions for secure access control.

### 5.1 Permission Classes

Create custom DRF permissions:
- `IsOwnerOrReadOnly` - Only owner can modify
- `IsTeamMember` - Must be team member to access
- `IsTeamAdminOrOwner` - Admin/owner actions only
- `IsAssignedOrCreator` - Task assigned to user or created by user

### 5.2 Access Control Rules

- Users can only see their own tasks and team tasks
- Only task creator or assignee can update status
- Only team admins can delete tasks
- Comments can be edited only by author
- Team owners can remove members

**Validation**:
- Permission tests verify access control
- Unauthorized requests return 403 Forbidden
- Token-less requests return 401 Unauthorized
- Use `python-task-validator` to check permission code

## 6. Testing

Comprehensive test suite for backend code.

### 6.1 Test Coverage

- Unit tests for models (validation, methods)
- API endpoint tests (CRUD operations)
- Authentication flow tests
- Permission tests
- Edge case tests (empty results, invalid data)

### 6.2 Test Data

- Use factory_boy for test data generation
- Create fixtures for common scenarios
- Set up test database that resets between tests

**Validation**:
- Test coverage > 85%
- All tests pass with no warnings
- Tests run in < 30 seconds
- Use `python-task-validator` to verify test quality

## Sprint 1 Completion Criteria

Sprint 1 is complete when:

1. Django application runs in Docker containers
2. User registration and JWT authentication work end-to-end
3. All task CRUD operations function correctly
4. Permission system prevents unauthorized access
5. Test suite passes with >85% coverage
6. Code quality checks pass (`python-task-validator` reports no issues)
7. API documentation is generated (via drf-spectacular)
8. Database migrations are clean and reversible

## Deliverables

- Django project with configured settings
- Docker configuration for local development
- User authentication system with JWT
- Task, Team, Tag, and Comment models
- REST API with serializers and viewsets
- Permission classes for access control
- Test suite with fixtures
- API documentation
- README with setup instructions
