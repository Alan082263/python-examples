def check_password(password):
    failed = []

    if len(password) < 8:
        failed.append("At least 8 characters long")

    if not any(char.isupper() for char in password):
        failed.append("Contains at least one uppercase letter")

    if not any(char.islower() for char in password):
        failed.append("Contains at least one lowercase letter")

    if not any(char.isdigit() for char in password):
        failed.append("Contains at least one digit")

    special_characters = "!@#$%^&*"
    if not any(char in special_characters for char in password):
        failed.append("Contains at least one special character")

    if any(char.isspace() for char in password):
        failed.append("No whitespace allowed")

    return failed


print("Password Checker")
print("Enter a password to check whether it meets the required security rules.")
print()

password = input("Enter your password: ")

failed_rules = check_password(password)

if failed_rules:
    print("\nYour password failed these rules:")
    for rule in failed_rules:
        print("-", rule)
else:
    print("\nYour password meets all the requirements!")