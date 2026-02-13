from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50))
    email = db.Column(db.String(120))
    password = db.Column(db.String(50))


class Student(db.Model):
    roll_no = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    dept = db.Column(db.String(50))


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    roll_no = db.Column(db.Integer)
    total = db.Column(db.Integer)
    present = db.Column(db.Integer)


class Marks(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    roll_no = db.Column(db.Integer)
    subject = db.Column(db.String(50))
    marks = db.Column(db.Integer)
