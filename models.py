from flask_sqlalchemy import SQLAlchemy
from app import app

db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    role= db.Column(db.String(120), nullable=False)#admin, user, teacher
    full_name = db.Column(db.String(150))


class Subject(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(500))
    chapters=db.relationship('Chapter', backref='subject', lazy=True)


class Chapter(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150), nullable=False)
    description = db.Column(db.String(500))
    subject_id = db.Column(db.Integer, db.ForeignKey('subject.id'))
    quizzes=db.relationship('Quiz', backref='chapter', lazy=True)


class Quiz(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'))
    date_of_quiz = db.Column(db.Date)
    time_duration = db.Column(db.String(10))
    remarks = db.Column(db.String(500))
    questions=db.relationship('Question', backref='quiz', lazy=True)


class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'))
    question_statement = db.Column(db.String(500))
    question_type = db.Column(db.String(10), nullable=False)#MCQ, MSQ, TITA

class MCQQuestion(Question):
    option1 = db.Column(db.String(150), nullable=False)
    option2 = db.Column(db.String(150), nullable=False)
    option3 = db.Column(db.String(150), nullable=False)
    option4 = db.Column(db.String(150), nullable=False)
    correct_option = db.Column(db.Integer, nullable=False)
class MSQQuestion(Question):
    option1 = db.Column(db.String(150), nullable=False)
    option2 = db.Column(db.String(150), nullable=False)
    option3 = db.Column(db.String(150), nullable=False)
    option4 = db.Column(db.String(150), nullable=False)
    correct_options = db.Column(db.String(150), nullable=False)
class TITAQuestion(Question):
    correct_answer = db.Column(db.String(500), nullable=False)    


class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    time_stamp_of_attempt = db.Column(db.DateTime)
    total_scored = db.Column(db.Integer)

with app.app_context():
    db.create_all()