from flask import Flask, render_template, request
import random
import csv

Allwords = []

with open('/Users/vasanthgovindappa/Desktop/Phrasl/words4K.csv', newline='') as csvfile:
    csvreader = csv.reader(csvfile)
    for row in csvreader:
        Allwords.append(row)

# Select a random word from the list
A = random.randint(0, len(Allwords) - 1)
word = ''.join(Allwords[A]).lower()
wordl = list(word)
print(word)


# Initialize the empty list with underscores
emptylist = ['_'] * len(word)

# Welcome message
print("Welcome to the game")
guesses = 10

# Game loop
while ''.join(emptylist) != word and guesses != 0:
    print(' '.join(emptylist))
    print(f"You have {guesses} guesses left")
    guess = input('Guess a letter or a phrase: ').lower()

    # Check if the guess is in the word
    if guess in word:
        for i in range(len(word) - len(guess) + 1):
            if word[i:i+len(guess)] == guess:
                emptylist[i:i+len(guess)] = list(guess)
                print(f"Correct, '{guess}' is in the word")
    else:
        print(f"'{guess}' is not in the word")

    guesses -= 1

# Check if the player has won or lost
if ''.join(emptylist) == word:
    print(' '.join(emptylist))
    print(f"Congratulations! You guessed the word: {word}")
else:
    print(f"Unlucky, the word was {word}")