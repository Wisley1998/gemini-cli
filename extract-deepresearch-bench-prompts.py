#!/usr/bin/env python3
"""
DeepResearch Bench 任务提取器
从 DeepResearch Bench 数据集中提取研究任务并生成独立的 prompt 文件

使用方法:
    python extract-deepresearch-bench-prompts.py --limit 5
    python extract-deepresearch-bench-prompts.py --limit 10 --output-dir ./deepresearch-bench-prompts
    python extract-deepresearch-bench-prompts.py --data-url https://raw.githubusercontent.com/Ayanami0730/deep_research_bench/main/data/prompt_data/query.jsonl
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Dict, Any, List
import urllib.request


def download_benchmark_data(url: str, output_file: str) -> bool:
    """
    从 GitHub 下载 DeepResearch Bench 数据文件
    
    Args:
        url: 数据文件的 URL
        output_file: 本地保存路径
        
    Returns:
        是否下载成功
    """
    try:
        print(f"📥 正在从 {url} 下载数据...")
        with urllib.request.urlopen(url) as response:
            data = response.read()
            with open(output_file, 'wb') as f:
                f.write(data)
        print(f"✅ 数据已保存到 {output_file}")
        return True
    except Exception as e:
        print(f"❌ 下载失败: {e}")
        return False


def format_research_task_prompt(task: Dict[str, Any], task_number: int) -> str:
    """
    将 DeepResearch Bench 任务格式化为简洁的研究 prompt
    
    Args:
        task: DeepResearch Bench 任务数据
        task_number: 任务编号
        
    Returns:
        格式化后的 prompt 文本
    """
    
    # 提取基本信息
    task_id = task.get('id', f'task_{task_number:03d}')
    prompt = task.get('prompt', 'No research prompt provided')
    
    # 去掉所有换行和引号
    prompt = ' '.join(prompt.split()).replace('"', '').replace("'", '')
    
    # 尝试从 prompt 中提取主题和领域
    topic = extract_topic_from_prompt(prompt)
    
    # 构建简洁的研究任务 prompt - 一段式，无分隔符，无引号
    research_prompt = f"DeepResearch Bench 任务 #{task_number} - 任务 ID: {task_id} - 领域: {topic}. 研究目标: {prompt}. 🔧 MCP 工具使用要求（核心重点）：1. 必须使用 MCP 工具收集所有信息，严禁编造或凭记忆生成内容 2. 优先使用工具列表：Playwright MCP, Fetcher MCP, GitHub MCP. 📝 输出格式要求（极简原则）：1. 要点式输出：使用短句和列表，避免长段落 2. 禁止啰嗦：直接给出结论，不要过渡语和废话"
    
    return research_prompt


def extract_topic_from_prompt(prompt: str) -> str:
    """
    从 prompt 文本中提取主题/领域
    
    Args:
        prompt: 研究任务描述
        
    Returns:
        识别出的主题/领域
    """
    # DeepResearch Bench 的 22 个领域
    topics = {
        'physics': '物理学 (Physics)',
        'chemistry': '化学 (Chemistry)',
        'biology': '生物学 (Biology)',
        'environmental': '环境科学 (Environmental Science)',
        'engineering': '工程学 (Engineering)',
        'investment': '投资 (Investment)',
        'finance': '金融 (Finance)',
        'marketing': '市场营销 (Marketing)',
        'business': '商业 (Business)',
        'software': '软件 (Software)',
        'programming': '编程 (Programming)',
        'technology': '技术 (Technology)',
        'art': '艺术设计 (Art & Design)',
        'entertainment': '娱乐 (Entertainment)',
        'history': '历史 (History)',
        'industrial': '工业 (Industrial)',
        'transportation': '交通运输 (Transportation)',
        'travel': '旅游 (Travel)',
        'health': '健康 (Health)',
        'education': '教育 (Education)',
        'law': '法律 (Law)',
        'economics': '经济学 (Economics)'
    }
    
    prompt_lower = prompt.lower()
    for keyword, topic_name in topics.items():
        if keyword in prompt_lower:
            return topic_name
    
    return '通用研究 (General Research)'


def format_test_list(tests: List[str], limit: int | None = None) -> str:
    """格式化测试列表"""
    if not tests:
        return "  • 无"
    
    if limit and len(tests) > limit:
        formatted = '\n'.join(f"  • {test}" for test in tests[:limit])
        formatted += f"\n  • ... 以及其他 {len(tests) - limit} 个测试"
        return formatted
    
    return '\n'.join(f"  • {test}" for test in tests)


def load_tasks_from_jsonl(file_path: str) -> List[Dict[str, Any]]:
    """
    从 JSONL 文件加载任务数据
    
    Args:
        file_path: JSONL 文件路径
        
    Returns:
        任务列表
    """
    tasks = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if not line:
                    continue
                try:
                    task = json.loads(line)
                    tasks.append(task)
                except json.JSONDecodeError as e:
                    print(f"⚠️  警告: 第 {line_num} 行 JSON 解析失败: {e}")
                    continue
        print(f"✅ 成功加载 {len(tasks)} 个任务")
    except FileNotFoundError:
        print(f"❌ 错误: 文件 {file_path} 不存在")
    except Exception as e:
        print(f"❌ 错误: 加载文件时发生异常: {e}")
    
    return tasks


def save_prompt_to_file(prompt: str, output_path: Path) -> bool:
    """
    保存 prompt 到文件
    
    Args:
        prompt: prompt 文本
        output_path: 输出文件路径
        
    Returns:
        是否保存成功
    """
    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(prompt)
        return True
    except Exception as e:
        print(f"❌ 保存文件失败 {output_path}: {e}")
        return False


def create_index_file(output_dir: Path, tasks: List[Dict[str, Any]], limit: int | None = None):
    """
    创建索引文件
    
    Args:
        output_dir: 输出目录
        tasks: 任务列表
        limit: 提取任务数量限制
    """
    actual_limit = min(limit, len(tasks)) if limit else len(tasks)
    
    index_content = f"""# DeepResearch Bench 任务索引

本目录包含从 DeepResearch Bench 提取的研究任务。

## 📊 统计信息

- 总任务数: {len(tasks)}
- 已提取: {actual_limit}
- 数据来源: [DeepResearch Bench](https://github.com/Ayanami0730/deep_research_bench)

## 📋 任务列表

| 编号 | 任务 ID | 主题 | 文件 |
|------|---------|------|------|
"""
    
    for i in range(actual_limit):
        task = tasks[i]
        task_id = task.get('id', f'task_{i+1:03d}')
        task_number = i + 1
        prompt = task.get('prompt', '')
        topic = extract_topic_from_prompt(prompt)
        filename = f"prompt_{task_number:03d}_{task_id}.txt"
        
        # 截取 prompt 的前 50 个字符作为预览
        preview = prompt[:50] + '...' if len(prompt) > 50 else prompt
        preview = preview.replace('\n', ' ').strip()
        
        index_content += f"| {task_number} | `{task_id}` | {topic} | [{filename}](./{filename}) |\n"
    
    index_content += f"""
## 🎯 如何使用

### 方法 1: 直接使用 gemini-cli

```bash
# 读取任务文件并执行
gemini --prompt "$(cat deepresearch-bench-prompts/prompt_001_*.txt)"
```

### 方法 2: 使用批处理脚本

```bash
# 运行所有任务
./run-deepresearch-bench.sh

# 运行前 5 个任务
./run-deepresearch-bench.sh --limit 5
```

### 方法 3: 交互式执行

```bash
# 启动 gemini-cli
gemini

# 在交互模式中粘贴任务内容
```

## 📖 评估标准

DeepResearch Bench 使用两个评估框架：

### RACE (报告质量评估)
- 📚 全面性 (Comprehensiveness)
- 🔍 洞察力/深度 (Insight/Depth)
- 📋 指令遵循 (Instruction-Following)
- 📖 可读性 (Readability)

### FACT (事实和引用评估)
- 引用准确性 (Citation Accuracy)
- 有效引用数量 (Effective Citations)

## 🔗 相关资源

- [DeepResearch Bench GitHub](https://github.com/Ayanami0730/deep_research_bench)
- [DeepResearch Bench 论文](https://arxiv.org/abs/2506.11763)
- [排行榜](https://huggingface.co/spaces/Ayanami0730/DeepResearch-Leaderboard)
- [项目网站](https://deepresearch-bench.github.io/)

## 📝 输出格式

建议将研究报告保存为 Markdown 格式：

```markdown
# [研究主题]

## 执行摘要
...

## 背景
...

## 主要发现
...

## 结论
...

## 参考文献
[1] 来源标题 - URL
[2] 来源标题 - URL
...
```
"""
    
    index_path = output_dir / "INDEX.md"
    with open(index_path, 'w', encoding='utf-8') as f:
        f.write(index_content)
    
    print(f"✅ 索引文件已创建: {index_path}")


def create_readme(output_dir: Path):
    """
    创建 README 文件
    """
    readme_content = """# DeepResearch Bench 任务集

这是从 [DeepResearch Bench](https://github.com/Ayanami0730/deep_research_bench) 提取的研究任务集合。

## 什么是 DeepResearch Bench?

DeepResearch Bench 是一个全面的深度研究代理基准测试，包含 100 个 PhD 级别的研究任务，涵盖 22 个不同领域：

- 🔬 科学技术：物理、化学、生物、环境科学、工程
- 💼 金融商业：投资、个人理财、市场营销、人力资源
- 💻 软件：软件使用和互联网相关主题
- 🌍 其他：艺术设计、娱乐、历史、工业、交通、旅游等

## 评估框架

### RACE (Reference-based Adaptive Criteria-driven Evaluation)
评估报告生成质量的四个维度：
1. 📚 全面性：研究主题的覆盖广度和深度
2. 🔍 洞察力/深度：分析质量和洞察生成
3. 📋 指令遵循：对特定任务要求的遵守程度
4. 📖 可读性：清晰度、组织和呈现质量

### FACT (Framework for Factual Abundance and Citation Trustworthiness)
评估信息检索和事实支撑能力：
- 引用准确性：正确支持的引用百分比
- 有效引用：每个任务的可验证引用平均数量

## 使用指南

查看 [INDEX.md](./INDEX.md) 获取任务列表和详细使用说明。

## 引用

如果你在研究中使用 DeepResearch Bench，请引用：

```bibtex
@article{du2025deepresearch,
  author    = {Mingxuan Du and Benfeng Xu and Chiwei Zhu and Xiaorui Wang and Zhendong Mao},
  title     = {DeepResearch Bench: A Comprehensive Benchmark for Deep Research Agents},
  journal   = {arXiv preprint},
  year      = {2025},
}
```

## 许可证

遵循 DeepResearch Bench 的 Apache-2.0 许可证。
"""
    
    readme_path = output_dir / "README.md"
    with open(readme_path, 'w', encoding='utf-8') as f:
        f.write(readme_content)
    
    print(f"✅ README 文件已创建: {readme_path}")


def main():
    parser = argparse.ArgumentParser(
        description='从 DeepResearch Bench 提取研究任务并生成 prompt 文件',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 提取前 5 个任务
  python extract-deepresearch-bench-prompts.py --limit 5
  
  # 提取所有任务到指定目录
  python extract-deepresearch-bench-prompts.py --output-dir ./my-research-tasks
  
  # 从指定 URL 下载数据
  python extract-deepresearch-bench-prompts.py --data-url https://example.com/data.jsonl
        """
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='提取的任务数量限制 (默认: 全部)'
    )
    
    parser.add_argument(
        '--output-dir',
        type=str,
        default='./deepresearch-bench-prompts',
        help='输出目录 (默认: ./deepresearch-bench-prompts)'
    )
    
    parser.add_argument(
        '--data-file',
        type=str,
        default=None,
        help='本地 JSONL 数据文件路径'
    )
    
    parser.add_argument(
        '--data-url',
        type=str,
        default='https://raw.githubusercontent.com/Ayanami0730/deep_research_bench/main/data/prompt_data/query.jsonl',
        help='远程 JSONL 数据文件 URL'
    )
    
    args = parser.parse_args()
    
    # 创建输出目录
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print("=" * 80)
    print("DeepResearch Bench 任务提取器")
    print("=" * 80)
    print()
    
    # 确定数据文件
    data_file = args.data_file
    if not data_file:
        # 下载数据文件
        data_file = output_dir / "query.jsonl"
        if not data_file.exists():
            if not download_benchmark_data(args.data_url, str(data_file)):
                print("❌ 无法获取数据文件，退出")
                sys.exit(1)
        else:
            print(f"✅ 使用已存在的数据文件: {data_file}")
    
    # 加载任务
    print(f"\n📂 正在加载任务数据: {data_file}")
    tasks = load_tasks_from_jsonl(str(data_file))
    
    if not tasks:
        print("❌ 没有加载到任何任务，退出")
        sys.exit(1)
    
    # 确定要提取的任务数量
    limit = args.limit if args.limit else len(tasks)
    actual_limit = min(limit, len(tasks))
    
    print(f"\n📊 数据统计:")
    print(f"  • 总任务数: {len(tasks)}")
    print(f"  • 将提取: {actual_limit} 个任务")
    print(f"  • 输出目录: {output_dir}")
    print()
    
    # 提取并保存任务
    print("🔄 正在生成 prompt 文件...")
    success_count = 0
    
    for i in range(actual_limit):
        task = tasks[i]
        task_number = i + 1
        task_id = task.get('id', f'task_{task_number:03d}')
        
        # 生成 prompt
        prompt = format_research_task_prompt(task, task_number)
        
        # 保存到文件
        filename = f"prompt_{task_number:03d}_{task_id}.txt"
        output_path = output_dir / filename
        
        if save_prompt_to_file(prompt, output_path):
            success_count += 1
            print(f"  ✅ [{task_number}/{actual_limit}] {filename}")
        else:
            print(f"  ❌ [{task_number}/{actual_limit}] {filename} - 保存失败")
    
    print()
    print(f"✅ 成功生成 {success_count}/{actual_limit} 个 prompt 文件")
    
    # 创建索引文件
    print("\n📝 正在创建索引文件...")
    create_index_file(output_dir, tasks, actual_limit)
    
    # 创建 README
    print("📝 正在创建 README 文件...")
    create_readme(output_dir)
    
    print()
    print("=" * 80)
    print("🎉 任务提取完成！")
    print("=" * 80)
    print()
    print("📁 输出目录:", output_dir.absolute())
    print("📄 查看 INDEX.md 了解任务列表")
    print("📖 查看 README.md 了解使用说明")
    print()
    print("💡 快速开始:")
    print(f"   gemini --prompt \"$(cat {output_dir}/prompt_001_*.txt)\"")
    print()


if __name__ == '__main__':
    main()
