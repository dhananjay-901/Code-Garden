# rock paper scissor game
import random 
import string 

# List of words for the game
words = ["rock", "paper", "scissors"]
scorepc = 0
scoreuser = 0
m = int(input("best of 3 or 5: "))
for i in range(m):
    b = str(input("please enter your choice (r - rock, p - paper, s - scissor): "))
    # Select a random word from the list
    a = random.choice(words)
    print("user chose: ",b)
    print("pc chose: ",a)
    if b=="r" and a =="rock": 
        print("draw")
    elif b=="p" and a =="paper": 
        print("draw")
    elif b=="s" and a =="scissors": 
        print("draw")
    elif b=="r" and a=="paper":
        print("you lose")
        scorepc += 1
    elif b=="p" and a=="scissors":
        print("you lose")
        scorepc += 1
    elif b=="s" and a=="rock":
        print("you lose")
        scorepc += 1
    else:
        print("you win")
        scoreuser += 1
print ("score of pc is", scorepc)
print ("score of user is", scoreuser)
if scorepc>scoreuser:
    print("pc wins")
    print('WELL DONE!')
elif scorepc<scoreuser:
    print("user wins")
    print('BETTER LUCK NEXT TIME!')
else:
    print("draw")
