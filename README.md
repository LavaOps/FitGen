# FitGen: Validation and Guided Repair of LLM Generated Executable Fitness Functions for Search Based Software Testing

This repository contains the implementation and experimental artifacts for the paper:

**FitGen: Validation and Guided Repair of LLM Generated Executable Fitness Functions for Search Based Software Testing**

FitGen automatically generates branch-aware fitness functions from Python source code using Large Language Models (LLMs), validates the generated fitness functions through a multi-stage validation pipeline (output, syntax, compilation, and semantic validation), repairs incorrect generations using validation-guided regeneration, and evaluates the repaired fitness functions using multiple Search-Based Software Testing (SBST) algorithms.


The repository includes:

- Source code
- Benchmark programs
- Generated fitness functions
- Experimental scripts
- Evaluation results
- Scripts used to generate the tables reported in the paper

---

# Quick Start

Create and activate a Python environment, then install the dependencies:

```bash
python -m venv fitgen_env
source fitgen_env/bin/activate
pip install -r requirements.txt
```

# Repository Structure
```bash
benchmark_registry.py           #Benchmark definitions
target_functions.py             #Benchmark programs
input_generators.py             #Input generators

generate_fitness_zero_shot.py   #Main FitGen framework
validation.py                   #Multi-stage validation pipeline
ga_comparison.py                #Genetic Algorithm experiments
hill_climbing.py                #Hill Climbing experiments
random_baseline.py              #Random Search experiments
compare_all_methods.py          #Overall comparison
validate_generated_inputs.py    #Execution-based branch validation
generated_fitness_*.py          #Generated fitness functions
generated_outputs/              #Raw LLM outputs
results/                        #Experimental results
    gemini_2_5_flash/
    qwen_qwen3_32b/
    openai_gpt_oss_120b/
    openai_gpt_oss_20b/
    llama_3_3_70b_versatile/
    meta_llama_llama_4_scout_17b_16e_instruct/                       
tests/                          #Validation tests
```

# Artifact Organization

The repository is organized according to the workflow presented in the paper.

## Benchmark Programs

The benchmark programs evaluated in the paper are located in:
```
target_functions.py
```


This file contains the 11 Python benchmark programs used throughout the evaluation.

The benchmark metadata (target branches, names, and configuration) is maintained in

```
benchmark_registry.py
```
---
## Evaluated LLMs

FitGen was evaluated on the following models:

- Gemini 2.5 Flash
- Qwen3-32B
- GPT-OSS-120B
- GPT-OSS-20B
- Llama 3.3 70B
- Llama 4 Scout
---

## FitGen Framework

The core implementation of FitGen consists of the following files.

| File | Description |
|------|-------------|
| generate_fitness_zero_shot.py | Main implementation of FitGen. Generates candidate fitness functions using LLMs, performs validation-guided repair, and produces repaired fitness functions. |
| validation.py | Implements output validation, syntax validation, compilation validation, and semantic validation. |
| input_generators.py | Generates candidate inputs from inferred schemas. |
| ga_search.py | Core implementation of the Genetic Algorithm used during search. |

---

## Prompt Templates
```
prompts/
```


Contains the structured prompt templates used for automatic fitness-function generation and validation-guided repair.

These prompts correspond to the prompt structure illustrated in Figure 3 of the paper.

---

## Raw LLM Outputs
```
generated_outputs/
```

Contains the raw JSON responses returned by each evaluated LLM before repair.

Each model has its own directory containing

- raw generated responses
- generation logs
- generation summaries
- repair attempts

These files illustrate how FitGen performs validation-guided regeneration after generation failures.

---

## Repaired Fitness Functions

```
generated_fitness_*.py
```

Examples:
```
generated_fitness_gemini_2_5_flash.py
generated_fitness_qwen_qwen3_32b.py
generated_fitness_openai_gpt_oss_120b.py
generated_fitness_openai_gpt_oss_20b.py
generated_fitness_llama_3_3_70b_versatile.py
generated_fitness_meta_llama_llama_4_scout_17b_16e_instruct.py
```


These files contain the repaired fitness functions produced after FitGen successfully completes

- output validation
- syntax validation
- compilation validation
- semantic validation

Each file contains

- inferred target branches
- inferred input schemas
- repaired executable fitness functions

These repaired fitness functions are used in every experiment reported in the paper.

---

## Fitness Functions without Semantic Validation
```
generated_fitness_no_semantic_*.py
```

Examples:
```
generated_fitness_no_semantic_gemini_2_5_flash.py
generated_fitness_no_semantic_qwen_qwen3_32b.py
generated_fitness_no_semantic_openai_gpt_oss_120b.py
generated_fitness_no_semantic_openai_gpt_oss_20b.py
generated_fitness_no_semantic_llama_3_3_70b_versatile.py
generated_fitness_no_semantic_meta_llama_llama_4_scout_17b_16e_instruct.py
```

These files contain the first-pass LLM-generated fitness functions without semantic validation.

They are used only for the semantic-validation ablation study reported in the paper.

---

# Experimental Results

The `results/` directory contains all intermediate and final experimental outputs used to generate the figures and tables reported in the paper.

## Per-model Results

Each evaluated LLM has a dedicated directory:
```
results/
gemini_2_5_flash/
qwen_qwen3_32b/
openai_gpt_oss_120b/
openai_gpt_oss_20b/
llama_3_3_70b_versatile/
meta_llama_llama_4_scout_17b_16e_instruct/
```


Each directory contains the complete experimental outputs generated using the repaired fitness functions produced by FitGen.


directories contain the results obtained without semantic validation.

---

## CSV Files

The top-level CSV files summarize the experiments reported in the paper.

| File | Description |
|------|-------------|
| llm_generation_table5.csv | Cross-LLM fitness-function generation statistics. |
| llm_search_table6.csv | Overall SBST performance across all evaluated LLMs. |
| llm_search_table6_long.csv | Detailed per-model search results. |
| semantic_validation_ablation_table.csv | Results used for the semantic-validation ablation study. |
| ga_comparison_results.csv | Results of GA-Fixed and GA-Adaptive experiments. |
| hill_climbing_results.csv | Hill Climbing evaluation results. |
| random_results.csv | Random Search baseline results. |
| validated_all_methods_results.csv | Execution-based branch-validation results after search. |
| all_methods_results.csv | Combined results from all search algorithms. |
| actual_branch_coverage_by_method.csv | Branch coverage summarized by search algorithm. |
| actual_branch_coverage_by_method_function.csv | Branch coverage summarized by benchmark function. |
| summary_by_method.csv | Overall summary statistics for each search algorithm. |
| summary_by_method_function.csv | Summary statistics grouped by benchmark program. |
| summary_by_method_target.csv | Summary statistics grouped by target branch. |
| failed_targets_summary.csv | Targets not successfully covered during evaluation. |

---

## Figures

The PNG figures summarize the experimental results presented in the paper.

| Figure | Description |
|---------|-------------|
| success_rate_by_method.png | Success rate of each search algorithm. |
| success_rate_by_function_method.png | Success rate for each benchmark program. |
| validation_rate_by_method.png | Branch-validation rate after execution. |
| validation_rate_by_function_method.png | Branch-validation rate for individual benchmark programs. |
| avg_best_fitness_by_method.png | Average best fitness achieved by each search algorithm. |
| avg_generation_by_method.png | Average GA generations required before convergence. |
| avg_runtime_by_method.png | Average runtime of each search algorithm. |
| avg_evaluations_by_method.png | Average number of fitness evaluations performed. |



---

## To reproduce the complete experimental pipeline:

1. Generate fitness functions using each LLM.
2. Repeat generation with semantic validation disabled.
3. Run GA experiments.
4. Run Hill Climbing.
5. Run Random Search.
6. Run overall comparison.
7. Validate generated test inputs.
8. Generate the evaluation tables.

Following these steps reproduces all experimental results reported in the paper.

## Requirements

Install dependencies:

```bash
pip install -r requirements.txt
```
- Python 3.10+ is recommended.

## Phase 1: Generate Fitness Functions

Set the desired provider and model, then execute


### python generate_fitness_zero_shot.py
  
- Gemini
```
export LLM_PROVIDER=gemini
export LLM_MODEL=gemini-2.5-flash
export GEMINI_API_KEY=<GEMINI_API_KEY>

python generate_fitness_zero_shot.py
```

- Qwen3-32B
```
export LLM_PROVIDER=groq
export LLM_MODEL="qwen/qwen3-32b"
export GROQ_API_KEY=<GROQ_API_KEY>

python generate_fitness_zero_shot.py
```

- GPT-OSS-120B
```
export LLM_PROVIDER=groq
export LLM_MODEL="openai/gpt-oss-120b"
export GROQ_API_KEY=<GROQ_API_KEY>

python generate_fitness_zero_shot.py
```
- GPT-OSS-20B
```
export LLM_PROVIDER=groq
export LLM_MODEL="openai/gpt-oss-20b"
export GROQ_API_KEY=<GROQ_API_KEY>

python generate_fitness_zero_shot.py
```

- Llama 3.3 70B
```
export LLM_PROVIDER=groq
export LLM_MODEL="llama-3.3-70b-versatile"
export GROQ_API_KEY=<GROQ_API_KEY>

python generate_fitness_zero_shot.py
```

- Llama 4 Scout

```
export LLM_PROVIDER=groq
export LLM_MODEL="meta-llama/llama-4-scout-17b-16e-instruct"
export GROQ_API_KEY=<GROQ_API_KEY>

python generate_fitness_zero_shot.py
```

These will generate the file containing fitness functions for corresponding LLMs.

Examples:
```
generated_fitness_gemini_2_5_flash.py
generated_fitness_qwen_qwen3_32b.py
generated_fitness_openai_gpt_oss_120b.py
generated_fitness_openai_gpt_oss_20b.py
generated_fitness_llama_3_3_70b_versatile.py
generated_fitness_meta_llama_llama_4_scout_17b_16e_instruct.py
```


### Disable Semantic Validation (Ablation)
To reproduce the semantic-validation ablation:
```
export ENABLE_SEMANTIC_VALIDATION=0
python generate_fitness_zero_shot.py
```

These will generate the file that contain the generated fitness functions **without semantic validation** and are used for the ablation study.

Examples:
```
generated_fitness_no_semantic_gemini_2_5_flash.py
generated_fitness_no_semantic_qwen_qwen3_32b.py
generated_fitness_no_semantic_openai_gpt_oss_120b.py
generated_fitness_no_semantic_openai_gpt_oss_20b.py
generated_fitness_no_semantic_llama_3_3_70b_versatile.py
generated_fitness_no_semantic_meta_llama_llama_4_scout_17b_16e_instruct.py
```


## Phase 2: Genetic Algorithm Evaluation

Select the generated fitness module.

Example:
```
export FITNESS_MODULE=generated_fitness_gemini_2_5_flash
python ga_comparison.py
```

### Replace the module with any supported model:

- generated_fitness_qwen_qwen3_32b
- generated_fitness_openai_gpt_oss_120b
- generated_fitness_openai_gpt_oss_20b
- generated_fitness_llama_3_3_70b_versatile
- generated_fitness_meta_llama_llama_4_scout_17b_16e_instruct

For the semantic-validation ablation, use the corresponding
```
generated_fitness_no_semantic_*
```
modules.

## Phase 3: Hill Climbing
```
export FITNESS_MODULE=<generated fitness module>

python hill_climbing.py
```

## Phase 4: Random Search
```
export FITNESS_MODULE=<generated fitness module>

python random_baseline.py
```

## Phase 5: Compare Search Algorithms
```
export FITNESS_MODULE=<generated fitness module>

python compare_all_methods.py
```

## Phase 6: Execution-Based Branch Validation

```
export FITNESS_MODULE=<generated fitness module>

python validate_generated_inputs.py
```

## Phase 7: Generate Evaluation Tables

Generate the cross-LLM evaluation table:
```
python create_llm_evaluation_tables.py
```

Generate the semantic-validation ablation table:

```
python create_semantic_validation_ablation_table.py
```


This repository contains both the repaired fitness functions produced by FitGen and the corresponding first-pass LLM generations without semantic validation, allowing reviewers to reproduce the semantic-validation ablation study and compare repaired versus unrepaired optimization objectives.
