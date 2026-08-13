# Ask user to input a number

userInput = int (input("Enter a number between 1 and 100: "))

# Display output
print("Hello, you entered,", userInput)

#Calculate if even or odd number
if (userInput % 2) == 0:
    print("{0} is Even".format(userInput))
else:
    print("{0} is Odd".format(userInput))     