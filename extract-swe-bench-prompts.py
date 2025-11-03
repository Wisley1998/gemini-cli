#!/usr/bin/env python3
"""
SWE-bench 任务提取器
从 SWE-bench 数据集中提取任务信息并生成独立的 prompt 文件

使用方法:
    python extract-swe-bench-prompts.py --limit 5
    python extract-swe-bench-prompts.py --limit 10 --output-dir ./swe-bench-prompts
"""

import argparse
import json
import os
from pathlib import Path
from typing import Dict, Any

def format_task_prompt(task: Dict[str, Any], task_number: int) -> str:
    """
    将 SWE-bench 任务格式化为简洁的 prompt（一段式）
    
    Args:
        task: SWE-bench 任务数据
        task_number: 任务编号
        
    Returns:
        格式化后的 prompt 文本
    """
    
    # 提取基本信息
    instance_id = task.get('instance_id', 'N/A')
    repo = task.get('repo', 'N/A')
    base_commit = task.get('base_commit', 'N/A')
    
    # 从 instance_id 中提取 issue/PR 编号
    issue_pr_link = 'N/A'
    if instance_id != 'N/A' and '-' in instance_id:
        issue_number = instance_id.split('-')[-1]
        if repo != 'N/A' and issue_number.isdigit():
            issue_pr_link = f"https://github.com/{repo}/issues/{issue_number}"
    
    # 提取测试信息
    fail_to_pass = task.get('FAIL_TO_PASS', [])
    pass_to_pass = task.get('PASS_TO_PASS', [])
    
    # 如果是字符串,尝试解析为 JSON
    if isinstance(fail_to_pass, str):
        try:
            fail_to_pass = json.loads(fail_to_pass)
        except:
            fail_to_pass = [fail_to_pass]
    
    if isinstance(pass_to_pass, str):
        try:
            pass_to_pass = json.loads(pass_to_pass)
        except:
            pass_to_pass = [pass_to_pass]
    
    # 格式化测试列表，去掉所有特殊字符和换行
    fail_tests = ', '.join(str(t).replace('\n', ' ').replace('"', '').replace("'", '') for t in fail_to_pass[:5]) if fail_to_pass else '无'
    if len(fail_to_pass) > 5:
        fail_tests += f' 等共{len(fail_to_pass)}个'
    
    # 构建一段式 prompt，无分隔符，无换行，无引号
    prompt = f"SWE-bench 任务 #{task_number} - 任务 ID: {instance_id} - GitHub 仓库: {repo} - Issue链接: {issue_pr_link} - 基础提交: {base_commit}. 需要通过的测试: {fail_tests}. 🔧 MCP 工具使用要求（核心重点）：1. 必须使用 MCP 工具收集所有信息，严禁编造或凭记忆生成内容 2. 优先使用工具列表：Playwright MCP, Fetcher MCP, GitHub MCP. 📝 输出格式要求（极简原则）：1. 要点式输出：使用短句和列表，避免长段落 2. 禁止啰嗦：直接给出结论，不要过渡语和废话"
    
    return prompt


def format_test_list(tests: list, limit: int = None) -> str:
    """格式化测试列表"""
    if not tests:
        return "  (无)"
    
    # 处理字符串列表
    test_list = []
    for test in tests:
        if isinstance(test, str):
            test_list.append(test)
        elif isinstance(test, list):
            # 如果是嵌套列表,展平它
            test_list.extend(str(t) for t in test)
        else:
            test_list.append(str(test))
    
    if limit and len(test_list) > limit:
        formatted = "\n".join(f"  • {test}" for test in test_list[:limit])
        formatted += f"\n  ... 以及其他 {len(test_list) - limit} 个测试"
        return formatted
    
    return "\n".join(f"  • {test}" for test in test_list)


def extract_swe_bench_prompts(
    dataset_name: str = "princeton-nlp/SWE-bench_Lite",
    output_dir: str = "./swe-bench-prompts",
    limit: int = 5,
    split: str = "test"
):
    """
    从 SWE-bench 数据集提取任务并生成 prompt 文件
    
    Args:
        dataset_name: HuggingFace 数据集名称
        output_dir: 输出目录
        limit: 提取的任务数量限制
        split: 数据集分割 (train/test/dev)
    """
    try:
        from datasets import load_dataset
    except ImportError:
        print("❌ 错误: 需要安装 datasets 库")
        print("请运行: pip install datasets")
        return
    
    print(f"📦 正在从 HuggingFace 下载 {dataset_name} 数据集...")
    print(f"   分割: {split}")
    
    try:
        # 加载数据集
        dataset = load_dataset(dataset_name, split=split)
        print(f"✅ 成功加载 {len(dataset)} 个任务")
    except Exception as e:
        print(f"❌ 加载数据集失败: {e}")
        return
    
    # 创建输出目录
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    print(f"📁 输出目录: {output_path.absolute()}")
    
    # 限制任务数量
    tasks_to_process = min(limit, len(dataset))
    print(f"📋 将提取前 {tasks_to_process} 个任务\n")
    
    # 处理每个任务
    for i in range(tasks_to_process):
        task = dataset[i]
        task_number = i + 1
        
        # 生成 prompt
        prompt = format_task_prompt(task, task_number)
        
        # 保存到文件
        instance_id = task.get('instance_id', f'task_{task_number}')
        # 清理文件名中的特殊字符
        safe_filename = instance_id.replace('/', '_').replace('\\', '_')
        filename = f"prompt_{task_number:03d}_{safe_filename}.txt"
        filepath = output_path / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(prompt)
        
        print(f"✅ [{task_number}/{tasks_to_process}] {instance_id}")
        print(f"   文件: {filename}")
        print(f"   仓库: {task.get('repo', 'N/A')}")
        print()
    
    # 生成索引文件
    index_file = output_path / "INDEX.md"
    with open(index_file, 'w', encoding='utf-8') as f:
        f.write(f"# SWE-bench 任务索引\n\n")
        f.write(f"数据集: {dataset_name}\n")
        f.write(f"分割: {split}\n")
        f.write(f"提取时间: {Path.cwd()}\n")
        f.write(f"任务数量: {tasks_to_process}\n\n")
        f.write(f"## 任务列表\n\n")
        
        for i in range(tasks_to_process):
            task = dataset[i]
            instance_id = task.get('instance_id', f'task_{i+1}')
            repo = task.get('repo', 'N/A')
            safe_filename = instance_id.replace('/', '_').replace('\\', '_')
            filename = f"prompt_{i+1:03d}_{safe_filename}.txt"
            
            f.write(f"{i+1}. **{instance_id}**\n")
            f.write(f"   - 仓库: {repo}\n")
            f.write(f"   - 文件: [{filename}](./{filename})\n\n")
    
    print(f"📊 索引文件: {index_file}")
    print(f"\n🎉 完成! 已生成 {tasks_to_process} 个 prompt 文件")
    print(f"📁 输出目录: {output_path.absolute()}")


def main():
    parser = argparse.ArgumentParser(
        description="从 SWE-bench 数据集提取任务并生成 prompt 文件",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 提取前 5 个任务
  python extract-swe-bench-prompts.py --limit 5
  
  # 提取前 10 个任务到指定目录
  python extract-swe-bench-prompts.py --limit 10 --output-dir ./my-prompts
  
  # 使用完整的 SWE-bench 数据集
  python extract-swe-bench-prompts.py --dataset princeton-nlp/SWE-bench --limit 20
        """
    )
    
    parser.add_argument(
        '--dataset',
        type=str,
        default='princeton-nlp/SWE-bench_Lite',
        help='HuggingFace 数据集名称 (默认: princeton-nlp/SWE-bench_Lite)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='./swe-bench-prompts',
        help='输出目录路径 (默认: ./swe-bench-prompts)'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=5,
        help='提取的任务数量 (默认: 5)'
    )
    
    parser.add_argument(
        '--split',
        type=str,
        default='test',
        choices=['train', 'test', 'dev'],
        help='数据集分割 (默认: test)'
    )
    
    args = parser.parse_args()
    
    extract_swe_bench_prompts(
        dataset_name=args.dataset,
        output_dir=args.output_dir,
        limit=args.limit,
        split=args.split
    )


if __name__ == "__main__":
    main()
