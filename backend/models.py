from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.Text, nullable=False)
    resume_text = db.Column(db.Text)  # NEW - parsed text from resume
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    sessions = db.relationship("InterviewSession", backref="user", cascade="all, delete-orphan")

class InterviewSession(db.Model):
    __tablename__ = "interview_sessions"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    ended_at = db.Column(db.DateTime)

    questions = db.relationship("InterviewQuestion", backref="session", cascade="all, delete-orphan")

class InterviewQuestion(db.Model):
    __tablename__ = "interview_questions"
    id = db.Column(db.Integer, primary_key=True)
    session_id = db.Column(db.Integer, db.ForeignKey("interview_sessions.id", ondelete="CASCADE"), nullable=False)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text)
    score = db.Column(db.JSON)  # Store evaluation JSON
    flagged_script = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)


