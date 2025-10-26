import os
import requests
from dotenv import load_dotenv

# 初始化环境变量
def init_environment():
    load_dotenv()
    return {
        "api_key": os.getenv("API_KEY"),
        "api_url": os.getenv("API_URL"),
        "model_name": os.getenv("MODEL_NAME")
    }

# 读取提示词模板
def load_prompt_template(template_path="prompt_template.txt"):
    try:
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read().strip()
    except Exception as e:
        return f"Error loading prompt template: {str(e)}"

# 构建API请求参数
def build_api_request(environment, prompt):
    return {
        "url": environment["api_url"],
        "headers": {
            "Authorization": f"Bearer {environment['api_key']}",
            "Content-Type": "application/json"
        },
        "json": {
            "model": environment["model_name"],
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.3
        }
    }

# 核心函数：生成函数注释
def generate_function_comment(function_code, environment):
    # 输入校验
    if not function_code.strip().startswith("def "):
        return "Input must be a Python function starting with 'def'"

    # 加载并填充提示词
    prompt_template = load_prompt_template()
    if prompt_template.startswith("Error"):
        return prompt_template
    prompt = prompt_template.replace("{function_code}", function_code)

    # 发送API请求
    try:
        request_params = build_api_request(environment, prompt)
        response = requests.post(**request_params, timeout=30)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        return "API key unauthorized" if e.response.status_code == 401 else f"HTTP error {e.response.status_code}"
    except Exception as e:
        return f"Request failed: {str(e)}"

    try:
        response_data = response.json()
        comment_content = response_data["choices"][0]["message"]["content"].strip()
    except (KeyError, IndexError) as e:
        return f"Invalid API response format: {str(e)}"
    return f'"""\n{comment_content}\n"""'

# 主流程：用"END"指令结束输入（支持函数内空行）
def main():
    environment = init_environment()
    print("=== Function Comment Generator ===")
    print("1. Paste your Python function (empty lines in function are allowed)")
    print("2. Enter 'END' (on a new line) to finish input\n")
    function_lines = []

    while True:
        line = input()
        if line.strip().upper() == "END":
            break
        function_lines.append(line)

    function_code = "\n".join(function_lines)
    print("\nGenerated comment:")
    print(generate_function_comment(function_code, environment))

if __name__ == "__main__":
    main()
