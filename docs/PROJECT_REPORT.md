# Faculty Analytics - Project Report (Final Viva)

## 1. Problem Statement
Faculty teams need a single system to track student profile data, attendance, marks, and risk indicators without switching between multiple tools.

## 2. Solution Overview
This project is a Flask backend with a React (CDN) frontend served by Flask.
It provides:
- Secure login with JWT-based API authorization.
- CRUD for students, attendance, and marks.
- Search/filter/pagination for large datasets.
- Reports for department and subject performance.

## 3. Architecture
- Backend: Flask + SQLAlchemy + SQLite
- Frontend: React 18 + Bootstrap 5 (served from `frontend/`)
- API style: JSON REST endpoints under `/api/*`
- Auth: `Bearer <token>` JWT for protected APIs

## 4. Key Features Implemented
### UI/UX Refinement
- Responsive layouts for desktop/mobile.
- Styled cards, gradients, and animated page entry (`fade-in-up`).
- Global loader overlay for async operations.
- Toast notifications for success/error feedback.

### Advanced Logic
- Students: search by roll/name + department filter + pagination.
- Marks: search by roll/subject + pagination.
- Attendance: pagination + summary metrics.
- Reports: department rows, subject analytics, top performers, at-risk students.

### Performance Improvements
- SQL indexes created for frequent query paths:
  - `student(dept)`, `student(name)`, `attendance(roll_no)`, `marks(roll_no)`, `marks(subject)`
- Aggregation endpoints use SQL aggregate functions instead of Python-heavy loops where possible.

### Testing
- Integration tests in `backend/tests/test_api.py` cover:
  - health check
  - login/token flow
  - students search/filter/pagination
  - attendance + marks create/list/statistics

### Deployment & CI/CD
- `render.yaml` for Render deployment.
- `Procfile` for Gunicorn start command.
- GitHub Actions CI: `.github/workflows/ci.yml` (install, compile check, tests).

### Documentation
- Swagger UI: `/api/docs`
- OpenAPI JSON: `/api/openapi.json`
- Thunder Client collection: `thunder-tests/`

## 5. API Quick Summary
- `POST /api/login`
- `GET /api/dashboard`
- `GET/POST /api/students`
- `PUT/DELETE /api/students/{roll}`
- `GET/POST /api/attendance`
- `PUT/DELETE /api/attendance/{row_id}`
- `GET/POST /api/marks`
- `PUT/DELETE /api/marks/{row_id}`
- `GET /api/reports`
- `POST /api/logout`
- `GET /healthz`

## 6. Run Instructions
```bash
pip install -r backend/requirements.txt
python backend/app.py
```

Open `http://127.0.0.1:5000/login`

Default credentials:
- Email: `mythish.ad23@bitsathy.ac.in`
- Password: `My1907`

## 7. Viva Talking Points
- Why pagination was added: predictable response size and better UI responsiveness.
- Why indexes were added: faster search/filter on high-frequency columns.
- Why aggregate SQL was used: lower Python-side computation and fewer full-table loops.
- Why CI was added: repeatable quality gate on each push/PR.
