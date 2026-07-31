import ast
import os
from pathlib import Path

import pandas as pd

import target_functions


BASE_RESULTS_DIR = Path("results")

FITNESS_MODULE_NAME = os.getenv("FITNESS_MODULE", "generated_fitness_gemini_2_5_flash")
MODEL_SLUG = FITNESS_MODULE_NAME.replace("generated_fitness_", "")

RESULTS_DIR = BASE_RESULTS_DIR / MODEL_SLUG
INPUT_FILE = RESULTS_DIR / "all_methods_results.csv"

OUTPUT_DETAILED = RESULTS_DIR / "validated_all_methods_results.csv"
OUTPUT_SUMMARY_METHOD = RESULTS_DIR / "actual_branch_coverage_by_method.csv"
OUTPUT_SUMMARY_FUNCTION = RESULTS_DIR / "actual_branch_coverage_by_method_function.csv"


def parse_chromosome(value):
    """
    Convert string representation of chromosome back to Python list.
    Example: "[1, 2, 3]" -> [1, 2, 3]
    """
    if pd.isna(value):
        return None

    if isinstance(value, list):
        return value

    try:
        return ast.literal_eval(str(value))
    except Exception:
        return None


def run_target_function(function_name, chromosome):
    """
    Run the original target function using the generated chromosome.
    """
    if chromosome is None:
        return None

    func = getattr(target_functions, function_name)

    try:
        return func(*chromosome)
    except Exception:
        return None


def main():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Missing {INPUT_FILE}. Run compare_all_methods.py first."
        )

    df = pd.read_csv(INPUT_FILE)
    if "model" not in df.columns:
        df["model"] = MODEL_SLUG

    actual_outputs = []
    actual_valid = []

    for _, row in df.iterrows():
        function_name = row["function_name"]
        target = row["target"]
        chromosome = parse_chromosome(row["best_chromosome"])

        actual_output = run_target_function(function_name, chromosome)

        actual_outputs.append(actual_output)
        actual_valid.append(actual_output == target)

    df["actual_output"] = actual_outputs
    df["actual_validated"] = actual_valid

    df.to_csv(OUTPUT_DETAILED, index=False)

    summary_method = df.groupby(["model", "method"]).agg(
        actual_success_rate=("actual_validated", "mean"),
        total_runs=("actual_validated", "count"),
    ).reset_index()

    summary_method["actual_success_rate"] *= 100

    summary_method.to_csv(OUTPUT_SUMMARY_METHOD, index=False)

    summary_function = df.groupby(
        ["model", "method", "function_name"]
    ).agg(
        actual_success_rate=("actual_validated", "mean"),
        total_runs=("actual_validated", "count"),
    ).reset_index()

    summary_function["actual_success_rate"] *= 100

    summary_function.to_csv(OUTPUT_SUMMARY_FUNCTION, index=False)

    print("\nActual validation by method:")
    print(summary_method.to_string(index=False))

    print("\nActual validation by method/function:")
    print(summary_function.to_string(index=False))

    print("\nGenerated files:")
    print(OUTPUT_DETAILED)
    print(OUTPUT_SUMMARY_METHOD)
    print(OUTPUT_SUMMARY_FUNCTION)


if __name__ == "__main__":
    main()
