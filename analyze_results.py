# analyze_results.py

"""
Analyze GA experiment results for zero-shot Gemini-generated fitness functions.

Input:
    results/zero_shot_ga_results.csv

Outputs:
    results/summary_by_function.csv
    results/summary_by_target.csv
    results/success_rate_by_function.png
    results/validation_rate_by_function.png
    results/avg_generation_by_function.png
    results/avg_runtime_by_function.png
    results/avg_best_fitness_by_function.png
"""

from pathlib import Path

import pandas as pd
import matplotlib.pyplot as plt


RESULTS_FILE = "results/zero_shot_ga_results.csv"
OUTPUT_DIR = Path("results")


def load_results():
    """
    Load experiment results and clean data types.
    """

    df = pd.read_csv(RESULTS_FILE)

    df["found"] = df["found"].astype(str).str.lower() == "true"
    df["validated"] = df["validated"].astype(str).str.lower() == "true"

    df["generation"] = pd.to_numeric(df["generation"], errors="coerce")
    df["evaluations"] = pd.to_numeric(df["evaluations"], errors="coerce")
    df["runtime"] = pd.to_numeric(df["runtime"], errors="coerce")
    df["best_fitness"] = pd.to_numeric(df["best_fitness"], errors="coerce")

    return df


def create_summary_tables(df):
    """
    Create summary tables by function and by target.
    """

    summary_by_function = df.groupby("function_name").agg(
        success_rate=("found", "mean"),
        validation_rate=("validated", "mean"),
        avg_generation=("generation", "mean"),
        avg_evaluations=("evaluations", "mean"),
        avg_runtime=("runtime", "mean"),
        avg_best_fitness=("best_fitness", "mean"),
        total_runs=("found", "count"),
    ).reset_index()

    summary_by_function["success_rate"] *= 100
    summary_by_function["validation_rate"] *= 100

    summary_by_target = df.groupby(["function_name", "target"]).agg(
        success_rate=("found", "mean"),
        validation_rate=("validated", "mean"),
        avg_generation=("generation", "mean"),
        avg_evaluations=("evaluations", "mean"),
        avg_runtime=("runtime", "mean"),
        avg_best_fitness=("best_fitness", "mean"),
        total_runs=("found", "count"),
    ).reset_index()

    summary_by_target["success_rate"] *= 100
    summary_by_target["validation_rate"] *= 100

    summary_by_function.to_csv(
        OUTPUT_DIR / "summary_by_function.csv",
        index=False,
    )

    summary_by_target.to_csv(
        OUTPUT_DIR / "summary_by_target.csv",
        index=False,
    )

    print("\nSummary by function:")
    print(summary_by_function.to_string(index=False))

    print("\nSummary by target:")
    print(summary_by_target.to_string(index=False))

    return summary_by_function, summary_by_target


def plot_bar(
    df,
    x_col,
    y_col,
    title,
    xlabel,
    ylabel,
    output_file,
    ylim_100=False,
):
    """
    Create and save a bar plot.
    """

    plot_df = df.sort_values(by=x_col)

    ax = plot_df.plot(
        kind="bar",
        x=x_col,
        y=y_col,
        legend=False,
        figsize=(12, 6),
    )

    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)

    if ylim_100:
        ax.set_ylim(0, 105)

    plt.xticks(rotation=45, ha="right")
    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / output_file, dpi=300)
    plt.close()


def main():
    OUTPUT_DIR.mkdir(exist_ok=True)

    df = load_results()

    summary_by_function, summary_by_target = create_summary_tables(df)

    plot_bar(
        summary_by_function,
        x_col="function_name",
        y_col="success_rate",
        title="GA Success Rate by Function",
        xlabel="Function",
        ylabel="Success Rate (%)",
        output_file="success_rate_by_function.png",
        ylim_100=True,
    )

    plot_bar(
        summary_by_function,
        x_col="function_name",
        y_col="validation_rate",
        title="GA Validation Rate by Function",
        xlabel="Function",
        ylabel="Validation Rate (%)",
        output_file="validation_rate_by_function.png",
        ylim_100=True,
    )

    plot_bar(
        summary_by_function,
        x_col="function_name",
        y_col="avg_generation",
        title="Average Generation by Function",
        xlabel="Function",
        ylabel="Average Generation",
        output_file="avg_generation_by_function.png",
        ylim_100=False,
    )

    plot_bar(
        summary_by_function,
        x_col="function_name",
        y_col="avg_runtime",
        title="Average Runtime by Function",
        xlabel="Function",
        ylabel="Runtime in Seconds",
        output_file="avg_runtime_by_function.png",
        ylim_100=False,
    )

    plot_bar(
        summary_by_function,
        x_col="function_name",
        y_col="avg_best_fitness",
        title="Average Best Fitness by Function",
        xlabel="Function",
        ylabel="Average Best Fitness",
        output_file="avg_best_fitness_by_function.png",
        ylim_100=False,
    )

    print("\nAnalysis complete.")
    print("Generated files:")
    print("results/summary_by_function.csv")
    print("results/summary_by_target.csv")
    print("results/success_rate_by_function.png")
    print("results/validation_rate_by_function.png")
    print("results/avg_generation_by_function.png")
    print("results/avg_runtime_by_function.png")
    print("results/avg_best_fitness_by_function.png")


if __name__ == "__main__":
    main()