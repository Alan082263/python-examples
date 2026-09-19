class Car:
    def __init__(self, make, model, year, colour):
        self.make = make
        self.model = model
        self.year = year
        self.colour = colour
        self.odometer = 0

    def info(self):
        return f"{self.year} {self.colour.title()} {self.make.title()} {self.model.title()}"

    def get_info(self):
        print(f"{self.info()}")

    def get_odometer(self):
        print(f"{self.info()} has done {self.odometer} km.")

    def update_odometer(self, km):
        """Set the odometer reading if km > current reading"""
        if km >= self.odometer:
            self.odometer = km
        else:
            print("Km on an odometer can't be lowered.")

    def increment_odometer(self, km):
        """Increase the odometer reading"""
        if km >= 0:
            self.odometer += km
        else:
            print("Km on an odometer can't be lowered.")

class Battery:
    """To be assigned to an attribute in the ElectricCar class"""

    def __init__(self, battery_size=75):
        """Initialize the battery's attributes."""
        self.battery_size = battery_size

    def get_battery_info(self):
        print(f"This car has a {self.battery_size}-kWh battery.")

    def get_range(self):
        if self.battery_size <= 75:
            range = 430
        elif self.battery_size <= 90:
            range = 480
        else:
            range = 500
        print(f"This car can go about {range} km on a full charge.")


class ElectricCar(Car):
    def __init__(self, make, model, year, colour, battery_size=75):
        super().__init__(make, model, year, colour)
        self.battery = Battery(battery_size)

    def get_battery_info(self):
        self.battery.get_battery_info()

    def get_range(self):
        self.battery.get_range()

    def fill_tank(self):
        print(f"{self.info()} doesn't have a fuel tank!")               


my_car = Car('ford', 'territory', 2005, "tan")
my_car.get_info()
my_car.get_odometer()
my_car.update_odometer(100_000)
my_car.get_odometer()
my_car.increment_odometer(275)
my_car.get_odometer()

my_tesla = ElectricCar('tesla', 'model s', 2020, "red")
my_tesla.get_info()
my_tesla.get_battery_info()
my_tesla.fill_tank()
my_tesla.get_range()

my_model_s = ElectricCar('tesla', 'model s', 2019, 'grey', 90)
my_model_s.get_info()
my_model_s.get_battery_info()
my_model_s.get_range()
