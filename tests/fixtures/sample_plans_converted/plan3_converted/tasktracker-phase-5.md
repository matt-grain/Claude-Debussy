# TaskTracker MVP Phase 5: Integration & Deployment

**Status:** Pending
**Master Plan:** [TaskTracker MVP - Master Plan](tasktracker-MASTER_PLAN.md)
**Depends On:** [Phase 4: User Interface](tasktracker-phase-4.md)

---

## Process Wrapper (MANDATORY)
- [ ] Read previous notes: `notes/NOTES_tasktracker_phase_4.md`
- [ ] **[IMPLEMENTATION - see Tasks below]**
- [ ] Pre-validation (ALL required):
  ```bash
  # Backend tests
  cd ../backend && npm test && npm audit --audit-level=moderate
  # Frontend tests
  cd ../tasktracker-ui && npm test && npm audit --audit-level=moderate
  # Build both
  npm run build && cd ../backend && npm run build 2>/dev/null || echo "No backend build"
  # Integration tests
  npm run test:e2e 2>/dev/null || echo "E2E tests optional for MVP"
  ```
- [ ] Fix loop: repeat pre-validation until clean
- [ ] Write `notes/NOTES_tasktracker_phase_5.md` (REQUIRED)

## Gates (must pass before completion)

**ALL gates are BLOCKING.**

- lint: Both frontend and backend pass linting
- tests: Backend tests >80%, Frontend tests >70%
- security: `npm audit --audit-level=moderate` passes on both
- performance: API <100ms, Frontend load <1.5s
- deployment: Successfully deployed to Vercel (frontend) and serverless (backend)

---

## Overview

This final phase brings together all completed modules into a cohesive, production-ready application. Focuses on end-to-end integration testing, performance optimization, security hardening, and deployment to production. Validates that all user workflows function correctly across the full stack, optimizes performance metrics, and ensures the application is secure, reliable, and ready for real users.

## Dependencies
- Previous phases: Phases 1-4 (all modules complete and tested)
- External: Vercel account, MongoDB Atlas, GitHub (for CI/CD)

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Frontend/backend API integration issues | Medium | High | Postman testing first, E2E tests before deployment, staging environment |
| Production database performance | Medium | Medium | MongoDB Atlas M2 cluster, query optimization, monitoring setup |
| CORS misconfiguration blocks requests | Low | High | Test CORS in staging, allow frontend domain in backend |
| Environment variables missing in production | Low | High | Document all required env vars, Vercel secrets configuration, pre-deployment checklist |
| Security vulnerabilities discovered | Low | High | Security audit, dependency scanning, OWASP top 10 check |
| Deployment downtime affects users | Low | Medium | Blue-green deployment, health checks, rollback plan |

---

## Tasks

### 1. Integration Testing Setup
- [ ] 1.1: Create tests/integration/ directory for end-to-end tests
- [ ] 1.2: Setup test database separate from development and production
- [ ] 1.3: Seed test database with sample users and tasks
- [ ] 1.4: Create test configuration (API URL, auth tokens, timeouts)
- [ ] 1.5: Document integration test running instructions

### 2. End-to-End User Flows
- [ ] 2.1: Test new user registration → create first task → view dashboard
  - Register with email, username, password
  - Verify user created in database
  - Auto-login after registration (if implemented)
  - Redirect to dashboard
  - Create a new task
  - Verify task appears in list
  - Verify task count updated in stats
- [ ] 2.2: Test login → view tasks → edit task → mark complete
  - Login with valid credentials
  - Dashboard loads with user's tasks
  - Edit existing task (change title, priority)
  - Verify changes saved in database
  - Mark task as complete
  - Verify status changed and completedAt set
- [ ] 2.3: Test filter and search → delete task
  - Filter tasks by status (todo, in_progress, done)
  - Verify correct tasks displayed
  - Search for task by title
  - Verify search results accurate
  - Delete a task
  - Verify task removed from list
  - Verify task deleted from database
- [ ] 2.4: Test multiple users isolation
  - Create user A and user B
  - User A creates tasks
  - User B logs in, creates different tasks
  - Verify user A cannot see user B's tasks
  - Verify task counts correct per user
- [ ] 2.5: Test error scenarios
  - Invalid login credentials → error message
  - Duplicate email registration → error message
  - Create task without title → validation error
  - Update non-existent task → 404 error
  - Delete task and verify can't access it → 404

### 3. API Contract Testing
- [ ] 3.1: Verify all API endpoints documented in Phase 3 work as expected
- [ ] 3.2: Test all request/response schemas match documentation
- [ ] 3.3: Test authentication token handling (valid, expired, invalid)
- [ ] 3.4: Test error responses return correct status codes
- [ ] 3.5: Test pagination with actual data volumes
- [ ] 3.6: Test filtering combinations (status + priority, search + filters)
- [ ] 3.7: Run Postman collection against live backend
- [ ] 3.8: Document any deviations from specification

### 4. Performance Testing
- [ ] 4.1: Measure API response times under load
  - List endpoint with 1000+ tasks: <100ms median
  - Search endpoint: <100ms median
  - Create task: <200ms
  - Update task: <200ms
  - Delete task: <200ms
- [ ] 4.2: Measure frontend load time
  - First contentful paint: <1s
  - Largest contentful paint: <1.5s
  - Time to interactive: <2s
  - Bundle size: <500KB gzipped
- [ ] 4.3: Run lighthouse audit on production build
  - Performance score: >80
  - Accessibility score: >80
  - Best practices score: >80
- [ ] 4.4: Profile database queries
  - Verify indexes used for all common queries
  - Check query execution plans
  - Identify any N+1 problems
- [ ] 4.5: Load test with concurrent users
  - Simulate 10 concurrent users
  - Simulate 50 concurrent users
  - Measure response times, error rates
  - Identify bottlenecks

### 5. Security Hardening
- [ ] 5.1: Review OWASP Top 10 for web applications
  - SQL/NoSQL injection: validated inputs, parameterized queries
  - Broken authentication: JWT tokens, secure storage
  - Sensitive data exposure: HTTPS only, no hardcoded secrets
  - Broken access control: ensureTaskOwnership middleware
  - Cross-site scripting (XSS): React escapes by default, validate user input
  - Cross-site request forgery (CSRF): JWT token required in header
- [ ] 5.2: Run npm audit on both frontend and backend
  - No high severity vulnerabilities
  - Review moderate vulnerabilities for false positives
  - Update dependencies if needed
- [ ] 5.3: Review environment variable handling
  - No secrets in .git (add to .gitignore)
  - No secrets in source code
  - All secrets in environment variables or Vercel secrets
  - Generate new JWT_SECRET for production
- [ ] 5.4: Enable CORS restrictions
  - Frontend origin must be whitelisted in backend
  - No "allow all origins" in production
- [ ] 5.5: Enable HTTPS everywhere
  - Vercel provides free HTTPS
  - Force HTTP → HTTPS redirect
  - Set secure flag on cookies (if using cookies)
- [ ] 5.6: Test password security
  - Bcrypt salt rounds >= 10
  - Password complexity enforced
  - No passwords logged
  - Hash password before storage
- [ ] 5.7: Security headers
  - X-Frame-Options: DENY (prevent clickjacking)
  - X-Content-Type-Options: nosniff
  - Strict-Transport-Security (HSTS)
  - Content-Security-Policy (CSP)
- [ ] 5.8: Create SECURITY.md with security guidelines

### 6. Database Optimization
- [ ] 6.1: Create MongoDB Atlas M2 cluster (if not already done)
  - Set IP whitelist to Vercel IP ranges
  - Create database user with minimal required permissions
  - Enable encryption at rest
  - Enable automatic backups
- [ ] 6.2: Verify all indexes created
  - User email (unique)
  - User username (unique)
  - Task userId (for filtering)
  - Task status (for filtering)
  - Task createdAt (for sorting)
  - Compound index on (userId, status)
- [ ] 6.3: Configure connection pooling
  - Min pool: 5 connections
  - Max pool: 10 connections
  - Connection timeout: 30s
  - Socket timeout: 30s
- [ ] 6.4: Setup monitoring and alerts
  - Monitor query performance
  - Alert on slow queries (>1000ms)
  - Monitor connection pool usage
  - Monitor disk space
- [ ] 6.5: Create backup and restore plan
  - Automatic daily backups enabled
  - Test restore procedure
  - Document backup/restore steps

### 7. Frontend Deployment to Vercel
- [ ] 7.1: Create GitHub repository for frontend (if not already done)
  - Push all code to GitHub
  - Verify main branch is clean
- [ ] 7.2: Connect GitHub repo to Vercel
  - Create Vercel account
  - Authorize GitHub
  - Import repository
- [ ] 7.3: Configure environment variables in Vercel
  - VITE_API_URL=production API URL
  - Verify no secrets in .env files in Git
- [ ] 7.4: Configure build settings in Vercel
  - Framework: Vite
  - Build command: `npm run build`
  - Output directory: `dist`
  - Node version: 18
- [ ] 7.5: Deploy to staging (preview) environment first
  - Merge PR to staging branch
  - Verify deployment succeeds
  - Test in staging environment
- [ ] 7.6: Deploy to production
  - Merge from staging to main
  - Verify production deployment succeeds
  - Test critical user flows in production
- [ ] 7.7: Configure custom domain (if applicable)
  - Add DNS records to domain registrar
  - Update Vercel settings
  - Verify HTTPS working
- [ ] 7.8: Setup Vercel analytics (optional)
  - Monitor performance metrics
  - Track user sessions

### 8. Backend Deployment (Serverless or VPS)
- [ ] 8.1: Choose deployment platform
  - Option A: Vercel Serverless Functions (Node.js)
  - Option B: Heroku (easy for MVP)
  - Option C: AWS Lambda + API Gateway
  - Option D: DigitalOcean App Platform
- [ ] 8.2: Create GitHub repository for backend (if not already done)
  - Push all code to GitHub
  - Verify main branch is clean
- [ ] 8.3: Configure environment variables for production
  - MONGODB_URI=Atlas connection string
  - NODE_ENV=production
  - JWT_SECRET=production secret (generate new)
  - CORS_ORIGIN=production frontend URL
- [ ] 8.4: Create deployment configuration (if needed)
  - Dockerfile for containerized deployment
  - docker-compose.yml for local testing
  - .env.production.example for documentation
- [ ] 8.5: Deploy backend to chosen platform
  - Connect GitHub for automatic deployments
  - Run health check after deployment
  - Verify API responding correctly
- [ ] 8.6: Configure custom domain for API (if applicable)
  - Point API subdomain to deployment
  - Update frontend API URL
  - Verify HTTPS working
- [ ] 8.7: Setup monitoring and logging
  - Log API requests and errors
  - Setup alerts for 5xx errors
  - Monitor uptime
- [ ] 8.8: Setup CI/CD pipeline (GitHub Actions)
  - Run tests on every push
  - Build and deploy on merge to main
  - Notify on deployment success/failure

### 9. Testing in Production-Like Environment
- [ ] 9.1: Create staging environment that mirrors production
  - Staging database (separate from production)
  - Staging frontend URL
  - Staging API URL
  - Same dependencies and versions as production
- [ ] 9.2: Run full integration test suite against staging
- [ ] 9.3: Perform user acceptance testing
  - Register new user
  - Create, edit, delete tasks
  - Test filters and search
  - Test on mobile device
  - Verify all features working
- [ ] 9.4: Test error scenarios in staging
  - Database connection failure
  - API timeout
  - Invalid token
  - Task not found
- [ ] 9.5: Verify email and notifications (if implemented)
  - Password reset emails send correctly
  - Welcome email on registration
  - Task reminders send at correct time
- [ ] 9.6: Monitor performance in staging
  - API response times acceptable
  - Frontend load times acceptable
  - No memory leaks
  - No unhandled errors in logs

### 10. Rollback Plan & Monitoring
- [ ] 10.1: Document rollback procedure
  - Revert frontend: redeploy previous commit from Vercel
  - Revert backend: deploy previous version
  - Database migration rollback steps
  - Data recovery procedure if needed
- [ ] 10.2: Setup monitoring in production
  - Application performance monitoring (APM)
  - Error tracking (Sentry optional)
  - Uptime monitoring
  - Database query monitoring
- [ ] 10.3: Create incident response plan
  - Who to notify if issues
  - Steps to diagnose issues
  - Rollback decision criteria
  - Post-incident review process
- [ ] 10.4: Setup health checks
  - Frontend: Vercel built-in health checks
  - Backend: GET /health endpoint
  - Database: Connection test on startup
  - Monitor health checks in production

### 11. Documentation & Knowledge Transfer
- [ ] 11.1: Create DEPLOYMENT.md
  - Step-by-step deployment instructions
  - Environment variable checklist
  - Troubleshooting guide
  - Rollback procedure
- [ ] 11.2: Create PRODUCTION.md
  - Production architecture overview
  - Scaling considerations
  - Monitoring dashboard links
  - Incident response procedures
- [ ] 11.3: Create MAINTENANCE.md
  - Regular maintenance tasks (weekly, monthly)
  - Dependency updates
  - Security updates
  - Backup verification
  - Database cleanup
- [ ] 11.4: Update README.md
  - Link to live application
  - Link to documentation
  - Tech stack summary
  - Contributing guidelines
- [ ] 11.5: Create runbooks for common operations
  - How to add new user (admin)
  - How to reset user password
  - How to back up database
  - How to scale resources

### 12. Final Testing & Launch
- [ ] 12.1: Create pre-launch checklist
  - All tests passing
  - Security audit passed
  - Performance targets met
  - Documentation complete
  - Rollback plan ready
  - Monitoring setup
  - Team trained
- [ ] 12.2: Perform final end-to-end test
  - Register new user
  - Create, edit, delete tasks
  - Test all filters and features
  - Test on mobile/tablet/desktop
  - Verify no errors in browser console
  - Verify no errors in server logs
- [ ] 12.3: Soft launch (optional)
  - Deploy to production but don't announce yet
  - Monitor closely for 24-48 hours
  - Test with real user load
  - Fix any issues discovered
- [ ] 12.4: Public launch
  - Announce publicly (social media, email, etc.)
  - Monitor closely for first week
  - Be ready to respond to issues
  - Celebrate with team!

---

## Files to Create/Modify

| File | Action | Purpose |
|------|--------|---------|
| `tests/integration/` | Create | End-to-end integration tests |
| `tests/fixtures/seed-data.json` | Create | Test data for integration tests |
| `docs/DEPLOYMENT.md` | Create | Deployment instructions |
| `docs/PRODUCTION.md` | Create | Production operations guide |
| `docs/MAINTENANCE.md` | Create | Maintenance procedures |
| `docs/SECURITY.md` | Modify | Add production security requirements |
| `.github/workflows/ci.yml` | Create | GitHub Actions CI/CD pipeline |
| `.github/workflows/deploy.yml` | Create | GitHub Actions deployment pipeline |
| `Dockerfile` | Create | (Optional) Container image for backend |
| `docker-compose.yml` | Create | (Optional) Local testing with containers |
| `.env.production.example` | Create | Production environment template |
| `vercel.json` | Create | Vercel configuration (if using Vercel for backend) |

## Patterns to Follow

| Pattern | Reference | Usage |
|---------|-----------|-------|
| E2E Testing | Supertest for API, Playwright for frontend | Test full workflows from UI through API to database |
| Performance Metrics | Lighthouse, WebPageTest | Measure and optimize user experience |
| Security Checklist | OWASP Top 10 | Systematically review and harden against known vulnerabilities |
| Monitoring | Application metrics, error tracking | Detect and respond to issues in production |
| Deployment | Blue-green or canary deployment | Minimize downtime and enable quick rollback |
| Documentation | Runbooks and checklists | Enable others to operate the system |

## Test Strategy

- [ ] **Integration Tests:** Test full user flows
  - `tests/integration/user-registration.test.js` - Register → Login → Dashboard
  - `tests/integration/task-crud.test.js` - Create → Read → Update → Delete
  - `tests/integration/filtering.test.js` - Filters and search working correctly
  - `tests/integration/multi-user.test.js` - Users can't access each other's tasks
  - Run against staging environment before production

- [ ] **API Contract Tests:** Verify API meets specification
  - All endpoints return expected status codes
  - Response schemas match documentation
  - Error responses are consistent
  - Pagination metadata correct

- [ ] **Performance Tests:** Measure production readiness
  - API endpoints <100ms median response (Phase 3 target)
  - Frontend load <1.5s (Phase 4 target)
  - Lighthouse score >80
  - No N+1 database queries
  - Concurrent load testing (10, 50 users)

- [ ] **Security Tests:** Verify no vulnerabilities
  - npm audit passes on both frontend and backend
  - No secrets in source code
  - OWASP Top 10 review completed
  - Authorization checks working
  - Input validation preventing injection

## Acceptance Criteria

**ALL must pass before launch:**

- [ ] All integration tests passing
- [ ] All API contract tests passing
- [ ] Performance targets met (API <100ms, Frontend <1.5s)
- [ ] Security audit passed
- [ ] npm audit passes on both projects
- [ ] Lighthouse score >80
- [ ] All user flows tested and working
- [ ] Multi-user isolation verified
- [ ] Error scenarios handled gracefully
- [ ] Production database configured and tested
- [ ] Deployment successful (frontend and backend)
- [ ] Monitoring setup and alerting working
- [ ] Rollback plan documented and tested
- [ ] Documentation complete and accurate
- [ ] Team trained on operations

## Rollback Plan

If critical issues discovered after launch:

1. **Frontend Issues:** Revert to previous deployment
   ```bash
   # In Vercel dashboard: click "Deployments" → select previous build → "Promote to Production"
   # Or via CLI: vercel rollback
   ```

2. **Backend Issues:** Revert to previous deployment
   ```bash
   # Depends on platform:
   # Heroku: heroku releases:rollback
   # Vercel: Deployments tab
   # Custom: git revert and redeploy
   ```

3. **Database Issues:** Use automated backups
   ```bash
   # MongoDB Atlas: Backup & Restore → restore from previous backup
   # Document exact restore steps
   ```

4. **Complete Rollback:** If major issues
   ```bash
   # Step 1: Stop accepting new requests (disable DNS or mark unhealthy)
   # Step 2: Revert frontend and backend to known good versions
   # Step 3: Restore database if needed
   # Step 4: Verify critical user flows working
   # Step 5: Resume accepting requests
   # Step 6: Post-incident review
   ```

---

## Implementation Notes

**Deployment Architecture:**
- Frontend (React): Vercel CDN + serverless functions
- Backend (Node.js): Vercel serverless, Heroku, or similar
- Database: MongoDB Atlas (managed service)
- Domain: Custom domain with DNS pointing to Vercel
- HTTPS: Automatic via Vercel

**Performance Optimization Priority:**
1. API response time <100ms (from Phase 3)
2. Frontend load time <1.5s (from Phase 4)
3. Lighthouse score >80 (from Phase 4)
4. Bundle size <500KB (from Phase 4)

**Security Hardening Priority:**
1. OWASP Top 10 review completed
2. npm audit passes (no high severity)
3. Environment variables secure (no secrets in code)
4. HTTPS enforced everywhere
5. Authorization checks in place
6. Input validation working

**Monitoring & Alerting:**
- Error tracking: Sentry (free tier) for error reporting
- Performance: Vercel Analytics, Lighthouse CI
- Uptime: UptimeRobot (free) for health checks
- Logs: Console logs + file logging for debugging
- Database: MongoDB Atlas built-in monitoring

**CI/CD Pipeline (GitHub Actions):**
```yaml
On push to main:
1. Run tests (npm test)
2. Run linting (npm run lint)
3. Run security audit (npm audit)
4. Build (npm run build)
5. Deploy to production
```

**Team Responsibilities After Launch:**
- Monitor error tracking and uptime
- Respond to user issues quickly
- Keep dependencies updated
- Backup and security checks
- Performance monitoring
- Scale resources if needed