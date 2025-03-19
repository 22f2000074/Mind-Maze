from flask import Flask,render_template, request, redirect, url_for, session, flash
from config import Config
from models import db, User, Subject,Chapter, Quiz, Question, Score
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, TextAreaField, SelectField, IntegerField
from wtforms.validators import DataRequired, Email, EqualTo
from datetime import datetime
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


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
#forms
class SubjectForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    submit = SubmitField('Save')

class ChapterForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    description = TextAreaField('Description', validators=[DataRequired()])
    subject_id = SelectField('Subject', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save')

class QuizForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired()])
    chapter_id = SelectField('Chapter', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save')

class QuestionForm(FlaskForm):
    statement = TextAreaField('Question Statement', validators=[DataRequired()])
    option1 = StringField('Option 1', validators=[DataRequired()])
    option2 = StringField('Option 2', validators=[DataRequired()])
    option3 = StringField('Option 3', validators=[DataRequired()])
    option4 = StringField('Option 4', validators=[DataRequired()])
    correct_option = IntegerField('Correct Option (1-4)', validators=[DataRequired()])
    quiz_id = SelectField('Quiz', coerce=int, validators=[DataRequired()])
    submit = SubmitField('Save')

#routes
@app.route('/')
def index():
    if current_user.is_authenticated:
        username = f"{current_user.first_name} {current_user.last_name}"
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

@app.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash("You have been logged out.","success")
    return redirect(url_for('login'))

#view Subject
@app.route('/admin/subjects', methods=['GET', 'POST'])
@login_required
def manage_subjects():
    if not current_user.is_admin:
        flash('Access Denied', 'danger')
        return redirect(url_for('login'))
    
    form = SubjectForm()
    
    if form.validate_on_submit():
        if not Subject.query.filter_by(name=form.name.data).first():
            subject = Subject(name=form.name.data, description=form.description.data)
            db.session.add(subject)
            db.session.commit()
            flash("Subject added successfully!", "success")
            return redirect(url_for('manage_subjects'))
        flash("Subject Already Exists", "danger")
    
    subjects = Subject.query.all()
    
    return render_template('manage_subjects.html', form=form, subjects=subjects)
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin@quizmaster.com').first():
            admin = User(username='admin@quizmaster.com', first_name='Admin', last_name='User', is_admin=True)
            admin.set_password('123456')
            db.session.add(admin)
            db.session.commit()
    app.run(debug="true")
