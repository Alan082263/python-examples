class Person:
    def __init__(self, name: str, country: str, date_of_birth: str):
        self.name = name
        self.country = country
        self.date_of_birth = date_of_birth

    def calculate_age(self) -> int:
        from datetime import datetime

        birth_date = datetime.strptime(self.date_of_birth, "%Y-%m-%d")
        today = datetime.today()
        age = today.year - birth_date.year - (
            (today.month, today.day) < (birth_date.month, birth_date.day)
        )
        return age

person1 = Person("Alice", "USA", "1990-05-15")
print("Person 1:")
print("Name:", person1.name)
print("Country:", person1.country)
print("Date of Birth:", person1.date_of_birth)
print("Age:", person1.calculate_age())