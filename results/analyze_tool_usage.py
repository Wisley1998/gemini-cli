#!/usr/bin/env python3
"""
工具使用分析脚本
分析 benchmark 结果文件中的工具使用情况和时间统计
"""
import re
import os
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict
from datetime import datetime

# 设置中文字体支持
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False

def parse_time_string(time_str):
    """将时间字符串转换为秒数 (例如: '1m 2s', '22.4s', '308ms')"""
    total_seconds = 0.0
    
    # 处理分钟
    min_match = re.search(r'(\d+)m\s', time_str)
    if min_match:
        total_seconds += int(min_match.group(1)) * 60
    
    # 优先处理毫秒
    ms_match = re.search(r'(\d+)ms\b', time_str)
    if ms_match:
        total_seconds += int(ms_match.group(1)) / 1000
        return total_seconds
    
    # 处理秒
    sec_match = re.search(r'([\d.]+)s\b', time_str)
    if sec_match:
        total_seconds += float(sec_match.group(1))
    
    return total_seconds

def parse_summary_file(filepath):
    """解析单个 summary 文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    data = {
        'filename': Path(filepath).name,
        'prompt_file': None,
        'prompt_type': None,
        'test_time': None,
        'wall_time': 0,
        'agent_active': 0,
        'api_time': 0,
        'tool_time': 0,
        'tool_calls': 0,
        'success_rate': 0,
        'tools': {},
        'mcp_servers': {},
        'models': {},
    }
    
    # 提取基本信息
    prompt_match = re.search(r'Prompt 文件:\s+(.+)', content)
    if prompt_match:
        data['prompt_file'] = prompt_match.group(1).strip()
    
    type_match = re.search(r'Prompt 类型:\s+(.+)', content)
    if type_match:
        data['prompt_type'] = type_match.group(1).strip()
    
    time_match = re.search(r'测试时间:\s+(.+)', content)
    if time_match:
        data['test_time'] = time_match.group(1).strip()
    
    # 提取 Tool Calls
    calls_match = re.search(r'Tool Calls:\s+(\d+)', content)
    if calls_match:
        data['tool_calls'] = int(calls_match.group(1))
    
    # 提取 Success Rate
    success_match = re.search(r'Success Rate:\s+([\d.]+)%', content)
    if success_match:
        data['success_rate'] = float(success_match.group(1))
    
    # 提取性能数据
    wall_time_match = re.search(r'Wall Time:\s+(.+?)\s+│', content)
    if wall_time_match:
        data['wall_time'] = parse_time_string(wall_time_match.group(1))
    
    agent_active_match = re.search(r'Agent Active:\s+(.+?)\s+│', content)
    if agent_active_match:
        data['agent_active'] = parse_time_string(agent_active_match.group(1))
    
    # 提取 API Time
    api_time_match = re.search(r'» API Time:\s+(.+?)\s+\((.+?)%\)', content)
    if api_time_match:
        data['api_time'] = parse_time_string(api_time_match.group(1))
        data['api_percentage'] = float(api_time_match.group(2))
    
    # 提取 Tool Time
    tool_time_match = re.search(r'» Tool Time:\s+(.+?)\s+\((.+?)%\)', content)
    if tool_time_match:
        data['tool_time'] = parse_time_string(tool_time_match.group(1))
        data['tool_percentage'] = float(tool_time_match.group(2))
    
    # 提取各个工具的使用时间 (包括子任务)
    tool_section = re.search(r'» Tool Time:.*?(?=» MCP Servers:|Detailed Timing Breakdown|$)', content, re.DOTALL)
    if tool_section:
        tool_text = tool_section.group(0)
        # 移除边框字符
        tool_text = re.sub(r'[│╰╭─]', '', tool_text)
        
        # 匹配主工具: • tool_name: time (percentage%)
        main_pattern = r'• ([^:]+):\s+(.+?)\s+\((.+?)%\)'
        for match in re.finditer(main_pattern, tool_text):
            tool_name = match.group(1).strip()
            time_str = match.group(2).strip()
            percentage = float(match.group(3))
            
            data['tools'][tool_name] = {
                'time': parse_time_string(time_str),
                'percentage': percentage,
                'subtasks': {}
            }
        
        # 匹配子工具: ‣ subtool_name: time (percentage%)
        current_tool = None
        lines = tool_text.split('\n')
        for line in lines:
            main_match = re.match(r'\s*• ([^:]+):', line)
            if main_match:
                current_tool = main_match.group(1).strip()
                continue
            
            sub_match = re.match(r'\s*‣ ([^:]+):\s+(.+?)\s+\((.+?)%\)', line)
            if sub_match and current_tool and current_tool in data['tools']:
                subtask_name = sub_match.group(1).strip()
                time_str = sub_match.group(2).strip()
                percentage = float(sub_match.group(3))
                
                data['tools'][current_tool]['subtasks'][subtask_name] = {
                    'time': parse_time_string(time_str),
                    'percentage': percentage
                }
    
    # 提取 MCP Servers
    mcp_section = re.search(r'» MCP Servers:.*?(?=» User|$)', content, re.DOTALL)
    if mcp_section:
        mcp_text = mcp_section.group(0)
        # 匹配服务器: • server_name: time (percentage%)
        server_pattern = r'• ([^:]+):\s+(.+?)\s+\((.+?)%\)'
        for match in re.finditer(server_pattern, mcp_text):
            server_name = match.group(1).strip()
            time_str = match.group(2).strip()
            percentage = float(match.group(3))
            
            data['mcp_servers'][server_name] = {
                'time': parse_time_string(time_str),
                'percentage': percentage
            }
    
    # 提取模型使用情况
    model_section = re.search(r'Model Usage.*?Reqs\s+Input Tokens\s+Output Tokens.*?─+\s+(.*?)(?=╰|$)', content, re.DOTALL)
    if model_section:
        model_text = model_section.group(1)
        # 匹配: model_name   requests   input_tokens   output_tokens
        model_pattern = r'([a-z0-9\-\.]+)\s+(\d+)\s+([\d,]+)\s+([\d,]+)'
        for match in re.finditer(model_pattern, model_text):
            model_name = match.group(1).strip()
            requests = int(match.group(2))
            input_tokens = int(match.group(3).replace(',', ''))
            output_tokens = int(match.group(4).replace(',', ''))
            
            data['models'][model_name] = {
                'requests': requests,
                'input_tokens': input_tokens,
                'output_tokens': output_tokens,
                'total_tokens': input_tokens + output_tokens
            }
    
    return data

def analyze_directory(directory_path):
    """分析目录中的所有 summary 文件"""
    results = []
    
    for file in sorted(Path(directory_path).glob('*_summary.txt')):
        if not file.is_file():
            continue
        try:
            data = parse_summary_file(file)
            results.append(data)
        except (PermissionError, OSError) as e:
            print(f"⚠️  跳过 {file.name}: {e}")
            continue
    
    return results

def aggregate_statistics(results):
    """聚合统计数据"""
    stats = {
        'total_tasks': len(results),
        'total_wall_time': 0,
        'total_agent_active': 0,
        'total_api_time': 0,
        'total_tool_time': 0,
        'total_tool_calls': 0,
        'avg_success_rate': 0,
        'tool_usage': defaultdict(lambda: {'count': 0, 'total_time': 0, 'times': []}),
        'mcp_usage': defaultdict(lambda: {'count': 0, 'total_time': 0, 'times': []}),
        'model_usage': defaultdict(lambda: {
            'requests': 0, 
            'input_tokens': 0, 
            'output_tokens': 0,
            'total_tokens': 0
        }),
    }
    
    for result in results:
        stats['total_wall_time'] += result['wall_time']
        stats['total_agent_active'] += result['agent_active']
        stats['total_api_time'] += result['api_time']
        stats['total_tool_time'] += result['tool_time']
        stats['total_tool_calls'] += result['tool_calls']
        stats['avg_success_rate'] += result['success_rate']
        
        # 聚合工具使用
        for tool_name, tool_data in result['tools'].items():
            stats['tool_usage'][tool_name]['count'] += 1
            stats['tool_usage'][tool_name]['total_time'] += tool_data['time']
            stats['tool_usage'][tool_name]['times'].append(tool_data['time'])
        
        # 聚合 MCP 服务器使用
        for server_name, server_data in result['mcp_servers'].items():
            stats['mcp_usage'][server_name]['count'] += 1
            stats['mcp_usage'][server_name]['total_time'] += server_data['time']
            stats['mcp_usage'][server_name]['times'].append(server_data['time'])
        
        # 聚合模型使用
        for model_name, model_data in result['models'].items():
            stats['model_usage'][model_name]['requests'] += model_data['requests']
            stats['model_usage'][model_name]['input_tokens'] += model_data['input_tokens']
            stats['model_usage'][model_name]['output_tokens'] += model_data['output_tokens']
            stats['model_usage'][model_name]['total_tokens'] += model_data['total_tokens']
    
    if stats['total_tasks'] > 0:
        stats['avg_success_rate'] /= stats['total_tasks']
        stats['avg_wall_time'] = stats['total_wall_time'] / stats['total_tasks']
        stats['avg_agent_active'] = stats['total_agent_active'] / stats['total_tasks']
        stats['avg_api_time'] = stats['total_api_time'] / stats['total_tasks']
        stats['avg_tool_time'] = stats['total_tool_time'] / stats['total_tasks']
        stats['avg_tool_calls'] = stats['total_tool_calls'] / stats['total_tasks']
        
        # 计算工具平均时间
        for tool_name, tool_data in stats['tool_usage'].items():
            tool_data['avg_time'] = tool_data['total_time'] / tool_data['count']
        
        # 计算 MCP 平均时间
        for server_name, server_data in stats['mcp_usage'].items():
            server_data['avg_time'] = server_data['total_time'] / server_data['count']
    
    return stats

def print_statistics(stats, task_type, output_file=None):
    """打印统计报告"""
    report_lines = []
    
    def add_line(line=""):
        """添加一行到报告"""
        print(line)
        report_lines.append(line)
    
    add_line("\n" + "=" * 80)
    add_line(f"工具使用分析报告 - {task_type}")
    add_line("=" * 80)
    
    add_line(f"\n📊 总体统计:")
    add_line(f"  任务总数:           {stats['total_tasks']}")
    add_line(f"  总墙钟时间:         {stats['total_wall_time']:.1f}s ({stats['total_wall_time']/60:.1f}分钟)")
    add_line(f"  总 Agent 活动时间:  {stats['total_agent_active']:.1f}s ({stats['total_agent_active']/60:.1f}分钟)")
    add_line(f"  总 API 时间:        {stats['total_api_time']:.1f}s ({stats['total_api_time']/60:.1f}分钟)")
    add_line(f"  总工具时间:         {stats['total_tool_time']:.1f}s ({stats['total_tool_time']/60:.1f}分钟)")
    add_line(f"  总工具调用次数:     {stats['total_tool_calls']}")
    add_line(f"  平均成功率:         {stats['avg_success_rate']:.1f}%")
    
    add_line(f"\n📈 平均统计:")
    add_line(f"  平均墙钟时间:       {stats['avg_wall_time']:.1f}s")
    add_line(f"  平均 Agent 活动:    {stats['avg_agent_active']:.1f}s")
    add_line(f"  平均 API 时间:      {stats['avg_api_time']:.1f}s")
    add_line(f"  平均工具时间:       {stats['avg_tool_time']:.1f}s")
    add_line(f"  平均工具调用:       {stats['avg_tool_calls']:.1f}次")
    
    add_line(f"\n🔧 工具使用统计 (按总时间排序):")
    sorted_tools = sorted(stats['tool_usage'].items(), 
                         key=lambda x: x[1]['total_time'], 
                         reverse=True)
    for tool_name, tool_data in sorted_tools:
        add_line(f"  • {tool_name}:")
        add_line(f"      使用次数:     {tool_data['count']}")
        add_line(f"      总时间:       {tool_data['total_time']:.1f}s")
        add_line(f"      平均时间:     {tool_data['avg_time']:.2f}s")
        add_line(f"      最小/最大:    {min(tool_data['times']):.2f}s / {max(tool_data['times']):.2f}s")
    
    add_line(f"\n🌐 MCP 服务器使用统计 (按总时间排序):")
    sorted_mcps = sorted(stats['mcp_usage'].items(), 
                        key=lambda x: x[1]['total_time'], 
                        reverse=True)
    for server_name, server_data in sorted_mcps:
        add_line(f"  • {server_name}:")
        add_line(f"      使用次数:     {server_data['count']}")
        add_line(f"      总时间:       {server_data['total_time']:.1f}s")
        add_line(f"      平均时间:     {server_data['avg_time']:.2f}s")
    
    add_line(f"\n🤖 模型使用统计:")
    for model_name, model_data in stats['model_usage'].items():
        add_line(f"  • {model_name}:")
        add_line(f"      请求次数:     {model_data['requests']}")
        add_line(f"      输入 tokens:  {model_data['input_tokens']:,}")
        add_line(f"      输出 tokens:  {model_data['output_tokens']:,}")
        add_line(f"      总 tokens:    {model_data['total_tokens']:,}")
    
    # 保存报告到文件
    if output_file:
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        print(f"\n💾 报告已保存: {output_file}")

def create_visualizations(stats, task_type, output_dir):
    """创建可视化图表"""
    
    # 1. 工具使用时间排名
    fig1, ax1 = plt.subplots(figsize=(12, 8))
    
    sorted_tools = sorted(stats['tool_usage'].items(), 
                         key=lambda x: x[1]['total_time'], 
                         reverse=True)[:15]  # 只显示前15个
    
    if sorted_tools:
        tool_names = [t[0] for t in sorted_tools]
        tool_times = [t[1]['total_time'] for t in sorted_tools]
        
        y_pos = np.arange(len(tool_names))
        bars = ax1.barh(y_pos, tool_times, color='#3498db', alpha=0.7, edgecolor='black')
        ax1.set_yticks(y_pos)
        ax1.set_yticklabels(tool_names, fontsize=9)
        ax1.set_xlabel('总时间 (秒)', fontsize=11)
        ax1.set_title(f'{task_type} - 工具使用时间排名 (Top 15)', fontsize=13, fontweight='bold')
        ax1.grid(axis='x', alpha=0.3)
        
        # 添加数值标签
        for i, (bar, time) in enumerate(zip(bars, tool_times)):
            ax1.text(time, i, f' {time:.1f}s', va='center', fontsize=8)
    
    plt.tight_layout()
    output_path1 = output_dir / f'{task_type}_01_tool_usage_time.png'
    plt.savefig(output_path1, dpi=300, bbox_inches='tight')
    print(f"✅ 图表 1 已保存: {output_path1}")
    plt.close()
    
    # 2. 工具使用频率
    fig2, ax2 = plt.subplots(figsize=(12, 8))
    
    sorted_tools_freq = sorted(stats['tool_usage'].items(), 
                               key=lambda x: x[1]['count'], 
                               reverse=True)[:15]
    
    if sorted_tools_freq:
        tool_names = [t[0] for t in sorted_tools_freq]
        tool_counts = [t[1]['count'] for t in sorted_tools_freq]
        
        y_pos = np.arange(len(tool_names))
        bars = ax2.barh(y_pos, tool_counts, color='#2ecc71', alpha=0.7, edgecolor='black')
        ax2.set_yticks(y_pos)
        ax2.set_yticklabels(tool_names, fontsize=9)
        ax2.set_xlabel('使用次数', fontsize=11)
        ax2.set_title(f'{task_type} - 工具使用频率 (Top 15)', fontsize=13, fontweight='bold')
        ax2.grid(axis='x', alpha=0.3)
        
        for i, (bar, count) in enumerate(zip(bars, tool_counts)):
            ax2.text(count, i, f' {count}', va='center', fontsize=8)
    
    plt.tight_layout()
    output_path2 = output_dir / f'{task_type}_02_tool_usage_count.png'
    plt.savefig(output_path2, dpi=300, bbox_inches='tight')
    print(f"✅ 图表 2 已保存: {output_path2}")
    plt.close()
    
    # 3. MCP 服务器使用统计
    fig3, (ax3a, ax3b) = plt.subplots(1, 2, figsize=(14, 6))
    
    sorted_mcps = sorted(stats['mcp_usage'].items(), 
                        key=lambda x: x[1]['total_time'], 
                        reverse=True)
    
    if sorted_mcps:
        mcp_names = [m[0] for m in sorted_mcps]
        mcp_times = [m[1]['total_time'] for m in sorted_mcps]
        mcp_counts = [m[1]['count'] for m in sorted_mcps]
        
        # 时间
        y_pos = np.arange(len(mcp_names))
        ax3a.barh(y_pos, mcp_times, color='#e74c3c', alpha=0.7, edgecolor='black')
        ax3a.set_yticks(y_pos)
        ax3a.set_yticklabels(mcp_names, fontsize=9)
        ax3a.set_xlabel('总时间 (秒)', fontsize=11)
        ax3a.set_title('MCP 服务器总时间', fontsize=12, fontweight='bold')
        ax3a.grid(axis='x', alpha=0.3)
        
        for i, time in enumerate(mcp_times):
            ax3a.text(time, i, f' {time:.1f}s', va='center', fontsize=8)
        
        # 频率
        ax3b.barh(y_pos, mcp_counts, color='#f39c12', alpha=0.7, edgecolor='black')
        ax3b.set_yticks(y_pos)
        ax3b.set_yticklabels(mcp_names, fontsize=9)
        ax3b.set_xlabel('使用次数', fontsize=11)
        ax3b.set_title('MCP 服务器使用次数', fontsize=12, fontweight='bold')
        ax3b.grid(axis='x', alpha=0.3)
        
        for i, count in enumerate(mcp_counts):
            ax3b.text(count, i, f' {count}', va='center', fontsize=8)
    
    plt.tight_layout()
    output_path3 = output_dir / f'{task_type}_03_mcp_usage.png'
    plt.savefig(output_path3, dpi=300, bbox_inches='tight')
    print(f"✅ 图表 3 已保存: {output_path3}")
    plt.close()
    
    # 4. 时间分布饼图
    fig4, ((ax4a, ax4b), (ax4c, ax4d)) = plt.subplots(2, 2, figsize=(14, 12))
    
    # API vs Tool Time
    if stats['total_api_time'] > 0 or stats['total_tool_time'] > 0:
        sizes = [stats['total_api_time'], stats['total_tool_time']]
        labels = ['API 时间', '工具时间']
        colors = ['#3498db', '#e74c3c']
        explode = (0.05, 0.05)
        
        ax4a.pie(sizes, explode=explode, labels=labels, colors=colors,
                autopct='%1.1f%%', shadow=True, startangle=90)
        ax4a.set_title('API vs 工具时间分布', fontsize=12, fontweight='bold')
    
    # 前5个工具时间分布
    if sorted_tools:
        top_tools = sorted_tools[:5]
        tool_names = [t[0] for t in top_tools]
        tool_times = [t[1]['total_time'] for t in top_tools]
        
        ax4b.pie(tool_times, labels=tool_names, autopct='%1.1f%%', 
                shadow=True, startangle=90)
        ax4b.set_title('Top 5 工具时间分布', fontsize=12, fontweight='bold')
    
    # MCP 服务器时间分布
    if sorted_mcps:
        mcp_names = [m[0] for m in sorted_mcps]
        mcp_times = [m[1]['total_time'] for m in sorted_mcps]
        
        ax4c.pie(mcp_times, labels=mcp_names, autopct='%1.1f%%',
                shadow=True, startangle=90)
        ax4c.set_title('MCP 服务器时间分布', fontsize=12, fontweight='bold')
    
    # 模型 Token 使用分布
    if stats['model_usage']:
        model_names = list(stats['model_usage'].keys())
        token_counts = [stats['model_usage'][m]['total_tokens'] for m in model_names]
        
        ax4d.pie(token_counts, labels=model_names, autopct='%1.1f%%',
                shadow=True, startangle=90)
        ax4d.set_title('模型 Token 使用分布', fontsize=12, fontweight='bold')
    
    plt.tight_layout()
    output_path4 = output_dir / f'{task_type}_04_distributions.png'
    plt.savefig(output_path4, dpi=300, bbox_inches='tight')
    print(f"✅ 图表 4 已保存: {output_path4}")
    plt.close()
    
    # 5. 工具平均时间对比
    fig5, ax5 = plt.subplots(figsize=(12, 8))
    
    sorted_tools_avg = sorted(stats['tool_usage'].items(), 
                             key=lambda x: x[1]['avg_time'], 
                             reverse=True)[:15]
    
    if sorted_tools_avg:
        tool_names = [t[0] for t in sorted_tools_avg]
        tool_avg_times = [t[1]['avg_time'] for t in sorted_tools_avg]
        
        y_pos = np.arange(len(tool_names))
        bars = ax5.barh(y_pos, tool_avg_times, color='#9b59b6', alpha=0.7, edgecolor='black')
        ax5.set_yticks(y_pos)
        ax5.set_yticklabels(tool_names, fontsize=9)
        ax5.set_xlabel('平均时间 (秒)', fontsize=11)
        ax5.set_title(f'{task_type} - 工具平均执行时间 (Top 15)', fontsize=13, fontweight='bold')
        ax5.grid(axis='x', alpha=0.3)
        
        for i, (bar, time) in enumerate(zip(bars, tool_avg_times)):
            ax5.text(time, i, f' {time:.2f}s', va='center', fontsize=8)
    
    plt.tight_layout()
    output_path5 = output_dir / f'{task_type}_05_tool_avg_time.png'
    plt.savefig(output_path5, dpi=300, bbox_inches='tight')
    print(f"✅ 图表 5 已保存: {output_path5}")
    plt.close()

def main():
    """主函数"""
    script_dir = Path(__file__).parent
    
    # 创建输出目录
    output_dir = script_dir / 'tool_usage_analysis'
    output_dir.mkdir(exist_ok=True)
    print(f"\n📁 输出目录: {output_dir}")
    
    # 分析 deep_research 目录
    research_dir = script_dir / 'deep_research'
    if research_dir.exists():
        print(f"\n🔍 分析目录: {research_dir}")
        research_results = analyze_directory(research_dir)
        research_stats = aggregate_statistics(research_results)
        report_file = output_dir / 'deep_research_report.txt'
        print_statistics(research_stats, 'Deep Research', report_file)
        create_visualizations(research_stats, 'deep_research', output_dir)
    
    # 分析 code 目录 (如果存在)
    code_dir = script_dir / 'code'
    if code_dir.exists():
        print(f"\n🔍 分析目录: {code_dir}")
        code_results = analyze_directory(code_dir)
        code_stats = aggregate_statistics(code_results)
        report_file = output_dir / 'code_report.txt'
        print_statistics(code_stats, 'Code Tasks', report_file)
        create_visualizations(code_stats, 'code', output_dir)
    
    print("\n" + "=" * 80)
    print(f"✨ 分析完成! 所有结果已保存到: {output_dir}")
    print("=" * 80)

if __name__ == '__main__':
    main()
