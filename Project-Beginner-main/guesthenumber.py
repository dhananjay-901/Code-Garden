import math
import random 
a = (random.randint(1,100))
while True:
    b = int(input("Enter a number between 1 and 100: "))
    c = abs(b-a)
    if b == a:
        print("You guessed it right!")
        break
    elif a>b and c<=10:
        print("Warm!")
    elif a>b and c>10:
        print("Cold!")
    elif a<b and c<=10:
        print("Very Hot!")
    elif a<b and c>10:
        print("Cold!")
    else: 
        continue