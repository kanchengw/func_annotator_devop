"""生成func_annotator.py: 生成Python函数注释的工具，集成API调用（适配GLM-4等通用模型）及实验跟踪功能
"""

# 导入必要的库
import os  # 用于处理环境变量和文件路径
import requests  # 用于发送HTTP请求，调用API
import mlflow  # 用于实验跟踪，记录参数、指标等
import dagshub  # 用于集成DAGShub平台，支持MLflow跟踪
from dotenv import load_dotenv  # 用于加载.env文件中的环境变量

load_dotenv()  # 加载.env文件中的环境变量到系统环境变量


def init_environment():
    """初始化环境变量（本地启用实验跟踪，CI仅验证API）"""
    # 从环境变量中获取API相关配置
    env = {
        "api_key": os.getenv("API_KEY"),  # API密钥
        "api_url": os.getenv("API_URL"),  # API请求地址
        "model_name": os.getenv("MODEL_NAME"),  # 使用的模型名称
        "model_temperature": os.getenv("MODEL_TEMPERATURE"),  # 模型生成的温度参数（控制随机性）
    }

    # 验证核心配置是否齐全（API密钥、地址、模型名称为必需）
    if not all(env[key] for key in ["api_key", "api_url", "model_name"]):
        return None  # 配置不齐全则返回None

    # 非CI环境（本地环境）初始化DAGShub和MLflow
    if not os.getenv("CI"):
        # 初始化DAGShub，关联仓库并启用MLflow集成
        dagshub.init(
            repo_name=os.getenv("DAGSHUB_REPO"),  # DAGShub仓库名称
            repo_owner=os.getenv("DAGSHUB_USER"),  # DAGShub仓库所有者
            mlflow=True,  # 启用MLflow跟踪
            host="https://dagshub.com"  # DAGShub主机地址
        )
        # 设置MLflow实验名称
        mlflow.set_experiment(os.getenv("MLFLOW_EXPERIMENT"))

    return env  # 返回初始化后的环境配置


def load_prompt_template(template_path="prompt_template.txt"):
    """加载提示词模板，默认返回备用模板"""
    try:
        # 尝试从指定路径读取提示词模板文件
        with open(template_path, 'r', encoding='utf-8') as f:
            return f.read().strip()  # 返回模板内容（去除首尾空白）
    except FileNotFoundError:
        # 若模板文件不存在，返回默认的备用模板
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
    """构建兼容主流模型的API请求参数"""
    # 检查环境配置中是否包含API地址和模型名称（必需参数）
    if not all([environment.get("api_url"), environment.get("model_name")]):
        return None  # 参数不全则返回None

    # 构建API请求参数（包含URL、请求头、请求体）
    return {
        "url": environment["api_url"],  # API请求地址
        "headers": {
            "Authorization": f"Bearer {environment['api_key']}",  # 认证头（Bearer令牌）
            "Content-Type": "application/json"  # 请求体格式为JSON
        },
        "json": {
            "model": environment["model_name"],  # 指定使用的模型
            "messages": [{"role": "user", "content": prompt}],  # 用户提示词（对话格式）
            "temperature": environment["model_temperature"]  # 模型生成温度参数
        }
    }


def generate_function_comment(function_code, environment):
    """生成函数注释（根据环境决定是否启用MLflow跟踪）"""
    # 检查环境配置是否有效
    if not environment:
        return "Problems in API settings, please check."  # 返回配置错误提示

    # 检查输入是否为合法的Python函数（以def开头）
    if not function_code.strip().startswith("def "):
        return "Input must be a Python function starting with 'def'"  # 返回输入格式错误提示

    # 加载提示词模板，并将函数代码注入模板中的{function_code}占位符
    prompt = load_prompt_template().replace("{function_code}", function_code)
    # 构建API请求参数
    request_params = build_api_request(environment, prompt)
    if not request_params:
        return "Problems in API settings, please check."  # 请求参数构建失败提示

    # 从函数代码中提取函数名（用于MLflow日志记录）
    func_name = function_code.split()[1].split('(')[0]

    try:
        # 发送API请求（使用**解包请求参数），设置30秒超时
        response = requests.post(** request_params, timeout=30)
        response.raise_for_status()  # 若HTTP状态码为错误码（4xx/5xx），抛出异常
    except requests.exceptions.RequestException as exc:
        # 处理API请求异常（网络错误、超时等）
        # 本地环境下，记录错误信息到MLflow
        if not os.getenv("CI"):
            with mlflow.start_run():  # 启动MLflow运行记录
                mlflow.log_param("model", environment["model_name"])  # 记录使用的模型
                mlflow.log_param("function_name", func_name)  # 记录函数名
                mlflow.log_param("error", f"API request failed: {str(exc)}")  # 记录错误信息
        return "Problems in API connection, please check."  # 返回连接错误提示

    try:
        # 解析API响应，提取生成的注释内容（假设响应为OpenAI兼容格式）
        comment_content = response.json()["choices"][0]["message"]["content"].strip()
        # 格式化注释为Python文档字符串格式（前后加"""）
        comment = f'"""\n{comment_content}\n"""'
        # 本地环境下，记录实验数据到MLflow
        if not os.getenv("CI"):
            with mlflow.start_run():  # 启动MLflow运行记录
                mlflow.log_param("model", environment["model_name"])  # 记录模型名称
                mlflow.log_param("temperature", environment["model_temperature"])  # 记录温度参数
                mlflow.log_param("function_name", func_name)  # 记录函数名
                mlflow.log_metric("status_code", response.status_code)  # 记录HTTP状态码
                mlflow.log_text(comment_content, "generated_comment.txt")  # 记录生成的注释
        return comment  # 返回生成的注释

    except (KeyError, ValueError) as exc:
        # 处理响应解析异常（响应格式错误、JSON解析失败等）
        if not os.getenv("CI"):
            with mlflow.start_run():
                mlflow.log_param("function_name", func_name)  # 记录函数名
                mlflow.log_param("error", f"Invalid API response: {str(exc)}")  # 记录解析错误
        return "Problems in API response, please check."  # 返回响应错误提示


def main():
    """命令行交互入口"""
    # 初始化环境配置
    env = init_environment()
    if not env:
        print("初始化失败：请检查环境变量配置")  # 环境初始化失败提示
        return

    # 显示命令行交互提示
    print("=== Function Comment Generator ===")
    print("1. 粘贴Python函数代码（允许空行）")
    print("2. 输入'END'（新行）结束输入\n")

    # 读取用户输入的函数代码（直到输入'END'为止）
    function_code = "\n".join(
        line for line in iter(input, 'END') if line.strip().upper() != 'END'
    )

    # 生成并打印注释
    print("\n生成的注释：")
    print(generate_function_comment(function_code, env))


# 当脚本直接运行时，执行main函数
if __name__ == "__main__":
    main()
