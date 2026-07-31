# check_ga_search.py

"""
Quick check for ga_search.py.

This checks that GA runs for different input types:
int, float, bool, str, and list[int].
"""

import random

from ga_search import run_ga


TEST_CASES = [
    ("sign_type", "zero"),
    ("number_kind", "even"),
    ("bmi_category", "normal"),
    ("loan_eligibility", "approve"),
    ("password_strength", "strong"),
    ("list_score", "high"),
    ("list_pattern", "sorted_with_duplicates"),
]


def main():
    random.seed(1)

    for function_name, target in TEST_CASES:
        print("=" * 80)
        print("Function:", function_name)
        print("Target:", target)

        result = run_ga(
            function_name=function_name,
            target=target,
            population_size=80,
            max_generations=100,
            mutation_rate=0.3,
            adaptive_mutation=True,
            verbose=False,
        )

        print("Found:", result["found"])
        print("Validated:", result["validated"])
        print("Best chromosome:", result["best_chromosome"])
        print("Best fitness:", result["best_fitness"])
        print("Reached branch:", result["reached_branch"])
        print("Generation:", result["generation"])
        print("Evaluations:", result["evaluations"])
        print("Runtime:", result["runtime"])

    print("=" * 80)
    print("GA search check completed.")


if __name__ == "__main__":
    main()