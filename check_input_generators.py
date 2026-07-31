# check_input_generators.py

"""
Quick check for input_generators.py.
"""

from benchmark_registry import BENCHMARKS
from input_generators import random_chromosome, mutate_chromosome, crossover


def main():
    for function_name, info in BENCHMARKS.items():
        input_schema = info["input_schema"]

        print("=" * 80)
        print("Function:", function_name)
        print("Input schema:", input_schema)

        parent1 = random_chromosome(input_schema)
        parent2 = random_chromosome(input_schema)

        child = crossover(parent1, parent2)
        mutated = mutate_chromosome(
            chromosome=child,
            input_schema=input_schema,
            mutation_rate=1.0,
        )

        print("Parent 1:", parent1)
        print("Parent 2:", parent2)
        print("Child:", child)
        print("Mutated:", mutated)

    print("=" * 80)
    print("Input generator check completed.")


if __name__ == "__main__":
    main()