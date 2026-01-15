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
