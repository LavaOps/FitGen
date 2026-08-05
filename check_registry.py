from benchmark_registry import BENCHMARKS


def main():
    total_targets = 0

    print("=" * 80)
    print("Loaded benchmarks")
    print("=" * 80)

    for function_name, info in BENCHMARKS.items():
        print("Function:", function_name)
        print("Arguments:", info["args"])
        print("Input schema:", info["input_schema"])
        print("Targets:", info["targets"])
        print("Known valid inputs:", info["known_valid_inputs"])
        print("-" * 80)

        total_targets += len(info["targets"])

    print("Total functions:", len(BENCHMARKS))
    print("Total target branches:", total_targets)


if __name__ == "__main__":
    main()