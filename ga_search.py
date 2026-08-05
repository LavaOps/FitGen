

import copy
import math
import random
import time


import importlib
import os

FITNESS_MODULE_NAME = os.getenv("FITNESS_MODULE", "generated_fitness_gemini_2_5_flash")
MODEL_SLUG = FITNESS_MODULE_NAME.replace("generated_fitness_", "")

fitness_module = importlib.import_module(FITNESS_MODULE_NAME)

evaluate_fitness = fitness_module.evaluate_fitness
GENERATED_INPUT_SCHEMAS = fitness_module.GENERATED_INPUT_SCHEMAS





import string


def sanitize_schema(schema):

    schema = dict(schema)
    t = schema.get("type")

    if t == "int":
        min_val = int(schema.get("min", -500))
        max_val = int(schema.get("max", 100000))

        # Keep integer domains broad enough for year, score, income, etc.
        min_val = max(-1000, min(min_val, 100000))
        max_val = max(-1000, min(max_val, 100000))

        if min_val >= max_val:
            min_val, max_val = -500, 100000

        schema["min"] = min_val
        schema["max"] = max_val

    elif t == "float":
        schema["min"] = max(0.0, float(schema.get("min", 0.0)))
        schema["max"] = min(3000.0, float(schema.get("max", 3000.0)))

        if schema["min"] > schema["max"]:
            schema["min"], schema["max"] = 0.0, 3000.0

    elif t == "bool":
        pass

    elif t == "str":
        schema["min_len"] = max(0, int(schema.get("min_len", 0)))
        schema["max_len"] = min(20, int(schema.get("max_len", 15)))

        if schema["min_len"] > schema["max_len"]:
            schema["min_len"], schema["max_len"] = 0, 15

    elif t == "list_int":
        schema["min_len"] = max(0, int(schema.get("min_len", 0)))
        schema["max_len"] = min(8, int(schema.get("max_len", 6)))
        schema["min"] = max(-100, int(schema.get("min", -20)))
        schema["max"] = min(100, int(schema.get("max", 20)))

        if schema["min_len"] > schema["max_len"]:
            schema["min_len"], schema["max_len"] = 0, 6

        if schema["min"] > schema["max"]:
            schema["min"], schema["max"] = -20, 20

    else:
        raise ValueError(f"Unsupported schema type: {t}")

    return schema

def random_value(schema):
    t = schema["type"]

    if t == "int":
        return random.randint(schema.get("min", -500), schema.get("max", 3000))

    if t == "float":
        return random.uniform(schema.get("min", 0.0), schema.get("max", 3000.0))

    if t == "bool":
        return random.choice([True, False])

    if t == "str":
        min_len = schema.get("min_len", 0)
        max_len = schema.get("max_len", 15)
        length = random.randint(min_len, max_len)
        alphabet = string.ascii_letters + string.digits
        return "".join(random.choice(alphabet) for _ in range(length))

    if t == "list_int":
        min_len = schema.get("min_len", 0)
        max_len = schema.get("max_len", 6)
        min_val = schema.get("min", -20)
        max_val = schema.get("max", 20)
        length = random.randint(min_len, max_len)
        return [random.randint(min_val, max_val) for _ in range(length)]

    raise ValueError(f"Unsupported schema type: {t}")


def random_chromosome(input_schema):
    return [random_value(schema) for schema in input_schema]


def mutate_value(value, schema):
    t = schema["type"]

    if t == "int":
        min_val = schema.get("min", -500)
        max_val = schema.get("max", 3000)

        if random.random() < 0.7:
            value = value + random.choice([-10, -5, -1, 1, 5, 10])
        else:
            value = random.randint(min_val, max_val)

        return max(min_val, min(max_val, value))

    if t == "float":
        min_val = schema.get("min", 0.0)
        max_val = schema.get("max", 3000.0)

        if random.random() < 0.7:
            value = value + random.choice([-1.0, -0.5, -0.1, 0.1, 0.5, 1.0])
        else:
            value = random.uniform(min_val, max_val)

        return max(min_val, min(max_val, value))

    if t == "bool":
        return not value

    if t == "str":
        alphabet = string.ascii_letters + string.digits
        chars = list(value)

        action = random.choice(["insert", "delete", "replace"])

        if action == "insert" and len(chars) < schema.get("max_len", 15):
            chars.append(random.choice(alphabet))
        elif action == "delete" and len(chars) > schema.get("min_len", 0):
            chars.pop(random.randrange(len(chars)))
        elif chars:
            chars[random.randrange(len(chars))] = random.choice(alphabet)
        else:
            chars.append(random.choice(alphabet))

        return "".join(chars)

    if t == "list_int":
        nums = list(value)
        min_len = schema.get("min_len", 0)
        max_len = schema.get("max_len", 6)
        min_val = schema.get("min", -20)
        max_val = schema.get("max", 20)

        action = random.choice(["insert", "delete", "modify"])

        if action == "insert" and len(nums) < max_len:
            nums.append(random.randint(min_val, max_val))
        elif action == "delete" and len(nums) > min_len:
            nums.pop(random.randrange(len(nums)))
        elif nums:
            idx = random.randrange(len(nums))
            nums[idx] += random.choice([-5, -1, 1, 5])
            nums[idx] = max(min_val, min(max_val, nums[idx]))
        else:
            nums.append(random.randint(min_val, max_val))

        return nums

    raise ValueError(f"Unsupported schema type: {t}")


def mutate_chromosome(chromosome, input_schema, mutation_rate):
    child = []

    for value, schema in zip(chromosome, input_schema):
        if random.random() < mutation_rate:
            child.append(mutate_value(value, schema))
        else:
            child.append(value)

    return child


def crossover(parent1, parent2):
    if len(parent1) <= 1:
        return parent1[:]

    point = random.randint(1, len(parent1) - 1)
    return parent1[:point] + parent2[point:]



def safe_fitness(function_name, chromosome, target):

    try:
        value = evaluate_fitness(
            function_name=function_name,
            chromosome=chromosome,
            target=target,
        )

        if value is None:
            return float("inf")

        value = float(value)

        if math.isnan(value) or value < 0:
            return float("inf")

        return value

    except Exception:
        return float("inf")


def tournament_selection(population, fitness_values, tournament_size=3):
    """
    Select one parent using tournament selection.
    Lower fitness is better.
    """

    selected_indices = random.sample(
        range(len(population)),
        k=min(tournament_size, len(population)),
    )

    best_index = selected_indices[0]

    for index in selected_indices[1:]:
        if fitness_values[index] < fitness_values[best_index]:
            best_index = index

    return copy.deepcopy(population[best_index])


def get_best(population, fitness_values):
    """
    Return the best chromosome and its fitness.
    """

    best_index = min(
        range(len(population)),
        key=lambda i: fitness_values[i],
    )

    return copy.deepcopy(population[best_index]), fitness_values[best_index]


def run_ga(
    function_name,
    target,
    population_size=80,
    max_generations=150,
    mutation_rate=0.3,
    crossover_rate=0.8,
    adaptive_mutation=True,
    tournament_size=3,
    verbose=False,
):


    input_schema = [
        sanitize_schema(schema)
        for schema in GENERATED_INPUT_SCHEMAS[function_name]
    ]

    start_time = time.perf_counter()

    population = [
        random_chromosome(input_schema)
        for _ in range(population_size)
    ]

    evaluations = 0
    best_chromosome = None
    best_fitness = float("inf")
    best_generation = 0
    no_improvement_count = 0

    for generation in range(max_generations + 1):
        fitness_values = []

        for chromosome in population:
            fitness = safe_fitness(function_name, chromosome, target)
            fitness_values.append(fitness)
            evaluations += 1

        current_best_chromosome, current_best_fitness = get_best(
            population,
            fitness_values,
        )

        if current_best_fitness < best_fitness:
            best_fitness = current_best_fitness
            best_chromosome = copy.deepcopy(current_best_chromosome)
            best_generation = generation
            no_improvement_count = 0
        else:
            no_improvement_count += 1

        

        if verbose:
            print(
                f"generation={generation}, "
                f"target={target}, "
                f"best_fitness={best_fitness}, "
                f"best_chromosome={best_chromosome}, "
                f"reached={target if best_fitness == 0 else None}, "
                f"validated={best_fitness == 0}"
            )

        if best_fitness == 0:
            runtime = time.perf_counter() - start_time

            return {
                "found": True,
                "validated": best_fitness == 0,
                "function_name": function_name,
                "target": target,
                "best_chromosome": best_chromosome,
                "best_fitness": best_fitness,
                "reached_branch": target if best_fitness == 0 else None,
                "generation": best_generation,
                "evaluations": evaluations,
                "runtime": runtime,
            }

        if generation == max_generations:
            break

        current_mutation_rate = mutation_rate

        if adaptive_mutation and no_improvement_count >= 10:
            current_mutation_rate = min(0.8, mutation_rate * 2)

        if adaptive_mutation and no_improvement_count >= 25:
            current_mutation_rate = min(1.0, mutation_rate * 3)

        new_population = [copy.deepcopy(current_best_chromosome)]

        while len(new_population) < population_size:
            parent1 = tournament_selection(
                population,
                fitness_values,
                tournament_size=tournament_size,
            )

            parent2 = tournament_selection(
                population,
                fitness_values,
                tournament_size=tournament_size,
            )

            if random.random() < crossover_rate:
                child = crossover(parent1, parent2)
            else:
                child = copy.deepcopy(parent1)

            child = mutate_chromosome(child, input_schema, current_mutation_rate)

            new_population.append(child)

        population = new_population

    runtime = time.perf_counter() - start_time

    

    return {
        "found": False,
        "validated": best_fitness == 0,
        "function_name": function_name,
        "target": target,
        "best_chromosome": best_chromosome,
        "best_fitness": best_fitness,
        "reached_branch": target if best_fitness == 0 else None,
        "generation": best_generation,
        "evaluations": evaluations,
        "runtime": runtime,
    }


if __name__ == "__main__":
    GENERATED_TARGETS = fitness_module.GENERATED_TARGETS

    random.seed(1)

    function_name = list(GENERATED_TARGETS.keys())[0]
    target = GENERATED_TARGETS[function_name][0]

    result = run_ga(
        function_name=function_name,
        target=target,
        verbose=True,
    )

    print(result)