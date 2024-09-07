from flask import Flask, render_template, request, redirect, url_for, session
import psycopg2
from werkzeug.security import generate_password_hash, check_password_hash
import random
import csv
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# Connect to PostgreSQL
conn = psycopg2.connect("dbname=game_db user=your_user password=your_password")
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

# Load words from CSV file
Allwords = []
with open('/Users/vasanthgovindappa/Desktop/Phrasl/words4K.csv', newline='') as csvfile:
    csvreader = csv.reader(csvfile)
    for row in csvreader:
        Allwords.append(row[0])  # Assuming each row is a list with one element

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
    return render_template('leaderboard.html', leaderboard=leaderboard)

def update_user_points(username, points):
    cursor.execute('UPDATE users SET points = points + %s WHERE username = %s', (points, username))
    conn.commit()

def get_user_points(username):
    cursor.execute('SELECT points FROM users WHERE username = %s', (username,))
    return cursor.fetchone()[0]

if __name__ == '__main__':
    app.run(debug=True, port=5001)
