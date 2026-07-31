# hill_climbing.py

"""
Hill Climbing search for the zero-shot LLM branch coverage project.

For each function-target pair:
    1. start from one random chromosome
    2. mutate the current chromosome
    3. keep the neighbor if it improves fitness
    4. stop when target is covered or max steps is reached

Output:
    results/hill_climbing_results.csv
"""

import csv
import copy
import math
import random
import time
from pathlib import Path
import string
import importlib
import os

FITNESS_MODULE_NAME = os.getenv("FITNESS_MODULE", "generated_fitness_gemini_2_5_flash")
MODEL_SLUG = FITNESS_MODULE_NAME.replace("generated_fitness_", "")

fitness_module = importlib.import_module(FITNESS_MODULE_NAME)

GENERATED_TARGETS = fitness_module.GENERATED_TARGETS
GENERATED_INPUT_SCHEMAS = fitness_module.GENERATED_INPUT_SCHEMAS
evaluate_fitness = fitness_module.evaluate_fitness


OUTPUT_FILE = f"results/{MODEL_SLUG}/hill_climbing_results.csv"

def sanitize_schema(schema):
    """
    Clamp LLM-generated input schema to safe practical limits.
    This prevents bad LLM schemas from creating huge strings/lists/ranges.
    """
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

# MIN_VAL = -500
# MAX_VAL = 3000


# def get_num_args(function_name):
#     import inspect
#     import target_functions

#     func = getattr(target_functions, function_name)
#     return len(inspect.signature(func).parameters)


# def random_chromosome(num_args):
#     return [random.randint(MIN_VAL, MAX_VAL) for _ in range(num_args)]


# def mutate_chromosome(chromosome, mutation_rate):
#     child = chromosome[:]

#     for i in range(len(child)):
#         if random.random() < mutation_rate:
#             if random.random() < 0.7:
#                 step = random.choice([-10, -5, -1, 1, 5, 10])
#                 child[i] += step
#             else:
#                 child[i] = random.randint(MIN_VAL, MAX_VAL)

#             child[i] = max(MIN_VAL, min(MAX_VAL, child[i]))

#     return child


def random_value(schema):
    t = schema["type"]

    if t == "int":
        return random.randint(schema.get("min", -500), schema.get("max", 3000))

    if t == "float":
        return random.uniform(schema.get("min", 0.0), schema.get("max", 3000.0))

    if t == "bool":
        return random.choice([True, False])

    if t == "str":
        length = random.randint(schema.get("min_len", 0), schema.get("max_len", 15))
        alphabet = string.ascii_letters + string.digits
        return "".join(random.choice(alphabet) for _ in range(length))

    if t == "list_int":
        length = random.randint(schema.get("min_len", 0), schema.get("max_len", 6))
        min_val = schema.get("min", -20)
        max_val = schema.get("max", 20)
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


def safe_fitness(function_name, chromosome, target):
    """
    Safely evaluate generated fitness.
    If the generated fitness function raises an error or returns invalid fitness,
    return infinity.
    """

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


def run_hill_climbing(
    function_name,
    target,
    max_steps=8080,
    mutation_rate=1.0,
    restart_after=500,
):
    """
    Run hill climbing for one function and one target branch.

    Parameters:
        max_steps: maximum number of neighbor evaluations
        mutation_rate: probability of mutating each gene
        restart_after: restart if no improvement for this many steps

    Returns:
        method
        function_name
        target
        found
        validated
        best_chromosome
        best_fitness
        reached_branch
        generation
        evaluations
        runtime
    """


    start_time = time.perf_counter()
    input_schema = [
        sanitize_schema(schema)
        for schema in GENERATED_INPUT_SCHEMAS[function_name]
    ]
    # current = random_chromosome(num_args)
    current = random_chromosome(input_schema)

    current_fitness = safe_fitness(function_name, current, target)

    best_chromosome = copy.deepcopy(current)
    best_fitness = current_fitness
    best_step = 0

    no_improvement_count = 0
    evaluations = 1

    for step in range(1, max_steps + 1):
        

        if best_fitness == 0:
            runtime = time.perf_counter() - start_time

            return {
                "model": MODEL_SLUG,
                "method": "HILL_CLIMBING",
                "function_name": function_name,
                "target": target,
                "found": best_fitness == 0,
                "validated": best_fitness == 0,
                "best_chromosome": best_chromosome,
                "best_fitness": best_fitness,
                "reached_branch": target if best_fitness == 0 else None,
                "generation": best_step,
                "evaluations": evaluations,
                "runtime": runtime,
            }

        neighbor = mutate_chromosome(current, input_schema, mutation_rate)

        neighbor_fitness = safe_fitness(function_name, neighbor, target)
        evaluations += 1

        # Keep neighbor if it improves or ties.
        # Ties help move across flat fitness landscapes.
        if neighbor_fitness <= current_fitness:
            current = copy.deepcopy(neighbor)
            current_fitness = neighbor_fitness
        else:
            no_improvement_count += 1

        if neighbor_fitness < best_fitness:
            best_chromosome = copy.deepcopy(neighbor)
            best_fitness = neighbor_fitness
            best_step = step
            no_improvement_count = 0

        # Random restart if stuck.
        if restart_after is not None and no_improvement_count >= restart_after:
            current = random_chromosome(input_schema)
            current_fitness = safe_fitness(function_name, current, target)
            evaluations += 1
            no_improvement_count = 0

            if current_fitness < best_fitness:
                best_chromosome = copy.deepcopy(current)
                best_fitness = current_fitness
                best_step = step

    runtime = time.perf_counter() - start_time

    reached_branch = target if best_fitness == 0 else None
    validated = best_fitness == 0

    return {
        "model": MODEL_SLUG,
        "method": "HILL_CLIMBING",
        "function_name": function_name,
        "target": target,
        "found": False,
        "validated": validated,
        "best_chromosome": best_chromosome,
        "best_fitness": best_fitness,
        "reached_branch": reached_branch,
        "generation": best_step,
        "evaluations": evaluations,
        "runtime": runtime,
    }


def run_one_experiment(function_name, target, run_id, target_index):
    """
    Run one hill-climbing experiment.
    """

    seed = 3000 + target_index * 100 + run_id
    random.seed(seed)

    result = run_hill_climbing(
        function_name=function_name,
        target=target,
        max_steps=8080,
        mutation_rate=1.0,
        restart_after=500,
    )

    result["run_id"] = run_id

    return result


def save_results(rows, output_file):
    """
    Save hill-climbing results to CSV.
    """

    output_path = Path(output_file)
    output_path.parent.mkdir(exist_ok=True)

    fieldnames = [
        "model",
        "method",
        "function_name",
        "target",
        "run_id",
        "found",
        "validated",
        "best_chromosome",
        "best_fitness",
        "reached_branch",
        "generation",
        "evaluations",
        "runtime",
    ]

    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def main():
    num_runs = 30
    rows = []

    targets = []

    for function_name, target_list in GENERATED_TARGETS.items():
        for target in target_list:
            targets.append((function_name, target))

    total_experiments = len(targets) * num_runs
    counter = 0

    for target_index, (function_name, target) in enumerate(targets):
        for run_id in range(num_runs):
            counter += 1

            print(
                f"[{counter}/{total_experiments}] "
                f"method=HILL_CLIMBING, "
                f"function={function_name}, "
                f"target={target}, "
                f"run={run_id + 1}/{num_runs}"
            )

            row = run_one_experiment(
                function_name=function_name,
                target=target,
                run_id=run_id,
                target_index=target_index,
            )

            rows.append(row)

    save_results(rows, OUTPUT_FILE)

    print("\nHill climbing finished.")
    print(f"Results saved to: {OUTPUT_FILE}")
    print(f"Total rows: {len(rows)}")


if __name__ == "__main__":
    main()