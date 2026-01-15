# Database and Models Phase

## Overview

This phase focuses on setting up the PostgreSQL database and creating SQLAlchemy models for the TaskTracker application.

## Database Setup

### PostgreSQL Configuration

1. Install PostgreSQL 14 or higher
2. Create a new database named `tasktracker_db`
3. Configure database connection settings in `.env` file
4. Set up connection pooling for production

### Environment Variables

```
DATABASE_URL=postgresql://user:password@localhost:5432/tasktracker_db
DATABASE_POOL_SIZE=10
DATABASE_MAX_OVERFLOW=20
```

## Model Definitions

### User Model

The User model represents authenticated users in the system.

**Fields:**
- `id` (UUID, primary key)
- `email` (String, unique, required)
- `username` (String, unique, required)
- `password_hash` (String, required)
- `created_at` (DateTime, auto-generated)
- `updated_at` (DateTime, auto-updated)

**Methods:**
- `set_password(password)` - Hash and store password
- `check_password(password)` - Verify password against hash
- `to_dict()` - Serialize user data (excluding password)

### Task Model

The Task model represents individual tasks created by users.

**Fields:**
- `id` (UUID, primary key)
- `title` (String, required, max 200 chars)
- `description` (Text, optional)
- `status` (Enum: pending, in_progress, completed)
- `priority` (Enum: low, medium, high)
- `due_date` (DateTime, optional)
- `user_id` (UUID, foreign key to User)
- `category_id` (UUID, foreign key to Category, nullable)
- `created_at` (DateTime, auto-generated)
- `updated_at` (DateTime, auto-updated)

**Relationships:**
- `user` - Many-to-one relationship with User
- `category` - Many-to-one relationship with Category

### Category Model

The Category model allows users to organize tasks.

**Fields:**
- `id` (UUID, primary key)
- `name` (String, required, max 100 chars)
- `color` (String, hex color code)
- `user_id` (UUID, foreign key to User)
- `created_at` (DateTime, auto-generated)

**Relationships:**
- `user` - Many-to-one relationship with User
- `tasks` - One-to-many relationship with Task

## Database Migrations

### Initial Migration

Create Alembic migration scripts to set up all tables with proper constraints:
- Primary keys and foreign keys
- Unique constraints on email and username
- Indexes on frequently queried fields (user_id, status, due_date)
- Check constraints for valid enum values

### Migration Commands

```bash
# Initialize Alembic
alembic init alembic

# Create migration
alembic revision --autogenerate -m "Initial database schema"

# Apply migration
alembic upgrade head
```

## Validation Criteria

The database phase is complete when:

1. **Schema Validation**
   - All tables are created with correct field types
   - Foreign key constraints are properly established
   - Indexes are created for performance optimization

2. **Model Validation**
   - All models inherit from SQLAlchemy Base
   - Relationships are bidirectional where appropriate
   - Model methods work correctly (password hashing, serialization)
   - Use `python-task-validator` to check model implementations

3. **Migration Validation**
   - Migration scripts run without errors
   - Database can be upgraded and downgraded
   - Sample data can be inserted and queried

4. **Testing**
   - Unit tests for model methods pass
   - Database connection pool works correctly
   - Transaction rollback works properly on errors

## Deliverables

- `models/user.py` - User model definition
- `models/task.py` - Task model definition
- `models/category.py` - Category model definition
- `database.py` - Database connection and session management
- `alembic/versions/` - Migration scripts
- `tests/test_models.py` - Model unit tests
