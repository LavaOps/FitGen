
import time
import ast
import inspect
import json
import os
from pathlib import Path
from typing import List, Optional, Tuple

from google import genai
from google.genai import types
from openai import OpenAI
from pydantic import BaseModel, Field

import target_functions
import random
import string


LLM_PROVIDER = os.getenv("LLM_PROVIDER", "gemini")
MODEL_NAME = os.getenv("LLM_MODEL", "gemini-2.5-flash")
MAX_GENERATION_ATTEMPTS = int(os.getenv("MAX_GENERATION_ATTEMPTS", "3"))

ENABLE_SEMANTIC_VALIDATION = (
    os.getenv("ENABLE_SEMANTIC_VALIDATION", "1").strip().lower()
    in {"1", "true", "yes", "on"}
)

def safe_model_slug(model_name: str) -> str:
    return (
        model_name
        .replace("/", "_")
        .replace("-", "_")
        .replace(".", "_")
        .replace(":", "_")
    )

MODEL_SLUG = os.getenv("MODEL_SLUG", safe_model_slug(MODEL_NAME))

if ENABLE_SEMANTIC_VALIDATION:
    OUTPUT_FILE = Path(f"generated_fitness_{MODEL_SLUG}.py")
    FITNESS_VERSION_LABEL = "final_validated_after_semantic_repair"
else:
    OUTPUT_FILE = Path(f"generated_fitness_no_semantic_{MODEL_SLUG}.py")
    FITNESS_VERSION_LABEL = "without_semantic_validation"

RAW_OUTPUT_DIR = Path("generated_outputs") / MODEL_SLUG
PROMPT_DIR = Path("prompts")


class InputSchemaItem(BaseModel):
    type: str = Field(description="One of: int, float, bool, str, list_int")
    min: Optional[float] = Field(default=None, description="Minimum numeric value if applicable")
    max: Optional[float] = Field(default=None, description="Maximum numeric value if applicable")
    min_len: Optional[int] = Field(default=None, description="Minimum length for strings/lists if applicable")
    max_len: Optional[int] = Field(default=None, description="Maximum length for strings/lists if applicable")

class FitnessGenerationResult(BaseModel):
    function_name: str = Field(description="Original benchmark function name.")
    fitness_function_name: str = Field(description="Generated fitness function name.")
    targets: List[str] = Field(description="Target branch/path names supported by the generated function.")
    input_schema: List[InputSchemaItem] = Field(description="Input schema for each argument in function signature order.")
    fitness_code: str = Field(description="Executable Python code defining the generated fitness function.")
    notes: str = Field(description="Short explanation of the generated fitness function.")


def build_zero_shot_prompt(function_name: str, function_source: str) -> str:
    """
    Build a generalized zero-shot prompt.

    We send:
    - function name
    - function source

    We do NOT send:
    - known valid inputs
    - explicit branch-distance formulas
    - manual fitness logic
    """

    return f"""
    You are helping with a Search-Based Software Testing project.

    Given the following Python function, infer the meaningful branch/path targets from the control flow and generate a branch-distance-style fitness function.

    Assumptions:
    - Infer argument types from how the function uses each argument.
    - Arguments may be int, float, bool, str, or list[int].
    - The generated fitness function must not call the original function.
    - Infer the input type of each argument from how the function uses it.
    - Supported argument types are: int, float, bool, str, and list_int.
    - The chromosome is a list of argument values in the same order as the function signature.
    - The generated fitness function must not import packages.
    - The generated fitness function must not use randomness.
    - For strings, assume normal Python strings.
    - For list[int], assume a Python list of integers.

    Generate Python code that defines:
    1. TARGETS_{function_name}: a list of target branch/path names.
    2. fitness_{function_name}(chromosome, target): returns 0 when the chromosome covers the selected target and a positive value otherwise.

    Requirements:
    - Use clear target names.
    - Return 0 only when the selected target branch/path is covered.
    - Use positive branch-distance-like values when the target is not covered.
    - Smaller positive values should mean closer to the target.
    - If target is unknown, raise ValueError.
    - The fitness_code field must contain properly formatted multi-line Python code with newline characters between statements and function definitions. Do not compress the code into a single line.
    - Return only executable Python code inside the fitness_code field.
    - Do not include markdown code fences inside fitness_code.
    - Do not include explanations outside the requested JSON object.
    - Every statement must appear on a separate line when needed.
    - Every function definition must start on its own line.
    - Do not compress the code into a single line.
    - The fitness function must never return a negative value.
    - Every return value must be >= 0.
    - If using arithmetic distances, wrap them with max(0, distance) when needed.
    - Every fitness value must be greater than or equal to 0.
    - If the original function returns string labels, target names must exactly match those return string labels.
    - Do not invent target names such as "positive_branch" if the function returns "positive".
    - For every target, fitness must return 0 if and only if the original function would return that exact target label.
    - Fitness must return a positive value for inputs that reach a different returned label.


    Function name:
    {function_name}

    Function source:
    {function_source}

    You must also generate an input_schema field.

    The input_schema must be a list with one dictionary per function argument, in the same order as the function signature.

    Strict input_schema rules:
    - Do not use extremely large numbers.
    - All numeric values in input_schema must be finite and less than 100000.
    - Use only these schema types: int, float, bool, str, list_int.
    - For int schemas, use practical bounded values only.
    - For float schemas, use practical bounded values only.
    - For str schemas, max_len must be at most 20.
    - For list_int schemas, max_len must be at most 8.
    - For list_int schemas, element min and max must be between -100 and 100.
    - Never use infinity, huge constants, exponential notation, or repeated long digits.
    - Prefer the exact schema examples below unless the function clearly needs a different range.

    Use these schema formats exactly:

    For integer:
    {{"type": "int", "min": -500, "max": 3000}}

    For float:
    {{"type": "float", "min": 0.0, "max": 3000.0}}

    For boolean:
    {{"type": "bool"}}

    For string:
    {{"type": "str", "min_len": 0, "max_len": 15}}

    For list of integers:
    {{"type": "list_int", "min_len": 0, "max_len": 6, "min": -100, "max": 100}}

    Return a JSON object with exactly these fields:
    - function_name
    - fitness_function_name
    - targets
    - input_schema
    - fitness_code
    - notes
    """.strip()


def build_repair_prompt(
    function_name: str,
    function_source: str,
    previous_error: str,
    previous_code: str,
) -> str:
    """
    Build a repair prompt when the previous generated fitness function failed.
    """

    return f"""
    The previous generated fitness function failed.

    Function name:
    {function_name}

    Original function source:
    {function_source}

    Previous generated fitness_code:
    {previous_code}

    Error message:
    {previous_error}

    Please regenerate the full corrected JSON response.

    Important:
    - Return the same JSON fields as before.
    - The fitness_code must be complete executable Python code.
    - Do not return partial code.
    - Do not include markdown fences.
    - Make sure the generated code compiles.
    - Fix semantic errors so that fitness == 0 exactly when the original function returns the selected target label.
    - Target names must exactly match the return string labels of the original function.

    {build_zero_shot_prompt(function_name, function_source)}
    """.strip()

def save_prompt_template() -> None:
    PROMPT_DIR.mkdir(exist_ok=True)

    template = """
    You are helping with a Search-Based Software Testing project.

    Given the following Python function, generate a fitness function for branch/path coverage.

    The generated fitness function must:
    1. Be named exactly fitness_<function_name>(chromosome, target).
    2. Treat chromosome as a list of argument values in the same order as the function signature.
    3. Use the target parameter to select which branch/path should be covered.
    4. Return 0 when the chromosome covers the selected target branch/path.
    5. Return a positive numeric value when the chromosome does not cover the selected target.
    6. Use branch-distance style logic where possible.
    7. Not call the original target function inside the fitness function.
    8. Not import any package.
    9. Not use random numbers.
    10. Not print anything.
    11. Return only executable Python code inside the fitness_code field.
    12. Do not include markdown code fences inside fitness_code.

    Python function name:
    <function_name>

    Python source code:
    <function_source>
    """.strip()

    (PROMPT_DIR / "zero_shot_prompt_template.txt").write_text(template + "\n", encoding="utf-8")




def discover_target_functions():

    functions = {}

    for name, obj in inspect.getmembers(target_functions, inspect.isfunction):
        if obj.__module__ == target_functions.__name__:
            functions[name] = obj

    return functions

def clean_generated_code(code: str) -> str:
    if code is None:
        return ""

    code = str(code).strip()

    cleaned_lines = []
    for line in code.splitlines():
        if line.strip().startswith("```"):
            continue
        cleaned_lines.append(line)

    code = "\n".join(cleaned_lines).strip()

    if code.startswith("python\n"):
        code = code[len("python\n"):].strip()

    code = code.replace("\\n", "\n")
    code = code.replace("\\t", "    ")

    # Only fix extremely obvious issue (multiple defs on one line)
    code = code.replace(")def ", ")\ndef ")

    if (code.startswith('"') and code.endswith('"')) or (
        code.startswith("'") and code.endswith("'")
    ):
        try:
            code = ast.literal_eval(code)
        except Exception:
            code = code[1:-1]

    return code.strip()


def check_code_compiles(code: str) -> Tuple[bool, Optional[str]]:
    code = clean_generated_code(code)

    try:
        ast.parse(code)
        compile(code, "<generated_fitness>", "exec")
        return True, None
    except SyntaxError as error:
        return False, str(error)


def is_zero(value) -> bool:
    try:
        return abs(float(value)) < 1e-9
    except Exception:
        return value == 0


def check_known_valid_inputs(function_name: str, code: str, known_valid_inputs: dict) -> Tuple[bool, Optional[str]]:

    if not known_valid_inputs:
        return True, None

    namespace = {}

    try:
        exec(code, namespace)
    except Exception as error:
        return False, f"Generated code failed during exec: {error}"

    fitness_name = f"fitness_{function_name}"

    if fitness_name not in namespace:
        return False, f"Generated code does not define {fitness_name}"

    fitness_function = namespace[fitness_name]

    failures = []

    for target, chromosome in known_valid_inputs.items():
        try:
            fitness_value = fitness_function(chromosome, target)
        except Exception as error:
            failures.append(f"target={target}, chromosome={chromosome}, error={error}")
            continue

        if not is_zero(fitness_value):
            failures.append(
                f"target={target}, chromosome={chromosome}, fitness={fitness_value}, expected 0"
            )

    if failures:
        return False, "\n".join(failures)

    return True, None


class LLMResponse:
    def __init__(self, text: str):
        self.text = text


def request_llm(client, prompt: str, function_name: str):
    max_retries = 5

    for attempt in range(1, max_retries + 1):
        try:
            print(
                f"Sending request for {function_name} | "
                f"provider={LLM_PROVIDER}, model={MODEL_NAME}, attempt {attempt}/{max_retries}"
            )

            if LLM_PROVIDER == "gemini":
                response = client.models.generate_content(
                    model=MODEL_NAME,
                    contents=prompt,
                    config=types.GenerateContentConfig(
                        response_mime_type="application/json",
                        response_schema=FitnessGenerationResult,
                    ),
                )
                return LLMResponse(response.text)

            elif LLM_PROVIDER == "groq":
                try:
                    response = client.chat.completions.create(
                        model=MODEL_NAME,
                        messages=[
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.0,
                        response_format={"type": "json_object"},
                    )
                except Exception:
                    response = client.chat.completions.create(
                        model=MODEL_NAME,
                        messages=[
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.0,
                    )

                content = response.choices[0].message.content

                if not content:
                    raise RuntimeError(f"Empty response from {LLM_PROVIDER}:{MODEL_NAME}")

                return LLMResponse(content)

            else:
                raise ValueError(f"Unsupported LLM_PROVIDER: {LLM_PROVIDER}")

        except Exception as error:
            msg = str(error)

            if (
                "503" in msg
                or "UNAVAILABLE" in msg
                or "429" in msg
                or "RESOURCE_EXHAUSTED" in msg
                or "rate_limit" in msg.lower()
            ):
                wait_time = 10 * attempt
                print(f"Temporary LLM error for {function_name}: {error}")
                print(f"Waiting {wait_time} seconds before retrying...")
                time.sleep(wait_time)
            else:
                raise

    raise RuntimeError(
        f"{LLM_PROVIDER}:{MODEL_NAME} failed after {max_retries} retries for {function_name}"
    )


def save_raw_response(function_name: str, response_text: str) -> None:
    RAW_OUTPUT_DIR.mkdir(exist_ok=True)

    path = RAW_OUTPUT_DIR / f"{function_name}_zero_shot_raw_response.json"

    try:
        parsed = json.loads(response_text)
        path.write_text(json.dumps(parsed, indent=2), encoding="utf-8")
    except Exception:
        path.write_text(response_text, encoding="utf-8")


def append_generation_log(message: str) -> None:
    RAW_OUTPUT_DIR.mkdir(exist_ok=True)

    path = RAW_OUTPUT_DIR / "zero_shot_generation_log.txt"

    with path.open("a", encoding="utf-8") as file:
        file.write(message + "\n")



def sample_value(schema):
    t = schema["type"]

    if t == "int":
        return random.randint(int(schema.get("min", -500)), int(schema.get("max", 3000)))

    if t == "float":
        return random.uniform(float(schema.get("min", 0.0)), float(schema.get("max", 3000.0)))

    if t == "bool":
        return random.choice([True, False])

    if t == "str":
        alphabet = string.ascii_letters + string.digits
        length = random.randint(int(schema.get("min_len", 0)), int(schema.get("max_len", 15)))
        return "".join(random.choice(alphabet) for _ in range(length))

    if t == "list_int":
        length = random.randint(int(schema.get("min_len", 0)), int(schema.get("max_len", 6)))
        min_val = int(schema.get("min", -20))
        max_val = int(schema.get("max", 20))
        return [random.randint(min_val, max_val) for _ in range(length)]

    raise ValueError(f"Unsupported schema type: {t}")


def sample_chromosome(input_schema):
    return [sample_value(schema) for schema in input_schema]


def semantic_validate_generated_fitness(function_name, function_obj, result, num_samples=300):

    namespace = {}
    exec(result.fitness_code, namespace)

    fitness_fn = namespace[f"fitness_{function_name}"]
    input_schema = [item.model_dump(exclude_none=True) for item in result.input_schema]

    mismatches = 0
    checked = 0
    actual_labels_seen = set()

    random.seed(12345)

    for _ in range(num_samples):
        chromosome = sample_chromosome(input_schema)

        try:
            actual_label = function_obj(*chromosome)
        except Exception:
            continue

        actual_labels_seen.add(actual_label)

        for target in result.targets:
            try:
                fitness_value = fitness_fn(chromosome, target)
                is_zero = abs(float(fitness_value)) < 1e-9
            except Exception:
                mismatches += 1
                checked += 1
                continue

            should_be_zero = actual_label == target

            if is_zero != should_be_zero:
                mismatches += 1

            checked += 1

    if checked == 0:
        return False, "No valid samples could be checked."

    mismatch_rate = mismatches / checked

    # Require target names to match observed labels when labels are strings.
    missing_targets = actual_labels_seen - set(result.targets)

    if missing_targets:
        return False, (
            f"Target names do not match original return labels. "
            f"Observed labels missing from targets: {missing_targets}"
        )

    if mismatch_rate > 0.05:
        return False, f"Semantic mismatch rate too high: {mismatch_rate:.3f}"

    return True, f"Semantic validation passed. mismatch_rate={mismatch_rate:.3f}"


def generate_for_one_function(function_name: str, function_obj) -> FitnessGenerationResult:
    if LLM_PROVIDER == "gemini":
        api_key = os.getenv("GEMINI_API_KEY")

        if not api_key:
            raise EnvironmentError(
                "GEMINI_API_KEY is not set. Run:\n"
                'export GEMINI_API_KEY="your_real_api_key_here"'
            )

        client = genai.Client(api_key=api_key)

    elif LLM_PROVIDER == "groq":
        api_key = os.getenv("GROQ_API_KEY")

        if not api_key:
            raise EnvironmentError(
                "GROQ_API_KEY is not set. Run:\n"
                'export GROQ_API_KEY="your_real_groq_api_key_here"'
            )

        client = OpenAI(
            api_key=api_key,
            base_url="https://api.groq.com/openai/v1",
        )

    else:
        raise ValueError(f"Unsupported LLM_PROVIDER: {LLM_PROVIDER}")
    function_source = inspect.getsource(function_obj)

    expected_name = f"fitness_{function_name}"

    last_error = ""
    last_code = ""

    for generation_attempt in range(1, MAX_GENERATION_ATTEMPTS + 1):
        print(
            f"Fitness generation attempt {generation_attempt}/"
            f"{MAX_GENERATION_ATTEMPTS} for {function_name}"
        )

        if generation_attempt == 1:
            prompt = build_zero_shot_prompt(
                function_name=function_name,
                function_source=function_source,
            )
        else:
            prompt = build_repair_prompt(
                function_name=function_name,
                function_source=function_source,
                previous_error=last_error,
                previous_code=last_code,
            )

        response = request_llm(client, prompt, function_name)

        save_raw_response(
            function_name=f"{function_name}_attempt_{generation_attempt}",
            response_text=response.text,
        )

        try:
            result = FitnessGenerationResult.model_validate_json(response.text)
        except Exception as error:
            last_error = f"JSON parse failed: {error}"
            last_code = response.text
            append_generation_log(
                f"{function_name}: attempt {generation_attempt} failed JSON parsing: {error}"
            )
            continue

        result.fitness_code = clean_generated_code(result.fitness_code)
        last_code = result.fitness_code

        if result.fitness_function_name != expected_name:
            last_error = (
                f"Wrong fitness function name. "
                f"Expected {expected_name}, got {result.fitness_function_name}"
            )
            append_generation_log(
                f"{function_name}: attempt {generation_attempt} failed name check: {last_error}"
            )
            continue

        compiles, syntax_error = check_code_compiles(result.fitness_code)

        if not compiles:
            last_error = f"Generated code does not compile: {syntax_error}"
            append_generation_log(
                f"{function_name}: attempt {generation_attempt} failed compile check: {syntax_error}"
            )

            print("=" * 80)
            print(f"INVALID GENERATED CODE FOR: {function_name}")
            print(f"Attempt: {generation_attempt}")
            print("=" * 80)
            print(result.fitness_code)
            print("=" * 80)

            continue
        if not ENABLE_SEMANTIC_VALIDATION:
            append_generation_log(
                f"{function_name}: accepted attempt {generation_attempt} "
                f"without semantic validation"
            )
            return result

        semantic_ok, semantic_message = semantic_validate_generated_fitness(
            function_name=function_name,
            function_obj=function_obj,
            result=result,
            num_samples=300,
        )

        if not semantic_ok:
            last_error = semantic_message
            append_generation_log(
                f"{function_name}: attempt {generation_attempt} failed semantic validation: {semantic_message}"
            )
            print(f"SEMANTIC VALIDATION FAILED for {function_name}: {semantic_message}")
            continue

        append_generation_log(
            f"{function_name}: semantic validation passed on attempt {generation_attempt}: {semantic_message}"
        )

        return result

    raise RuntimeError(
        f"{function_name}: failed after {MAX_GENERATION_ATTEMPTS} "
        f"generation attempts. Last error: {last_error}"
    )


def save_generated_fitness(
    results: List[FitnessGenerationResult],
    output_file: Path = OUTPUT_FILE,
    label: str = "validated",
) -> None:
    with output_file.open("w", encoding="utf-8") as file:
    
        file.write(f"# {output_file.name}\n")
        file.write("# Generated by generate_fitness_zero_shot.py\n")
        file.write(f"# Provider: {LLM_PROVIDER}\n")
        file.write(f"# Model: {MODEL_NAME}\n")
        file.write(f"# Fitness version: {label}\n")
        file.write("# One-function-at-a-time LLM fitness generation.\n\n")

        file.write("GENERATED_TARGETS = {\n")
        for result in results:
            file.write(f"    '{result.function_name}': {result.targets},\n")
        file.write("}\n\n")

        file.write("GENERATED_INPUT_SCHEMAS = {\n")
        for result in results:
            schema_as_dicts = [item.model_dump(exclude_none=True) for item in result.input_schema]
            file.write(f"    '{result.function_name}': {schema_as_dicts},\n")
        file.write("}\n\n")

        for result in results:
            file.write("# " + "=" * 80 + "\n")
            file.write(f"# Original function: {result.function_name}\n")
            file.write(f"# Fitness function: {result.fitness_function_name}\n")
            file.write(f"# LLM targets: {result.targets}\n")
            file.write(f"# Notes: {result.notes}\n")
            file.write("# " + "=" * 80 + "\n\n")
            file.write(result.fitness_code.strip())
            file.write("\n\n")

        file.write("# " + "=" * 80 + "\n")
        file.write("# Unified fitness interface\n")
        file.write("# " + "=" * 80 + "\n\n")

        file.write("def evaluate_fitness(function_name, chromosome, target):\n")

        for index, result in enumerate(results):
            keyword = "if" if index == 0 else "elif"
            file.write(f"    {keyword} function_name == '{result.function_name}':\n")
            file.write(f"        return {result.fitness_function_name}(chromosome, target)\n")

        file.write("    else:\n")
        file.write("        raise ValueError(f'Unknown function name: {function_name}')\n")

    print(f"Saved generated fitness functions to: {output_file}")



def save_generation_summary(results, failed) -> None:

    RAW_OUTPUT_DIR.mkdir(exist_ok=True)

    summary = {
        "provider": LLM_PROVIDER,
        "model": MODEL_NAME,
        "model_slug": MODEL_SLUG,
        "semantic_validation_enabled": ENABLE_SEMANTIC_VALIDATION,
        "max_generation_attempts": MAX_GENERATION_ATTEMPTS,
        "successful_count": len(results),
        "failed_count": len(failed),
        "successful_functions": [result.function_name for result in results],
        "failed_functions": failed,
    }

    path = RAW_OUTPUT_DIR / "generation_summary.json"

    path.write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )

    print(f"Generation summary saved to: {path}")



def main() -> None:
    save_prompt_template()

    results = []
    failed = []

    target_funcs = discover_target_functions()

    for function_name, function_obj in target_funcs.items():
        print("=" * 80)
        print(f"Generating zero-shot fitness function for: {function_name}")

        try:
            result = generate_for_one_function(function_name, function_obj)
            results.append(result)
            print(f"SUCCESS: {function_name}")

        except Exception as error:
            print(f"FAILED: {function_name}")
            print(f"Reason: {error}")

            append_generation_log(
                f"{function_name}: FAILED during generation: {error}"
            )

            failed.append({
                "function_name": function_name,
                "error": str(error),
            })

            continue

    if results:
        save_generated_fitness(
            results,
            output_file=OUTPUT_FILE,
            label=FITNESS_VERSION_LABEL,
        )
    else:
        print("No fitness functions were generated successfully.")

    save_generation_summary(results, failed)

    print("\nDone.")
    print(f"Successful generations: {len(results)}")
    print(f"Failed generations: {len(failed)}")

    if failed:
        print("\nFailed functions:")
        for item in failed:
            print(f" - {item['function_name']}: {item['error']}")

    if results:
        print(f"\nGenerated file: {OUTPUT_FILE}")
        print("Next step: run your generated-fitness checker or experiments.")


if __name__ == "__main__":
    main()