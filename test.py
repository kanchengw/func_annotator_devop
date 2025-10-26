from func_annotator import (
    init_environment,
    load_prompt_template,
    build_api_request,
    generate_function_comment
)

# 测试1：环境变量初始化（需提前配置.env文件，或手动设置环境变量）
def test_init_environment():
    env = init_environment()
    # 验证环境变量格式（不验证具体值，避免依赖本地配置）
    assert isinstance(env, dict)
    assert "api_key" in env
    assert "api_url" in env
    assert "model_name" in env

# 测试2：提示词模板加载（需确保prompt_template.txt存在于当前目录）
def test_load_prompt_template():
    template = load_prompt_template()
    # 验证模板非空且包含占位符
    assert len(template.strip()) > 0
    assert "{function_code}" in template

# 测试3：API请求参数构建
def test_build_api_request():
    # 构造测试环境配置
    test_env = {
        "api_key": "test_key_123",
        "api_url": "https://test-api.com/chat",
        "model_name": "test-model-v1"
    }
    test_prompt = "test prompt content"

    request = build_api_request(test_env, test_prompt)

    # 验证请求参数格式和内容
    assert request["url"] == test_env["api_url"]
    assert request["headers"]["Authorization"] == f"Bearer {test_env['api_key']}"
    assert request["headers"]["Content-Type"] == "application/json"
    assert request["json"]["model"] == test_env["model_name"]
    assert request["json"]["messages"][0]["content"] == test_prompt
    assert request["json"]["temperature"] == 0.3

# 测试4：输入校验逻辑
def test_generate_function_comment_input_check():
    # 测试非函数输入
    invalid_input1 = "print('hello')"
    result1 = generate_function_comment(invalid_input1, {})
    assert result1 == "Input must be a Python function starting with 'def'"

    # 测试空输入
    invalid_input2 = ""
    result2 = generate_function_comment(invalid_input2, {})
    assert result2 == "Input must be a Python function starting with 'def'"

    # 测试合法函数输入（仅验证格式，不调用真实API）
    valid_input = "def add(a, b):\n    return a + b"
    # 构造临时环境（避免真实API请求）
    temp_env = {"api_key": "temp", "api_url": "temp", "model_name": "temp"}
    # 捕获请求失败信息（非输入校验错误）
    result3 = generate_function_comment(valid_input, temp_env)
    assert "Request failed" in result3 or "HTTP error" in result3

# 测试5：注释输出格式（需配合真实API，或手动模拟响应）
def test_generate_function_comment_output_format():
    # 这个测试需要真实API，暂时跳过
    # 当有真实API时，可以取消注释以下代码进行测试
    # test_env = {
    #     "api_key": "your_valid_api_key",
    #     "api_url": "your_valid_api_url",
    #     "model_name": "your_valid_model_name"
    # }
    # test_function = "def multiply(x, y):\n    return x * y"
    # result = generate_function_comment(test_function, test_env)
    # assert result.startswith('"""')
    # assert result.endswith('"""')
    pass
