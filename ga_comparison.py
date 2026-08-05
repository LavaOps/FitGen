

import csv
import random
from pathlib import Path

import importlib
import os

FITNESS_MODULE_NAME = os.getenv("FITNESS_MODULE", "generated_fitness_gemini_2_5_flash")
MODEL_SLUG = FITNESS_MODULE_NAME.replace("generated_fitness_", "")

fitness_module = importlib.import_module(FITNESS_MODULE_NAME)
GENERATED_TARGETS = fitness_module.GENERATED_TARGETS

from ga_search import run_ga


OUTPUT_FILE = f"results/{MODEL_SLUG}/ga_comparison_results.csv"


METHOD_CONFIGS = {
    "GA_FIXED": {
        "adaptive_mutation": False,
    },
    "GA_ADAPTIVE": {
        "adaptive_mutation": True,
    },
}


def run_one_experiment(method, function_name, target, run_id, target_index):

    if method not in METHOD_CONFIGS:
        raise ValueError(f"Unknown method: {method}")

    seed = 4000 + target_index * 100 + run_id

    if method == "GA_ADAPTIVE":
        seed += 100000

    random.seed(seed)

    config = METHOD_CONFIGS[method]

    result = run_ga(
        function_name=function_name,
        target=target,
        population_size=80,
        max_generations=100,
        mutation_rate=0.3,
        crossover_rate=0.8,
        adaptive_mutation=config["adaptive_mutation"],
        tournament_size=3,
        verbose=False,
    )

    row = {
        "model": MODEL_SLUG,
        "method": method,
        "function_name": function_name,
        "target": target,
        "run_id": run_id,
        "found": result["found"],
        "validated": result["validated"],
        "best_chromosome": result["best_chromosome"],
        "best_fitness": result["best_fitness"],
        "reached_branch": result["reached_branch"],
        "generation": result["generation"],
        "evaluations": result["evaluations"],
        "runtime": result["runtime"],
    }

    return row


def save_results(rows, output_file):

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

    total_experiments = len(METHOD_CONFIGS) * len(targets) * num_runs
    counter = 0

    for method in METHOD_CONFIGS:
        for target_index, (function_name, target) in enumerate(targets):
            for run_id in range(num_runs):
                counter += 1

                print(
                    f"[{counter}/{total_experiments}] "
                    f"method={method}, "
                    f"function={function_name}, "
                    f"target={target}, "
                    f"run={run_id + 1}/{num_runs}"
                )

                row = run_one_experiment(
                    method=method,
                    function_name=function_name,
                    target=target,
                    run_id=run_id,
                    target_index=target_index,
                )

                rows.append(row)

    save_results(rows, OUTPUT_FILE)

    print("\nGA comparison finished.")
    print(f"Results saved to: {OUTPUT_FILE}")
    print(f"Total rows: {len(rows)}")


if __name__ == "__main__":
    main()