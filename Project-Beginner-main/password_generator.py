import random
import string 

a = int(input("please enter the number of alphabets you want in password: "))
password = ""
for i in range(a):    
    random_letter = random.choice(string.ascii_letters)
    #print(random_letter)
    password += random_letter
b = int(input("how many special characters you want in password (max 3): "))
for i in range(b):
    random_letter1 = random.choice(string.punctuation) 
    password += random_letter1
c = int(input("how many numbers you want in password (max 4): "))
for i in range(c):
    random_letter2 = random.choice(string.digits)
    password += random_letter2
print(password)
