from flask import Flask,render_template, request, redirect, url_for, session, flash
from config import Config
from models import db, User
from flask_login import LoginManager, login_user, logout_user, login_required, UserMixin, current_user

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

@app.route('/')
def index():
    if 'username' in session:
        first_name = session.get('first_name')
        last_name = session.get('last_name')    
        username=first_name+' '+last_name
        return render_template("dashboard.html", username= username)
    return render_template("index.html")
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        user=User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session['username'] = username
            session['first_name'] = user.first_name
            session['last_name'] = user.last_name
            if user.username == 'admin@quizmaster.com':
                flash("Login successful!", "success")
                return render_template("admin_dash.html", username=user.first_name+' '+user.last_name)
            else:
                flash("Login successful!", "success")
                return render_template("dashboard.html", username=user.first_name+' '+user.last_name)
        else:
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))
    return render_template("login.html")
@app.route('/signup', methods=['GET','POST'])
def signup():
    return render_template(url_for('signup'))

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.username != 'admin@quizmaster.com':
        flash('Access Denied', 'danger')
        return redirect(url_for('login.html'))
    return render_template('admin_dash.html')
@app.route('/dashboard')
@login_required
def user_dashboard():
    return render_template('dashboard.html')

@app.route('/logout')
@login_required
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(username='admin@quizmaster.com').first():
            admin = User(username='admin@quizmaster.com', first_name='Admin', last_name='User')
            admin.set_password('123456')
            db.session.add(admin)
            db.session.commit()
    app.run(debug="true")
    
