# Faculty Academic Analytics Platform

## Final Project Report

## 1. Title
Faculty Academic Analytics Platform

## 2. Abstract
The Faculty Academic Analytics Platform is a web-based academic management system developed to help faculty members manage student records, attendance, marks, and performance insights from a single interface. The application replaces fragmented manual workflows with a centralized portal that supports secure login, student data management, attendance tracking, marks entry, reporting, and academic risk identification. The project was developed as a full-stack web application using Flask, SQLAlchemy, SQLite, React, and Bootstrap, and was deployed on Render with CI/CD support through GitHub Actions.

## 3. Problem Statement
Faculty members often need to monitor student academic data across different sheets, notebooks, and tools. This causes duplication of effort, delayed decision-making, and difficulty in identifying students who need support. A single integrated system was required to:

- store student profile information
- record attendance and marks
- provide fast search and filtering
- generate academic summaries and reports
- improve usability through a responsive modern interface

## 4. Objectives
The main objectives of the project were:

- to build a centralized academic management portal for faculty
- to provide secure access to academic records
- to support CRUD operations for students, attendance, and marks
- to implement search, filtering, and pagination for better usability
- to provide dashboards and reports for academic insights
- to optimize performance through efficient queries and indexes
- to document and deploy the application professionally

## 5. Scope of the Project
The platform is designed for institutional academic monitoring and faculty operations. It covers:

- faculty authentication
- student record management
- attendance entry and tracking
- marks entry and evaluation tracking
- dashboard metrics
- subject-wise and department-wise reporting
- export and documentation support

The current project uses SQLite for development and demonstration. For larger production use, the same architecture can be extended to PostgreSQL or another managed relational database.

## 6. Technology Stack

### Frontend
- React 18 (CDN-based)
- Bootstrap 5
- Custom CSS for responsive design, animations, loaders, and toast notifications

### Backend
- Python
- Flask
- Flask-SQLAlchemy
- JWT-based token authentication for protected APIs

### Database
- SQLite

### Deployment and DevOps
- Render for live deployment
- Gunicorn as the production server
- GitHub Actions for CI/CD

## 7. System Architecture
The project follows a full-stack web application architecture.

### Frontend Layer
The frontend is served by Flask and built using React components. It provides:

- login page
- dashboard
- student management module
- attendance module
- marks module
- reports module

### Backend Layer
The Flask backend exposes REST-style endpoints under `/api/*` and handles:

- authentication and token validation
- business logic
- database read and write operations
- analytics and report generation
- export and documentation endpoints

### Data Layer
The SQLite database stores:

- faculty user credentials
- student profile records
- attendance records
- marks records

## 8. Database Design
The application uses relational tables for structured academic data.

### Main Tables
- `user`
  - stores login information for faculty access
- `student`
  - stores roll number, name, department, and profile details
- `attendance`
  - stores attendance records linked to students
- `marks`
  - stores subject-wise marks linked to students

### Relationships
- one student can have multiple attendance records
- one student can have multiple marks records

### Optimization
Indexes were added on frequently queried columns such as:

- student department
- student name
- attendance roll number
- marks roll number
- marks subject

This improves performance for filtering, searching, and reporting queries.

## 9. Functional Modules

### 9.1 Authentication Module
- secure login using email or username
- JWT token generation after successful login
- protected API routes using bearer token authentication
- logout flow support

### 9.2 Dashboard Module
- total students summary
- attendance and marks overview
- top performers section
- at-risk students section
- quick analytics for faculty monitoring

### 9.3 Students Module
- add student
- edit student
- delete student
- search by roll number or name
- department filtering
- pagination for large lists
- student profile view with full record details

### 9.4 Attendance Module
- add attendance records
- edit attendance records
- delete attendance records
- attendance percentage analytics
- paginated record view

### 9.5 Marks Module
- add marks
- edit marks
- delete marks
- subject-wise record view
- search and pagination
- performance band labels for quick analysis

### 9.6 Reports Module
- department-wise summary
- subject-wise summary
- academic risk indicators
- top performer reporting
- export actions for report-related data

## 10. UI/UX Refinement
The interface was refined according to the Phase 3 rubric with a focus on professional presentation and usability.

### Implemented UI/UX Features
- responsive layouts for desktop and mobile screens
- modern login page and dashboard styling
- polished internal pages for students, attendance, marks, and reports
- profile-style student presentation
- consistent visual hierarchy for cards, tables, and forms
- loaders for asynchronous actions
- toast notifications for success and error feedback
- smooth transitions and animations for a better user experience

## 11. Advanced Logic Implemented
The project includes the required advanced logic features:

- search in student and marks modules
- department and subject filtering
- server-side pagination for better performance and scalability
- dashboard analytics
- academic risk detection based on attendance and marks
- student detail view that combines record-level insights

## 12. Performance Improvements
The application was improved for reliability and performance through:

- indexed database columns for common query paths
- aggregate SQL queries for dashboards and reports
- reduced backend complexity by extracting helper logic from the main app file
- frontend code splitting with lazy-loaded views
- optimized paginated API responses

## 13. Testing and Reliability
Basic integration testing was implemented for core project workflows.

### Covered Areas
- health endpoint verification
- login and token flow
- students API listing and pagination
- attendance record flow
- marks record flow

### Test Location
- `backend/tests/test_api.py`

### Outcome
The integration tests pass successfully and confirm that the core application flows are working as expected.

## 14. API Documentation
The project includes proper API documentation for final evaluation.

### Available Documentation
- Swagger UI: `/api/docs`
- OpenAPI specification: `/api/openapi.json`
- Thunder Client collection: `thunder-tests/`

### Main API Endpoints
- `POST /api/login`
- `POST /api/logout`
- `GET /api/dashboard`
- `GET/POST /api/students`
- `PUT/DELETE /api/students/{roll}`
- `GET/POST /api/attendance`
- `PUT/DELETE /api/attendance/{row_id}`
- `GET/POST /api/marks`
- `PUT/DELETE /api/marks/{row_id}`
- `GET /api/reports`
- `GET /healthz`

## 15. Deployment and CI/CD
The project was deployed to Render and includes automated CI/CD support.

### Live Deployment
- Platform: Render
- Live URL: `https://researchanalytics.onrender.com`

### Deployment Files
- `render.yaml`
- `Procfile`

### CI/CD
GitHub Actions is configured to:

- install dependencies
- run compile checks
- execute tests automatically on code updates

CI workflow file:
- `.github/workflows/ci.yml`

## 16. Run Instructions

### Local Run
```bash
pip install -r backend/requirements.txt
python backend/app.py
```

Open:

`http://127.0.0.1:5000/login`

### Default Login Credentials
- Email: `mythish.ad23@bitsathy.ac.in`
- Password: `My1907`

## 17. Outcomes
The project successfully delivers:

- a complete academic analytics portal
- a working live deployment
- a responsive and professional user interface
- secure login and protected APIs
- end-to-end CRUD workflows
- analytics and reporting support
- documented APIs and CI/CD workflow

The final system meets the Phase 3 evaluation criteria for web development.

## 18. Challenges Faced
Some practical challenges during development included:

- balancing UI polish with responsiveness across screen sizes
- organizing a full-stack project while keeping the backend maintainable
- ensuring the deployed environment behaved correctly on Render
- handling SQLite limitations for local and deployed environments

These were addressed through refactoring, frontend refinement, deployment verification, and structured testing.

## 19. Future Enhancements
Possible improvements for future versions include:

- migration from SQLite to PostgreSQL for persistent hosted data
- role-based access for multiple faculty/admin users
- chart-based analytics and trend visualization
- email notifications for at-risk students
- import/export through Excel files
- stronger audit history and activity logs

## 20. Conclusion
The Faculty Academic Analytics Platform was developed as a complete academic management and analytics solution for faculty use. It centralizes student information, attendance, marks, and reporting into a single portal and improves efficiency through secure access, responsive design, analytics support, and deployment readiness. The project satisfies the functional, technical, and documentation goals expected for Phase 3 of the web development evaluation.

## 21. Viva Talking Points
Use these points during the final viva:

- The project solves the problem of scattered academic records by centralizing student, attendance, and marks data.
- Flask was used for the backend because it is lightweight, clear, and suitable for REST APIs.
- React was used for interactive frontend rendering and a better user experience.
- Pagination was added to keep responses small and interfaces responsive.
- Database indexes were added to improve search and filter performance.
- Swagger was used for API documentation.
- Render was used for deployment because it works well for Flask-based full-stack applications.
- GitHub Actions was added to automate testing and basic quality checks.
