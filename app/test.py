import json

from func_annotator import (
    init_environment,
    generate_function_comment,
    build_api_request,
    load_prompt_template
)

TEST_FUNCTION = """def add(a: int, b: int) -> int:
    return a + b
"""

def test_environment_init():
    """测试环境变量初始化"""
    env = init_environment()
    assert env is not None, "环境配置错误，请检查环境变量"
    for key in ["api_key", "api_url", "model_name"]:
        assert key in env and env[key], f"{key.upper()} 未配置"

def test_api_call_success():
    """测试API调用生成注释成功（修复返回值类型判断）"""
    env = init_environment()
    assert env is not None, "环境配置错误，无法进行API测试"
    # 关键修复：接收dict类型返回值，提取comment字段后再判断
    result = generate_function_comment(TEST_FUNCTION, env)
    # 1. 先判断返回值是否为正常的dict（排除错误场景）
    assert isinstance(result, dict), f"API调用异常，预期返回dict，实际返回: {type(result)}"
    assert "comment" in result, "返回结果缺少'comment'字段"
    # 2. 对提取的comment字段做格式判断（原逻辑保留）
    comment = result["comment"]
    assert comment.startswith('"""') and comment.endswith('"""'), \
        f"API调用失败，返回非注释格式: {comment}"
    assert len(comment) > 10, "生成的注释过短，可能不符合预期"
    # 可选：新增metrics字段校验（确保返回值完整）
    assert "metrics" in result, "返回结果缺少'metrics'字段"
    assert isinstance(result["metrics"], dict), "metrics字段应为dict类型"

def test_invalid_function_input():
    """测试无效函数输入的错误处理"""
    env = init_environment()
    assert env is not None, "环境配置错误，无法进行测试"
    result = generate_function_comment("this is not a function", env)
    expected_msg = "Input must be a Python function starting with 'def'"
    assert result == expected_msg, \
        f"无效输入处理错误，预期: {expected_msg}, 实际: {result}"

def test_api_response_debug():
    """调试API响应流程（同步修复返回值处理逻辑）"""
    env = init_environment()
    assert env, "环境配置失败，无法调试API响应"
    try:
        prompt = load_prompt_template().replace("{function_code}", TEST_FUNCTION)
        request_params = build_api_request(env, prompt)
        assert request_params, "API请求参数构建失败"
        # 发送请求（复用主函数的API调用逻辑，避免重复代码）
        result = generate_function_comment(TEST_FUNCTION, env)
        if isinstance(result, dict):
            print(f"\nAPI调用成功，生成注释: {result['comment'][:100]}...")
            print(f"API响应指标: {json.dumps(result['metrics'], indent=2)}")
        else:
            print(f"\nAPI调用失败，错误信息: {result}")
    except Exception as e:
        print(f"API调试过程出错: {str(e)}")
