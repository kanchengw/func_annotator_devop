import json
import requests
from func_annotator import init_environment, generate_function_comment, build_api_request, load_prompt_template


TEST_FUNCTION = """def add(a: int, b: int) -> int:
    return a + b
"""


def test_environment_init():
    """测试环境变量初始化有效性"""
    env = init_environment()
    assert env is not None, "环境配置错误，请检查环境变量"
    for key in ["api_key", "api_url", "model_name"]:
        assert key in env and env[key], f"{key.upper()} 未配置"


def test_api_call_success():
    """验证API调用生成有效注释"""
    env = init_environment()
    assert env is not None, "环境配置错误，无法进行API测试"

    comment = generate_function_comment(TEST_FUNCTION, env)
    assert comment.startswith('"""') and comment.endswith('"""'), \
        f"API调用失败，返回非注释格式: {comment}"
    assert len(comment) > 10, "生成的注释过短，可能不符合预期"


def test_invalid_function_input():
    """验证无效函数输入的错误处理"""
    env = init_environment()
    assert env is not None, "环境配置错误，无法进行测试"

    result = generate_function_comment("this is not a function", env)
    expected_msg = "Input must be a Python function starting with 'def'"
    assert result == expected_msg, \
        f"无效输入处理错误，预期: {expected_msg}, 实际: {result}"


def test_api_response_debug():
    """调试API响应格式（仅用于问题排查）"""
    env = init_environment()
    assert env, "环境配置失败，无法调试API响应"

    try:
        prompt = load_prompt_template().replace("{function_code}", TEST_FUNCTION)
        request_params = build_api_request(env, prompt)
        assert request_params, "API请求参数构建失败"

        response = requests.post(** request_params, timeout=30)
        print(f"\nAPI响应状态码: {response.status_code}")
        print(f"API响应内容: {response.text[:500]}")

        try:
            response.json()
            print("API响应格式为有效JSON")
        except json.JSONDecodeError:
            print("API响应不是有效JSON格式")

    except Exception as e:
        print(f"API调试过程出错: {str(e)}")
