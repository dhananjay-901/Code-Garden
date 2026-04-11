import time 
import random 
def choose_word():
    words = ['hangman','mother','father','brother','family','daughter','riverbed','refrigator','gallery','generator','country','government','bridge','flowerbed','canon','window']
    return random.choice(words)

def word_display(word, guesses):
    display_word = ''
    for char in word:
        if char in  guesses:
            display_word+=char+''
        else:             
            display_word += '_'
    return display_word.strip()

def winningcondition(updated_word, turns):
    if '_' not in updated_word:
        return 1
    elif turns ==0:
        return 0

if __name__ == '__main__':
    name = input("what is your name: ") 
    print("hello" + name + ", time to play hangman")
    time.sleep(1)
    print("start guessing...\n")
    time.sleep(0.5)
    word = choose_word()
    turns = 3*len(word)
    #print("word selected for this round is'" + word +"'")
    #print("string displayed during the game is", word_display(word))
    guesses = ''
    while turns>0:
        print("\nyou have", turns,'guess remaining')
        print(word_display(word, guesses))
        guess = input("\nguess a character: ").lower()
        if guess in guesses:
            print("\nyou have already guessed that character")
            continue
        else: 
            guesses+=guess
        
        if guess not in word: 
            print("\nWrong, try again")
        
        updated_word = word_display(word, guesses)
        turns -=1
        flag = winningcondition(updated_word, turns)
        if flag ==0:
            print("\nYou Lose")
            print("The word was:", word)
            break
        elif flag ==1:
            print("\nYou Win")
            break
    else: 
        print("\nYou Lose")
        print("The word was:", word)
