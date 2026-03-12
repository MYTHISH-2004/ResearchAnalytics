from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, index=True, nullable=False)
    email = db.Column(db.String(120), unique=True, index=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)


class Student(db.Model):
    roll_no = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), index=True, nullable=False)
    dept = db.Column(db.String(50), index=True, nullable=False)


class Attendance(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    roll_no = db.Column(db.Integer, index=True, nullable=False)
    total = db.Column(db.Integer, nullable=False)
    present = db.Column(db.Integer, nullable=False)


class Marks(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    roll_no = db.Column(db.Integer, index=True, nullable=False)
    subject = db.Column(db.String(50), index=True, nullable=False)
    marks = db.Column(db.Integer, index=True, nullable=False)
