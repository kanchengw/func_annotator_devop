"""生成Python函数注释的工具，集成API调用及实验跟踪功能
"""
import os
import requests
import mlflow
import dagshub
import time
import re
from dotenv import load_dotenv


env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), '.env')
load_dotenv(dotenv_path=env_path)


def init_environment():
    # 关键：加载挂载的 docker.env（容器内路径固定为 /app/config/docker.env）
    mounted_env_path = "/app/config/docker.env"
    if os.path.exists(mounted_env_path):
        load_dotenv(dotenv_path=mounted_env_path)  # 优先加载挂载的配置文件

    env = {
        "api_key": os.getenv("API_KEY"),
        "api_url": os.getenv("API_URL"),
        "model_name": os.getenv("MODEL_NAME"),
        "model_temperature": os.getenv("MODEL_TEMPERATURE"),
    }
    if not all(env[key] for key in ["api_key", "api_url", "model_name"]):
        return None
    if not os.getenv("CI"):
        mlflow_tracking_uri = os.getenv("MLFLOW_TRACKING_URI")
        mlflow_experiment = os.getenv("MLFLOW_EXPERIMENT")
        if mlflow_tracking_uri and mlflow_experiment:
            mlflow.set_tracking_uri(mlflow_tracking_uri)
            mlflow.set_experiment(mlflow_experiment)
        dagshub.init(
            repo_name=os.getenv("DAGSHUB_REPO"),
            repo_owner=os.getenv("DAGSHUB_USER"),
            mlflow=True,
            host="https://dagshub.com"
        )
    return env


def load_prompt_template():
    """加载根目录的prompt_template.txt提示词模板"""
    template_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'prompt_template.txt')
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except FileNotFoundError:
        return (
            "Please generate annotation for the following Python function.\n"
            "The annotation must include 3 parts:\n"
            "1. Input: description of input parameters\n"
            "2. Processing: specific operation steps\n"
            "3. Output: description of return value\n\n"
            "Requirements:\n"
            "- Use English only\n"
            "- Plain text format (no Markdown/code blocks)\n"
            "- No extra content\n- Keep concise\n\n{function_code}"
        )

def calculate_completeness(annotation: str) -> float:
    has_input = bool(re.search(r'input|parameters|param', annotation, re.IGNORECASE))
    has_processing = bool(re.search(r'processing|steps|operation|do', annotation, re.IGNORECASE))
    has_output = bool(re.search(r'output|return|result', annotation, re.IGNORECASE))
    return (has_input + has_processing + has_output) / 3

def calculate_comment_density(annotation: str, function_code: str) -> float:
    cleaned_annotation = re.sub(r'\s+', '', annotation)
    cleaned_annotation = re.sub(r'(.)\1+', r'\1', cleaned_annotation)
    function_valid_chars = re.sub(r'\s+', '', function_code)
    if len(function_valid_chars) == 0:
        return 0.0
    return round(len(cleaned_annotation) / len(function_valid_chars), 4)

def build_api_request(environment, prompt):
    model_name = environment["model_name"].lower()
    base_params = {
        "url": environment["api_url"],
        "headers": {
            "Authorization": f"Bearer {environment['api_key']}",
            "Content-Type": "application/json"
        }
    }
    temperature = float(environment["model_temperature"])
    
    if model_name.startswith("qwen"):
        return {
            **base_params,
            "json": {
                "model": environment["model_name"],
                "input": {"prompt": prompt},
                "parameters": {
                    "temperature": temperature,
                    "max_tokens": 1024
                }
            }
        }
    elif model_name.startswith("glm"):
        return {
            **base_params,
            "json": {
                "model": environment["model_name"],
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature,
                "max_tokens": 1024
            }
        }
    else:
        return {
            **base_params,
            "json": {
                "model": environment["model_name"],
                "messages": [{"role": "user", "content": prompt}],
                "temperature": temperature
            }
        }

def generate_function_comment(function_code, environment):
    error_occurred = False
    error_msg = ""
    func_name = "unknown"
    input_length = len(function_code.strip())
    
    if not environment:
        error_msg = "Problems in API settings, please check."
        error_occurred = True
    elif not function_code.strip().startswith("def "):
        error_msg = "Input must be a Python function starting with 'def'"
        error_occurred = True
    else:
        func_name = function_code.split()[1].split('(')[0]
        prompt = load_prompt_template().replace("{function_code}", function_code)
        request_params = build_api_request(environment, prompt)
        if not request_params:
            error_msg = "Problems in API settings, please check."
            error_occurred = True

    if error_occurred:
        if not os.getenv("CI"):
            with mlflow.start_run(run_name=f"{environment['model_name']}_{func_name}_error"):
                mlflow.log_param("model", environment["model_name"] if environment else "unknown")
                mlflow.log_param("function_name", func_name)
                mlflow.log_param("error", error_msg)
                mlflow.log_metric("input_length", input_length)
                mlflow.log_metric("error_rate", 1.0)
        return error_msg

    try:
        start_time = time.time()
        response = requests.post(**request_params, timeout=30)
        response.raise_for_status()
        latency = round(time.time() - start_time, 4)
    except requests.exceptions.RequestException as exc:
        error_msg = f"API request failed: {str(exc)}"
        if not os.getenv("CI"):
            with mlflow.start_run(run_name=f"{environment['model_name']}_{func_name}_api_error"):
                mlflow.log_param("model", environment["model_name"])
                mlflow.log_param("function_name", func_name)
                mlflow.log_param("error", error_msg)
                mlflow.log_metric("input_length", input_length)
                mlflow.log_metric("error_rate", 1.0)
        return "Problems in API connection, please check."

    try:
        response_data = response.json()
        model_name = environment["model_name"].lower()
        
        if model_name.startswith("qwen"):
            comment_content = response_data["output"]["text"].strip()
        else:
            comment_content = response_data["choices"][0]["message"]["content"].strip()
        
        output_length = len(comment_content)
        completeness = calculate_completeness(comment_content)
        comment_density = calculate_comment_density(comment_content, function_code)
        error_rate = 0.0

        comment = f'"""\n{comment_content}\n"""'

        if not os.getenv("CI"):
            with mlflow.start_run(run_name=f"{environment['model_name']}_{func_name}"):
                mlflow.log_param("model", environment["model_name"])
                mlflow.log_param("temperature", environment["model_temperature"])
                mlflow.log_param("function_name", func_name)
                mlflow.log_metric("input_length", input_length)
                mlflow.log_metric("output_length", output_length)
                mlflow.log_metric("latency", latency)
                mlflow.log_metric("completeness", completeness)
                mlflow.log_metric("comment_density", comment_density)
                mlflow.log_metric("error_rate", error_rate)
                mlflow.log_text(comment_content, f"{func_name}_annotation.txt")
                mlflow.log_text(function_code, f"{func_name}_input.txt")
        
        return comment
    except (KeyError, ValueError) as exc:
        error_msg = f"Invalid API response: {str(exc)}"
        if not os.getenv("CI"):
            with mlflow.start_run(run_name=f"{environment['model_name']}_{func_name}_response_error"):
                mlflow.log_param("model", environment["model_name"])
                mlflow.log_param("function_name", func_name)
                mlflow.log_param("error", error_msg)
                mlflow.log_metric("input_length", input_length)
                mlflow.log_metric("error_rate", 1.0)
        return "Problems in API response, please check."

def main():
    print("=== Function Comment Generator ===")
    print("1. Paste your Python function code (empty lines allowed)")
    print("2. Type 'END' on a new line and press Enter to finish input\n")
    function_lines = []
    while True:
        line = input()
        if line.strip().upper() == 'END':
            break
        function_lines.append(line)
    function_code = "\n".join(function_lines)
    env = init_environment()
    print("\nGenerated comment:")
    print(generate_function_comment(function_code, env))

if __name__ == "__main__":
    main()