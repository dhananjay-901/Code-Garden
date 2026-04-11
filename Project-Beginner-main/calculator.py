while True:
    print('''
          welcome to calculator
           1. Add
           2. Subtract
           3. Multiply
           4. Divide
           5. Exit
          ''')
    choice = int(input("your choice: "))
    if choice ==1:
        print ("let's perform addition")
        num1 = float(input("Number 1: "))
        num2 = float(input("Number 2: "))
        print("Addition of two numbers is: ", num1+num2)
    elif choice ==2:
        print ("let's perform subtraction")
        num1 = float(input("Number 1: "))
        num2 = float(input("Number 2: "))
        print("Subtraction of two numbers is: ", num1-num2)
    elif choice ==3:
        print ("let's perform multiplication")
        num1 = float(input("Number 1: "))
        num2 = float(input("Number 2: "))
        print("Multiplication of two numbers is: ", num1*num2)
    elif choice ==4:
        print ("let's perform division")
        num1 = float(input("Number 1: "))
        num2 = float(input("Number 2: "))
        print("Division of two numbers is: ", num1/num2)
    elif choice ==5:
        print("Exiting the program")
        break
    else:
        print("Invalid choice")
        continue
    
    