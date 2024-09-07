from flask import Flask, render_template, request
import random
import csv

app = Flask(__name__)

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

@app.route('/', methods=['GET', 'POST'])
def index():
    global word, emptylist, guesses

    if request.method == 'POST':
        # Initialize an empty list to collect guesses
        guesses_list = []
        for i in range(len(word)):
            guess_key = f'guess_{i}'
            if guess_key in request.form:
                guess = request.form[guess_key].lower()
                guesses_list.append(guess)
        
        # Process the guesses_list as needed
        for guess in guesses_list:
            if guess in word:
                for i in range(len(word) - len(guess) + 1):
                    if word[i:i+len(guess)] == guess:
                        emptylist[i:i+len(guess)] = list(guess)
                message = f"Correct, {guess} is in the word"
                
            else:
                message = f"{guess} is not in the word"
                guesses -= 1

        # Check if the player has won or lost
        if ''.join(emptylist) == word:
            message = f"Congratulations! You got it"
            return render_template('index.html', word_tuples=list(enumerate(emptylist)), message=message, game_over=True)
        
        elif guesses == 0:
            message = f"Unlucky, the word was {word}"
            return render_template('index.html', word_tuples=list(enumerate(emptylist)), message=message, game_over=True)
        
        return render_template('index.html', word_tuples=list(enumerate(emptylist)), message=message, guesses=guesses)

    # Initialize a new game
    A = random.randint(0, len(Allwords) - 1)
    word = ''.join(Allwords[A]).lower()
    print(word)
    emptylist = ['_'] * len(word)
    guesses = 8
    return render_template('index.html', word_tuples=list(enumerate(emptylist)), guesses=guesses)

if __name__ == '__main__':
    app.run(debug=True, port=5001)