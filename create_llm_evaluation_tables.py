from pathlib import Path
import json
import pandas as pd

BASE_RESULTS_DIR = Path("results")
BASE_GENERATED_DIR = Path("generated_outputs")

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


def count_attempts(model_slug):
    log_path = BASE_GENERATED_DIR / model_slug / "zero_shot_generation_log.txt"
    if not log_path.exists():
        return None

    attempts = {}
    for line in log_path.read_text(encoding="utf-8").splitlines():
        if ":" in line:
            function_name = line.split(":", 1)[0].strip()
            attempts[function_name] = attempts.get(function_name, 0) + 1

    if not attempts:
        return None

    return sum(attempts.values()) / len(attempts)


def build_table5():
    rows = []

    for model_slug in MODELS:
        summary_path = BASE_GENERATED_DIR / model_slug / "generation_summary.json"

        if not summary_path.exists():
            print(f"Missing generation summary: {summary_path}")
            continue

        summary = json.loads(summary_path.read_text(encoding="utf-8"))

        successful = summary.get("successful_count", 0)
        failed = summary.get("failed_count", 0)
        total = successful + failed
        accepted_rate = (successful / total * 100) if total else 0.0

        failed_items = summary.get("failed_functions", [])
        failed_names = ", ".join(item.get("function_name", "") for item in failed_items)

        rows.append({
            "model": MODEL_DISPLAY.get(model_slug, model_slug),
            "model_slug": model_slug,
            "total_functions": total,
            "accepted_functions": successful,
            "failed_functions_count": failed,
            "accepted_rate": accepted_rate,
            "avg_attempts_per_function": count_attempts(model_slug),
            "failed_functions": failed_names,
        })

    df = pd.DataFrame(rows)
    output = BASE_RESULTS_DIR / "llm_generation_table5.csv"
    df.to_csv(output, index=False)
    print(f"Saved Table 5 data to: {output}")
    print(df.to_string(index=False))


def build_table6():
    rows = []

    for model_slug in MODELS:
        path = BASE_RESULTS_DIR / model_slug / "actual_branch_coverage_by_method.csv"

        if not path.exists():
            print(f"Missing actual validation file: {path}")
            continue

        df = pd.read_csv(path)

        for method in ["RANDOM", "HILL_CLIMBING", "GA_FIXED", "GA_ADAPTIVE"]:
            mdf = df[df["method"] == method]
            if mdf.empty:
                continue

            rows.append({
                "model": MODEL_DISPLAY.get(model_slug, model_slug),
                "model_slug": model_slug,
                "method": method,
                "actual_success_rate": float(mdf["actual_success_rate"].iloc[0]),
                "total_runs": int(mdf["total_runs"].iloc[0]),
            })

    out = pd.DataFrame(rows)

    pivot = out.pivot(
        index="model",
        columns="method",
        values="actual_success_rate"
    ).reset_index()

    total_runs = out.groupby("model")["total_runs"].sum().reset_index()
    total_runs = total_runs.rename(columns={"total_runs": "total_runs_all_methods"})

    pivot = pivot.merge(total_runs, on="model", how="left")

    output_long = BASE_RESULTS_DIR / "llm_search_table6_long.csv"
    output_pivot = BASE_RESULTS_DIR / "llm_search_table6.csv"

    out.to_csv(output_long, index=False)
    pivot.to_csv(output_pivot, index=False)

    print(f"\nSaved Table 6 long data to: {output_long}")
    print(f"Saved Table 6 paper-ready data to: {output_pivot}")
    print(pivot.to_string(index=False))


def main():
    build_table5()
    build_table6()


if __name__ == "__main__":
    main()