import ast
from pathlib import Path

import pandas as pd
import target_functions


BASE_RESULTS_DIR = Path("results")

MODELS = [
    "gemini_2_5_flash",
    "qwen_qwen3_32b",
    "openai_gpt_oss_120b",
    "openai_gpt_oss_20b",
    "llama_3_3_70b_versatile",
    "meta_llama_llama_4_scout_17b_16e_instruct",
]

MODEL_DISPLAY = {
    "gemini_2_5_flash": "Gemini 2.5 Flash",
    "qwen_qwen3_32b": "Qwen3-32B",
    "openai_gpt_oss_120b": "GPT-OSS-120B",
    "openai_gpt_oss_20b": "GPT-OSS-20B",
    "llama_3_3_70b_versatile": "Llama 3.3 70B",
    "meta_llama_llama_4_scout_17b_16e_instruct": "Llama 4 Scout",
}


def parse_chromosome(value):
    if pd.isna(value):
        return None
    try:
        return ast.literal_eval(str(value))
    except Exception:
        return None


def actual_validate(row):
    chromosome = parse_chromosome(row["best_chromosome"])
    if chromosome is None:
        return False

    func = getattr(target_functions, row["function_name"])

    try:
        actual_output = func(*chromosome)
    except Exception:
        return False

    return actual_output == row["target"]


def compute_ga_fixed_rate(results_dir):
    path = results_dir / "ga_comparison_results.csv"

    if not path.exists():
        print(f"Missing file: {path}")
        return None, 0

    df = pd.read_csv(path)

    df = df[df["method"] == "GA_FIXED"].copy()

    if df.empty:
        return None, 0

    df["actual_validated"] = df.apply(actual_validate, axis=1)

    rate = df["actual_validated"].mean() * 100
    total_runs = len(df)

    return rate, total_runs


def main():
    rows = []

    for model_slug in MODELS:
        before_dir = BASE_RESULTS_DIR / f"no_semantic_{model_slug}"
        after_dir = BASE_RESULTS_DIR / model_slug

        before_rate, before_runs = compute_ga_fixed_rate(before_dir)
        after_rate, after_runs = compute_ga_fixed_rate(after_dir)

        if before_rate is None or after_rate is None:
            continue

        rows.append({
            "model": MODEL_DISPLAY[model_slug],
            "before_semantic_validation": before_rate,
            "after_semantic_validation": after_rate,
            "improvement": after_rate - before_rate,
            "before_runs": before_runs,
            "after_runs": after_runs,
        })

    out = pd.DataFrame(rows)

    output_path = BASE_RESULTS_DIR / "semantic_validation_ablation_table.csv"
    out.to_csv(output_path, index=False)

    print(f"Saved semantic validation ablation table to: {output_path}")
    print(out.to_string(index=False, formatters={
        "before_semantic_validation": "{:.2f}".format,
        "after_semantic_validation": "{:.2f}".format,
        "improvement": "{:+.2f}".format,
    }))


if __name__ == "__main__":
    main()
