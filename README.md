# MindMaze Quiz Application

MindMaze is a comprehensive web-based quiz platform built with Flask that enables administrators to create and manage educational content while allowing students to take quizzes and track their progress.

---

## 🚀 Features

### 🎓 Admin Features
- User management (block/unblock users)
- Subject management (create, edit, delete)
- Chapter management within subjects
- Quiz creation and management
- Question bank management
- Performance analytics dashboard
- View individual student performance

### 🧑‍🎓 Student Features
- Take quizzes with timer functionality
- View available and attempted quizzes
- Check quiz results and performance
- Personal performance analytics dashboard
- Change account password

---

## 🛠️ Tech Stack
- **Backend**: Flask (Python)
- **Database**: SQLAlchemy
- **Frontend**: HTML, CSS, JavaScript
- **Visualization**: Charts.js

---

## 📥 Installation & Setup

### 1️⃣ Clone the Repository
```bash
git clone https://github.com/22f2000074/Mind-Maze.git
cd Mind-Maze
```

### 2️⃣ Create a Virtual Environment & Activate It
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3️⃣ Install Dependencies
```bash
pip install -r requirements.txt
```

### 4️⃣ Set Up Configuration
Create a `config.py` file with the following content:
```python
from dotenv import load_dotenv
import os
load_dotenv()
class Config:
    SECRET_KEY = os.getenv("SECRET_KEY")
    SQLALCHEMY_DATABASE_URI = os.getenv("SQLALCHEMY_DATABASE_URI")
    SQLALCHEMY_TRACK_MODIFICATIONS = os.getenv("SQLALCHEMY_TRACK_MODIFICATIONS")
    UPLOAD_FOLDER='static/uploads'
    ALLOWED_EXTENSIONS=set(['png','jpg','jpeg'])
```

### 5️⃣ Run the Application
```bash
python app.py
```

### 6️⃣ Access the Application
- Open your browser and go to: `http://localhost:5000`
- Default admin login:
  - **Username**: `admin@mindmaze.com`
  - **Password**: `admin123`

---

## 📂 Application Structure
- **Models**: User, Subject, Chapter, Quiz, Question, Score
- **Forms**: SubjectForm, ChapterForm, QuizForm, QuestionForm

---

## 📸 Video Tutorial


🎯 *MindMaze – Engage, Learn, and Excel!*


