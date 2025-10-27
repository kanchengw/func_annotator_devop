"""
批量函数注释生成工具
从 feedings/ 目录读取函数样本，批量生成注释并保存到 outputs/ 目录
"""

import os
import sys
import ast
from pathlib import Path

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from func_annotator import init_environment, generate_function_comment


def extract_functions_from_file(file_path):
    """
    从 Python 文件中提取所有函数定义
    
    Args:
        file_path: Python 文件路径
        
    Returns:
        list: 函数代码列表
    """
    functions = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 解析 Python AST
        tree = ast.parse(content)
        
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # 获取函数的起始和结束行号
                func_lines = content.split('\n')[node.lineno - 1:node.end_lineno]
                func_code = '\n'.join(func_lines)
                
                # 如果函数有文档字符串，包括进去
                for child in ast.walk(node):
                    if isinstance(child, ast.Expr) and isinstance(child.value, ast.Constant):
                        if isinstance(child.value.value, str) and node.body:
                            break
                
                functions.append({
                    'name': node.name,
                    'code': func_code,
                    'line': node.lineno
                })
                
    except Exception as e:
        print(f"[ERROR] 读取文件 {file_path} 时出错: {e}")
    
    return functions


def process_sample_file(sample_file, env, output_dir):
    """
    处理单个样本文件，为所有函数生成注释
    
    Args:
        sample_file: 样本文件路径
        env: 环境配置
        output_dir: 输出目录
    """
    print(f"\n[FILE] 处理文件: {sample_file}")
    print("=" * 60)
    
    # 提取函数
    functions = extract_functions_from_file(sample_file)
    print(f"   找到 {len(functions)} 个函数")
    
    # 创建输出文件
    output_file = output_dir / f"{Path(sample_file).stem}_annotated.py"
    annotated_code = []
    
    # 添加文件头注释
    annotated_code.append(f'"""自动生成的函数注释：{Path(sample_file).name}"""\n')
    
    success_count = 0
    error_count = 0
    
    # 处理每个函数
    for func_info in functions:
        func_name = func_info['name']
        func_code = func_info['code']
        
        print(f"\n   [PROCESSING] 处理函数: {func_name} (第 {func_info['line']} 行)")
        
        # 生成注释
        result = generate_function_comment(func_code, env)
        
        # 检查结果
        if result.startswith('"""'):
            # 成功生成注释
            annotated_function = result + '\n' + func_code
            annotated_code.append(annotated_function + '\n')
            success_count += 1
            print(f"   [SUCCESS] 成功")
        else:
            # 失败或错误
            annotated_code.append(func_code + '\n')
            error_count += 1
            print(f"   [FAILED] 失败: {result}")
    
    # 保存结果
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write('\n'.join(annotated_code))
    
    print(f"\n[STATS] 统计:")
    print(f"   [SUCCESS] 成功: {success_count}")
    print(f"   [FAILED] 失败: {error_count}")
    print(f"   [OUTPUT] 输出文件: {output_file}")


def batch_annotate():
    """
    批量处理所有样本文件
    """
    print("=" * 60)
    print("批量函数注释生成器")
    print("=" * 60)
    
    # 初始化环境
    env = init_environment()
    if not env:
        print("\n[ERROR] 环境配置错误，请检查环境变量")
        return
    
    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    feedings_dir = project_root / 'feedings'
    output_dir = project_root / 'outputs'
    
    # 创建输出目录
    output_dir.mkdir(exist_ok=True)
    
    # 获取所有 Python 样本文件
    sample_files = list(feedings_dir.glob('function_sample*.py'))
    
    if not sample_files:
        print(f"\n[ERROR] 未找到样本文件在 {feedings_dir}")
        return
    
    print(f"\n[FOUND] 找到 {len(sample_files)} 个样本文件")
    
    # 处理每个文件
    total_files = len(sample_files)
    for idx, sample_file in enumerate(sample_files, 1):
        print(f"\n[{idx}/{total_files}]", end=" ")
        process_sample_file(sample_file, env, output_dir)
    
    print("\n" + "=" * 60)
    print("[COMPLETE] 批量处理完成！")
    print(f"[OUTPUT_DIR] 输出目录: {output_dir}")
    print("=" * 60)


if __name__ == "__main__":
    batch_annotate()

