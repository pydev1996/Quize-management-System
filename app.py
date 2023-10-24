from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_sqlalchemy import SQLAlchemy
import easygui
app = Flask(__name__, template_folder='templates', static_url_path='/static')
app.secret_key = '034c426c843d013262dd0d4292ba9d55'  # Replace with a strong secret key

# Configure the SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quiz.db'  # Replace with your database file
db = SQLAlchemy(app)

class Question(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    question_text = db.Column(db.String(500), nullable=False)
    option1 = db.Column(db.String(100), nullable=False)
    option2 = db.Column(db.String(100), nullable=False)
    option3 = db.Column(db.String(100), nullable=False)
    correct_option = db.Column(db.Integer, nullable=False)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    scores = db.relationship('Score', backref='user', lazy=True)

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
class TimerStatus(db.Model):
    enabled = db.Column(db.Boolean, default=True, primary_key=True)


current_question_index = 0
score = 0
u=[]
@app.route('/index')
def index():
    global current_question_index
    question = Question.query.get(current_question_index + 1)
    timer_status = TimerStatus.query.first() 
    if question:
        current_question = question
        print(question.question_text)
        options = [question.option1, question.option2, question.option3]

        return render_template('quize.html', question=current_question, index=current_question_index,options=options,timer_status=timer_status)
    else:
        return render_template('result.html', score=score, total=current_question_index, username=session.get('username'))
    
from flask import request, jsonify

@app.route('/get_timer', methods=['GET'])
def get_timer():
    timer = session.get('timer', 0)

    # Decrease the timer by 1 second
    if timer > 0:
        timer -= 1
        session['timer'] = timer

    return jsonify(timer=timer)

from flask import request, redirect, url_for

@app.route('/update_timer_status', methods=['POST'])
def update_timer_status():
    timer_enabled = request.form.get('enableTimer')
    print(timer_enabled)
    # Update the timer status in the database
    timer_status = TimerStatus.query.first()
    if not timer_status:
        timer_status = TimerStatus()

    # Update the enabled attribute based on the form input
    timer_status.enabled = timer_enabled == 'on'

    # Add and commit the changes to the database
    db.session.add(timer_status)
    db.session.commit()

    return redirect(url_for('admin'))

@app.route('/check_answer', methods=['POST'])
def check_answer():
    global current_question_index, score
    user_answer = int(request.form['answer'])
    current_question = Question.query.get(current_question_index + 1)
    # username=session.get('username')
    # user=User.query.get(username)

    if current_question.correct_option == user_answer:
        score += 1

    current_question_index += 1
    username2=session.get('username')
    user2=User.query.filter_by(username=username2).all()
    #print(user2[0].id)
    user_id = user2[0].id  # Replace with the actual user ID
    score_record = Score(score=score, user_id=user_id)
    db.session.add(score_record)
    db.session.commit()

    return redirect(url_for('index'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username, password=password).first()
        #print(user)
        if user:
            scr=Score.query.filter_by(user_id=user.id).first()
            print(scr)
            if scr:
                easygui.msgbox('Quize already done for this user', 'error')
            else:
                session['user_id'] = user.id
                session['username'] = user.username
                return redirect(url_for('user_dashboard'))
        else:
            easygui.msgbox("Invalid credentials. Please try again.")
            flash('Invalid credentials. Please try again.', 'error')
    return render_template('login.html')
@app.route('/adminlogin', methods=['GET', 'POST'])
def adminlogin():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username=='Admin' and password=="Admin111":
            u.append(username)
            return redirect(url_for('admin'))
        else:
            flash('Invalid credentials. Please try again.', 'error')
    return render_template('adminlogin.html')
@app.route('/user_dashboard')
def user_dashboard():
    username = session.get('username')
    return render_template('user_dashboard.html', username=username)

@app.route('/quiz', methods=['GET', 'POST'])
def start_quiz():
    global current_question_index, score
    current_question_index = 0
    score = 0
    return redirect(url_for('index'))
@app.route('/add_question_form')
def add_question_form():
    return render_template('add_question.html')
@app.route('/add_question', methods=['POST'])
def add_question():
    if request.method == 'POST':
        question_text = request.form['question_text']
        option1 = request.form['option1']
        option2 = request.form['option2']
        option3 = request.form['option3']
        correct_option = int(request.form['correct_option'])

        # Create a new Question object and add it to the database
        new_question = Question(
            question_text=question_text,
            option1=option1,
            option2=option2,
            option3=option3,
            correct_option=correct_option
        )
        db.session.add(new_question)
        db.session.commit()

    return redirect(url_for('add_question_form'))  # Redirect to the main quiz page after adding the question
@app.route('/admin')
def admin():
    return render_template('admin.html')
from flask import render_template


@app.route('/show_scores')
def show_scores():
    users = User.query.all()  # Retrieve all users

    user_scores = {}
    
   
    for user in users:
        # Find the scores for the user
        scores = Score.query.filter_by(user_id=user.id).all()

        # Store the scores for this user
        user_scores[user.username] = [score.score for score in scores]

    return render_template('show_scores.html', user_scores=user_scores)

@app.route('/questions')
def display_questions():
    questions = Question.query.all()
    return render_template('questions.html', questions=questions)

@app.route('/update_question/<int:question_id>', methods=['GET', 'POST'])
def update_question(question_id):
    question = Question.query.get(question_id)

    if request.method == 'POST':
        # Update the question based on the form data
        question.question_text = request.form['question_text']
        question.option1 = request.form['option1']
        question.option2 = request.form['option2']
        question.option3 = request.form['option3']
        question.correct_option = int(request.form['correct_option'])
        db.session.commit()

        return redirect(url_for('display_questions'))

    return render_template('update_question.html', question=question)

@app.route('/delete_question/<int:question_id>')
def delete_question(question_id):
    question = Question.query.get(question_id)
    db.session.delete(question)
    db.session.commit()

    return redirect(url_for('display_questions'))

@app.route('/show_users')
def show_users():
    users = User.query.all()  # Retrieve all users

    return render_template('show_users.html', users=users)
@app.route('/delete_user/<int:user_id>', methods=['POST'])
def delete_user(user_id):
    user = User.query.get(user_id)

    if user:
        # First, delete the associated scores
        Score.query.filter_by(user_id=user_id).delete()

        # Then, delete the user
        db.session.delete(user)
        db.session.commit()

    return redirect(url_for('show_users'))

@app.route('/')
def home():
    

    return render_template('home.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
