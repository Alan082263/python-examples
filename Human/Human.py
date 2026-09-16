class Human:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def introduce(self):
        print(f"Hi, I'm {self.name}, {self.age} years old.")

    def __repr__(self):
        return f"{type(self).__name__}({self.name!r}, {self.age!r})"

    def __str__(self):
        return f"{self.name} ({self.age})"    


class Male(Human):
    def __init__(self, name, age):
        super().__init__(name, age)
        self.gender = "Male"


class Female(Human):
    def __init__(self, name, age):
        super().__init__(name, age)
        self.gender = "Female"


# Example usage
person1 = Male("Alex", 30)
person2 = Female("Jamie", 28)

person1.introduce()
person2.introduce()

print(person1)
print([person1, person2])
print(person1 == Male("Alex", 30))

