"""生成func_annotator.py: 生成Python函数注释的工具，集成API调用（适配GLM-4等通用模型）及实验跟踪功能
"""

# 导入必要的库
import os
import requests
import mlflow
import dagshub
from dotenv import load_dotenv

load_dotenv()  # 加载.env文件中的环境变量到系统环境变量


def init_environment():
    """初始化环境变量（本地启用实验跟踪，CI仅验证API）"""
    env = {
        "api_key": os.getenv("API_KEY"),
        "api_url": os.getenv("API_URL"),
        "model_name": os.getenv("MODEL_NAME"),
        "model_temperature": os.getenv("MODEL_TEMPERATURE"),
    }

    if not all(env[key] for key in ["api_key", "api_url", "model_name"]):
        return None

    if not os.getenv("CI"):
        dagshub.init(
            repo_name=os.getenv("DAGSHUB_REPO"),
            repo_owner=os.getenv("DAGSHUB_USER"),
            mlflow=True,
            host="https://dagshub.com"
        )
        mlflow.set_experiment(os.getenv("MLFLOW_EXPERIMENT"))

    return env


def load_prompt_template(template_path="prompt_template.txt"):
    """加载提示词模板，默认返回备用模板"""
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
            ** base_params,
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
    """生成函数注释（根据环境决定是否启用MLflow跟踪）"""
    if not environment:
        return "Problems in API settings, please check."

    if not function_code.strip().startswith("def "):
        return "Input must be a Python function starting with 'def'"

    prompt = load_prompt_template().replace("{function_code}", function_code)
    request_params = build_api_request(environment, prompt)
    if not request_params:
        return "Problems in API settings, please check."

    func_name = function_code.split()[1].split('(')[0]

    try:
        response = requests.post(**request_params, timeout=30)
        response.raise_for_status()
    except requests.exceptions.RequestException as exc:
        if not os.getenv("CI"):
            with mlflow.start_run():
                mlflow.log_param("model", environment["model_name"])
                mlflow.log_param("function_name", func_name)
                mlflow.log_param("error", f"API request failed: {str(exc)}")
        return "Problems in API connection, please check."

    try:
        response_data = response.json()
        model_name = environment["model_name"].lower()
        
        if model_name.startswith("qwen"):
            comment_content = response_data["output"]["text"].strip()
        else:
            comment_content = response_data["choices"][0]["message"]["content"].strip()

        comment = f'"""\n{comment_content}\n"""'
        if not os.getenv("CI"):
            with mlflow.start_run():
                mlflow.log_param("model", environment["model_name"])
                mlflow.log_param("temperature", environment["model_temperature"])
                mlflow.log_param("function_name", func_name)
                mlflow.log_metric("status_code", response.status_code)
                mlflow.log_text(comment_content, "generated_comment.txt")
        return comment

    except (KeyError, ValueError) as exc:
        if not os.getenv("CI"):
            with mlflow.start_run():
                mlflow.log_param("function_name", func_name)
                mlflow.log_param("error", f"Invalid API response: {str(exc)}")
        return "Problems in API response, please check."


def main():
    """命令行交互入口"""
    env = init_environment()
    if not env:
        print("Initialization failed: please check environment variables")
        return

    # 显示英文交互提示
    print("=== Function Comment Generator ===")
    print("1. Paste your Python function code (empty lines allowed)")
    print("2. Type 'END' on a new line and press Enter to finish input\n")

    # 读取用户输入（忽略END大小写）
    function_lines = []
    while True:
        line = input()
        if line.strip().upper() == 'END':  # 大小写不敏感
            break
        function_lines.append(line)
    function_code = "\n".join(function_lines)

    # 生成并打印注释（英文提示）
    print("\nGenerated comment:")
    print(generate_function_comment(function_code, env))


if __name__ == "__main__":
    main()