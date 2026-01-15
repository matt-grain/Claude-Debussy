# Frontend Dashboard Phase

## Overview

Build a modern, responsive React application with TypeScript for managing tasks. The frontend will communicate with the Flask API and provide an intuitive user experience.

## Technology Stack

- React 18 with TypeScript
- React Router for navigation
- Axios for API requests
- Context API for state management
- Tailwind CSS for styling
- React Hook Form for form handling
- date-fns for date manipulation

## Application Structure

```
src/
├── components/
│   ├── auth/
│   │   ├── LoginForm.tsx
│   │   └── RegisterForm.tsx
│   ├── tasks/
│   │   ├── TaskList.tsx
│   │   ├── TaskItem.tsx
│   │   ├── TaskForm.tsx
│   │   └── TaskFilters.tsx
│   ├── categories/
│   │   ├── CategoryList.tsx
│   │   └── CategoryForm.tsx
│   └── common/
│       ├── Header.tsx
│       ├── Sidebar.tsx
│       └── Modal.tsx
├── contexts/
│   ├── AuthContext.tsx
│   └── TaskContext.tsx
├── services/
│   ├── api.ts
│   ├── auth.ts
│   └── tasks.ts
├── hooks/
│   ├── useAuth.ts
│   └── useTasks.ts
├── types/
│   └── index.ts
├── utils/
│   └── helpers.ts
└── pages/
    ├── Login.tsx
    ├── Register.tsx
    ├── Dashboard.tsx
    └── NotFound.tsx
```

## Core Features

### Authentication Flow

**Login Page**
- Email and password input fields
- Form validation with error messages
- "Remember me" checkbox
- Link to registration page
- Loading state during authentication
- Redirect to dashboard on success

**Registration Page**
- Email, username, and password fields
- Password strength indicator
- Confirm password field
- Form validation
- Link back to login page

**Auth Context**
- Store JWT token in localStorage
- Provide login, logout, and register functions
- Track authentication state
- Automatically attach token to API requests
- Handle token expiration

### Dashboard Page

The main application interface where users manage their tasks.

**Layout:**
- Top navigation bar with user info and logout button
- Left sidebar with category filters
- Main content area with task list
- Floating action button to create new task

**Task List Component**
- Display tasks in card format
- Show task title, description, priority, and due date
- Color-coded priority indicators (red: high, yellow: medium, green: low)
- Status badges (pending, in progress, completed)
- Quick actions: edit, delete, change status
- Empty state when no tasks exist

**Task Filters**
- Filter by status (all, pending, in progress, completed)
- Filter by category
- Sort by due date, priority, or creation date
- Search by title or description
- Clear all filters button

**Task Form (Modal)**
- Title input (required)
- Description textarea
- Priority dropdown
- Status dropdown
- Due date picker
- Category selector
- Save and cancel buttons
- Form validation with error messages

### Category Management

**Category Sidebar**
- List all user categories
- Show task count per category
- Color indicator for each category
- Create new category button
- Edit/delete category options

**Category Form**
- Name input
- Color picker
- Validation for unique names

## State Management

### Auth Context

```typescript
interface AuthContextType {
  user: User | null;
  token: string | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, username: string, password: string) => Promise<void>;
  logout: () => void;
  isAuthenticated: boolean;
}
```

### Task Context

```typescript
interface TaskContextType {
  tasks: Task[];
  categories: Category[];
  loading: boolean;
  error: string | null;
  fetchTasks: (filters?: TaskFilters) => Promise<void>;
  createTask: (task: CreateTaskDto) => Promise<void>;
  updateTask: (id: string, task: UpdateTaskDto) => Promise<void>;
  deleteTask: (id: string) => Promise<void>;
  fetchCategories: () => Promise<void>;
}
```

## API Integration

### API Service Configuration

Create an Axios instance with:
- Base URL from environment variables
- Request interceptor to add JWT token
- Response interceptor to handle errors
- Automatic retry on network failures

### Error Handling

- Display user-friendly error messages
- Handle 401 errors by redirecting to login
- Show toast notifications for success/error
- Log errors to console in development

## Responsive Design

### Mobile (< 768px)
- Hamburger menu for sidebar
- Stacked layout for task cards
- Full-width modals
- Bottom navigation for quick actions

### Tablet (768px - 1024px)
- Collapsible sidebar
- Two-column task grid
- Overlay modals

### Desktop (> 1024px)
- Persistent sidebar
- Three-column task grid
- Larger modals with side-by-side fields

## Validation Criteria

The frontend phase is complete when:

1. **User Experience**
   - All pages are responsive on mobile, tablet, and desktop
   - Loading states are shown during async operations
   - Error messages are clear and actionable
   - Forms provide real-time validation feedback

2. **Functionality**
   - Users can log in and register
   - Authentication state persists across page refreshes
   - Tasks can be created, edited, and deleted
   - Filters and sorting work correctly
   - Categories can be managed

3. **Integration**
   - All API calls successfully communicate with backend
   - JWT tokens are properly sent with requests
   - API errors are handled gracefully
   - Data updates are reflected in the UI immediately

4. **Code Quality**
   - Components are properly typed with TypeScript
   - No console errors or warnings
   - Code follows React best practices
   - Reusable components are properly abstracted

## Deliverables

- Complete React application with all features
- Responsive CSS using Tailwind
- API service layer with error handling
- Auth and Task contexts
- Custom hooks for common operations
- Unit tests for critical components
- README with setup instructions
- Environment variable configuration
