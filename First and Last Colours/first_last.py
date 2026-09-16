from abc import ABC, abstractmethod


class Print(ABC):
    def __init__(self, colours):
        self.colours = colours

    def first_colour(self):
        if not self.colours:
            raise ValueError("The colour list is empty.")
        return self.colours[0]

    def last_colour(self):
        if not self.colours:
            raise ValueError("The colour list is empty.")
        return self.colours[-1]


class ColourPrinter(Print):
    pass


# Create a Python program to pick the first and last colour from a list of colours.
colours = ["Pink", "Green", "White", "Black"]
printer = ColourPrinter(colours)

print("First colour:", printer.first_colour())
print("Last colour:", printer.last_colour())