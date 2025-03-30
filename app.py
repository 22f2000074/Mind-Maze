from flask import Flask,render_template, request, redirect, url_for, session, flash, jsonify
from config import Config
from models import db, User, Subject,Chapter, Quiz, Question, Score
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField,TimeField, TextAreaField, SelectField, IntegerField, DateTimeField, FieldList, FormField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from datetime import datetime, timedelta
import time
from flask_wtf.file import FileField, FileAllowed
import os
from werkzeug.utils import secure_filename

from flask_cors import CORS

from flask import current_app


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)
    
    db.init_app(app)
    with app.app_context():
        db.create_all()
        

    return app

 

app=create_app()
login_manager = LoginManager(app)
login_manager.login_view = "login"
def allowed_files(filename):
    return '.'in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
#forms
class SubjectForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    image = FileField('Upload Image')
    submit = SubmitField('Save')

class ChapterForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    image = FileField('Upload Image')
    submit = SubmitField('Save')

class QuestionForm(FlaskForm):
    question_text = StringField("Question", validators=[DataRequired(), Length(min=5, max=500)])
    option1 = StringField("Option 1", validators=[DataRequired()])
    option2 = StringField("Option 2", validators=[DataRequired()])
    option3 = StringField("Option 3", validators=[DataRequired()])
    option4 = StringField("Option 4", validators=[DataRequired()])
    correct_option = SelectField("Correct Answer", choices=[('1', 'Option 1'), ('2', 'Option 2'), ('3', 'Option 3'), ('4', 'Option 4')], validators=[DataRequired()])
    marks = IntegerField("Marks", validators=[DataRequired()])

class QuizForm(FlaskForm):
    name = StringField('Quiz Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    duration = TimeField('Duration', format='%H:%M', validators=[DataRequired()])
    deadline = DateTimeField('Deadline', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    image = FileField('Upload Image')
    submit = SubmitField('Add Quiz')
class QuizeForm(FlaskForm):
    name = StringField('Quiz Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    duration = TimeField('Duration', format='%H:%M:%S', validators=[DataRequired()])
    deadline = DateTimeField('Deadline', format='%Y-%m-%dT%H:%M', validators=[DataRequired()])
    image = FileField('Upload Image')
    submit = SubmitField('Add Quiz')


#routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        username = f"{current_user.first_name} {current_user.last_name}"
        if current_user.is_admin:
            username = f"{current_user.first_name} {current_user.last_name}"
            return render_template("admin_dash.html", username=username)
        return render_template("user_dash.html", username=username)
        
    return render_template("index.html")

#login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    # If user is already logged in, redirect them
    if current_user.is_authenticated:
        if current_user.is_admin:
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('user_dashboard'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember') == 'on'
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            if hasattr(user, 'is_active') and not user.is_active:
                flash('Your account has been blocked. Please contact an administrator.', 'danger')
                return redirect(url_for('login'))
            
            # Login the user with the remember flag
            login_user(user, remember=remember)
            
            # Store user info in session
            session['username'] = username
            session['first_name'] = user.first_name
            session['last_name'] = user.last_name
            session['is_admin'] = user.is_admin
            
            flash("Login successful!", "success")
            
            # Get the page the user was trying to access before login
            next_page = request.args.get('next')
            
            # Redirect to appropriate dashboard
            if user.is_admin:
                return redirect(next_page or url_for('admin_dashboard'))
            else:
                return redirect(next_page or url_for('user_dashboard'))
        else:
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))
            
    return render_template("login.html")
#signup route
@app.route('/signup', methods=['GET','POST'])
def signup():
    if request.method == 'POST':
        if not User.query.filter_by(username=request.form.get('username')).first():
            user = User(username=request.form.get('username'), first_name=request.form.get('first_name'), last_name=request.form.get('last_name'))
            user.set_password(request.form.get('password'))
            db.session.add(user)
            db.session.commit()
            flash('Signup Successful', 'success')
            return render_template("login.html")
        flash("User Already Exists",'danger')
    return render_template('signup.html')

#admin dashboard
@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if not current_user.is_admin:
        flash('Access Denied', 'danger')
        return redirect(url_for('login'))
    return render_template('admin_dash.html')

#user dashboard
@app.route('/dashboard')
@login_required
def user_dashboard():
    return render_template('user_dash.html')

#logout
# Updated logout route that explicitly handles the remember me cookie
@app.route('/logout')
@login_required
def logout():
    # Get the user before we log them out
    user = current_user
    
    # Standard logout process
    logout_user()
    
    # Clear all session data
    session.clear()
    
    # Clear the "remember me" cookie if it exists
    response = redirect(url_for('index'))
    response.delete_cookie('remember_token')  # This is the default cookie name used by Flask-Login
    
    flash("You have been logged out.", "success")
    return response

@app.route('/admin/subjects', methods=['GET', 'POST'])
@login_required
def manage_subjects():
    if not current_user.is_admin:
        flash('Access Denied', 'danger')
        return redirect(url_for('login'))
    
    form = SubjectForm()
    
    if form.validate_on_submit():
        if not Subject.query.filter_by(name=form.name.data).first():
            name = form.name.data
            description = form.description.data
            image = form.image.data

            filename = None
            if image and allowed_files(image.filename):
                filename = secure_filename(image.filename)
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                subject = Subject(
                name=name,
                description=description,
                image_filename=filename)

                db.session.add(subject)
                db.session.commit()
            
                flash("Subject added successfully!", "success")
                return redirect(url_for('manage_subjects'))
            else:
                flash("Image extension not supported", "danger")
            return redirect(url_for('manage_subjects'))

            
        
        flash("Subject Already Exists", "danger")
    
    subjects = Subject.query.all()
    return render_template('manage_subjects.html', form=form, subjects=subjects)
#Edit subjects
@app.route('/admin/subjects/edit/<int:subject_id>', methods=['GET', 'POST'])
@login_required
def edit_subject(subject_id):
    if not current_user.is_admin:
        flash('Access Denied', 'danger')
        return redirect(url_for('login'))

    subject = Subject.query.get_or_404(subject_id)
    form = SubjectForm(obj=subject)

    if request.method == 'POST' and form.validate_on_submit():
        subject.name = form.name.data
        subject.description = form.description.data

        if form.image.data:
            # Delete old image if exists
            if subject.image_filename:
                old_image_path = os.path.join(current_app.root_path, 'static/uploads', subject.image_filename)
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)

            # Save new image
            filename = secure_filename(form.image.data.filename)
            filepath = os.path.join(current_app.root_path, 'static/uploads', filename)
            form.image.data.save(filepath)
            subject.image_filename = filename

        db.session.commit()
        flash('Subject updated successfully!', 'success')
        return redirect(url_for('manage_subjects'))

    return render_template('edit_subject.html', form=form, subject=subject)

#delete subject
@app.route('/admin/subjects/delete/<int:subject_id>', methods=['GET','POST'])
@login_required
def delete_subject(subject_id):
    if not current_user.is_admin:
        flash('Access Denied', 'danger')
        return redirect(url_for('manage_subjects'))

    subject = Subject.query.get_or_404(subject_id)

    # Delete image if it exists
    if subject.image_filename:
        image_path = os.path.join(current_app.root_path, 'static/uploads', subject.image_filename)
        if os.path.exists(image_path):
            os.remove(image_path)
    chapters=Chapter.query.filter_by(subject_id=subject_id).all()
    for chapter in chapters:
        delete_chapters(chapter.id)
    db.session.delete(subject)
    db.session.commit()

    flash('Subject deleted successfully!', 'success')
    return redirect(url_for('manage_subjects'))

#view chapter
@app.route('/admin/chapters/<int:subject_id>', methods=['GET', 'POST'])
@login_required
def manage_chapters(subject_id):
    if not current_user.is_admin:
        flash('Access Denied', 'danger')
        return redirect(url_for('login'))

    form = ChapterForm()
    
    if form.validate_on_submit():
        if not Chapter.query.filter_by(name=form.name.data).first():
            name = form.name.data
            description = form.description.data
            image = form.image.data

            filename = None
            if image and allowed_files(image.filename):
                filename = secure_filename(image.filename)
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                chapter = Chapter(
                name=name,
                description=description,
                image_filename=filename,
                subject_id=subject_id)

                db.session.add(chapter)
                db.session.commit()
            
                flash("Chapter added successfully!", "success")
                return redirect(url_for('manage_chapters',subject_id=subject_id))
            else:
                flash("Image extension not supported", "danger")
            return redirect(url_for('manage_chapters',subject_id=subject_id))

            
        
        flash("Chapter Already Exists", "danger")

    chapters = Chapter.query.filter_by(subject_id=subject_id).all()
    return render_template("manage_chapters.html", form=form, chapters=chapters, subject_id=subject_id)

#edit chapter
@app.route('/admin/chapters/edit/<int:chapter_id>', methods=['POST'])
@login_required
def edit_chapters(chapter_id):
    if not current_user.is_admin:
        flash('Access Denied', 'danger')
        return redirect(url_for('login'))
    chapter=Chapter.query.get_or_404(chapter_id)
    subject_id=chapter.subject_id
    form = ChapterForm(obj=chapter)
    
    

    if request.method == 'POST' and form.validate_on_submit():
        chapter.name = form.name.data
        chapter.description = form.description.data

        if form.image.data:
            if chapter.image_filename:
                old_image_path = os.path.join(current_app.root_path, 'static/uploads', chapter.image_filename)
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)

            filename = secure_filename(form.image.data.filename)
            filepath = os.path.join(current_app.root_path, 'static/uploads', filename)
            form.image.data.save(filepath)
            chapter.image_filename = filename

        db.session.commit()
        flash('Chapter updated successfully!', 'success')
        return redirect(url_for('manage_chapters',subject_id=subject_id))

    flash("Error updating chapter", "danger")
    return redirect(url_for('manage_chapters',subject_id=subject_id ))

#delete chapter
@app.route('/admin/chapters/delete/<int:chapter_id>', methods=['GET', 'POST'])
@login_required
def delete_chapters(chapter_id):
    if not current_user.is_admin:
        flash('Access Denied', 'danger')
        return redirect(url_for('login'))
    chapter=Chapter.query.get_or_404(chapter_id)
    subject_id=chapter.subject_id

    if chapter.image_filename:
        image_path = os.path.join(current_app.root_path, 'static/uploads', chapter.image_filename)
        if os.path.exists(image_path):
            os.remove(image_path)
    quizzes=Quiz.query.filter_by(chapter_id=chapter_id).all()
    for quiz in quizzes:
        delete_quizzes(quiz.id)
    db.session.delete(chapter)
    db.session.commit()
    flash('Chapter deleted successfully!', 'success')
    return redirect(url_for('manage_chapters', subject_id=subject_id))

#view Quiz
@app.route('/admin/quizzes/<int:chapter_id>', methods=['GET', 'POST'])
@login_required
def manage_quizzes(chapter_id):
    if not current_user.is_admin:
        flash('Access Denied', 'danger')
        return redirect(url_for('login'))

    form = QuizForm()
    
    if form.validate_on_submit():
        
        if not Quiz.query.filter_by(name=form.name.data).first():
            name = form.name.data
            description = form.description.data
            duration = form.duration.data
            

            deadline = form.deadline.data
            image = form.image.data

            filename = None
            if image and allowed_files(image.filename):
                filename = secure_filename(image.filename)
                image.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                quiz = Quiz(
                name=name,
                description=description,
                duration=duration,
                deadline=deadline,
                image_filename=filename,
                chapter_id=chapter_id)

                db.session.add(quiz)
                db.session.commit()
                
            
                flash("Quiz added successfully!", "success")
                return redirect(url_for('manage_quizzes',chapter_id=chapter_id))
            else:
                flash("Image extension not supported", "danger")
            return redirect(url_for('manage_quizzes',chapter_id=chapter_id))

            
        
        flash("Quiz Already Exists", "danger")
    quizzes = Quiz.query.filter_by(chapter_id=chapter_id).all()
    return render_template("manage_quizzes.html", form=form, quizzes=quizzes, chapter_id=chapter_id)
    



#edit Quiz
@app.route('/admin/quizzes/edit/<int:quiz_id>', methods=['POST'])
@login_required
def edit_quizzes(quiz_id):
    if not current_user.is_admin:
        flash('Access Denied', 'danger')
        return redirect(url_for('login'))
    quiz=Quiz.query.get_or_404(quiz_id)
    chapter_id=quiz.chapter_id
    form = QuizeForm()
    
    

    if request.method == 'POST' and form.validate_on_submit():
        quiz.name = form.name.data
        quiz.description = form.description.data
        
        quiz.duration = form.duration.data
        quiz.deadline = form.deadline.data
        
        if form.image.data:
            if quiz.image_filename:
                old_image_path = os.path.join(current_app.root_path, 'static/uploads', quiz.image_filename)
                if os.path.exists(old_image_path):
                    os.remove(old_image_path)

            filename = secure_filename(form.image.data.filename)
            filepath = os.path.join(current_app.root_path, 'static/uploads', filename)
            form.image.data.save(filepath)
            quiz.image_filename = filename
        print(form.data)
        db.session.commit()
        flash('Quiz updated successfully!', 'success')
        return redirect(url_for('manage_quizzes',chapter_id=chapter_id))
    print(form.errors)
    flash("Error updating quiz", "danger")
    return redirect(url_for('manage_quizzes',chapter_id=chapter_id))

#delete Quiz
@app.route('/admin/quizzes/delete/<int:quiz_id>', methods=[ 'GET','POST'])
@login_required
def delete_quizzes(quiz_id):
    if not current_user.is_admin:
        flash('Access Denied', 'danger')
        return redirect(url_for('login'))
    quiz=Quiz.query.get_or_404(quiz_id)
    chapter_id=quiz.chapter_id

    if quiz.image_filename and Quiz.query.filter(Quiz.image_filename == quiz.image_filename, Quiz.id != quiz_id).first() is None:
        # No other quiz is using this image, so we can delete it
        image_path = os.path.join("static/uploads", quiz.image_filename)
        if os.path.exists(image_path):
            os.remove(image_path)
    questions=Question.query.filter_by(quiz_id=quiz_id).all()
    for question in questions:
        delete_question(question.id)
    db.session.delete(quiz)
    db.session.commit()
    flash('Quiz deleted successfully!', 'success')
    return redirect(url_for('manage_quizzes', chapter_id=chapter_id))

@app.route('/admin/questions/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
def manage_questions(quiz_id):
    if not current_user.is_admin:
        flash('Access Denied', 'danger')
        return redirect(url_for('login'))
    
    quiz = Quiz.query.get_or_404(quiz_id)
    chapter = Chapter.query.get_or_404(quiz.chapter_id)
    form = QuestionForm()

    if form.validate_on_submit():
        question_id = request.form.get("question_id")
        
        if question_id:  # If editing
            question = Question.query.get(question_id)
            question.question_text = form.question_text.data
            question.option1 = form.option1.data
            question.option2 = form.option2.data
            question.option3 = form.option3.data
            question.option4 = form.option4.data
            question.correct_option = form.correct_option.data
            question.marks = form.marks.data
        else:  # If adding
            question = Question(question_text=form.question_text.data,
                                option1=form.option1.data,
                                option2=form.option2.data,
                                option3=form.option3.data,
                                option4=form.option4.data,
                                correct_option=form.correct_option.data,
                                marks=form.marks.data,
                                quiz_id=quiz_id)
        db.session.add(question)
        
        db.session.commit()
        flash("Question saved successfully!", "success")
        return redirect(url_for('manage_questions', quiz_id=quiz_id))

    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    return render_template("add_question.html", form=form, questions=questions, quiz_id=quiz_id, quiz=quiz, chapter=chapter)

#delete
@app.route('/admin/question/delete/<int:question_id>', methods=['POST'])
@login_required
def delete_question(question_id):
    question = Question.query.get_or_404(question_id)
    db.session.delete(question)
    db.session.commit()
    flash("Question deleted successfully!", "success")
    return redirect(url_for('manage_questions', quiz_id=question.quiz_id))

#User Management
@app.route('/admin/users')
@login_required
def manage_users():
    if not current_user.is_admin:
        flash('Access Denied', 'danger')
        return redirect(url_for('login'))
    
    # Get all non-admin users with their scores
    users = User.query.filter_by(is_admin=False).all()
    return render_template('manage_users.html', users=users)

@app.route('/admin/users/block/<int:user_id>')
@login_required
def block_user(user_id):
    if not current_user.is_admin:
        flash('Access Denied', 'danger')
        return redirect(url_for('login'))
    
    user = User.query.get_or_404(user_id)
    user.is_active = False
    db.session.commit()
    flash(f'User {user.username} has been blocked', 'success')
    return redirect(url_for('manage_users'))

@app.route('/admin/users/unblock/<int:user_id>')
@login_required
def unblock_user(user_id):
    if not current_user.is_admin:
        flash('Access Denied', 'danger')
        return redirect(url_for('login'))
    
    user = User.query.get_or_404(user_id)
    user.is_active = True
    db.session.commit()
    flash(f'User {user.username} has been unblocked', 'success')
    return redirect(url_for('manage_users'))
@app.route('/available-quizzes')
@login_required
def available_quizzes():
    # Get all quizzes
    quizzes = Quiz.query.all()
    
    # Get already attempted quizzes with their score IDs
    completed_scores = {}
    user_scores = Score.query.filter_by(user_id=current_user.id).all()
    
    for score in user_scores:
        # If there are multiple attempts, this will keep the most recent one
        completed_scores[score.quiz_id] = score.id
    
    # Get just the quiz IDs for simple checking
    attempted_quiz_ids = list(completed_scores.keys())
    
    return render_template('available_quizzes.html', 
                          quizzes=quizzes, 
                          attempted_quiz_ids=attempted_quiz_ids,
                          completed_scores=completed_scores)
@app.route('/attempted-quizzes', methods=['GET'])
@login_required
def attempted_quizzes():
    # Get all scores for the current user
    scores = Score.query.filter_by(user_id=current_user.id).order_by(Score.id.desc()).all()
    
    # Create a list to hold all the data we need for the template
    attempted_quizzes = []
    
    for score in scores:
        # Get the quiz details
        quiz = Quiz.query.get(score.quiz_id)
        
        if quiz:  # Make sure the quiz still exists
            # Get chapter and subject
            chapter = Chapter.query.get(quiz.chapter_id)
            subject = Subject.query.get(chapter.subject_id) if chapter else None
            
            # Get total possible marks
            questions = Question.query.filter_by(quiz_id=quiz.id).all()
            total_marks = sum(q.marks for q in questions)
            
            # Prepare the data
            quiz_data = {
                'score_id': score.id,
                'score_value': score.total_scored,
                'created_at': getattr(score, 'created_at', datetime.now()),
                'quiz_name': quiz.name,
                'chapter_name': chapter.name if chapter else "Unknown",
                'subject_name': subject.name if subject else "Unknown",
                'total_marks': total_marks
            }
            
            attempted_quizzes.append(quiz_data)
    
    # Pass the list to the template
    return render_template('attempted_quizzes.html', scores=attempted_quizzes)


@app.route('/attempt-quiz/<int:quiz_id>', methods=['GET', 'POST'])
@login_required
def attempt_quiz(quiz_id):
    # Check if user has already attempted this quiz
    previous_attempt = Score.query.filter_by(user_id=current_user.id, quiz_id=quiz_id).first()
    
    if previous_attempt:
        flash('You have already attempted this quiz. You cannot take it again.', 'warning')
        return redirect(url_for('available_quizzes'))
    
    # Rest of your existing code...
    
    # Fetch the quiz with all questions
    quiz = Quiz.query.get_or_404(quiz_id)
    
    # Check if quiz is available
    if quiz.is_expired():
        flash('This quiz is no longer available.', 'danger')
        return redirect(url_for('available_quizzes'))
    
    # Calculate time remaining
    now = datetime.now()
    time_to_deadline = quiz.deadline - now
    
    # Convert quiz duration from Time to timedelta
    duration_parts = str(quiz.duration).split(':')
    quiz_duration = timedelta(
        hours=int(duration_parts[0]),
        minutes=int(duration_parts[1]),
        seconds=int(duration_parts[2]) if len(duration_parts) > 2 else 0
    )
    
    # Use the smaller of the two: quiz duration or time to deadline
    if time_to_deadline < quiz_duration:
        allowed_time = time_to_deadline
    else:
        allowed_time = quiz_duration
    
    # Store the quiz end time in the session
    end_time = now + allowed_time
    session['quiz_end_time'] = end_time.timestamp()
    
    # Format the time for display
    total_seconds = int(allowed_time.total_seconds())
    hours = total_seconds // 3600
    minutes = (total_seconds % 3600) // 60
    seconds = total_seconds % 60
    formatted_time = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    return render_template('attempt_quiz.html', quiz=quiz, formatted_time=formatted_time)

@app.route('/check-time')
@login_required
def check_time():
    if 'quiz_end_time' in session:
        current_time = time.time()
        end_time = session.get('quiz_end_time')
        
        if current_time >= end_time:
            # Time is up
            return {"status": "expired"}
        else:
            # Calculate remaining time
            remaining = end_time - current_time
            hours = int(remaining // 3600)
            minutes = int((remaining % 3600) // 60)
            seconds = int(remaining % 60)
            formatted = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
            
            return {"status": "active", "remaining": formatted}
    
    return {"status": "no_session"}

@app.route('/submit-quiz/<int:quiz_id>', methods=['POST'])
@login_required
def submit_quiz(quiz_id):
    # Check if time expired
    if 'quiz_end_time' in session:
        if time.time() > session.get('quiz_end_time'):
            flash('Time expired. Your quiz has been submitted automatically.', 'warning')
    
    # Process the quiz submission as before
    quiz = Quiz.query.get_or_404(quiz_id)
    total_score = 0
    
    # Get all questions for this quiz
    questions = Question.query.filter_by(quiz_id=quiz_id).all()
    
    # Check each answer
    for question in questions:
        selected_option = request.form.get(f'answer_{question.id}')
        
        if selected_option and int(selected_option) == question.correct_option:
            total_score += question.marks
    
    # Save the score
    score = Score(
        quiz_id=quiz_id,
        user_id=current_user.id,
        total_scored=total_score
    )
    db.session.add(score)
    db.session.commit()
    
    # Clear the quiz session data
    session.pop('quiz_end_time', None)
    
    flash(f'Quiz submitted successfully! Your score: {total_score}', 'success')
    return redirect(url_for('quiz_results', score_id=score.id))
@app.route('/quiz-results/<int:score_id>')
@login_required
def quiz_results(score_id):
    # Get the score
    score = Score.query.get_or_404(score_id)
    
    # Ensure the score belongs to the current user
    if score.user_id != current_user.id:
        flash("You don't have permission to view this result", "danger")
        return redirect(url_for('attempted_quizzes'))
    
    # Get the quiz
    quiz = Quiz.query.get_or_404(score.quiz_id)
    
    # Get the questions
    questions = Question.query.filter_by(quiz_id=quiz.id).all()
    
    # Calculate total possible marks
    total_marks = sum(q.marks for q in questions)
    
    # Add a created_at attribute if it doesn't exist
    if not hasattr(score, 'created_at'):
        score.created_at = datetime.now()
    
    
    
    return render_template('quiz_results.html', 
                          score=score, 
                          quiz=quiz,
                          questions=questions,
                          total_marks=total_marks,
                          )


# This is the only endpoint used in the performance dashboard

# Update the api_get_user_scores route in app.py to handle admin requests for other users' scores
# Add this new API endpoint to your app.py file
@app.route('/api/admin/student-scores/<int:user_id>', methods=['GET'])
@login_required
def api_admin_student_scores(user_id):
    """Fetch scores for a specific student (admin only)"""
    if not current_user.is_admin:
        return jsonify({"error": "Unauthorized access"}), 403
    
    user = User.query.get_or_404(user_id)
    scores = Score.query.filter_by(user_id=user.id).all()
    result = []
    
    for score in scores:
        # Get the quiz
        quiz = Quiz.query.get(score.quiz_id)
        
        # Get chapter and subject
        chapter = None
        subject = None
        
        if quiz:
            chapter = Chapter.query.get(quiz.chapter_id)
            if chapter:
                subject = Subject.query.get(chapter.subject_id)
        
        # Get total possible marks
        questions = Question.query.filter_by(quiz_id=score.quiz_id).all()
        total_marks = sum(q.marks for q in questions) if questions else 0
        
        # Calculate percentage
        percentage = round((score.total_scored / total_marks * 100), 2) if total_marks > 0 else 0
        
        score_data = {
            'id': score.id,
            'quiz_id': score.quiz_id,
            'quiz_name': quiz.name if quiz else "Unknown",
            'chapter_name': chapter.name if chapter else "Unknown",
            'subject_name': subject.name if subject else "Unknown",
            'score': score.total_scored,
            'total_marks': total_marks,
            'percentage': percentage,
            'created_at': score.created_at.isoformat()
        }
        
        result.append(score_data)
    
    return jsonify(result)

# Keep your original api_get_user_scores route unchanged
@app.route('/api/scores', methods=['GET'])
@login_required
def api_get_user_scores():
    """Fetch all scores for the current user"""
    scores = Score.query.filter_by(user_id=current_user.id).all()
    result = []
    
    for score in scores:
        # Get the quiz
        quiz = Quiz.query.get(score.quiz_id)
        
        # Get chapter and subject
        chapter = None
        subject = None
        
        if quiz:
            chapter = Chapter.query.get(quiz.chapter_id)
            if chapter:
                subject = Subject.query.get(chapter.subject_id)
        
        # Get total possible marks
        questions = Question.query.filter_by(quiz_id=score.quiz_id).all()
        total_marks = sum(q.marks for q in questions) if questions else 0
        
        # Calculate percentage
        percentage = round((score.total_scored / total_marks * 100), 2) if total_marks > 0 else 0
        
        score_data = {
            'id': score.id,
            'quiz_id': score.quiz_id,
            'quiz_name': quiz.name if quiz else "Unknown",
            'chapter_name': chapter.name if chapter else "Unknown",
            'subject_name': subject.name if subject else "Unknown",
            # Important: The frontend expects 'score', not 'total_scored'
            'score': score.total_scored,
            'total_marks': total_marks,
            'percentage': percentage,  # This field is critical for the visualizations
            'created_at': score.created_at.isoformat()
        }
        
        result.append(score_data)
    
    return jsonify(result)
#----------------------------------------
# Admin API Endpoints
#----------------------------------------

@app.route('/api/admin/users', methods=['GET'])
@login_required
def api_get_users():
    """Fetch all users (admin only)"""
    if not current_user.is_admin:
        return jsonify({"error": "Unauthorized access"}), 403
    
    users = User.query.filter_by(is_admin=False).all()
    result = []
    
    for user in users:
        # Get scores for this user
        user_scores = Score.query.filter_by(user_id=user.id).all()
        
        # Calculate statistics
        total_quizzes_attempted = len(user_scores)
        total_score = sum(score.total_scored for score in user_scores)
        
        # Format scores data
        scores_data = []
        for score in user_scores:
            quiz = Quiz.query.get(score.quiz_id)
            scores_data.append({
                'id': score.id,
                'quiz_id': score.quiz_id,
                'quiz_name': quiz.name if quiz else "Unknown",
                'score': score.total_scored,
                'created_at': score.created_at.isoformat()
            })
        
        user_data = {
            'id': user.id,
            'username': user.username,
            'name': f"{user.first_name} {user.last_name}",
            'is_active': user.is_active,
            'quizzes_attempted': total_quizzes_attempted,
            'total_score': total_score,
            'scores': scores_data
        }
        
        result.append(user_data)
    
    return jsonify(result)

@app.route('/api/admin/user/<int:user_id>', methods=['GET'])
@login_required
def api_get_user(user_id):
    """Fetch a specific user by ID (admin only)"""
    if not current_user.is_admin:
        return jsonify({"error": "Unauthorized access"}), 403
    
    user = User.query.get_or_404(user_id)
    
    # Get scores for this user
    user_scores = Score.query.filter_by(user_id=user.id).all()
    
    # Calculate statistics
    total_quizzes_attempted = len(user_scores)
    total_score = sum(score.total_scored for score in user_scores)
    
    # Format scores data
    scores_data = []
    for score in user_scores:
        quiz = Quiz.query.get(score.quiz_id)
        scores_data.append({
            'id': score.id,
            'quiz_id': score.quiz_id,
            'quiz_name': quiz.name if quiz else "Unknown",
            'score': score.total_scored,
            'created_at': score.created_at.isoformat()
        })
    
    result = {
        'id': user.id,
        'username': user.username,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'name': f"{user.first_name} {user.last_name}",
        'is_active': user.is_active,
        'quizzes_attempted': total_quizzes_attempted,
        'total_score': total_score,
        'scores': scores_data
    }
    
    return jsonify(result)

# Add this route to your app.py file
@app.route('/admin/analytics')
@login_required
def admin_analytics():
    if not current_user.is_admin:
        flash('Access Denied', 'danger')
        return redirect(url_for('login'))
    
    # Get subjects data
    subjects_data = []
    for subject in Subject.query.all():
        chapters = Chapter.query.filter_by(subject_id=subject.id).all()
        chapters_count = len(chapters)
        
        quizzes_count = 0
        total_score_percentage = 0
        total_attempts = 0
        students_set = set()
        
        for chapter in chapters:
            chapter_quizzes = Quiz.query.filter_by(chapter_id=chapter.id).all()
            quizzes_count += len(chapter_quizzes)
            
            for quiz in chapter_quizzes:
                scores = Score.query.filter_by(quiz_id=quiz.id).all()
                questions = Question.query.filter_by(quiz_id=quiz.id).all()
                total_marks = sum(q.marks for q in questions) if questions else 0
                
                for score in scores:
                    if total_marks > 0:
                        total_score_percentage += (score.total_scored / total_marks) * 100
                        total_attempts += 1
                        students_set.add(score.user_id)
        
        avg_score = round(total_score_percentage / total_attempts, 1) if total_attempts > 0 else 0
        
        subjects_data.append({
            'name': subject.name,
            'description': subject.description or "",
            'chapters_count': chapters_count,
            'quizzes_count': quizzes_count,
            'students_count': len(students_set),
            'avg_score': avg_score
        })
    
    # Get chapters data
    chapters_data = []
    for chapter in Chapter.query.all():
        subject = Subject.query.get(chapter.subject_id)
        quizzes = Quiz.query.filter_by(chapter_id=chapter.id).all()
        
        total_score_percentage = 0
        total_attempts = 0
        students_set = set()
        
        for quiz in quizzes:
            scores = Score.query.filter_by(quiz_id=quiz.id).all()
            questions = Question.query.filter_by(quiz_id=quiz.id).all()
            total_marks = sum(q.marks for q in questions) if questions else 0
            
            for score in scores:
                if total_marks > 0:
                    total_score_percentage += (score.total_scored / total_marks) * 100
                    total_attempts += 1
                    students_set.add(score.user_id)
        
        avg_score = round(total_score_percentage / total_attempts, 1) if total_attempts > 0 else 0
        
        chapters_data.append({
            'name': chapter.name,
            'subject_name': subject.name if subject else "Unknown",
            'quizzes_count': len(quizzes),
            'students_count': len(students_set),
            'avg_score': avg_score
        })
    
    # Get quizzes data and chart data
    quizzes_data = []
    quiz_names = []
    quiz_scores = []
    
    for quiz in Quiz.query.all():
        chapter = Chapter.query.get(quiz.chapter_id)
        subject = Subject.query.get(chapter.subject_id) if chapter else None
        
        questions = Question.query.filter_by(quiz_id=quiz.id).all()
        questions_count = len(questions)
        total_marks = sum(q.marks for q in questions) if questions else 0
        
        scores = Score.query.filter_by(quiz_id=quiz.id).all()
        total_score = 0
        
        for score in scores:
            if total_marks > 0:
                total_score += (score.total_scored / total_marks) * 100
        
        avg_score = round(total_score / len(scores), 1) if scores and total_marks > 0 else 0
        
        quizzes_data.append({
            'name': quiz.name,
            'chapter_name': chapter.name if chapter else "Unknown",
            'subject_name': subject.name if subject else "Unknown",
            'questions_count': questions_count,
            'students_count': len(scores),
            'avg_score': avg_score,
            'deadline': quiz.deadline
        })
        
        # Add to chart data if there were attempts
        if scores and total_marks > 0:
            quiz_names.append(quiz.name)
            quiz_scores.append(avg_score)
    
    # Get student performance data
    student_names = []
    student_scores = []
    
    for user in User.query.filter_by(is_admin=False).all():
        scores = Score.query.filter_by(user_id=user.id).all()
        
        if scores:
            total_percentage = 0
            valid_scores = 0
            
            for score in scores:
                quiz = Quiz.query.get(score.quiz_id)
                questions = Question.query.filter_by(quiz_id=quiz.id).all()
                total_marks = sum(q.marks for q in questions) if questions else 0
                
                if total_marks > 0:
                    total_percentage += (score.total_scored / total_marks) * 100
                    valid_scores += 1
            
            if valid_scores > 0:
                avg_score = round(total_percentage / valid_scores, 1)
                student_names.append(f"{user.first_name} {user.last_name}")
                student_scores.append(avg_score)
    
    # Limit chart data to top 10 for readability
    if len(quiz_names) > 10:
        quiz_names = quiz_names[:10]
        quiz_scores = quiz_scores[:10]
    
    if len(student_names) > 10:
        student_names = student_names[:10]
        student_scores = student_scores[:10]
    
    return render_template('admin_analytics.html',
                          subjects=subjects_data,
                          chapters=chapters_data,
                          quizzes=quizzes_data,
                          quiz_names=quiz_names,
                          quiz_scores=quiz_scores,
                          student_names=student_names,
                          student_scores=student_scores)


@app.route('/admin/student-performance/<int:user_id>')
@login_required
def admin_student_performance(user_id):
    if not current_user.is_admin:
        flash('Access Denied', 'danger')
        return redirect(url_for('login'))
    
    user = User.query.get_or_404(user_id)
    
    return render_template('user_analytics.html', 
                          username=f"{user.first_name} {user.last_name}",
                          user_id=user.id,
                          viewing_as_admin=True)


@app.route('/my-performance')
@login_required
def user_performance():
    if not current_user.is_authenticated:
        return redirect(url_for('login'))
    return render_template('user_analytics.html', 
                          username=f"{current_user.first_name} {current_user.last_name}",
                          user_id=current_user.id,
                          viewing_as_admin=False)
@app.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    
    if request.method == 'POST':
        current_password = request.form.get('current_password')
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')
        
        # Check if current password is correct
        if not current_user.check_password(current_password):
            flash('Current password is incorrect', 'danger')
            return redirect(url_for('settings'))
        
        # Check if new passwords match
        if new_password != confirm_password:
            flash('New passwords do not match', 'danger')
            return redirect(url_for('settings'))
        
        # Update the password
        current_user.set_password(new_password)
        db.session.commit()
        
        flash('Password updated successfully', 'success')
        return redirect(url_for('settings'))
    
    return render_template('settings.html')

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin@mindmaze.com').first():
            admin = User(username='admin@mindmaze.com', first_name='Admin', last_name='User', is_admin=True)
            admin.set_password('admin123')
            db.session.add(admin)
            db.session.commit()
    app.run(debug="true")
