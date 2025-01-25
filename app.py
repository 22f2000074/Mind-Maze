from flask import Flask,render_template
from config import Config



app = Flask(__name__)
app.config.from_object(Config)

import models

@app.route('/')
def index():
    return render_template("index.html")
@app.route('/login')
def login():
    return render_template("login.html")
@app.route('/signup')
def signup():
    return render_template("signup.html")

if __name__ == "__main__":
    app.run(debug="true")
