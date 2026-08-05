

from benchmark_registry import BENCHMARKS
from generated_fitness import evaluate_fitness


def is_zero(value):

    try:
        return abs(float(value)) < 1e-9
    except Exception:
        return value == 0


def main():
    all_passed = True
    total_checks = 0
    failed_checks = 0

    for function_name, info in BENCHMARKS.items():
        print("=" * 80)
        print("Function:", function_name)

        for target, chromosome in info["known_valid_inputs"].items():
            total_checks += 1

            try:
                fitness_value = evaluate_fitness(
                    function_name=function_name,
                    chromosome=chromosome,
                    target=target,
                )

                print("Target:", target)
                print("Input:", chromosome)
                print("Fitness:", fitness_value)

                if not is_zero(fitness_value):
                    all_passed = False
                    failed_checks += 1
                    print("FAILED: expected fitness 0")

            except Exception as error:
                all_passed = False
                failed_checks += 1

                print("Target:", target)
                print("Input:", chromosome)
                print("ERROR:", error)
                print("FAILED: generated fitness function raised an error")

            print("-" * 40)

    print("=" * 80)
    print("Total checks:", total_checks)
    print("Failed checks:", failed_checks)

    if all_passed:
        print("All zero-shot Gemini-generated fitness functions passed the quick check.")
    else:
        print("Some generated fitness functions failed. Check generated_fitness.py.")


if __name__ == "__main__":
    main()