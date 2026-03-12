# Faculty Academic Analytics Platform

Web-based application for faculty to manage students, attendance, marks, and academic insights from one dashboard.

## Features
- Secure login (email/username + JWT API auth)
- Students module with search, filter, pagination
- Attendance module with percentage analytics and pagination
- Marks module with search, bulk insert, and pagination
- Dashboard with top performers and at-risk students
- Reports with department and subject insights
- CSV export endpoints
- Responsive UI, loader overlay, toast notifications, smooth animations

## Tech Stack
- Frontend: React 18 (CDN), Bootstrap 5
- Backend: Python, Flask, Flask-SQLAlchemy
- Database: SQLite
- Deployment: Render + Gunicorn

## Phase 3 Completion
### UI/UX Refinement
- Responsive layouts for mobile and desktop
- Polished styling and animation (`fade-in-up`)
- Loader and toast-based feedback

### Advanced Logic
- Search/filter/pagination implemented in core modules
- Analytics and risk detection

### Performance & Testing
- Database indexes for frequent query paths
- Aggregate SQL optimizations
- Integration tests in `backend/tests/test_api.py`

### Production Deployment
- `render.yaml` and `Procfile` included
- CI pipeline in `.github/workflows/ci.yml`

### Documentation & Viva
- Swagger UI: `/api/docs`
- OpenAPI JSON: `/api/openapi.json`
- Thunder Client collection: `thunder-tests/`
- Viva report: `docs/PROJECT_REPORT.md`

## Local Run
```bash
pip install -r backend/requirements.txt
python backend/app.py
```

Open: `http://127.0.0.1:5000/login`

Default login:
- Email: `mythish.ad23@bitsathy.ac.in`
- Password: `My1907`
