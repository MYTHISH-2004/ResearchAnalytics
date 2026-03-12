from flask import Flask, Response, request, redirect, session, jsonify, send_from_directory
from models import db, User, Student, Attendance, Marks
from sqlalchemy import inspect, text, func, case
from werkzeug.security import generate_password_hash, check_password_hash
import csv
import os
import json
import base64
import hashlib
import hmac
import logging
import time
import math
from io import StringIO
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent
FRONTEND_DIR = PROJECT_ROOT / "frontend"
DB_FILE = CURRENT_DIR / "instance" / "database.db"
DB_FILE.parent.mkdir(parents=True, exist_ok=True)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "secret")
DEFAULT_USERNAME = os.getenv("DEFAULT_USERNAME", "Mythish")
DEFAULT_EMAIL = os.getenv("DEFAULT_EMAIL", "mythish.ad23@bitsathy.ac.in")
DEFAULT_PASSWORD = os.getenv("DEFAULT_PASSWORD", "My1907")
API_JWT_EXPIRES_SECONDS = 24 * 60 * 60

app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_FILE.as_posix()}"
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


def validation_error(message):
    return jsonify({"success": False, "error": message}), 400


def parse_int_field(payload, field_name, minimum=None):
    value = payload.get(field_name)
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise ValueError(f"Invalid {field_name}")

    if minimum is not None and parsed < minimum:
        raise ValueError(f"{field_name} must be >= {minimum}")
    return parsed


def parse_pagination_args(default_page=1, default_per_page=10, max_per_page=100):
    raw_page = (request.args.get("page") or str(default_page)).strip()
    raw_per_page = (request.args.get("per_page") or str(default_per_page)).strip()

    try:
        page = int(raw_page)
    except ValueError:
        page = default_page

    try:
        per_page = int(raw_per_page)
    except ValueError:
        per_page = default_per_page

    page = max(1, page)
    per_page = max(1, min(per_page, max_per_page))
    return page, per_page


def paginate_query(query, page, per_page):
    total = query.order_by(None).count()
    items = query.offset((page - 1) * per_page).limit(per_page).all()
    total_pages = max(1, math.ceil(total / per_page)) if total else 1
    return items, {
        "page": page,
        "per_page": per_page,
        "total": total,
        "total_pages": total_pages
    }


def seed_demo_data_if_empty():
    if Student.query.count() or Attendance.query.count() or Marks.query.count():
        return

    demo_students = [
        Student(roll_no=101, name="Asha R", dept="CSE"),
        Student(roll_no=102, name="Bharath K", dept="ECE"),
        Student(roll_no=103, name="Charan M", dept="IT"),
        Student(roll_no=104, name="Divya S", dept="CSE"),
        Student(roll_no=105, name="Eswar P", dept="AIML"),
        Student(roll_no=106, name="Farhana N", dept="EEE"),
    ]
    demo_attendance = [
        Attendance(roll_no=101, total=40, present=37),
        Attendance(roll_no=102, total=40, present=30),
        Attendance(roll_no=103, total=40, present=35),
        Attendance(roll_no=104, total=40, present=39),
        Attendance(roll_no=105, total=40, present=28),
        Attendance(roll_no=106, total=40, present=33),
    ]
    demo_marks = [
        Marks(roll_no=101, subject="Maths", marks=92),
        Marks(roll_no=101, subject="Physics", marks=88),
        Marks(roll_no=102, subject="Maths", marks=61),
        Marks(roll_no=102, subject="Circuits", marks=58),
        Marks(roll_no=103, subject="Python", marks=84),
        Marks(roll_no=103, subject="DBMS", marks=79),
        Marks(roll_no=104, subject="Maths", marks=95),
        Marks(roll_no=104, subject="Chemistry", marks=90),
        Marks(roll_no=105, subject="ML", marks=49),
        Marks(roll_no=105, subject="Python", marks=55),
        Marks(roll_no=106, subject="Machines", marks=72),
        Marks(roll_no=106, subject="Networks", marks=68),
    ]

    db.session.add_all(demo_students)
    db.session.add_all(demo_attendance)
    db.session.add_all(demo_marks)
    db.session.commit()
    logger.info("Seeded demo data for empty database")


with app.app_context():
    db.create_all()
    inspector = inspect(db.engine)

  
    user_columns = [col["name"] for col in inspector.get_columns("user")]
    if "email" not in user_columns:
        db.session.execute(text("ALTER TABLE user ADD COLUMN email VARCHAR(120)"))
        db.session.commit()

    user = User.query.filter_by(username=DEFAULT_USERNAME).first()
    admin_user = User.query.filter_by(username="admin").first()

    if user:
        user.email = DEFAULT_EMAIL
        if not verify_password(user.password, DEFAULT_PASSWORD):
            user.password = hash_password(DEFAULT_PASSWORD)
        db.session.commit()
    elif admin_user:
        admin_user.username = DEFAULT_USERNAME
        admin_user.email = DEFAULT_EMAIL
        admin_user.password = hash_password(DEFAULT_PASSWORD)
        db.session.commit()
    else:
        db.session.add(
            User(
                username=DEFAULT_USERNAME,
                email=DEFAULT_EMAIL,
                password=hash_password(DEFAULT_PASSWORD)
            )
        )
        db.session.commit()

    # Migrate legacy plain-text passwords to hashes for existing users.
    users = User.query.all()
    changed = False
    for row in users:
        if row.password and not is_hashed_password(row.password):
            row.password = hash_password(row.password)
            changed = True
    if changed:
        db.session.commit()

    # Add hot-path indexes for list/search APIs.
    db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_student_dept ON student(dept)"))
    db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_student_name ON student(name)"))
    db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_attendance_roll_no ON attendance(roll_no)"))
    db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_marks_roll_no ON marks(roll_no)"))
    db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_marks_subject ON marks(subject)"))
    db.session.commit()
    seed_demo_data_if_empty()


def build_student_insights():
    students_data = Student.query.order_by(Student.roll_no.asc()).all()

    attendance_rows = db.session.query(
        Attendance.roll_no,
        func.coalesce(func.sum(Attendance.total), 0),
        func.coalesce(func.sum(Attendance.present), 0)
    ).group_by(Attendance.roll_no).all()
    attendance_by_roll = {
        roll_no: {"total": int(total), "present": int(present)}
        for roll_no, total, present in attendance_rows
    }

    marks_rows = db.session.query(
        Marks.roll_no,
        func.coalesce(func.avg(Marks.marks), 0),
        func.count(Marks.id)
    ).group_by(Marks.roll_no).all()
    marks_by_roll = {
        roll_no: {"avg": round(float(avg_marks), 2), "count": int(total_rows)}
        for roll_no, avg_marks, total_rows in marks_rows
    }

    student_profiles = []
    for student in students_data:
        roll_no = student.roll_no
        attendance_stats = attendance_by_roll.get(roll_no, {"total": 0, "present": 0})
        attendance_total = attendance_stats["total"]
        attendance_present = attendance_stats["present"]
        attendance_pct = round((attendance_present / attendance_total) * 100, 2) if attendance_total else 0

        marks_stats = marks_by_roll.get(roll_no, {"avg": 0, "count": 0})
        avg_marks = marks_stats["avg"]
        marks_count = marks_stats["count"]

        risk_flags = []
        if attendance_total and attendance_pct < 75:
            risk_flags.append("Low Attendance")
        if marks_count and avg_marks < 50:
            risk_flags.append("Low Marks")

        student_profiles.append({
            "roll_no": roll_no,
            "name": student.name,
            "dept": student.dept,
            "attendance_pct": attendance_pct,
            "avg_marks": avg_marks,
            "risk_flags": risk_flags
        })

    top_performers = sorted(
        [s for s in student_profiles if s["avg_marks"] > 0],
        key=lambda item: item["avg_marks"],
        reverse=True
    )[:5]

    at_risk_students = [s for s in student_profiles if s["risk_flags"]][:5]

    departments = sorted({student.dept for student in students_data})
    department_rows = []
    for dept in departments:
        dept_students = [s for s in student_profiles if s["dept"] == dept]
        count = len(dept_students)
        avg_attendance = round(sum(s["attendance_pct"] for s in dept_students) / count, 2) if count else 0
        avg_marks = round(sum(s["avg_marks"] for s in dept_students) / count, 2) if count else 0
        at_risk_count = sum(1 for s in dept_students if s["risk_flags"])
        department_rows.append({
            "dept": dept,
            "students": count,
            "avg_attendance": avg_attendance,
            "avg_marks": avg_marks,
            "at_risk_count": at_risk_count
        })

    subject_rows = []
    subject_data = db.session.query(
        Marks.subject,
        func.count(Marks.id),
        func.coalesce(func.avg(Marks.marks), 0),
        func.coalesce(func.max(Marks.marks), 0),
        func.coalesce(func.min(Marks.marks), 0)
    ).group_by(Marks.subject).order_by(Marks.subject.asc()).all()
    for subject, entries, avg_score, max_score, min_score in subject_data:
        subject_rows.append({
            "subject": subject,
            "entries": int(entries),
            "avg_score": round(float(avg_score), 2),
            "max_score": int(max_score),
            "min_score": int(min_score)
        })

    return {
        "profiles": student_profiles,
        "top_performers": top_performers,
        "at_risk_students": at_risk_students,
        "department_rows": department_rows,
        "subject_rows": subject_rows
    }


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


def student_to_dict(student):
    return {
        "roll_no": student.roll_no,
        "name": student.name,
        "dept": student.dept
    }


def attendance_to_dict(row):
    percentage = round((row.present / row.total) * 100, 2) if row.total else 0
    return {
        "id": row.id,
        "roll_no": row.roll_no,
        "total": row.total,
        "present": row.present,
        "percentage": percentage
    }


def marks_to_dict(row):
    return {
        "id": row.id,
        "roll_no": row.roll_no,
        "subject": row.subject,
        "marks": row.marks
    }


def get_students_query(search_query="", dept_filter=""):
    query = Student.query
    if search_query:
        if search_query.isdigit():
            query = query.filter(Student.roll_no == int(search_query))
        else:
            query = query.filter(Student.name.ilike(f"%{search_query}%"))

    if dept_filter:
        query = query.filter(Student.dept == dept_filter)

    return query.order_by(Student.roll_no.asc())


def get_marks_query(search_query=""):
    query = Marks.query
    if search_query:
        if search_query.isdigit():
            query = query.filter(Marks.roll_no == int(search_query))
        else:
            query = query.filter(Marks.subject.ilike(f"%{search_query}%"))
    return query.order_by(Marks.id.desc())


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
        selected_roll = int(selected_roll)
        student_obj = Student.query.get(selected_roll)
        if student_obj:
            attendance_rows = Attendance.query.filter_by(roll_no=selected_roll).all()
            marks_rows = Marks.query.filter_by(roll_no=selected_roll).all()

            total_classes = sum(row.total for row in attendance_rows)
            total_present = sum(row.present for row in attendance_rows)
            attendance_pct = round((total_present / total_classes) * 100, 2) if total_classes else 0
            avg_marks = round(sum(row.marks for row in marks_rows) / len(marks_rows), 2) if marks_rows else 0

            subject_scores = [
                {"subject": row.subject, "marks": row.marks}
                for row in sorted(marks_rows, key=lambda item: item.id, reverse=True)
            ]

            risk_flags = []
            if total_classes and attendance_pct < 75:
                risk_flags.append("Low Attendance")
            if marks_rows and avg_marks < 50:
                risk_flags.append("Low Marks")

            selected_student = {
                "roll_no": student_obj.roll_no,
                "name": student_obj.name,
                "dept": student_obj.dept,
                "attendance_pct": attendance_pct,
                "avg_marks": avg_marks,
                "total_classes": total_classes,
                "total_present": total_present,
                "subject_scores": subject_scores,
                "risk_flags": risk_flags
            }

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


def create_marks_rows_from_payload(payload):
    roll = parse_int_field(payload, "roll", minimum=1)
    rows_to_add = []

    if str(payload.get("bulk_mode", "0")) == "1":
        bulk_entries = (payload.get("bulk_entries") or "").strip().splitlines()
        for entry in bulk_entries:
            line = entry.strip()
            if not line:
                continue

            subject = ""
            marks_value = ""
            if ":" in line:
                subject, marks_value = line.split(":", 1)
            elif "," in line:
                subject, marks_value = line.split(",", 1)
            elif "-" in line:
                subject, marks_value = line.rsplit("-", 1)
            else:
                continue

            subject = subject.strip()
            marks_value = marks_value.strip()
            if not subject:
                continue

            try:
                score = int(marks_value)
            except ValueError:
                continue

            if score < 0 or score > 100:
                continue
            rows_to_add.append(Marks(roll_no=roll, subject=subject, marks=score))
    else:
        subject = (payload.get("subject") or "").strip()
        marks_value = parse_int_field(payload, "marks", minimum=0)
        if marks_value > 100:
            raise ValueError("marks must be <= 100")
        if not subject:
            raise ValueError("subject is required")
        rows_to_add.append(Marks(roll_no=roll, subject=subject, marks=marks_value))

    return rows_to_add


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

    stats_query = get_marks_query(search_query)
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

