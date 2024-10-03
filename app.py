from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash
import random
import csv
from flask_mail import Mail, Message

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Configure Flask-Mail
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USERNAME'] = 'vibhavgithub@gmail.com'  # SMTP server email
app.config['MAIL_PASSWORD'] = 'olfq iecl dqzv fpbg'  # SMTP server password
app.config['MAIL_DEFAULT_SENDER'] = 'your_email@gmail.com'  # Default sender email
app.config['MAIL_DEBUG'] = True
app.config['MAIL_SUPPRESS_SEND'] = False
app.config['TESTING'] = False
mail = Mail(app)

# Connect to PostgreSQL
conn = psycopg2.connect("dbname=game_db user=your_user password=your_password host=localhost")
cursor = conn.cursor()

# Create users table if it doesn't exist
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id SERIAL PRIMARY KEY,
        first_name VARCHAR(50),
        last_name VARCHAR(50),
        email VARCHAR(100) UNIQUE NOT NULL,
        password VARCHAR(255) NOT NULL,
        username VARCHAR(50) UNIQUE NOT NULL,
        points INTEGER DEFAULT 0
    );
''')
conn.commit()

# Check if 'reset_token' column exists and add it if not
cursor.execute("SELECT column_name FROM information_schema.columns WHERE table_name='users'")
columns = [row[0] for row in cursor.fetchall()]

if 'reset_token' not in columns:
    cursor.execute("ALTER TABLE users ADD COLUMN reset_token VARCHAR(255)")
    conn.commit()

# Load words from CSV file
Allwords = []
with open('/Users/vasanthgovindappa/Desktop/Phrasl/words4K.csv', newline='') as csvfile:
    csvreader = csv.reader(csvfile)
    for row in csvreader:
        Allwords.append(row[0])

# Initialize game variables
word = ''
emptylist = []
guesses = 8

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        first_name = request.form['first_name']
        last_name = request.form['last_name']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        username = request.form['username']

        cursor.execute('INSERT INTO users (first_name, last_name, email, password, username) VALUES (%s, %s, %s, %s, %s)',
                       (first_name, last_name, email, password, username))
        conn.commit()
        return redirect(url_for('login'))
    return render_template('signup.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        cursor.execute('SELECT * FROM users WHERE username = %s', (username,))
        user = cursor.fetchone()

        if user and check_password_hash(user[4], password):
            session['user_id'] = user[0]
            session['username'] = user[5]
            return redirect(url_for('index'))
        else:
            return 'Invalid credentials'
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    session.pop('username', None)
    return redirect(url_for('index'))

@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        cursor.execute('SELECT * FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()
        if user:
            token = generate_password_hash(email + str(random.random()))
            cursor.execute('UPDATE users SET reset_token = %s WHERE email = %s', (token, email))
            conn.commit()
            send_password_reset_email(email, user[5], token)  # Pass username to the email function
            return 'A password reset link has been sent to your email.'
        else:
            return 'Email not found.'
    return render_template('forgot_password.html')

@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if request.method == 'POST':
        new_password = generate_password_hash(request.form['password'])
        cursor.execute('SELECT email FROM users WHERE reset_token = %s', (token,))
        user = cursor.fetchone()
        if user:
            cursor.execute('UPDATE users SET password = %s, reset_token = NULL WHERE email = %s', (new_password, user[0]))
            conn.commit()
            return redirect(url_for('login'))
        else:
            return 'Invalid or expired token.'
    return render_template('reset_password.html')

@app.route('/forgot_username', methods=['GET', 'POST'])
def forgot_username():
    if request.method == 'POST':
        email = request.form['email']
        cursor.execute('SELECT username FROM users WHERE email = %s', (email,))
        user = cursor.fetchone()
        if user:
            send_username_email(email, user[0])
            return 'Your username has been sent to your email.'
        else:
            return 'Email not found.'
    return render_template('forgot_username.html')

@app.route('/', methods=['GET', 'POST'])
def index():
    global word, emptylist, guesses

    if 'username' not in session:
        return redirect(url_for('login'))

    if request.method == 'POST':
        guesses_list = []
        for i in range(len(word)):
            guess_key = f'guess_{i}'
            if guess_key in request.form:
                guess = request.form[guess_key].lower()
                guesses_list.append(guess)
        
        for guess in guesses_list:
            if guess in word:
                for i in range(len(word) - len(guess) + 1):
                    if word[i:i+len(guess)] == guess:
                        emptylist[i:i+len(guess)] = list(guess)
                message = f"Correct, {guess} is in the word"
            else:
                message = f"{guess} is not in the word"
                guesses -= 1

        if ''.join(emptylist) == word:
            update_user_points(session['username'], guesses)
            message = f"Congratulations! You got it. Your total points: {get_user_points(session['username'])}"
            return render_template('index.html', word_tuples=list(enumerate(emptylist)), message=message, game_over=True, points=get_user_points(session['username']))
        
        elif guesses == 0:
            message = f"Unlucky, the word was {word}. Your total points: {get_user_points(session['username'])}"
            return render_template('index.html', word_tuples=list(enumerate(emptylist)), message=message, game_over=True, points=get_user_points(session['username']))
        
        return render_template('index.html', word_tuples=list(enumerate(emptylist)), message=message, guesses=guesses, points=get_user_points(session['username']))

    A = random.randint(0, len(Allwords) - 1)
    word = ''.join(Allwords[A]).lower()
    print(word)
    emptylist = ['_'] * len(word)
    guesses = 8
    return render_template('index.html', word_tuples=list(enumerate(emptylist)), guesses=guesses, points=get_user_points(session['username']))

@app.route('/leaderboard')
def leaderboard():
    cursor.execute('SELECT username, points FROM users ORDER BY points DESC')
    leaderboard = cursor.fetchall()
    return render_template('leaderboard.html', leaderboard=leaderboard,)

def update_user_points(username, points):
    cursor.execute('UPDATE users SET points = points + %s WHERE username = %s', (points, username))
    conn.commit()

def get_user_points(username):
    cursor.execute('SELECT points FROM users WHERE username = %s', (username,))
    return cursor.fetchone()[0]

def send_password_reset_email(email, username, token):
    msg = Message('Password Reset Request', recipients=[email])
    msg.body = f"Hello {username}, a request has been received to reset your password. Please use the following link to reset your password: http://localhost:5001/reset_password/{token}"
    try:
        mail.send(msg)
        print(f"Password reset email sent to {email}")
    except Exception as e:
        print(f"Error sending password reset email to {email}: {e}")

def send_username_email(email, username):
    msg = Message('Your Username', recipients=[email])
    msg.body = f"Hello, your username is: {username}"
    try:
        mail.send(msg)
        print(f"Username recovery email sent to {email}")
    except Exception as e:
        print(f"Error sending username recovery email to {email}: {e}")

@app.context_processor
def every_context():
  return {'points': get_user_points(session['username'])}

if __name__ == '__main__':
    app.run(debug=True, port=5001)