# Faculty Analytics

Faculty Analytics is a web-based academic management system built for faculty members to manage student records, attendance, marks, and academic insights from a single dashboard. The application provides a responsive user interface, secure login, data analytics, reporting features, and production deployment support.

## Features

- Secure login with email/username and JWT-based API authentication
- Student management with add, update, delete, search, filter, and pagination
- Attendance management with percentage calculation and low-attendance analysis
- Marks management with search, pagination, and score analytics
- Dashboard with top performers and at-risk student insights
- Reports module with department-wise and subject-wise analytics
- CSV export for students, attendance, and marks
- Swagger/OpenAPI API documentation
- Responsive UI with loaders, animations, and toast notifications
- PostgreSQL support for shared local and live database usage
- Deployment support with Render and GitHub Actions CI

## Tech Stack

- Frontend: React 18, Bootstrap 5, CSS
- Backend: Python, Flask, Flask-SQLAlchemy
- Database: PostgreSQL / SQLite
- Deployment: Render
- Testing: Python unittest

## Project Structure

```text
faculty_analytics/
├── backend/
│   ├── app.py
│   ├── app_helpers.py
│   ├── models.py
│   ├── requirements.txt
│   └── tests/
├── frontend/
│   ├── app.jsx
│   ├── index.html
│   ├── styles.css
│   └── assets/
├── docs/
│   └── PROJECT_REPORT.md
├── .github/workflows/
├── render.yaml
├── Procfile
└── README.md
```

## Modules

### 1. Login

The system supports secure login using email or username and password. After successful login, a JWT token is generated for authenticated API access.

### 2. Students

Faculty can manage student details such as roll number, name, and department. Search, department filter, and pagination are supported.

### 3. Attendance

Attendance entries can be added, updated, and deleted. The module also calculates attendance percentage and identifies low-attendance cases.

### 4. Marks

Marks for different subjects can be entered, updated, searched, and deleted. The module shows average marks, number of high scorers, and total subject entries.

### 5. Dashboard

The dashboard provides a quick overview of total students, attendance entries, marks entries, top performers, and at-risk students.

### 6. Reports

The reports section provides department-wise and subject-wise analytics along with average attendance and marks.

## Setup Instructions

### 1. Clone the Repository

```bash
git clone <your-github-repository-url>
cd faculty_analytics
```

### 2. Create Virtual Environment

```bash
python -m venv venv
```

### 3. Activate Virtual Environment

For Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

### 4. Install Dependencies

```bash
pip install -r backend/requirements.txt
```

## Environment Configuration

Create a `.env` file in the project root.

Example:

```env
DATABASE_URL=your_postgresql_database_url
SECRET_KEY=your_secret_key
DEFAULT_USERNAME=Mythish
DEFAULT_EMAIL=mythish.ad23@bitsathy.ac.in
DEFAULT_PASSWORD=My1907
SEED_DEMO_DATA=false
```

If `DATABASE_URL` is not provided, the application falls back to local SQLite.

## Run the Project Locally

```powershell
python backend/app.py
```

Open:

```text
http://127.0.0.1:5000/login
```

## API Documentation

Swagger documentation is available at:

```text
/api/docs
```

OpenAPI JSON:

```text
/api/openapi.json
```

## Testing

Run backend integration tests with:

```bash
python -m unittest backend.tests.test_api
```

## Deployment

The project is configured for deployment on Render.

### Render Build Command

```text
pip install -r backend/requirements.txt
```

### Render Start Command

```text
gunicorn --chdir backend app:app
```

The project also includes CI configuration using GitHub Actions in `.github/workflows/ci.yml`.

## Key Highlights

- Responsive academic analytics dashboard
- Clean CRUD workflow for student academic data
- PostgreSQL integration for consistent local and live database usage
- API documentation and testing included
- Production-ready deployment configuration
