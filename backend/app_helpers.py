from flask import jsonify, request
from sqlalchemy import inspect, text, func, case
import math

from models import db, User, Student, Attendance, Marks


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


def seed_demo_data_if_empty(logger):
    if Student.query.count() or Attendance.query.count() or Marks.query.count():
        return

    db.session.add_all([
        Student(roll_no=101, name="Asha R", dept="CSE"),
        Student(roll_no=102, name="Bharath K", dept="ECE"),
        Student(roll_no=103, name="Charan M", dept="IT"),
        Student(roll_no=104, name="Divya S", dept="CSE"),
        Student(roll_no=105, name="Eswar P", dept="AIML"),
        Student(roll_no=106, name="Farhana N", dept="EEE"),
    ])
    db.session.add_all([
        Attendance(roll_no=101, total=40, present=37),
        Attendance(roll_no=102, total=40, present=30),
        Attendance(roll_no=103, total=40, present=35),
        Attendance(roll_no=104, total=40, present=39),
        Attendance(roll_no=105, total=40, present=28),
        Attendance(roll_no=106, total=40, present=33),
    ])
    db.session.add_all([
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
    ])
    db.session.commit()
    logger.info("Seeded demo data for empty database")


def initialize_database_state(default_username, default_email, default_password, hash_password, verify_password, is_hashed_password, logger):
    db.create_all()
    inspector = inspect(db.engine)
    user_columns = [col["name"] for col in inspector.get_columns("user")]
    if "email" not in user_columns:
        db.session.execute(text("ALTER TABLE user ADD COLUMN email VARCHAR(120)"))
        db.session.commit()

    user = User.query.filter_by(username=default_username).first()
    admin_user = User.query.filter_by(username="admin").first()

    if user:
        user.email = default_email
        if not verify_password(user.password, default_password):
            user.password = hash_password(default_password)
        db.session.commit()
    elif admin_user:
        admin_user.username = default_username
        admin_user.email = default_email
        admin_user.password = hash_password(default_password)
        db.session.commit()
    else:
        db.session.add(User(username=default_username, email=default_email, password=hash_password(default_password)))
        db.session.commit()

    changed = False
    for row in User.query.all():
        if row.password and not is_hashed_password(row.password):
            row.password = hash_password(row.password)
            changed = True
    if changed:
        db.session.commit()

    db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_student_dept ON student(dept)"))
    db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_student_name ON student(name)"))
    db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_attendance_roll_no ON attendance(roll_no)"))
    db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_marks_roll_no ON marks(roll_no)"))
    db.session.execute(text("CREATE INDEX IF NOT EXISTS idx_marks_subject ON marks(subject)"))
    db.session.commit()
    seed_demo_data_if_empty(logger)


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
        total_classes = attendance_stats["total"]
        total_present = attendance_stats["present"]
        attendance_pct = round((total_present / total_classes) * 100, 2) if total_classes else 0

        marks_stats = marks_by_roll.get(roll_no, {"avg": 0, "count": 0})
        avg_marks = marks_stats["avg"]

        risk_flags = []
        if total_classes and attendance_pct < 75:
            risk_flags.append("Low Attendance")
        if marks_stats["count"] and avg_marks < 50:
            risk_flags.append("Low Marks")

        student_profiles.append({
            "roll_no": roll_no,
            "name": student.name,
            "dept": student.dept,
            "attendance_pct": attendance_pct,
            "avg_marks": avg_marks,
            "risk_flags": risk_flags
        })

    top_performers = sorted(student_profiles, key=lambda item: item["avg_marks"], reverse=True)[:5]
    at_risk_students = [row for row in student_profiles if row["risk_flags"]]

    department_rows = []
    grouped_departments = {}
    for row in student_profiles:
        grouped_departments.setdefault(row["dept"], []).append(row)

    for dept, dept_students in sorted(grouped_departments.items()):
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


def student_to_dict(student):
    return {"roll_no": student.roll_no, "name": student.name, "dept": student.dept}


def attendance_to_dict(row):
    percentage = round((row.present / row.total) * 100, 2) if row.total else 0
    return {"id": row.id, "roll_no": row.roll_no, "total": row.total, "present": row.present, "percentage": percentage}


def marks_to_dict(row):
    return {"id": row.id, "roll_no": row.roll_no, "subject": row.subject, "marks": row.marks}


def build_student_profile(roll_no):
    student_obj = Student.query.get(roll_no)
    if not student_obj:
        return None

    attendance_rows = Attendance.query.filter_by(roll_no=roll_no).all()
    marks_rows = Marks.query.filter_by(roll_no=roll_no).all()
    total_classes = sum(row.total for row in attendance_rows)
    total_present = sum(row.present for row in attendance_rows)
    attendance_pct = round((total_present / total_classes) * 100, 2) if total_classes else 0
    avg_marks = round(sum(row.marks for row in marks_rows) / len(marks_rows), 2) if marks_rows else 0

    risk_flags = []
    if total_classes and attendance_pct < 75:
        risk_flags.append("Low Attendance")
    if marks_rows and avg_marks < 50:
        risk_flags.append("Low Marks")

    return {
        "roll_no": student_obj.roll_no,
        "name": student_obj.name,
        "dept": student_obj.dept,
        "attendance_pct": attendance_pct,
        "avg_marks": avg_marks,
        "total_classes": total_classes,
        "total_present": total_present,
        "subject_scores": [{"subject": row.subject, "marks": row.marks} for row in sorted(marks_rows, key=lambda item: item.id, reverse=True)],
        "attendance_history": [{
            "id": row.id,
            "total": row.total,
            "present": row.present,
            "percentage": round((row.present / row.total) * 100, 2) if row.total else 0
        } for row in sorted(attendance_rows, key=lambda item: item.id, reverse=True)],
        "risk_flags": risk_flags
    }


def get_students_query(search_query="", dept_filter=""):
    query = Student.query
    if search_query:
        query = query.filter(Student.roll_no == int(search_query)) if search_query.isdigit() else query.filter(Student.name.ilike(f"%{search_query}%"))
    if dept_filter:
        query = query.filter(Student.dept == dept_filter)
    return query.order_by(Student.roll_no.asc())


def get_marks_query(search_query=""):
    query = Marks.query
    if search_query:
        query = query.filter(Marks.roll_no == int(search_query)) if search_query.isdigit() else query.filter(Marks.subject.ilike(f"%{search_query}%"))
    return query.order_by(Marks.id.desc())


def create_marks_rows_from_payload(payload):
    roll = parse_int_field(payload, "roll", minimum=1)
    rows_to_add = []

    if str(payload.get("bulk_mode", "0")) == "1":
        for entry in (payload.get("bulk_entries") or "").strip().splitlines():
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

            if 0 <= score <= 100:
                rows_to_add.append(Marks(roll_no=roll, subject=subject, marks=score))
        return rows_to_add

    subject = (payload.get("subject") or "").strip()
    marks_value = parse_int_field(payload, "marks", minimum=0)
    if marks_value > 100:
        raise ValueError("marks must be <= 100")
    if not subject:
        raise ValueError("subject is required")
    rows_to_add.append(Marks(roll_no=roll, subject=subject, marks=marks_value))
    return rows_to_add
