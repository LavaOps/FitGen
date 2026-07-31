.
├── target_functions.py                 # Benchmark programs
├── generate_fitness_zero_shot.py      # LLM-based fitness-function generation
├── generated_fitness_zero_shot.py     # Auto-generated fitness functions
├── ga_search.py                       # GA implementation utilities
├── ga_comparison.py                   # GA-Fixed vs GA-Adaptive evaluation
├── hill_climbing.py                   # Hill Climbing evaluation
├── random_baseline.py                 # Random Search baseline
├── compare_all_methods.py             # Combined analysis and figure generation
├── validate_generated_inputs.py       # Actual branch validation using Coverage.py
├── results/                           # Generated CSV files and plots
└── generated_outputs/                 # Raw LLM outputs and summaries


Step 1: Create Virtual Environment
python3 -m venv llm_env
source llm_env/bin/activate

Step 2: Install Required Packages

pip install -r requirements.txt
pip install google-genai numpy pandas matplotlib coverage pytest pytest-cov


Step 3: FitGen uses Google's Gemini API (gemini-2.5-flash) for fitness-function generation.

Set your Gemini API key:
export GEMINI_API_KEY="YOUR_API_KEY"

Or directly inside generate_fitness_zero_shot.py.


Step-by-Step Reproduction
Step 1: Generate Fitness Functions

Run: 
python generate_fitness_zero_shot.py

Step 2: Run Genetic Algorithm Experiments

Run:
python ga_comparison.py

Step 3: Check Failed Optimization Cases

Step 4: Run Hill Climbing:
python hill_climbing.py

Step 5: Run Random Search Baseline

python random_baseline.py


Step 7: Generate Combined Evaluation Results
python compare_all_methods.py

This generates:

combined CSV summaries,
success-rate plots,
runtime plots,
fitness comparison plots.

Generated outputs include:

results/all_methods_results.csv
results/summary_by_method.csv
results/success_rate_by_method.png
results/avg_runtime_by_method.png
results/avg_best_fitness_by_method.png
results/success_rate_by_function_method.png
Step 8: Validate Actual Branch Coverage
python validate_generated_inputs.py

This step:

executes generated inputs against the original benchmark programs,
validates actual branch coverage,
uses Coverage.py instrumentation and branch-label matching.

Generated outputs:

results/validated_all_methods_results.csv
results/actual_branch_coverage_by_method.csv
results/actual_branch_coverage_by_method_function.csv