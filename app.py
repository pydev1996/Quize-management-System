from flask import Flask, render_template, request, redirect, url_for
from flask import Flask, render_template, request, redirect, url_for, session,flash



from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__, template_folder='templates')
app.secret_key = '034c426c843d013262dd0d4292ba9d55'  # Replace with a strong secret key

# Configure the SQLite database
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///quize.db'  # Replace 'your_database.db' with your database file
db = SQLAlchemy(app)

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(120), nullable=False)
    scores = db.relationship('Score', backref='user', lazy=True)

class Score(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    score = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

class Question:
    def __init__(self, question, options, correct_answer):
        self.question = question
        self.options = options
        self.correct_answer = correct_answer

    def check_answer(self, user_answer):
        return user_answer == self.correct_answer

questions = [
    Question("What is the capital of France?", ["London", "Berlin", "Paris"], 3),
    Question("What is 2 + 2?", ["3", "4", "5"], 2),
    Question("Which planet is known as the Red Planet?", ["Mars", "Venus", "Jupiter"], 1),
]

current_question_index = 0
score = 0

@app.route('/index')
def index():
    global current_question_index
    if current_question_index < len(questions):
        current_question = questions[current_question_index]
        return render_template('quize.html', question=current_question, index=current_question_index)
    else:
        return render_template('result.html', score=score, total=len(questions), username=session.get('username'))


@app.route('/check_answer', methods=['POST'])
def check_answer():
    global current_question_index, score
    try:
        user_answer = int(request.form['answer'])
    except:
        user_answer=0
    current_question = questions[current_question_index]

    if current_question.check_answer(user_answer):
        score += 1

    current_question_index += 1

    # Store the score for the current user (you can implement user tracking based on their login status)
    # Replace 'user_id' with the actual user ID once you implement user registration and login
    user_id = 1  # Replace with the actual user ID
    score_record = Score(score=score, user_id=user_id)
    db.session.add(score_record)
    db.session.commit()

    return redirect(url_for('index'))

@app.route('/', methods=['GET', 'POST'])
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
        if user:
            print(user.username)
            # Authentication successful, store user information in session
            session['user_id'] = user.id
            session['username'] = user.username  # Store the username in the session
            return redirect(url_for('user_dashboard'))
        else:
            # Authentication failed, provide error message
            flash('Invalid credentials. Please try again.', 'error')
    return render_template('login.html')
@app.route('/user_dashboard')
def user_dashboard():
    # Get the username from the session
    username = session.get('username')
    return render_template('user_dashboard.html', username=username)
@app.route('/quiz', methods=['GET', 'POST'])
def start_quiz():
    # Reset the quiz variables to start a new quiz
    global current_question_index, score
    current_question_index = 0
    score = 0
    return redirect(url_for('index'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)
