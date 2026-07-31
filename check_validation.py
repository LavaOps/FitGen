# check_validation.py

"""
Check whether validation.py correctly validates known valid inputs.
"""

from benchmark_registry import BENCHMARKS
from validation import get_reached_branch, validate_branch


def main():
    all_passed = True
    total_checks = 0
    failed_checks = 0

    for function_name, info in BENCHMARKS.items():
        print("=" * 80)
        print("Function:", function_name)

        for target, chromosome in info["known_valid_inputs"].items():
            total_checks += 1

            reached_branch = get_reached_branch(function_name, chromosome)
            validated = validate_branch(function_name, chromosome, target)

            print("Target:", target)
            print("Input:", chromosome)
            print("Reached branch:", reached_branch)
            print("Validated:", validated)

            if not validated:
                all_passed = False
                failed_checks += 1
                print("FAILED")

            print("-" * 40)

    print("=" * 80)
    print("Total validation checks:", total_checks)
    print("Failed validation checks:", failed_checks)

    if all_passed:
        print("All validation checks passed.")
    else:
        print("Some validation checks failed.")


if __name__ == "__main__":
    main()