# random_baseline.py

"""
Random testing baseline for the zero-shot LLM branch coverage project.

This script compares against GA by using pure random input generation.

For each function-target pair:
    1. randomly generate chromosomes
    2. run the original target function
    3. check whether the generated input reaches the target branch
    4. stop when target is covered or max evaluations is reached

Output:
    results/random_results.csv
"""

import csv
import math
import random
import time
from pathlib import Path
import string
import inspect
import target_functions

import importlib
import os

FITNESS_MODULE_NAME = os.getenv("FITNESS_MODULE", "generated_fitness_gemini_2_5_flash")
MODEL_SLUG = FITNESS_MODULE_NAME.replace("generated_fitness_", "")

fitness_module = importlib.import_module(FITNESS_MODULE_NAME)

GENERATED_TARGETS = fitness_module.GENERATED_TARGETS
GENERATED_INPUT_SCHEMAS = fitness_module.GENERATED_INPUT_SCHEMAS
evaluate_fitness = fitness_module.evaluate_fitness


OUTPUT_FILE = f"results/{MODEL_SLUG}/random_results.csv"



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
#     func = getattr(target_functions, function_name)
#     return len(inspect.signature(func).parameters)


# def random_chromosome(num_args):
#     return [random.randint(MIN_VAL, MAX_VAL) for _ in range(num_args)]



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


def run_random_search(
    function_name,
    target,
    max_evaluations=1000,
):
    """
    Run random testing for one function and one target branch.

    Returns a dictionary with:
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

    generation is set to 0 because random testing has no generations.
    """

    

    start_time = time.perf_counter()

    best_chromosome = None
    best_fitness = float("inf")
    best_reached_branch = None
    input_schema = [
        sanitize_schema(schema)
        for schema in GENERATED_INPUT_SCHEMAS[function_name]
    ]
    
    for evaluation in range(1, max_evaluations + 1):
        
        chromosome = random_chromosome(input_schema)
        #chromosome = random_chromosome(num_args)

        fitness = safe_fitness(function_name, chromosome, target)

        if fitness < best_fitness:
            best_fitness = fitness
            best_chromosome = chromosome

            best_reached_branch = target if fitness == 0 else None

        validated = fitness == 0
        reached_branch = target if validated else None

        if validated:
            runtime = time.perf_counter() - start_time

            return {
                "model": MODEL_SLUG,
                "method": "RANDOM",
                "function_name": function_name,
                "target": target,
                "found": True,
                "validated": True,
                "best_chromosome": chromosome,
                "best_fitness": 0.0,
                "reached_branch": reached_branch,
                "generation": 0,
                "evaluations": evaluation,
                "runtime": runtime,
            }

    runtime = time.perf_counter() - start_time

    return {
        "model": MODEL_SLUG,
        "method": "RANDOM",
        "function_name": function_name,
        "target": target,
        "found": False,
        "validated": False,
        "best_chromosome": best_chromosome,
        "best_fitness": best_fitness,
        "reached_branch": best_reached_branch,
        "generation": 0,
        "evaluations": max_evaluations,
        "runtime": runtime,
    }


def run_one_experiment(function_name, target, run_id, target_index):
    """
    Run one random-testing experiment.

    We use a deterministic seed so results can be reproduced.
    """

    seed = 2000 + target_index * 100 + run_id
    random.seed(seed)

    result = run_random_search(
        function_name=function_name,
        target=target,
        max_evaluations=8080,
    )

    result["run_id"] = run_id

    return result


def save_results(rows, output_file):
    """
    Save random baseline results to CSV.
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
                f"method=RANDOM, "
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

    print("\nRandom baseline finished.")
    print(f"Results saved to: {OUTPUT_FILE}")
    print(f"Total rows: {len(rows)}")


if __name__ == "__main__":
    main()
