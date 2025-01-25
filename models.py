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
    questions = db.relationship('Question', backref='quiz', lazy=True)


class Question(db.Model):
    __tablename__ = 'question'
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'), nullable=False)
    question_statement = db.Column(db.String(500), nullable=False)
    question_type = db.Column(db.String(10), nullable=False)  # MCQ, MSQ, TITA
    __mapper_args__ = {
        'polymorphic_identity': 'question',  # Base identifier
        'polymorphic_on': question_type     # Determines the subclass
    }


class MCQQuestion(Question):
    __tablename__ = 'mcq_question'
    id = db.Column(db.Integer, db.ForeignKey('question.id'), primary_key=True)
    option1 = db.Column(db.String(150), nullable=False)
    option2 = db.Column(db.String(150), nullable=False)
    option3 = db.Column(db.String(150), nullable=False)
    option4 = db.Column(db.String(150), nullable=False)
    correct_option = db.Column(db.Integer, nullable=False)
    __mapper_args__ = {
        'polymorphic_identity': 'MCQ'  # Identifier for this subclass
    }


class MSQQuestion(Question):
    __tablename__ = 'msq_question'
    id = db.Column(db.Integer, db.ForeignKey('question.id'), primary_key=True)
    option1 = db.Column(db.String(150), nullable=False)
    option2 = db.Column(db.String(150), nullable=False)
    option3 = db.Column(db.String(150), nullable=False)
    option4 = db.Column(db.String(150), nullable=False)
    correct_options = db.Column(db.String(150), nullable=False)  # Comma-separated values
    __mapper_args__ = {
        'polymorphic_identity': 'MSQ'
    }


class TITAQuestion(Question):
    __tablename__ = 'tita_question'
    id = db.Column(db.Integer, db.ForeignKey('question.id'), primary_key=True)
    correct_answer = db.Column(db.String(500), nullable=False)
    __mapper_args__ = {
        'polymorphic_identity': 'TITA'
    }



class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    quiz_id = db.Column(db.Integer, db.ForeignKey('quiz.id'))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    time_stamp_of_attempt = db.Column(db.DateTime)
    total_scored = db.Column(db.Integer)

with app.app_context():
    db.create_all()

