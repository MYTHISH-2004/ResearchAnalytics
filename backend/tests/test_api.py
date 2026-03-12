import unittest
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app import app, db, User, Student, Attendance, Marks, hash_password


class FacultyAnalyticsApiTests(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()
        with app.app_context():
            Marks.query.delete()
            Attendance.query.delete()
            Student.query.delete()
            user = User.query.filter_by(username="Mythish").first()
            if not user:
                user = User(username="Mythish", email="mythish.ad23@bitsathy.ac.in", password=hash_password("My1907"))
                db.session.add(user)
            else:
                user.email = "mythish.ad23@bitsathy.ac.in"
                user.password = hash_password("My1907")
            db.session.commit()

        login_response = self.client.post(
            "/api/login",
            json={"login_mode": "email", "email": "mythish.ad23@bitsathy.ac.in", "password": "My1907"}
        )
        payload = login_response.get_json()
        self.assertEqual(login_response.status_code, 200)
        self.token = payload["token"]
        self.auth_header = {"Authorization": f"Bearer {self.token}"}

    def test_health_endpoint(self):
        response = self.client.get("/healthz")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["status"], "ok")

    def test_students_search_filter_and_pagination(self):
        with app.app_context():
            db.session.add_all([
                Student(roll_no=1, name="Asha", dept="CSE"),
                Student(roll_no=2, name="Bala", dept="ECE"),
                Student(roll_no=3, name="Aneesh", dept="CSE"),
            ])
            db.session.commit()

        response = self.client.get("/api/students?q=A&dept=CSE&page=1&per_page=1", headers=self.auth_header)
        self.assertEqual(response.status_code, 200)
        payload = response.get_json()
        self.assertEqual(len(payload["students"]), 1)
        self.assertEqual(payload["pagination"]["total"], 2)
        self.assertEqual(payload["pagination"]["total_pages"], 2)

    def test_marks_and_attendance_endpoints(self):
        with app.app_context():
            db.session.add(Student(roll_no=101, name="Kavin", dept="IT"))
            db.session.commit()

        attendance_create = self.client.post(
            "/api/attendance",
            json={"roll": 101, "total": 20, "present": 18},
            headers=self.auth_header
        )
        self.assertEqual(attendance_create.status_code, 201)

        marks_create = self.client.post(
            "/api/marks",
            json={"roll": 101, "subject": "Maths", "marks": 91},
            headers=self.auth_header
        )
        self.assertEqual(marks_create.status_code, 201)

        attendance_list = self.client.get("/api/attendance?page=1&per_page=5", headers=self.auth_header)
        self.assertEqual(attendance_list.status_code, 200)
        self.assertGreaterEqual(attendance_list.get_json()["overall_percentage"], 0)

        marks_list = self.client.get("/api/marks?q=Maths&page=1&per_page=5", headers=self.auth_header)
        self.assertEqual(marks_list.status_code, 200)
        marks_payload = marks_list.get_json()
        self.assertEqual(marks_payload["subject_count"], 1)
        self.assertGreaterEqual(marks_payload["avg_marks"], 0)


if __name__ == "__main__":
    unittest.main()
