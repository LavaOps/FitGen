# compare_all_methods.py

"""
Combine and analyze all method results using LLM-generated fitness functions.

Methods:
    RANDOM
    HILL_CLIMBING
    GA_FIXED
    GA_ADAPTIVE

Inputs:
    results/random_results.csv
    results/hill_climbing_results.csv
    results/ga_comparison_results.csv

Outputs:
    results/all_methods_results.csv
    results/summary_by_method.csv
    results/summary_by_method_function.csv
    results/summary_by_method_target.csv
    results/success_rate_by_method.png
    results/validation_rate_by_method.png
    results/avg_evaluations_by_method.png
    results/avg_runtime_by_method.png
    results/avg_best_fitness_by_method.png
"""

from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


import os

BASE_RESULTS_DIR = Path("results")

FITNESS_MODULE_NAME = os.getenv("FITNESS_MODULE", "generated_fitness_gemini_2_5_flash")
MODEL_SLUG = FITNESS_MODULE_NAME.replace("generated_fitness_", "")

RESULTS_DIR = BASE_RESULTS_DIR / MODEL_SLUG

RANDOM_FILE = RESULTS_DIR / "random_results.csv"
HILL_FILE = RESULTS_DIR / "hill_climbing_results.csv"
GA_FILE = RESULTS_DIR / "ga_comparison_results.csv"


def load_one_file(path, expected_methods=None):
    """
    Load one result CSV file and clean data types.
    """

    if not path.exists():
        raise FileNotFoundError(f"Missing result file: {path}")

    df = pd.read_csv(path)

    if "method" not in df.columns:
        raise ValueError(f"File {path} does not have a method column.")

    if expected_methods is not None:
        existing_methods = set(df["method"].unique())
        missing = set(expected_methods) - existing_methods

        if missing:
            raise ValueError(
                f"File {path} is missing expected methods: {missing}. "
                f"Existing methods: {existing_methods}"
            )

    return df


def clean_results(df):
    """
    Convert result columns into useful numeric/boolean types.
    """

    df["found"] = df["found"].astype(str).str.lower() == "true"
    df["validated"] = df["validated"].astype(str).str.lower() == "true"

    df["generation"] = pd.to_numeric(df["generation"], errors="coerce")
    df["evaluations"] = pd.to_numeric(df["evaluations"], errors="coerce")
    df["runtime"] = pd.to_numeric(df["runtime"], errors="coerce")
    df["best_fitness"] = pd.to_numeric(df["best_fitness"], errors="coerce")

    return df


def load_all_results():
    """
    Load RANDOM, HILL_CLIMBING, GA_FIXED, and GA_ADAPTIVE result files.
    """

    random_df = load_one_file(
        RANDOM_FILE,
        expected_methods=["RANDOM"],
    )

    hill_df = load_one_file(
        HILL_FILE,
        expected_methods=["HILL_CLIMBING"],
    )

    ga_df = load_one_file(
        GA_FILE,
        expected_methods=["GA_FIXED", "GA_ADAPTIVE"],
    )

    all_df = pd.concat(
        [random_df, hill_df, ga_df],
        ignore_index=True,
    )

    all_df = clean_results(all_df)

    method_order = [
        "RANDOM",
        "HILL_CLIMBING",
        "GA_FIXED",
        "GA_ADAPTIVE",
    ]

    all_df["method"] = pd.Categorical(
        all_df["method"],
        categories=method_order,
        ordered=True,
    )

    all_df = all_df.sort_values(
        by=["method", "function_name", "target", "run_id"]
    )

    return all_df


def create_summary_tables(df):
    """
    Create summary tables:
        1. by method
        2. by method and function
        3. by method, function, and target
    """

    summary_by_method = df.groupby("method", observed=False).agg(
        success_rate=("found", "mean"),
        validation_rate=("validated", "mean"),
        avg_generation=("generation", "mean"),
        avg_evaluations=("evaluations", "mean"),
        median_evaluations=("evaluations", "median"),
        avg_runtime=("runtime", "mean"),
        median_runtime=("runtime", "median"),
        avg_best_fitness=("best_fitness", "mean"),
        total_runs=("found", "count"),
    ).reset_index()

    summary_by_method["success_rate"] *= 100
    summary_by_method["validation_rate"] *= 100

    summary_by_method_function = df.groupby(
        ["method", "function_name"],
        observed=False,
    ).agg(
        success_rate=("found", "mean"),
        validation_rate=("validated", "mean"),
        avg_generation=("generation", "mean"),
        avg_evaluations=("evaluations", "mean"),
        median_evaluations=("evaluations", "median"),
        avg_runtime=("runtime", "mean"),
        median_runtime=("runtime", "median"),
        avg_best_fitness=("best_fitness", "mean"),
        total_runs=("found", "count"),
    ).reset_index()

    summary_by_method_function["success_rate"] *= 100
    summary_by_method_function["validation_rate"] *= 100

    summary_by_method_target = df.groupby(
        ["method", "function_name", "target"],
        observed=False,
    ).agg(
        success_rate=("found", "mean"),
        validation_rate=("validated", "mean"),
        avg_generation=("generation", "mean"),
        avg_evaluations=("evaluations", "mean"),
        median_evaluations=("evaluations", "median"),
        avg_runtime=("runtime", "mean"),
        median_runtime=("runtime", "median"),
        avg_best_fitness=("best_fitness", "mean"),
        total_runs=("found", "count"),
    ).reset_index()

    summary_by_method_target["success_rate"] *= 100
    summary_by_method_target["validation_rate"] *= 100


    failed_targets = summary_by_method_target[
        summary_by_method_target["success_rate"] < 100
    ].sort_values(
        by=["success_rate", "function_name", "target"]
    )

    failed_targets.to_csv(
        RESULTS_DIR / "failed_targets_summary.csv",
        index=False,
    )

    df.to_csv(
        RESULTS_DIR / "all_methods_results.csv",
        index=False,
    )

    summary_by_method.to_csv(
        RESULTS_DIR / "summary_by_method.csv",
        index=False,
    )

    summary_by_method_function.to_csv(
        RESULTS_DIR / "summary_by_method_function.csv",
        index=False,
    )

    summary_by_method_target.to_csv(
        RESULTS_DIR / "summary_by_method_target.csv",
        index=False,
    )

    print("\nSummary by method:")
    print(summary_by_method.to_string(index=False))

    print("\nSummary by method and function:")
    print(summary_by_method_function.to_string(index=False))

    return (
        summary_by_method,
        summary_by_method_function,
        summary_by_method_target,
    )


def plot_bar(df, x_col, y_col, title, xlabel, ylabel, output_file, ylim_100=False):
    """
    Create one bar plot with value labels.
    """

    ax = df.plot(
        kind="bar",
        x=x_col,
        y=y_col,
        legend=False,
        figsize=(8, 5),
    )

    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    if ylim_100:
        ax.set_ylim(0, 110)

    for container in ax.containers:
        labels = []

        for i, bar in enumerate(container):
            value = bar.get_height()

            if y_col in ["success_rate", "validation_rate"]:
                total = int(df.iloc[i]["total_runs"])
                success_count = int(round((value / 100.0) * total))
                labels.append(f"{value:.1f}%\n({success_count}/{total})")
            else:
                if y_col == "avg_runtime":
                    labels.append(f"{value:.4f}")
                else:
                    labels.append(f"{value:.2f}")

        ax.bar_label(container, labels=labels, padding=3, fontsize=9)

    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(RESULTS_DIR / output_file, dpi=300)
    plt.close()


def plot_grouped_bar(
    df,
    index_col,
    column_col,
    value_col,
    title,
    xlabel,
    ylabel,
    output_file,
    ylim_100=False,
):
    """
    Create a grouped bar chart, usually method by function.
    """

    pivot = df.pivot(
        index=index_col,
        columns=column_col,
        values=value_col,
    )

    ax = pivot.plot(
        kind="bar",
        figsize=(14, 6),
    )

    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    if ylim_100:
        ax.set_ylim(0, 105)

    plt.xticks(rotation=45, ha="right")
    plt.legend(title=column_col)
    plt.tight_layout()
    plt.savefig(RESULTS_DIR / output_file, dpi=300)
    plt.close()


def create_plots(summary_by_method, summary_by_method_function):
    """
    Create comparison plots.
    """

    plot_bar(
        summary_by_method,
        x_col="method",
        y_col="success_rate",
        title="Success Rate by Method",
        xlabel="Method",
        ylabel="Success Rate (%)",
        output_file="success_rate_by_method.png",
        ylim_100=True,
    )

    plot_bar(
        summary_by_method,
        x_col="method",
        y_col="validation_rate",
        title="Validation Rate by Method",
        xlabel="Method",
        ylabel="Validation Rate (%)",
        output_file="validation_rate_by_method.png",
        ylim_100=True,
    )

    plot_bar(
        summary_by_method,
        x_col="method",
        y_col="avg_evaluations",
        title="Average Evaluations by Method",
        xlabel="Method",
        ylabel="Average Evaluations",
        output_file="avg_evaluations_by_method.png",
        ylim_100=False,
    )

    plot_bar(
        summary_by_method,
        x_col="method",
        y_col="avg_generation",
        title="Average Generation/Step of Best Solution by Method",
        xlabel="Method",
        ylabel="Average Generation/Step",
        output_file="avg_generation_by_method.png",
        ylim_100=False,
    )

    plot_bar(
        summary_by_method,
        x_col="method",
        y_col="avg_runtime",
        title="Average Runtime by Method",
        xlabel="Method",
        ylabel="Average Runtime (seconds)",
        output_file="avg_runtime_by_method.png",
        ylim_100=False,
    )

    plot_bar(
        summary_by_method,
        x_col="method",
        y_col="avg_best_fitness",
        title="Average Best Fitness by Method",
        xlabel="Method",
        ylabel="Average Best Fitness",
        output_file="avg_best_fitness_by_method.png",
        ylim_100=False,
    )

    plot_grouped_bar(
        summary_by_method_function,
        index_col="function_name",
        column_col="method",
        value_col="success_rate",
        title="Success Rate by Function and Method",
        xlabel="Function",
        ylabel="Success Rate (%)",
        output_file="success_rate_by_function_method.png",
        ylim_100=True,
    )

    plot_grouped_bar(
        summary_by_method_function,
        index_col="function_name",
        column_col="method",
        value_col="validation_rate",
        title="Validation Rate by Function and Method",
        xlabel="Function",
        ylabel="Validation Rate (%)",
        output_file="validation_rate_by_function_method.png",
        ylim_100=True,
    )
    


def main():
    RESULTS_DIR.mkdir(exist_ok=True)

    df = load_all_results()

    (
        summary_by_method,
        summary_by_method_function,
        summary_by_method_target,
    ) = create_summary_tables(df)

    create_plots(
        summary_by_method,
        summary_by_method_function,
    )

    print("\nCombined analysis complete.")
    print("Generated files:")
    print(f"{RESULTS_DIR}/all_methods_results.csv")
    print(f"{RESULTS_DIR}/summary_by_method.csv")
    print(f"{RESULTS_DIR}/summary_by_method_function.csv")
    print(f"{RESULTS_DIR}/summary_by_method_target.csv")
    print(f"{RESULTS_DIR}/success_rate_by_method.png")
    print(f"{RESULTS_DIR}/validation_rate_by_method.png")
    print(f"{RESULTS_DIR}/avg_evaluations_by_method.png")
    print(f"{RESULTS_DIR}/avg_runtime_by_method.png")
    print(f"{RESULTS_DIR}/avg_best_fitness_by_method.png")
    print(f"{RESULTS_DIR}/success_rate_by_function_method.png")
    print(f"{RESULTS_DIR}/validation_rate_by_function_method.png")
    print(f"{RESULTS_DIR}/avg_generation_by_method.png")


if __name__ == "__main__":
    main()