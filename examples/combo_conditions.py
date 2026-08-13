def check_password(password):
    has_upper = False
    has_lower = False
    has_digit = False
    has_special = False
    has_space = False

    special_characters = "!@#$%^&*"

    for char in password:
        if char.isupper():
            has_upper = True
        elif char.islower():
            has_lower = True
        elif char.isdigit():
            has_digit = True
        elif char in special_characters:
            has_special = True

        if char.isspace():
            has_space = True

    failed = []

    if len(password) < 8:
        failed.append("At least 8 characters long")
    if not has_upper:
        failed.append("Contains at least one uppercase letter")
    if not has_lower:
        failed.append("Contains at least one lowercase letter")
    if not has_digit:
        failed.append("Contains at least one digit")
    if not has_special:
        failed.append("Contains at least one special character")
    if has_space:
        failed.append("No whitespace allowed")

    return failed