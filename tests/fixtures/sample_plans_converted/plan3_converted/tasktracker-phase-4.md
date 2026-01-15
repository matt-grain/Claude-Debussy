# TaskTracker MVP Phase 4: User Interface

**Status:** Pending
**Master Plan:** [TaskTracker MVP - Master Plan](tasktracker-MASTER_PLAN.md)
**Depends On:** [Phase 3: Task API Development](tasktracker-phase-3.md)

---

## Process Wrapper (MANDATORY)
- [ ] Read previous notes: `notes/NOTES_tasktracker_phase_3.md`
- [ ] **[IMPLEMENTATION - see Tasks below]**
- [ ] Pre-validation (ALL required):
  ```bash
  npm run lint --fix
  npm run type-check
  npm test -- tests/components/
  npm audit --audit-level=moderate
  # Verify bundle size
  npm run build && ls -lh dist/ | tail -5
  ```
- [ ] Fix loop: repeat pre-validation until clean
- [ ] Write `notes/NOTES_tasktracker_phase_4.md` (REQUIRED)

## Gates (must pass before completion)

**ALL gates are BLOCKING.**

- lint: `npm run lint` returns 0 errors
- type-check: `npm run type-check` returns 0 errors
- tests: `npm test -- tests/components/` - all pass, >70% coverage
- security: `npm audit --audit-level=moderate` - no high severity issues
- bundle: Production build <500KB (gzipped)

---

## Overview

This phase implements the React frontend application with Material-UI components. Builds a responsive, intuitive interface for task management with real-time feedback and smooth interactions. Focuses on component reusability, state management with React Query, and responsive design across mobile, tablet, and desktop breakpoints.

## Dependencies
- Previous phases: Phases 1-3 (backend API must be running and tested)
- External: React 18+, Material-UI, React Query, React Router, Vite, axios

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Frontend state complexity grows unchecked | Medium | Medium | Use React Query for server state, keep local state minimal, component composition rules |
| API integration issues delay completion | Low | Medium | Postman collection from Phase 3, mock API responses in development, test API endpoints first |
| Responsive design breaks on certain breakpoints | Medium | Low | Test on actual devices (mobile simulator, tablet), use Material-UI breakpoints, grid testing |
| Bundle size grows too large | Low | Medium | Code splitting, tree shaking, production build optimization, lazy loading |
| Accessibility not considered | Medium | Medium | Use semantic HTML, aria labels, keyboard navigation, test with screen readers |

---

## Tasks

### 1. Project Setup & Architecture
- [ ] 1.1: Create React project with Vite: `npm create vite@latest tasktracker-ui -- --template react`
- [ ] 1.2: Install dependencies: React, Material-UI, React Query, Router, axios
- [ ] 1.3: Create project directory structure (components/, pages/, services/, hooks/, store/, utils/)
- [ ] 1.4: Setup Vite environment variables (.env.development, .env.production)
- [ ] 1.5: Configure routing with React Router (BrowserRouter, Routes)
- [ ] 1.6: Setup React Query QueryClient with sensible defaults
- [ ] 1.7: Configure Material-UI theme (colors, typography, breakpoints)
- [ ] 1.8: Setup vitest for component testing

### 2. API Service Layer
- [ ] 2.1: Create src/services/api.js with Axios instance
- [ ] 2.2: Add request interceptor to attach JWT token to Authorization header
- [ ] 2.3: Add response interceptor to handle 401 errors (redirect to login)
- [ ] 2.4: Create src/services/auth.js with registration, login, logout, getCurrentUser
- [ ] 2.5: Create src/services/tasks.js with all task CRUD operations
- [ ] 2.6: Implement getTasks with filter support
- [ ] 2.7: Implement getTask, createTask, updateTask, deleteTask
- [ ] 2.8: Implement markComplete, getStats, searchTasks
- [ ] 2.9: Handle API errors gracefully with try-catch
- [ ] 2.10: Write tests for API service layer

### 3. State Management
- [ ] 3.1: Create src/store/authStore.js with Zustand (or Context)
- [ ] 3.2: Implement auth state (user, token, isAuthenticated)
- [ ] 3.3: Implement setUser, setToken, logout actions
- [ ] 3.4: Persist auth state to localStorage
- [ ] 3.5: Create custom hooks: useAuth() for auth state
- [ ] 3.6: Create custom hooks: useTasks() for React Query task operations
- [ ] 3.7: Create custom hooks: useTaskFilters() for filter state and logic
- [ ] 3.8: Write tests for state management and hooks

### 4. Authentication Pages
- [ ] 4.1: Create src/pages/Login.jsx
  - Email and password form inputs
  - Form validation with react-hook-form
  - Submit to auth service
  - Redirect to dashboard on success
  - Display error messages on failure
  - Link to register page
- [ ] 4.2: Create src/pages/Register.jsx
  - Email, username, password, password confirmation inputs
  - Form validation (password match, strength requirements)
  - Submit to auth service
  - Redirect to login on success
  - Display error messages on failure
  - Link to login page
- [ ] 4.3: Create src/components/auth/PrivateRoute.jsx
  - Check if user authenticated
  - Redirect to login if not
  - Render component if authenticated
- [ ] 4.4: Write integration tests for auth pages

### 5. Layout Components
- [ ] 5.1: Create src/components/layout/Layout.jsx (main app layout)
  - AppBar with logo, user menu
  - Sidebar with navigation
  - Main content area
  - Responsive on mobile (drawer instead of sidebar)
- [ ] 5.2: Create src/components/layout/AppBar.jsx
  - TaskTracker title/logo
  - User profile dropdown menu
  - Logout button
  - Mobile menu toggle (hamburger)
- [ ] 5.3: Create src/components/layout/Sidebar.jsx
  - Filter section (status, priority checkboxes)
  - Statistics section (task counts)
  - Quick actions (create task button)
  - Collapse on mobile
- [ ] 5.4: Create src/components/common/Loading.jsx (skeleton screens)
- [ ] 5.5: Create src/components/common/ErrorMessage.jsx (error display)
- [ ] 5.6: Create src/components/common/ConfirmDialog.jsx (delete confirmation)
- [ ] 5.7: Write tests for layout components

### 6. Task List Component
- [ ] 6.1: Create src/components/tasks/TaskList.jsx
  - Fetch tasks via React Query (getTasks with filters)
  - Display in grid (responsive: 1 col mobile, 2 col tablet, 3 col desktop)
  - Show loading skeleton while fetching
  - Show error message if failed
  - Show empty state if no tasks
- [ ] 6.2: Create src/components/tasks/TaskCard.jsx
  - Display task title, description
  - Show status chip (to-do, in-progress, done)
  - Show priority chip (low, medium, high)
  - Show due date (relative format: "Due in 3 days")
  - Show action buttons: complete (if not done), edit, delete
  - Handle complete/delete with optimistic updates
- [ ] 6.3: Create src/components/tasks/TaskFilters.jsx
  - Status checkboxes (to-do, in-progress, done)
  - Priority checkboxes (low, medium, high)
  - Search input field
  - Sort dropdown (created date, due date, priority)
  - Clear filters button
  - Apply filters immediately (query param update)
- [ ] 6.4: Create src/components/tasks/TaskStats.jsx
  - Display counts: total, to-do, in-progress, done
  - Update in real-time as tasks change
  - Use React Query useQuery for stats
- [ ] 6.5: Write integration tests for task components

### 7. Task Form Component
- [ ] 7.1: Create src/components/tasks/TaskForm.jsx (create/edit modal)
  - Title input (required, max 200 chars)
  - Description textarea (optional, max 2000 chars)
  - Status select (to-do, in-progress, done)
  - Priority select (low, medium, high)
  - Due date picker (date-fns, Material-UI DatePicker)
  - Tags input (comma-separated strings, optional)
  - Save button
  - Cancel button
- [ ] 7.2: Use react-hook-form for form state and validation
- [ ] 7.3: Submit to taskService.createTask or updateTask
- [ ] 7.4: Refetch tasks list after successful save
- [ ] 7.5: Show success/error messages (snackbar or toast)
- [ ] 7.6: Handle edit mode (pre-populate form with existing task data)
- [ ] 7.7: Write tests for form validation and submission

### 8. Dashboard Page
- [ ] 8.1: Create src/pages/Dashboard.jsx (main page after login)
  - Render Layout component
  - Render TaskStats in sidebar
  - Render TaskFilters in sidebar
  - Render TaskList in main content area
  - Handle create task button (open modal form)
  - Handle edit task button (open modal form with data)
  - Handle delete task (confirm dialog, delete, refresh list)
  - Responsive: sidebar collapses on mobile, becomes drawer
- [ ] 8.2: Wire up React Query with filters
- [ ] 8.3: Implement task create/edit flow
- [ ] 8.4: Write integration tests for dashboard

### 9. Responsive Design
- [ ] 9.1: Test Mobile (xs breakpoint <600px)
  - Single column task grid
  - Full-width inputs and buttons
  - Drawer for sidebar
  - Touch-friendly button sizes (44px+)
  - Mobile-optimized navigation
- [ ] 9.2: Test Tablet (sm/md breakpoints 600-1200px)
  - Two column task grid
  - Collapsible sidebar
  - Medium-sized cards
  - Visible navigation
- [ ] 9.3: Test Desktop (lg+ breakpoints >1200px)
  - Three column task grid
  - Persistent sidebar
  - Spacious layout
  - Full navigation
- [ ] 9.4: Test on actual devices (iOS, Android, Windows, macOS)
- [ ] 9.5: Verify touch interactions work on mobile
- [ ] 9.6: Test landscape/portrait orientation changes

### 10. Loading States & Offline Support
- [ ] 10.1: Create skeleton loaders for task cards
- [ ] 10.2: Show loading spinner for form submission
- [ ] 10.3: Implement skeleton for task list while fetching
- [ ] 10.4: Show loading state while statistics updating
- [ ] 10.5: Implement basic offline detection (navigator.onLine)
- [ ] 10.6: Queue mutations when offline, sync when back online
- [ ] 10.7: Show offline banner to user

### 11. Error Handling & Validation
- [ ] 11.1: Display network errors with helpful messages
- [ ] 11.2: Handle 401 errors (redirect to login)
- [ ] 11.3: Handle 403 errors (permission denied)
- [ ] 11.4: Handle 404 errors (task not found, task deleted)
- [ ] 11.5: Display form validation errors
- [ ] 11.6: Show loading errors with retry button
- [ ] 11.7: Use Material-UI Snackbar for notifications

### 12. App Configuration & Main Entry
- [ ] 12.1: Create src/App.jsx with routing
  - QueryClientProvider wrapper
  - ThemeProvider wrapper
  - BrowserRouter with Routes
  - Public routes: /login, /register, /
  - Protected routes: /dashboard
  - Fallback route: 404 page
- [ ] 12.2: Create src/main.jsx (entry point)
- [ ] 12.3: Create public/index.html (HTML template)
- [ ] 12.4: Configure vite.config.js (development server, build settings)
- [ ] 12.5: Write tests for routing

### 13. Testing
- [ ] 13.1: Create tests/components/Login.test.jsx
- [ ] 13.2: Create tests/components/Register.test.jsx
- [ ] 13.3: Create tests/components/TaskCard.test.jsx
- [ ] 13.4: Create tests/components/TaskForm.test.jsx
- [ ] 13.5: Create tests/components/TaskList.test.jsx
- [ ] 13.6: Create tests/components/TaskFilters.test.jsx
- [ ] 13.7: Create tests/components/Dashboard.test.jsx
- [ ] 13.8: Write snapshot tests for components
- [ ] 13.9: Achieve >70% component test coverage
- [ ] 13.10: Test API integration (mock API responses)

### 14. Documentation & Performance
- [ ] 14.1: Create docs/FRONTEND.md with component architecture
- [ ] 14.2: Create docs/COMPONENTS.md with component library
- [ ] 14.3: Create USER_GUIDE.md with how-to instructions
- [ ] 14.4: Create DEPLOYMENT.md with Vercel deployment instructions
- [ ] 14.5: Optimize images (compress, lazy load)
- [ ] 14.6: Code splitting for routes (React.lazy)
- [ ] 14.7: Verify bundle size <500KB gzipped
- [ ] 14.8: Run lighthouse audit for performance

---

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `package.json` | Create | Project metadata and dependencies |
| `vite.config.js` | Create | Vite build configuration |
| `vitest.config.js` | Create | Vitest test configuration |
| `.env.development` | Create | Development API URL |
| `.env.production` | Create | Production API URL |
| `src/main.jsx` | Create | React app entry point |
| `src/App.jsx` | Create | Main routing and providers |
| `src/services/api.js` | Create | Axios instance with interceptors |
| `src/services/auth.js` | Create | Authentication API calls |
| `src/services/tasks.js` | Create | Task API calls |
| `src/store/authStore.js` | Create | Zustand auth state |
| `src/hooks/useAuth.js` | Create | Auth custom hook |
| `src/hooks/useTasks.js` | Create | Tasks React Query hook |
| `src/hooks/useTaskFilters.js` | Create | Filter state hook |
| `src/pages/Login.jsx` | Create | Login page component |
| `src/pages/Register.jsx` | Create | Register page component |
| `src/pages/Dashboard.jsx` | Create | Main dashboard page |
| `src/pages/NotFound.jsx` | Create | 404 page |
| `src/components/auth/PrivateRoute.jsx` | Create | Protected route wrapper |
| `src/components/layout/Layout.jsx` | Create | Main app layout |
| `src/components/layout/AppBar.jsx` | Create | Top navigation bar |
| `src/components/layout/Sidebar.jsx` | Create | Side navigation/filters |
| `src/components/tasks/TaskList.jsx` | Create | Task grid component |
| `src/components/tasks/TaskCard.jsx` | Create | Individual task card |
| `src/components/tasks/TaskForm.jsx` | Create | Create/edit task form |
| `src/components/tasks/TaskFilters.jsx` | Create | Filter controls |
| `src/components/tasks/TaskStats.jsx` | Create | Task statistics display |
| `src/components/common/Loading.jsx` | Create | Skeleton/loading state |
| `src/components/common/ErrorMessage.jsx` | Create | Error display component |
| `src/components/common/ConfirmDialog.jsx` | Create | Confirmation modal |
| `src/utils/formatters.js` | Create | Date/text formatting utilities |
| `tests/components/` | Create | Component test files |
| `public/index.html` | Create | HTML template |
| `docs/FRONTEND.md` | Create | Frontend architecture docs |
| `docs/COMPONENTS.md` | Create | Component library documentation |
| `docs/USER_GUIDE.md` | Create | User-facing how-to guide |
| `docs/DEPLOYMENT.md` | Create | Deployment instructions |

## Patterns to Follow

| Pattern | Reference | Usage |
|---------|-----------|-------|
| Component Composition | React function components | Break UI into small, reusable components |
| Custom Hooks | useAuth, useTasks, useTaskFilters | Extract logic into reusable hooks |
| React Query | @tanstack/react-query | Manage server state, caching, refetching |
| Form Handling | react-hook-form | Form state, validation, submission |
| Material-UI | MUI components and theme | Consistent UI, responsive design |
| Responsive Design | MUI breakpoints (xs, sm, md, lg, xl) | Adapt layout for different screen sizes |
| Error Handling | Try-catch, error boundaries | Display helpful error messages |
| Loading States | Skeleton screens, spinners | Provide feedback during async operations |
| Routing | React Router v6 | Navigate between pages, protected routes |

## Test Strategy

- [ ] **Component Tests:** Test UI components in isolation
  - `tests/components/TaskCard.test.jsx` - rendering, actions, props
  - `tests/components/TaskForm.test.jsx` - form validation, submission
  - `tests/components/TaskList.test.jsx` - rendering tasks, filters applied
  - `tests/components/TaskFilters.test.jsx` - filter state changes
  - Mock API responses with msw (Mock Service Worker)

- [ ] **Page Tests:** Test full page workflows
  - `tests/components/Login.test.jsx` - login flow, error handling
  - `tests/components/Register.test.jsx` - registration flow
  - `tests/components/Dashboard.test.jsx` - task list, filters, create/edit
  - Mock API responses

- [ ] **Integration Tests:** Test API integration
  - Verify API calls made with correct parameters
  - Verify responses parsed correctly
  - Verify error handling

- [ ] **Responsive Design Tests:** Test breakpoints
  - Test grid changes from 1 to 2 to 3 columns
  - Test sidebar collapses on mobile
  - Use MUI testing utilities for breakpoint testing

- [ ] **Accessibility Tests:** WCAG 2.1 compliance
  - Semantic HTML (button, form, nav)
  - ARIA labels for icon buttons
  - Keyboard navigation support
  - Color contrast sufficient

- [ ] **Coverage Requirement:** Minimum 70% coverage for Phase 4
  - Run: `npm test -- --coverage`
  - Focus on critical paths (auth, task CRUD)

## Acceptance Criteria

**ALL must pass:**

- [ ] All 14 task groups completed
- [ ] All gates passing (lint, type-check, tests, security, bundle size)
- [ ] >70% test coverage for components
- [ ] Users can register and log in
- [ ] Users can create, view, edit, delete tasks
- [ ] Filters and sorting work correctly
- [ ] Search finds tasks by title and description
- [ ] Responsive on mobile, tablet, desktop
- [ ] Loading states display during async operations
- [ ] Error messages are helpful and user-friendly
- [ ] API calls succeed with backend from Phase 3
- [ ] No console errors or warnings in production build
- [ ] Lighthouse score >80 for performance
- [ ] Bundle size <500KB gzipped

## Rollback Plan

If frontend issues arise:

1. **API Connection Fails:** If backend unavailable
   ```bash
   # Verify backend is running on correct port
   curl http://localhost:3000/health
   # Check API URL in .env.development
   # Mock API responses for development: use msw (Mock Service Worker)
   ```

2. **Build Fails:** If Vite build has errors
   ```bash
   rm -rf node_modules package-lock.json
   npm install
   npm run build
   ```

3. **Test Failures:** If component tests fail
   ```bash
   # Run single test file
   npm test -- tests/components/TaskCard.test.jsx
   # Update snapshots if intentional UI changes
   npm test -- -u
   ```

4. **State Management Issues:** If auth state not persisting
   ```bash
   # Check localStorage: localStorage.getItem('auth-token')
   # Verify zustand store initialization
   # Check React Query QueryClient config
   ```

5. **Bundle Too Large:** If production build >500KB
   ```bash
   # Analyze bundle: npm run build && npx vite-plugin-visualizer -o dist/stats.html
   # Enable code splitting for routes
   # Remove unused dependencies
   # Tree-shake unused Material-UI components
   ```

6. **Complete Revert:**
   ```bash
   git stash
   git reset --hard HEAD~1
   npm install
   npm test
   ```

---

## Implementation Notes

**Component Architecture:**
- Container components (TaskList, Dashboard) handle data fetching and state
- Presentational components (TaskCard, TaskFilters) receive props and render UI
- Custom hooks (useAuth, useTasks) extract logic for reusability
- Separate service layer (api.js, auth.js, tasks.js) for API calls

**State Management:**
- Server state: React Query (caching, refetching, mutations)
- Auth state: Zustand store (user, token, isAuthenticated)
- UI state: Component useState (modals open/close, form inputs)
- Filters: Custom hook with localStorage persistence

**Responsive Design Strategy:**
- Use Material-UI Grid component with responsive column spans
- Sidebar becomes drawer on mobile (MUI Drawer component)
- TaskList: xs={12} (1 col), sm={6} (2 cols), md={4} (3 cols)
- Touch targets at least 44x44px on mobile
- Test on real devices, not just browser DevTools

**API Integration:**
- Axios service layer handles all API calls
- React Query manages caching and refetching
- Auth interceptor adds JWT token to requests
- Error interceptor handles 401 (logout) and displays errors

**Performance Optimizations:**
- Code splitting: React.lazy for page components
- Image optimization: compress, lazy load
- Tree shaking: Material-UI only imports used components
- Production build: minification, gzip compression
- Lighthouse audit to identify remaining issues

**Testing Philosophy:**
- Mock API responses (don't call real backend in tests)
- Test user workflows, not implementation details
- Component snapshot tests for UI regression detection
- >70% coverage sufficient for MVP (not 100%)
- Focus on critical paths: auth, task CRUD, filters