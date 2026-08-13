# Read user input (always a string)
firstName = input("Enter your first name: ")
lastName = input("Enter your last name: ")
year = int(input("What year were you born?: "))

# Display output
print("Hello," ,firstName,lastName)
print(f"Welcome, {firstName}!")  # f-string formatting

#year = int(input("What year were you born? "))
age = 2025 - year
print("You are", age, "years old.")
