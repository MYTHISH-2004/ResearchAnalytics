from flask import Flask, Response, request, redirect, session, jsonify, send_from_directory
from models import db, User, Student, Attendance, Marks
from sqlalchemy import func, case
from werkzeug.security import generate_password_hash, check_password_hash
import csv
import os
import json
import base64
import hashlib
import hmac
import logging
import time
from io import StringIO
from pathlib import Path
from app_helpers import (
    validation_error,
    parse_int_field,
    parse_pagination_args,
    paginate_query,
    initialize_database_state,
    build_student_insights,
    student_to_dict,
    attendance_to_dict,
    marks_to_dict,
    build_student_profile,
    get_students_query,
    get_marks_query,
    create_marks_rows_from_payload,
)

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"


def load_local_env_file():
    env_file = PROJECT_ROOT / ".env"
    if not env_file.exists():
        return

    for raw_line in env_file.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


load_local_env_file()


def build_database_uri():
    database_url = (os.getenv("DATABASE_URL") or "").strip()
    if database_url:
        if database_url.startswith("postgres://"):
            database_url = "postgresql://" + database_url[len("postgres://"):]
        return database_url

    sqlite_path = (os.getenv("SQLITE_PATH") or "").strip()
    db_file = Path(sqlite_path) if sqlite_path else CURRENT_DIR / "instance" / "database.db"
    db_file.parent.mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{db_file.resolve().as_posix()}"

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "secret")
DEFAULT_USERNAME = os.getenv("DEFAULT_USERNAME", "Mythish")
DEFAULT_EMAIL = os.getenv("DEFAULT_EMAIL", "mythish.ad23@bitsathy.ac.in")
DEFAULT_PASSWORD = os.getenv("DEFAULT_PASSWORD", "My1907")
API_JWT_EXPIRES_SECONDS = 24 * 60 * 60

app.config["SQLALCHEMY_DATABASE_URI"] = build_database_uri()
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("faculty_analytics")


def hash_password(password):
    return generate_password_hash(password)


def is_hashed_password(value):
    if not value:
        return False
    return value.startswith("pbkdf2:") or value.startswith("scrypt:")


def verify_password(stored_password, provided_password):
    if not stored_password or not provided_password:
        return False
    if is_hashed_password(stored_password):
        return check_password_hash(stored_password, provided_password)
    return stored_password == provided_password


def _jwt_b64_encode(data):
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _jwt_b64_decode(data):
    padding = "=" * (-len(data) % 4)
    return base64.urlsafe_b64decode((data + padding).encode("ascii"))


def create_api_jwt(username, exp_seconds=API_JWT_EXPIRES_SECONDS):
    header = {"alg": "HS256", "typ": "JWT"}
    now = int(time.time())
    payload = {"sub": username, "iat": now, "exp": now + exp_seconds}
    header_part = _jwt_b64_encode(json.dumps(header, separators=(",", ":")).encode("utf-8"))
    payload_part = _jwt_b64_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8"))
    signing_input = f"{header_part}.{payload_part}".encode("ascii")
    signature = hmac.new(app.secret_key.encode("utf-8"), signing_input, hashlib.sha256).digest()
    signature_part = _jwt_b64_encode(signature)
    return f"{header_part}.{payload_part}.{signature_part}"


def decode_api_jwt(token):
    try:
        header_part, payload_part, signature_part = token.split(".")
    except ValueError:
        return None

    signing_input = f"{header_part}.{payload_part}".encode("ascii")
    expected_sig = hmac.new(app.secret_key.encode("utf-8"), signing_input, hashlib.sha256).digest()
    try:
        provided_sig = _jwt_b64_decode(signature_part)
    except Exception:
        return None

    if not hmac.compare_digest(expected_sig, provided_sig):
        return None

    try:
        payload = json.loads(_jwt_b64_decode(payload_part).decode("utf-8"))
    except Exception:
        return None

    if int(payload.get("exp", 0)) < int(time.time()):
        return None
    return payload


def get_api_user_from_request():
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.split(" ", 1)[1].strip()
        payload = decode_api_jwt(token)
        if payload and payload.get("sub"):
            return payload.get("sub")
    return None


with app.app_context():
    initialize_database_state(
        DEFAULT_USERNAME,
        DEFAULT_EMAIL,
        DEFAULT_PASSWORD,
        hash_password,
        verify_password,
        is_hashed_password,
        logger,
    )


def authenticate_user(login_mode, username, email, password):
    if not password:
        return None

    user = None
    email = (email or "").strip().lower()
    username = (username or "").strip()

    if login_mode == "username":
        if username:
            user = User.query.filter_by(username=username).first()
            if user and verify_password(user.password, password):
                return user
        if email:
            user = User.query.filter_by(email=email).first()
            if user and verify_password(user.password, password):
                return user
        return None

    if email:
        user = User.query.filter_by(email=email).first()
        if user and verify_password(user.password, password):
            return user
    if username:
        user = User.query.filter_by(username=username).first()
        if user and verify_password(user.password, password):
            return user
    return None


def get_template_api_token():
    username = session.get("user")
    if not username:
        return ""
    return create_api_jwt(username)


def require_login_api():
    user = get_api_user_from_request()
    if not user:
        return jsonify({"error": "Unauthorized"}), 401
    return None


def require_login_or_session():
    if get_api_user_from_request() or "user" in session:
        return None
    return jsonify({"error": "Unauthorized"}), 401


def serve_frontend_app():
    return send_from_directory(str(FRONTEND_DIR), "index.html")


# ---------------- LOGIN ----------------
# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    return serve_frontend_app()


@app.route("/login")
def login_page():
    return serve_frontend_app()


@app.route("/api/login", methods=["POST"])
def api_login():
    payload = request.get_json(silent=True) or {}
    login_mode = payload.get("login_mode", "email")
    password = (payload.get("password") or "").strip()
    username = payload.get("username")
    email = payload.get("email")

    user = authenticate_user(login_mode, username, email, password)

    if not user:
        return jsonify({"success": False, "message": "Invalid login details"}), 401

    session["user"] = user.username
    token = create_api_jwt(user.username)
    return jsonify({"success": True, "user": user.username, "token": token})


@app.route("/dashboard")
def dashboard():
    return serve_frontend_app()


@app.route("/api/dashboard")
def api_dashboard():
    unauthorized = require_login_api()
    if unauthorized:
        return unauthorized

    students = Student.query.count()
    attendance = Attendance.query.count()
    marks = Marks.query.count()

    records = db.session.query(Attendance.roll_no, Attendance.total, Attendance.present).all()
    rolls = []
    percentages = []
    for roll_no, total, present in records:
        if total > 0:
            rolls.append(roll_no)
            percentages.append(round((present / total) * 100, 2))

    insights = build_student_insights()
    selected_student = None
    selected_roll = (request.args.get("student_roll") or "").strip()
    if selected_roll.isdigit():
        selected_student = build_student_profile(int(selected_roll))

    return jsonify({
        "students": students,
        "attendance": attendance,
        "marks": marks,
        "rolls": rolls,
        "percentages": percentages,
        "top_performers": insights["top_performers"],
        "at_risk_students": insights["at_risk_students"],
        "selected_student": selected_student
    })


@app.route("/students", methods=["GET", "POST"])
def students():
    return serve_frontend_app()


@app.route("/api/students", methods=["GET", "POST"])
def api_students():
    unauthorized = require_login_api()
    if unauthorized:
        return unauthorized

    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        try:
            roll = parse_int_field(payload, "roll", minimum=1)
            name = (payload.get("name") or "").strip()
            dept = (payload.get("dept") or "").strip()
        except ValueError as exc:
            return validation_error(str(exc))

        if not name or not dept:
            return validation_error("Name and department are required")

        if Student.query.get(roll):
            return jsonify({"error": "Student already exists"}), 409

        row = Student(roll_no=roll, name=name, dept=dept)
        db.session.add(row)
        db.session.commit()
        return jsonify({"success": True, "student": student_to_dict(row)}), 201

    search_query = (request.args.get("q") or "").strip()
    dept_filter = (request.args.get("dept") or "").strip()

    page, per_page = parse_pagination_args(default_page=1, default_per_page=10, max_per_page=100)
    query = get_students_query(search_query, dept_filter)
    items, pagination = paginate_query(query, page, per_page)
    students_data = [student_to_dict(s) for s in items]
    departments = [row[0] for row in db.session.query(Student.dept).distinct().order_by(Student.dept.asc()).all()]

    return jsonify({
        "students": students_data,
        "search_query": search_query,
        "dept_filter": dept_filter,
        "departments": departments,
        "pagination": pagination
    })


@app.route("/api/students/<int:roll>", methods=["PUT"])
def api_update_student(roll):
    unauthorized = require_login_api()
    if unauthorized:
        return unauthorized

    row = Student.query.get(roll)
    if not row:
        return jsonify({"error": "Student not found"}), 404

    payload = request.get_json(silent=True) or {}
    name = (payload.get("name") or "").strip()
    dept = (payload.get("dept") or "").strip()

    if not name or not dept:
        return validation_error("Name and department are required")

    row.name = name
    row.dept = dept
    db.session.commit()
    return jsonify({"success": True, "student": student_to_dict(row)})


@app.route("/api/students/<int:roll>/profile", methods=["GET"])
def api_student_profile(roll):
    unauthorized = require_login_api()
    if unauthorized:
        return unauthorized

    profile = build_student_profile(roll)
    if not profile:
        return jsonify({"error": "Student not found"}), 404
    return jsonify({"student": profile})


@app.route("/api/students/<int:roll>", methods=["DELETE"])
def api_delete_student(roll):
    unauthorized = require_login_api()
    if unauthorized:
        return unauthorized

    row = Student.query.get(roll)
    if not row:
        return jsonify({"error": "Student not found"}), 404

    db.session.delete(row)
    db.session.commit()
    return jsonify({"success": True})


@app.route("/delete_student/<int:roll>")
def delete_student(roll):
    if "user" not in session:
        return redirect("/")

    s = Student.query.get(roll)
    if s:
        db.session.delete(s)
        db.session.commit()

    return redirect("/students")


# ---------------- ATTENDANCE ----------------
@app.route("/attendance", methods=["GET", "POST"])
def attendance():
    return serve_frontend_app()


@app.route("/api/attendance", methods=["GET", "POST"])
def api_attendance():
    unauthorized = require_login_api()
    if unauthorized:
        return unauthorized

    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        try:
            roll = parse_int_field(payload, "roll", minimum=1)
            total = parse_int_field(payload, "total", minimum=0)
            present = parse_int_field(payload, "present", minimum=0)
        except ValueError as exc:
            return validation_error(str(exc))

        if present > total:
            return validation_error("present cannot exceed total")

        row = Attendance(roll_no=roll, total=total, present=present)
        db.session.add(row)
        db.session.commit()
        return jsonify({"success": True, "attendance": attendance_to_dict(row)}), 201

    page, per_page = parse_pagination_args(default_page=1, default_per_page=10, max_per_page=100)
    query = Attendance.query.order_by(Attendance.id.desc())
    data, pagination = paginate_query(query, page, per_page)

    totals_row = db.session.query(
        func.coalesce(func.sum(Attendance.total), 0),
        func.coalesce(func.sum(Attendance.present), 0),
        func.count(Attendance.id)
    ).one()
    total_classes = int(totals_row[0])
    total_present = int(totals_row[1])
    overall_percentage = round((total_present / total_classes) * 100, 2) if total_classes else 0
    low_attendance_count = Attendance.query.filter(
        Attendance.total > 0,
        (Attendance.present * 100.0 / Attendance.total) < 75
    ).count()

    return jsonify({
        "data": [attendance_to_dict(r) for r in data],
        "overall_percentage": overall_percentage,
        "low_attendance_count": low_attendance_count,
        "total_attendance_rows": int(totals_row[2]),
        "pagination": pagination
    })


@app.route("/api/attendance/<int:row_id>", methods=["PUT"])
def api_update_attendance(row_id):
    unauthorized = require_login_api()
    if unauthorized:
        return unauthorized

    row = Attendance.query.get(row_id)
    if not row:
        return jsonify({"error": "Attendance row not found"}), 404

    payload = request.get_json(silent=True) or {}
    try:
        roll = parse_int_field(payload, "roll", minimum=1)
        total = parse_int_field(payload, "total", minimum=0)
        present = parse_int_field(payload, "present", minimum=0)
    except ValueError as exc:
        return validation_error(str(exc))

    if present > total:
        return validation_error("present cannot exceed total")

    row.roll_no = roll
    row.total = total
    row.present = present
    db.session.commit()
    return jsonify({"success": True, "attendance": attendance_to_dict(row)})


@app.route("/api/attendance/<int:row_id>", methods=["DELETE"])
def api_delete_attendance(row_id):
    unauthorized = require_login_api()
    if unauthorized:
        return unauthorized

    row = Attendance.query.get(row_id)
    if not row:
        return jsonify({"error": "Attendance row not found"}), 404

    db.session.delete(row)
    db.session.commit()
    return jsonify({"success": True})


# delete attendance
@app.route("/delete_attendance/<int:id>")
def delete_attendance(id):
    if "user" not in session:
        return redirect("/")

    a = Attendance.query.get(id)
    if a:
        db.session.delete(a)
        db.session.commit()

    return redirect("/attendance")


# ---------------- MARKS ----------------
@app.route("/marks", methods=["GET", "POST"])
def marks():
    return serve_frontend_app()


@app.route("/api/marks", methods=["GET", "POST"])
def api_marks():
    unauthorized = require_login_api()
    if unauthorized:
        return unauthorized

    if request.method == "POST":
        payload = request.get_json(silent=True) or {}
        try:
            rows_to_add = create_marks_rows_from_payload(payload)
        except ValueError as exc:
            return validation_error(str(exc))

        if not rows_to_add:
            return jsonify({"error": "No valid marks rows to insert"}), 400

        db.session.add_all(rows_to_add)
        db.session.commit()
        return jsonify({
            "success": True,
            "inserted": len(rows_to_add),
            "rows": [marks_to_dict(row) for row in rows_to_add]
        }), 201

    search_query = (request.args.get("q") or "").strip()
    page, per_page = parse_pagination_args(default_page=1, default_per_page=10, max_per_page=100)
    filtered_query = get_marks_query(search_query)
    data, pagination = paginate_query(filtered_query, page, per_page)

    stats_query = get_marks_query(search_query).order_by(None)
    avg_marks_raw, high_scorers_raw, total_rows, subject_count = stats_query.with_entities(
        func.coalesce(func.avg(Marks.marks), 0),
        func.coalesce(func.sum(case((Marks.marks >= 90, 1), else_=0)), 0),
        func.count(Marks.id),
        func.count(func.distinct(func.lower(Marks.subject)))
    ).first()
    avg_marks = round(float(avg_marks_raw), 2) if avg_marks_raw is not None else 0
    high_scorers = int(high_scorers_raw or 0)
    total_rows = int(total_rows or 0)
    subject_count = int(subject_count or 0)

    return jsonify({
        "data": [marks_to_dict(m) for m in data],
        "search_query": search_query,
        "avg_marks": avg_marks,
        "high_scorers": high_scorers,
        "subject_count": subject_count,
        "total_marks_rows": total_rows,
        "pagination": pagination
    })


@app.route("/api/marks/<int:row_id>", methods=["PUT"])
def api_update_marks(row_id):
    unauthorized = require_login_api()
    if unauthorized:
        return unauthorized

    row = Marks.query.get(row_id)
    if not row:
        return jsonify({"error": "Marks row not found"}), 404

    payload = request.get_json(silent=True) or {}
    try:
        roll = parse_int_field(payload, "roll", minimum=1)
        marks_value = parse_int_field(payload, "marks", minimum=0)
    except ValueError as exc:
        return validation_error(str(exc))

    subject = (payload.get("subject") or "").strip()
    if not subject:
        return validation_error("subject is required")
    if marks_value > 100:
        return validation_error("marks must be <= 100")

    row.roll_no = roll
    row.subject = subject
    row.marks = marks_value
    db.session.commit()
    return jsonify({"success": True, "marks": marks_to_dict(row)})


@app.route("/api/marks/<int:row_id>", methods=["DELETE"])
def api_delete_marks(row_id):
    unauthorized = require_login_api()
    if unauthorized:
        return unauthorized

    row = Marks.query.get(row_id)
    if not row:
        return jsonify({"error": "Marks row not found"}), 404

    db.session.delete(row)
    db.session.commit()
    return jsonify({"success": True})


# delete marks
@app.route("/delete_marks/<int:id>")
def delete_marks(id):
    if "user" not in session:
        return redirect("/")

    m = Marks.query.get(id)
    if m:
        db.session.delete(m)
        db.session.commit()

    return redirect("/marks")


# ---------------- LOGOUT ----------------
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/")


@app.route("/api/logout", methods=["POST"])
def api_logout():
    session.pop("user", None)
    return jsonify({"success": True})


@app.route("/reports")
def reports():
    return serve_frontend_app()


@app.route("/api/reports")
def api_reports():
    unauthorized = require_login_api()
    if unauthorized:
        return unauthorized

    insights = build_student_insights()

    total_students = len(insights["profiles"])
    total_at_risk = len([s for s in insights["profiles"] if s["risk_flags"]])
    avg_attendance = round(
        sum(s["attendance_pct"] for s in insights["profiles"]) / total_students, 2
    ) if total_students else 0
    avg_marks = round(
        sum(s["avg_marks"] for s in insights["profiles"]) / total_students, 2
    ) if total_students else 0

    return jsonify({
        "department_rows": insights["department_rows"],
        "subject_rows": insights["subject_rows"],
        "top_performers": insights["top_performers"],
        "total_students": total_students,
        "total_at_risk": total_at_risk,
        "avg_attendance": avg_attendance,
        "avg_marks": avg_marks
    })


def generate_csv(filename, headers, rows):
    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(headers)
    writer.writerows(rows)
    csv_data = output.getvalue()
    output.close()

    return Response(
        csv_data,
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.route("/export/students")
def export_students():
    unauthorized = require_login_or_session()
    if unauthorized:
        return unauthorized

    rows = [(s.roll_no, s.name, s.dept) for s in Student.query.order_by(Student.roll_no.asc()).all()]
    return generate_csv("students.csv", ["Roll No", "Name", "Department"], rows)


@app.route("/export/attendance")
def export_attendance():
    unauthorized = require_login_or_session()
    if unauthorized:
        return unauthorized

    rows = [
        (a.id, a.roll_no, a.total, a.present, round((a.present / a.total) * 100, 2) if a.total else 0)
        for a in Attendance.query.order_by(Attendance.id.asc()).all()
    ]
    return generate_csv("attendance.csv", ["ID", "Roll No", "Total", "Present", "Percentage"], rows)


@app.route("/export/marks")
def export_marks():
    unauthorized = require_login_or_session()
    if unauthorized:
        return unauthorized

    rows = [(m.id, m.roll_no, m.subject, m.marks) for m in Marks.query.order_by(Marks.id.asc()).all()]
    return generate_csv("marks.csv", ["ID", "Roll No", "Subject", "Marks"], rows)


@app.route("/api/openapi.json")
def api_openapi():
    return jsonify({
        "openapi": "3.0.3",
        "info": {
            "title": "Faculty Analytics API",
            "version": "1.0.0",
            "description": "API documentation for the Faculty Analytics project."
        },
        "servers": [{"url": "/"}],
        "components": {
            "securitySchemes": {
                "bearerAuth": {"type": "http", "scheme": "bearer", "bearerFormat": "JWT"}
            }
        },
        "paths": {
            "/api/login": {
                "post": {
                    "summary": "Login and receive JWT token",
                    "requestBody": {"required": True},
                    "responses": {"200": {"description": "Login success"}, "401": {"description": "Invalid credentials"}}
                }
            },
            "/api/dashboard": {"get": {"summary": "Dashboard summary", "security": [{"bearerAuth": []}]}},
            "/api/students": {
                "get": {"summary": "List students with search/filter/pagination", "security": [{"bearerAuth": []}]},
                "post": {"summary": "Create student", "security": [{"bearerAuth": []}]}
            },
            "/api/students/{roll}": {
                "put": {"summary": "Update student", "security": [{"bearerAuth": []}]},
                "delete": {"summary": "Delete student", "security": [{"bearerAuth": []}]}
            },
            "/api/attendance": {
                "get": {"summary": "List attendance with pagination", "security": [{"bearerAuth": []}]},
                "post": {"summary": "Create attendance row", "security": [{"bearerAuth": []}]}
            },
            "/api/attendance/{row_id}": {
                "put": {"summary": "Update attendance row", "security": [{"bearerAuth": []}]},
                "delete": {"summary": "Delete attendance row", "security": [{"bearerAuth": []}]}
            },
            "/api/marks": {
                "get": {"summary": "List marks with search/pagination", "security": [{"bearerAuth": []}]},
                "post": {"summary": "Create marks row(s)", "security": [{"bearerAuth": []}]}
            },
            "/api/marks/{row_id}": {
                "put": {"summary": "Update marks row", "security": [{"bearerAuth": []}]},
                "delete": {"summary": "Delete marks row", "security": [{"bearerAuth": []}]}
            },
            "/api/reports": {"get": {"summary": "Analytics reports", "security": [{"bearerAuth": []}]}},
            "/api/logout": {"post": {"summary": "Logout", "security": [{"bearerAuth": []}]}},
            "/healthz": {"get": {"summary": "Health check"}}
        }
    })


@app.route("/api/docs")
def api_docs():
    html = """
    <!doctype html>
    <html>
    <head>
      <meta charset="utf-8" />
      <title>Faculty Analytics API Docs</title>
      <link rel="stylesheet" href="https://unpkg.com/swagger-ui-dist@5/swagger-ui.css" />
    </head>
    <body>
      <div id="swagger-ui"></div>
      <script src="https://unpkg.com/swagger-ui-dist@5/swagger-ui-bundle.js"></script>
      <script>
        window.ui = SwaggerUIBundle({ url: '/api/openapi.json', dom_id: '#swagger-ui' });
      </script>
    </body>
    </html>
    """
    return Response(html, mimetype="text/html")


@app.route("/frontend/<path:filename>")
def serve_frontend_assets(filename):
    return send_from_directory(str(FRONTEND_DIR), filename)


@app.route("/healthz")
def healthz():
    return jsonify({"status": "ok"})


@app.after_request
def add_security_headers(response):
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self' https: data: blob: 'unsafe-inline' 'unsafe-eval'; "
        "img-src 'self' https: data:; "
        "connect-src 'self' https:;"
    )
    return response


@app.errorhandler(400)
def handle_bad_request(error):
    logger.warning("Bad request: %s %s", request.method, request.path)
    if request.path.startswith("/api/"):
        return jsonify({"success": False, "error": "Bad request"}), 400
    return "Bad request", 400


@app.errorhandler(404)
def handle_not_found(error):
    logger.info("Not found: %s %s", request.method, request.path)
    if request.path.startswith("/api/"):
        return jsonify({"success": False, "error": "Not found"}), 404
    return "Not found", 404


@app.errorhandler(Exception)
def handle_unexpected_error(error):
    logger.exception("Unhandled exception on %s %s", request.method, request.path)
    if request.path.startswith("/api/"):
        return jsonify({"success": False, "error": "Internal server error"}), 500
    return "Internal server error", 500


if __name__ == "__main__":
    app.run(debug=True)

