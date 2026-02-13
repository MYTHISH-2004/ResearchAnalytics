from flask import Flask, Response, render_template, request, redirect, session
from models import db, User, Student, Attendance, Marks
from sqlalchemy import inspect, text
import csv
from io import StringIO
from collections import defaultdict

app = Flask(__name__)
app.secret_key = "secret"
DEFAULT_USERNAME = "Mythish"
DEFAULT_EMAIL = "mythish.ad23@bitsathy.ac.in"
DEFAULT_PASSWORD = "My1907"

app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///database.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# create tables + default admin
with app.app_context():
    db.create_all()
    inspector = inspect(db.engine)

    # Add email column for existing databases without migrations.
    user_columns = [col["name"] for col in inspector.get_columns("user")]
    if "email" not in user_columns:
        db.session.execute(text("ALTER TABLE user ADD COLUMN email VARCHAR(120)"))
        db.session.commit()

    # Ensure default login is Mythish / mythish.ad23@bitsathy.ac.in / My1907.
    user = User.query.filter_by(username=DEFAULT_USERNAME).first()
    admin_user = User.query.filter_by(username="admin").first()

    if user:
        user.email = DEFAULT_EMAIL
        if user.password != DEFAULT_PASSWORD:
            user.password = DEFAULT_PASSWORD
        db.session.commit()
    elif admin_user:
        admin_user.username = DEFAULT_USERNAME
        admin_user.email = DEFAULT_EMAIL
        admin_user.password = DEFAULT_PASSWORD
        db.session.commit()
    else:
        db.session.add(
            User(
                username=DEFAULT_USERNAME,
                email=DEFAULT_EMAIL,
                password=DEFAULT_PASSWORD
            )
        )
        db.session.commit()


def build_student_insights():
    students_data = Student.query.all()
    attendance_data = Attendance.query.all()
    marks_data = Marks.query.all()

    attendance_by_roll = defaultdict(lambda: {"total": 0, "present": 0})
    for record in attendance_data:
        attendance_by_roll[record.roll_no]["total"] += record.total
        attendance_by_roll[record.roll_no]["present"] += record.present

    marks_by_roll = defaultdict(list)
    subject_scores = defaultdict(list)
    for record in marks_data:
        marks_by_roll[record.roll_no].append(record.marks)
        subject_scores[record.subject].append(record.marks)

    student_profiles = []
    for student in students_data:
        roll_no = student.roll_no
        attendance_total = attendance_by_roll[roll_no]["total"]
        attendance_present = attendance_by_roll[roll_no]["present"]
        attendance_pct = round((attendance_present / attendance_total) * 100, 2) if attendance_total else 0

        marks_list = marks_by_roll[roll_no]
        avg_marks = round(sum(marks_list) / len(marks_list), 2) if marks_list else 0

        risk_flags = []
        if attendance_total and attendance_pct < 75:
            risk_flags.append("Low Attendance")
        if marks_list and avg_marks < 50:
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
    for subject, scores in sorted(subject_scores.items()):
        subject_rows.append({
            "subject": subject,
            "entries": len(scores),
            "avg_score": round(sum(scores) / len(scores), 2),
            "max_score": max(scores),
            "min_score": min(scores)
        })

    return {
        "profiles": student_profiles,
        "top_performers": top_performers,
        "at_risk_students": at_risk_students,
        "department_rows": department_rows,
        "subject_rows": subject_rows
    }


# ---------------- LOGIN ----------------
# ---------------- LOGIN ----------------
@app.route("/", methods=["GET", "POST"])
def login():
    message = ""

    if request.method == "POST":
        login_mode = request.form.get("login_mode", "email")
        p = request.form.get("password", "")
        user = None

        if login_mode == "username":
            u = request.form.get("username", "").strip()
            user = User.query.filter_by(username=u, password=p).first()
            if not user:
                e = request.form.get("email", "").strip().lower()
                if e:
                    user = User.query.filter_by(email=e, password=p).first()
        else:
            e = request.form.get("email", "").strip().lower()
            user = User.query.filter_by(email=e, password=p).first()
            if not user:
                u = request.form.get("username", "").strip()
                if u:
                    user = User.query.filter_by(username=u, password=p).first()

        if user:
            session["user"] = user.username
            return redirect("/dashboard")
        else:
            message = "Invalid login details"

    return render_template("login.html", message=message)



# ---------------- DASHBOARD ----------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect("/")

    students = Student.query.count()
    attendance = Attendance.query.count()
    marks = Marks.query.count()

    records = Attendance.query.all()
    rolls = []
    percentages = []

    for r in records:
        if r.total > 0:
            rolls.append(r.roll_no)
            percentages.append(round((r.present / r.total) * 100, 2))

    insights = build_student_insights()
    selected_student = None
    selected_roll = request.args.get("student_roll", "").strip()
    if selected_roll.isdigit():
        selected_roll = int(selected_roll)
        student_obj = Student.query.get(selected_roll)
        if student_obj:
            attendance_rows = Attendance.query.filter_by(roll_no=selected_roll).all()
            marks_rows = Marks.query.filter_by(roll_no=selected_roll).all()

            total_classes = sum(row.total for row in attendance_rows)
            total_present = sum(row.present for row in attendance_rows)
            attendance_pct = round((total_present / total_classes) * 100, 2) if total_classes else 0

            avg_marks = round(
                sum(row.marks for row in marks_rows) / len(marks_rows), 2
            ) if marks_rows else 0

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

    return render_template("dashboard.html",
                           students=students,
                           attendance=attendance,
                           marks=marks,
                           rolls=rolls,
                           percentages=percentages,
                           top_performers=insights["top_performers"],
                           at_risk_students=insights["at_risk_students"],
                           selected_student=selected_student)


# ---------------- STUDENTS ----------------
@app.route("/students", methods=["GET", "POST"])
def students():
    if "user" not in session:
        return redirect("/")

    if request.method == "POST":
        roll = int(request.form["roll"])
        name = request.form["name"]
        dept = request.form["dept"]

        db.session.add(Student(roll_no=roll, name=name, dept=dept))
        db.session.commit()

        return redirect("/students")

    search_query = request.args.get("q", "").strip()
    dept_filter = request.args.get("dept", "").strip()

    query = Student.query
    if search_query:
        if search_query.isdigit():
            query = query.filter(Student.roll_no == int(search_query))
        else:
            query = query.filter(Student.name.ilike(f"%{search_query}%"))

    if dept_filter:
        query = query.filter(Student.dept == dept_filter)

    students_data = query.order_by(Student.roll_no.asc()).all()
    departments = [
        row[0] for row in db.session.query(Student.dept).distinct().order_by(Student.dept.asc()).all()
    ]

    return render_template(
        "students.html",
        students=students_data,
        search_query=search_query,
        dept_filter=dept_filter,
        departments=departments
    )


# delete student
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
    if "user" not in session:
        return redirect("/")

    if request.method == "POST":
        roll = int(request.form["roll"])
        total = int(request.form["total"])
        present = int(request.form["present"])

        db.session.add(Attendance(roll_no=roll, total=total, present=present))
        db.session.commit()

        return redirect("/attendance")

    data = Attendance.query.order_by(Attendance.id.desc()).all()
    total_classes = sum(r.total for r in data)
    total_present = sum(r.present for r in data)
    overall_percentage = round((total_present / total_classes) * 100, 2) if total_classes else 0
    low_attendance_count = sum(
        1 for r in data if r.total > 0 and ((r.present / r.total) * 100) < 75
    )

    return render_template(
        "attendance.html",
        data=data,
        overall_percentage=overall_percentage,
        low_attendance_count=low_attendance_count,
        total_attendance_rows=len(data)
    )


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
    if "user" not in session:
        return redirect("/")

    if request.method == "POST":
        roll = int(request.form["roll"])

        # Bulk mode: add multiple subjects for one student in a single submit.
        if request.form.get("bulk_mode") == "1":
            bulk_entries = request.form.get("bulk_entries", "").strip().splitlines()
            rows_to_add = []

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

                rows_to_add.append(Marks(roll_no=roll, subject=subject, marks=score))

            if rows_to_add:
                db.session.add_all(rows_to_add)
                db.session.commit()
        else:
            subject = request.form["subject"]
            marks_value = int(request.form["marks"])
            db.session.add(Marks(roll_no=roll, subject=subject, marks=marks_value))
            db.session.commit()

        return redirect("/marks")

    search_query = request.args.get("q", "").strip()
    query = Marks.query

    if search_query:
        if search_query.isdigit():
            query = query.filter(Marks.roll_no == int(search_query))
        else:
            query = query.filter(Marks.subject.ilike(f"%{search_query}%"))

    data = query.order_by(Marks.id.desc()).all()
    all_marks = [m.marks for m in data]
    avg_marks = round(sum(all_marks) / len(all_marks), 2) if all_marks else 0
    high_scorers = sum(1 for value in all_marks if value >= 90)
    subject_count = len({m.subject.strip().lower() for m in data if m.subject})

    return render_template(
        "marks.html",
        data=data,
        search_query=search_query,
        avg_marks=avg_marks,
        high_scorers=high_scorers,
        subject_count=subject_count,
        total_marks_rows=len(data)
    )


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


@app.route("/reports")
def reports():
    if "user" not in session:
        return redirect("/")

    insights = build_student_insights()

    total_students = len(insights["profiles"])
    total_at_risk = len([s for s in insights["profiles"] if s["risk_flags"]])
    avg_attendance = round(
        sum(s["attendance_pct"] for s in insights["profiles"]) / total_students, 2
    ) if total_students else 0
    avg_marks = round(
        sum(s["avg_marks"] for s in insights["profiles"]) / total_students, 2
    ) if total_students else 0

    return render_template(
        "reports.html",
        department_rows=insights["department_rows"],
        subject_rows=insights["subject_rows"],
        top_performers=insights["top_performers"],
        total_students=total_students,
        total_at_risk=total_at_risk,
        avg_attendance=avg_attendance,
        avg_marks=avg_marks
    )


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
    if "user" not in session:
        return redirect("/")

    rows = [(s.roll_no, s.name, s.dept) for s in Student.query.order_by(Student.roll_no.asc()).all()]
    return generate_csv("students.csv", ["Roll No", "Name", "Department"], rows)


@app.route("/export/attendance")
def export_attendance():
    if "user" not in session:
        return redirect("/")

    rows = [
        (a.id, a.roll_no, a.total, a.present, round((a.present / a.total) * 100, 2) if a.total else 0)
        for a in Attendance.query.order_by(Attendance.id.asc()).all()
    ]
    return generate_csv("attendance.csv", ["ID", "Roll No", "Total", "Present", "Percentage"], rows)


@app.route("/export/marks")
def export_marks():
    if "user" not in session:
        return redirect("/")

    rows = [(m.id, m.roll_no, m.subject, m.marks) for m in Marks.query.order_by(Marks.id.asc()).all()]
    return generate_csv("marks.csv", ["ID", "Roll No", "Subject", "Marks"], rows)


if __name__ == "__main__":
    app.run(debug=True)
