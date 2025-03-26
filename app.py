from flask import Flask,render_template, request, redirect, url_for, session, flash
from config import Config
from models import db, User, Subject,Chapter, Quiz, Question, Score
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField,TimeField, TextAreaField, SelectField, IntegerField, DateTimeField, FieldList, FormField
from wtforms.validators import DataRequired, Email, EqualTo, Length
from datetime import datetime
from flask_wtf.file import FileField, FileAllowed
import os
from werkzeug.utils import secure_filename
import werkzeug


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
        return render_template("dashboard.html", username=username)
        
    return render_template("index.html")

#login route
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        remember = request.form.get('remember') == 'on'
        user=User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            login_user(user,remember=remember)
            session['username'] = username
            session['first_name'] = user.first_name
            session['last_name'] = user.last_name
            session['is_admin']=user.is_admin
            flash("Login successful!", "success")
            if user.is_admin:
                
                return render_template("admin_dash.html", username=user.first_name+' '+user.last_name)
            else:
                
                return render_template("dashboard.html", username=user.first_name+' '+user.last_name)
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
    return render_template('dashboard.html')

#logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash("You have been logged out.","success")
    return redirect(url_for('login'))

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
    db.session.delete(quiz)
    db.session.commit()
    flash('Quiz deleted successfully!', 'success')
    return redirect(url_for('manage_quizzes', chapter_id=chapter_id))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin@quizmaster.com').first():
            admin = User(username='admin@quizmaster.com', first_name='Admin', last_name='User', is_admin=True)
            admin.set_password('123456')
            db.session.add(admin)
            db.session.commit()
    app.run(debug="true")
