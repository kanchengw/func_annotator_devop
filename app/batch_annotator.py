"""
批量函数注释生成工具
从 feedings/ 目录读取函数样本，批量生成注释（不保存文件）
对每个函数进行评分和记录
"""
import ast
import time
from pathlib import Path
from datetime import datetime
import mlflow
from tqdm import tqdm
from func_annotator import (
    init_environment,
    generate_function_comment
)


def extract_functions_from_file(file_path):
    """从 Python 文件中提取所有函数定义"""
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
                functions.append({
                    'name': node.name,
                    'code': func_code,
                    'line': node.lineno
                })
    except Exception as e:
        print(f"[ERROR] 读取文件 {file_path} 时出错: {e}")
    return functions


def extract_annotation_content(annotation):
    """从注释字符串中提取纯文本内容"""
    if annotation.startswith('"""'):
        lines = annotation.strip().split('\n')
        return '\n'.join(lines[1:-1])  # 去掉前后 """
    return annotation


def process_sample_file(sample_file, env):
    """处理单个样本文件，生成注释但不保存输出文件"""
    # 提取文件名
    function_name = Path(sample_file).name
    functions = extract_functions_from_file(sample_file)
    # 记录每个函数的结果
    function_records = []
    success_count = 0
    error_count = 0
    # 创建函数处理进度条（显示 当前/总数，时间格式改为运行耗时）
    func_progress = tqdm(
        functions,
        desc=f"处理 {function_name}",
        leave=True,  # 处理完文件后保留进度条
        unit="函数",
        bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [运行耗时：{elapsed_s:.1f}秒]"
    )
    # 处理每个函数
    for func_info in func_progress:
        func_name = func_info['name']
        func_code = func_info['code']
        input_length = len(func_code.strip())
        # 生成注释（接收字典格式结果或错误信息）
        result = generate_function_comment(func_code, env)
        # 创建函数记录
        record = {
            'file': function_name,
            'function_name': func_name,
            'latency': 0.0,
            'success': False,
            'input_length': input_length,
            'output_length': 0,
            'completeness': 0.0,
            'comment_density': 0.0,
            'error_message': None
        }
        # 1. 成功场景：result为字典（包含注释和指标）
        if isinstance(result, dict):
            comment = result["comment"]
            metrics = result["metrics"]
            annotation_content = extract_annotation_content(comment)
            # 更新记录
            record['success'] = True
            record['latency'] = metrics["latency"]
            record['output_length'] = metrics["output_length"]
            record['completeness'] = metrics["completeness"]
            record['comment_density'] = metrics["comment_density"]
            success_count += 1
            # 统一记录MLflow日志（外层唯一日志）
            with mlflow.start_run(
                run_name=f"{env['model_name']}_{function_name}_{func_name}",
                nested=True
            ):
                mlflow.log_param("file", function_name)
                mlflow.log_param("function_name", func_name)
                mlflow.log_param("model", env["model_name"])
                mlflow.log_param("temperature", env["model_temperature"])
                mlflow.log_metric("input_length", input_length)
                mlflow.log_metric("output_length", metrics["output_length"])
                mlflow.log_metric("耗时", metrics["latency"])
                mlflow.log_metric("completeness", metrics["completeness"])
                mlflow.log_metric("comment_density", metrics["comment_density"])
                mlflow.log_metric("success", 1)
                mlflow.log_text(annotation_content, f"{func_name}_annotation.txt")
                mlflow.log_text(func_code, f"{func_name}_input.txt")
        # 2. 错误场景：result为字符串（错误信息）
        else:
            record['error_message'] = result
            record['latency'] = (datetime.now() - datetime.now()).total_seconds()  # 错误场景耗时为0
            error_count += 1
            # 统一记录MLflow错误日志
            with mlflow.start_run(
                run_name=f"{env['model_name']}_{function_name}_{func_name}_error",
                nested=True
            ):
                mlflow.log_param("file", function_name)
                mlflow.log_param("function_name", func_name)
                mlflow.log_param("model", env["model_name"])
                mlflow.log_param("error_message", result)
                mlflow.log_metric("input_length", input_length)
                mlflow.log_metric("耗时", 0.0)
                mlflow.log_metric("success", 0)

        function_records.append(record)
        # 更新进度条时计算已用秒数（保留1位小数）
        func_progress.set_postfix(elapsed_s=func_progress.format_dict['elapsed'])
    # 关闭当前文件的进度条
    func_progress.close()
    # 计算文件级统计（修改平均耗时计算方式：总和/数量）
    success_records = [r for r in function_records if r['success']]
    total_success_latency = sum(r['latency'] for r in success_records)
    avg_completeness = sum(r['completeness'] for r in success_records) / len(success_records) if success_records else 0
    avg_density = sum(r['comment_density'] for r in success_records) / len(success_records) if success_records else 0
    avg_duration = total_success_latency / len(success_records) if success_records else 0
    return {
        'file': function_name,
        'success_count': success_count,
        'error_count': error_count,
        'avg_completeness': avg_completeness,
        'avg_density': avg_density,
        'avg_duration': avg_duration,
        'total_success_latency': total_success_latency  # 新增总耗时字段用于全局计算
    }


def batch_annotate():
    """批量处理所有样本文件（不保存输出文件，仅输出统计）"""
    # 初始化环境
    env = init_environment()
    if not env:
        print("\n[ERROR] 环境配置错误，请检查环境变量")
        return
    # 获取项目根目录
    project_root = Path(__file__).parent.parent
    feedings_dir = project_root / 'feedings'
    # 获取所有 Python 样本文件
    sample_files = list(feedings_dir.glob('function_sample*.py'))
    if not sample_files:
        print(f"\n[ERROR] 未找到样本文件在 {feedings_dir}")
        return
    # 启动MLflow主运行
    with mlflow.start_run(run_name=f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}"):
        mlflow.log_param("batch_start_time", datetime.now().isoformat())
        mlflow.log_param("total_files", len(sample_files))
        mlflow.log_param("model", env["model_name"])
        mlflow.log_param("temperature", env["model_temperature"])
        # 记录所有文件的统计信息
        all_stats = []
        # 处理每个文件
        start_time = time.time()
        for sample_file in sample_files:
            stats = process_sample_file(sample_file, env)
            all_stats.append(stats)
        total_time = time.time() - start_time
        # 计算总体统计
        total_functions = sum(s['success_count'] + s['error_count'] for s in all_stats)
        total_success = sum(s['success_count'] for s in all_stats)
        total_errors = sum(s['error_count'] for s in all_stats)
        total_latency = sum(s['total_success_latency'] for s in all_stats)
        overall_success_rate = total_success / total_functions if total_functions > 0 else 0
        overall_avg_completeness = (
            sum(s['avg_completeness'] * s['success_count'] for s in all_stats)
            / total_success if total_success > 0 else 0
        )
        overall_avg_density = (
            sum(s['avg_density'] * s['success_count'] for s in all_stats)
            / total_success if total_success > 0 else 0
        )
        overall_avg_duration = total_time / total_success if total_success > 0 else 0  # 总耗时/总成功数
        overall_avg_latency = (
            total_latency/ total_success if total_success > 0 else 0
        )
        # 记录总体指标到MLflow
        mlflow.log_metric("total_functions", total_functions)
        mlflow.log_metric("total_success", total_success)
        mlflow.log_metric("total_errors", total_errors)
        mlflow.log_metric("success_rate", overall_success_rate)
        mlflow.log_metric("avg_completeness", overall_avg_completeness)
        mlflow.log_metric("avg_density", overall_avg_density)
        mlflow.log_metric("avg_duration", overall_avg_duration)
        mlflow.log_metric("total_time", total_time)
    # 输出最终统计结果
    print("\n" + "=" * 60)
    print("[STATS] 统计：")
    print(f"   [SUCCESS] 成功：{total_success}")
    print(f"   [FAILED] 失败：{total_errors}")
    print(f"   [AVG_LATENCY] 平均延迟：{overall_avg_latency:.2f}s")
    print(f"   [AVG_COMPLETENESS] 平均完整性：{overall_avg_completeness:.2%}")
    print(f"   [AVG_DENSITY] 平均注释密度：{overall_avg_density:.4f}")
    print(f"   [AVG_DURATION] 平均耗时：{overall_avg_duration:.2f}s")
    print("=" * 60)


if __name__ == "__main__":
    batch_annotate()
