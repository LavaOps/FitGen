# experiments.py

"""
Run GA experiments for all 12 benchmark programs and all target branches.

This version uses zero-shot Gemini-generated fitness functions from
generated_fitness.py.

Output:
    results/zero_shot_ga_results.csv
"""

import csv
import random
from pathlib import Path

from benchmark_registry import BENCHMARKS
from ga_search import run_ga


OUTPUT_FILE = "results/zero_shot_ga_results.csv"


def run_one_experiment(function_name, target, run_id):
    """
    Run GA once for one function and one target branch.
    """

    seed = 1000 + run_id
    random.seed(seed)

    result = run_ga(
        function_name=function_name,
        target=target,
        population_size=80,
        max_generations=100,
        mutation_rate=0.3,
        crossover_rate=0.8,
        adaptive_mutation=True,
        tournament_size=3,
        verbose=False,
    )

    row = {
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
    """
    Save all experiment rows to CSV.
    """

    output_path = Path(output_file)
    output_path.parent.mkdir(exist_ok=True)

    fieldnames = [
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

    total_targets = sum(len(info["targets"]) for info in BENCHMARKS.values())
    total_experiments = total_targets * num_runs

    counter = 0

    for function_name, info in BENCHMARKS.items():
        for target in info["targets"]:
            for run_id in range(num_runs):
                counter += 1

                print(
                    f"[{counter}/{total_experiments}] "
                    f"function={function_name}, "
                    f"target={target}, "
                    f"run={run_id + 1}/{num_runs}"
                )

                row = run_one_experiment(
                    function_name=function_name,
                    target=target,
                    run_id=run_id,
                )

                rows.append(row)

    save_results(rows, OUTPUT_FILE)

    print("\nExperiments finished.")
    print(f"Results saved to: {OUTPUT_FILE}")
    print(f"Total rows: {len(rows)}")


if __name__ == "__main__":
    main()