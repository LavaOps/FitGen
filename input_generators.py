# input_generators.py

"""
Input generation, mutation, and crossover for mixed-type chromosomes.

A chromosome is always a list of argument values.

Examples:
    sign_type(x)                         -> [x]
    max_of_three(a, b, c)                -> [a, b, c]
    loan_eligibility(age, income, emp)   -> [age, income, employed]
    password_strength(s)                 -> [s]
    list_score(nums)                     -> [nums]
"""

import random
import string


ALPHABET = string.ascii_letters + string.digits


def random_value(spec):
    input_type = spec["type"]

    if input_type == "int":
        return random.randint(spec["min"], spec["max"])

    if input_type == "float":
        return random.uniform(spec["min"], spec["max"])

    if input_type == "bool":
        return random.choice([True, False])

    if input_type == "str":
        length = random.randint(spec["min_len"], spec["max_len"])
        return "".join(random.choice(ALPHABET) for _ in range(length))

    if input_type == "list_int":
        length = random.randint(spec["min_len"], spec["max_len"])
        return [
            random.randint(spec["min"], spec["max"])
            for _ in range(length)
        ]

    raise ValueError(f"Unsupported input type: {input_type}")


def random_chromosome(input_schema):
    return [
        random_value(spec)
        for spec in input_schema
    ]


def clamp_int(value, minimum, maximum):
    return max(minimum, min(maximum, int(value)))


def clamp_float(value, minimum, maximum):
    return max(minimum, min(maximum, float(value)))


def mutate_int(value, spec):
    mutation_type = random.choice(["small_step", "random_reset"])

    if mutation_type == "small_step":
        delta = random.randint(-5, 5)
        return clamp_int(value + delta, spec["min"], spec["max"])

    return random.randint(spec["min"], spec["max"])


def mutate_float(value, spec):
    mutation_type = random.choice(["small_step", "random_reset"])

    if mutation_type == "small_step":
        delta = random.uniform(-0.5, 0.5)
        return clamp_float(value + delta, spec["min"], spec["max"])

    return random.uniform(spec["min"], spec["max"])


def mutate_bool(value, spec):
    return not value


def mutate_str(value, spec):
    value = str(value)

    min_len = spec["min_len"]
    max_len = spec["max_len"]

    operation = random.choice(["replace", "add", "delete", "random_reset"])

    if operation == "add" and len(value) < max_len:
        index = random.randint(0, len(value))
        ch = random.choice(ALPHABET)
        return value[:index] + ch + value[index:]

    if operation == "delete" and len(value) > min_len:
        index = random.randrange(len(value))
        return value[:index] + value[index + 1:]

    if operation == "replace" and len(value) > 0:
        index = random.randrange(len(value))
        ch = random.choice(ALPHABET)
        return value[:index] + ch + value[index + 1:]

    if operation == "random_reset":
        length = random.randint(min_len, max_len)
        return "".join(random.choice(ALPHABET) for _ in range(length))

    return value


def mutate_list_int(value, spec):
    nums = list(value)

    min_len = spec["min_len"]
    max_len = spec["max_len"]
    min_value = spec["min"]
    max_value = spec["max"]

    operation = random.choice([
        "add",
        "delete",
        "mutate_element",
        "swap",
        "sort",
        "duplicate",
        "random_reset",
    ])

    if operation == "add" and len(nums) < max_len:
        nums.append(random.randint(min_value, max_value))
        return nums

    if operation == "delete" and len(nums) > min_len:
        index = random.randrange(len(nums))
        nums.pop(index)
        return nums

    if operation == "mutate_element":
        if len(nums) == 0:
            if max_len > 0:
                nums.append(random.randint(min_value, max_value))
            return nums

        index = random.randrange(len(nums))
        nums[index] = clamp_int(
            nums[index] + random.randint(-5, 5),
            min_value,
            max_value,
        )
        return nums

    if operation == "swap" and len(nums) >= 2:
        i, j = random.sample(range(len(nums)), 2)
        nums[i], nums[j] = nums[j], nums[i]
        return nums

    if operation == "sort":
        return sorted(nums)

    if operation == "duplicate" and len(nums) > 0 and len(nums) < max_len:
        nums.append(random.choice(nums))
        return nums

    if operation == "random_reset":
        length = random.randint(min_len, max_len)
        return [
            random.randint(min_value, max_value)
            for _ in range(length)
        ]

    return nums


def mutate_value(value, spec, mutation_rate):
    if random.random() >= mutation_rate:
        return value

    input_type = spec["type"]

    if input_type == "int":
        return mutate_int(value, spec)

    if input_type == "float":
        return mutate_float(value, spec)

    if input_type == "bool":
        return mutate_bool(value, spec)

    if input_type == "str":
        return mutate_str(value, spec)

    if input_type == "list_int":
        return mutate_list_int(value, spec)

    raise ValueError(f"Unsupported input type: {input_type}")


def mutate_chromosome(chromosome, input_schema, mutation_rate=0.2):
    return [
        mutate_value(value, spec, mutation_rate)
        for value, spec in zip(chromosome, input_schema)
    ]


def crossover(parent1, parent2):
    child = []

    for value1, value2 in zip(parent1, parent2):
        child.append(random.choice([value1, value2]))

    return child