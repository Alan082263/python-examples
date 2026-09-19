class Dog: 
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def get_info(self):
        return f"{self.name} is {self.age} years old."

    def roll_over(self):
        return f"{self.name} rolled over."

    def sit(self):
        return f"{self.name} is sitting."

    def chase_ball(self):
        return f"{self.name} ran after the ball."
    


dog1 = Dog("Milo", 2)
dog2 = Dog("Daisy", 4)
print(dog1.get_info())
print(dog1.roll_over())
print(dog1.sit())
print(dog2.get_info())
# print(dog2.roll_over())
# print(dog2.sit())
print(dog2.chase_ball())