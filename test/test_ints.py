
def has_exactly_two_19_and_at_least_three_5(numbers: list[int]) -> bool:
    return numbers.count(19) == 2 and numbers.count(5) >= 3


print(has_exactly_two_19_and_at_least_three_5([19, 19, 15, 5, 3, 5, 5, 2]))
print(has_exactly_two_19_and_at_least_three_5([19, 15, 15, 5, 3, 3, 5, 2]))
print(has_exactly_two_19_and_at_least_three_5([19, 19, 5, 5, 5, 5, 5]))
