#!/usr/bin/env python3
import re
import os
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
from collections import defaultdict

def parse_time_string(time_str):
    """Convert time string (e.g., '1m 2s', '22.4s', '308ms') to seconds"""
    total_seconds = 0.0
    
    # Handle minutes (e.g., "1m 2s")
    min_match = re.search(r'(\d+)m\s', time_str)
    if min_match:
        total_seconds += int(min_match.group(1)) * 60
    
    # Handle milliseconds first (to avoid confusion with seconds)
    ms_match = re.search(r'(\d+)ms\b', time_str)
    if ms_match:
        total_seconds += int(ms_match.group(1)) / 1000
        return total_seconds
    
    # Handle seconds
    sec_match = re.search(r'([\d.]+)s\b', time_str)
    if sec_match:
        total_seconds += float(sec_match.group(1))
    
    return total_seconds

def parse_detailed_tool_breakdown(filepath):
    """Parse a summary file and extract extremely detailed tool breakdown including sub-tasks"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    data = {
        'filename': Path(filepath).name,
        'tools': {},
        'tool_subtasks': defaultdict(dict),  # tool_name -> {subtask_name: time}
        'mcp_servers': {},
        'fetch_url_details': {},  # Special handling for fetch_url details
        'total_tool_time': 0,
        'mcp_init_time': 0
    }
    
    # Extract Tool Time section - need to handle the box drawing characters
    tool_section_match = re.search(r'» Tool Time:.*?(?=Detailed Timing Breakdown)', content, re.DOTALL)
    if not tool_section_match:
        return data
    
    tool_section = tool_section_match.group(0)
    # Remove box drawing characters
    tool_section = re.sub(r'[│╰╭─]', '', tool_section)
    lines = tool_section.split('\n')
    
    current_tool = None
    current_subtool = None
    
    for i, line in enumerate(lines):
        # Match main tool entry: • tool_name: time (percentage)
        main_tool_match = re.match(r'\s*• ([^:]+):\s+(.+?)\s+\((.+?)%\)', line)
        if main_tool_match:
            tool_name = main_tool_match.group(1).strip()
            time_str = main_tool_match.group(2).strip()
            percentage = float(main_tool_match.group(3))
            
            current_tool = tool_name
            data['tools'][tool_name] = {
                'time': parse_time_string(time_str),
                'percentage': percentage
            }
            continue
        
        # Match sub-tool entry: ‣ subtool_name: time (percentage)
        sub_tool_match = re.match(r'\s*‣ ([^:]+):\s+(.+?)\s+\((.+?)%\)', line)
        if sub_tool_match and current_tool:
            subtool_name = sub_tool_match.group(1).strip()
            time_str = sub_tool_match.group(2).strip()
            percentage = float(sub_tool_match.group(3))
            
            current_subtool = subtool_name
            data['tool_subtasks'][current_tool][subtool_name] = {
                'time': parse_time_string(time_str),
                'percentage': percentage
            }
            continue
        
        # Match detailed sub-sub-task entry: - task_name: time (percentage)
        detail_match = re.match(r'\s*- ([^:]+):\s+(.+?)\s+\((.+?)%\)', line)
        if detail_match and current_tool and current_subtool:
            detail_name = detail_match.group(1).strip()
            time_str = detail_match.group(2).strip()
            percentage = float(detail_match.group(3))
            
            # Store as subtool of current_subtool
            full_key = f"{current_subtool} → {detail_name}"
            data['tool_subtasks'][current_tool][full_key] = {
                'time': parse_time_string(time_str),
                'percentage': percentage
            }
    
    # Extract MCP Init time
    mcp_init_match = re.search(r'• MCP Init:\s+(.+?)\s+\((.+?)%\)', content)
    if mcp_init_match:
        data['mcp_init_time'] = parse_time_string(mcp_init_match.group(1))
    
    # Extract MCP Servers section
    mcp_section = re.search(r'» MCP Servers:.*?(?=» Tool|$)', content, re.DOTALL)
    if mcp_section:
        mcp_text = mcp_section.group(0)
        server_pattern = r'• ([^:]+):\s+(.+?)\s+\((.+?)%\)'
        for match in re.finditer(server_pattern, mcp_text):
            server_name = match.group(1).strip()
            time_str = match.group(2).strip()
            data['mcp_servers'][server_name] = parse_time_string(time_str)
    
    return data

def analyze_directory(directory_path, task_type):
    """Analyze all summary files in a directory"""
    results = []
    
    for file in sorted(Path(directory_path).glob('*_summary.txt')):
        if not file.is_file():
            continue
        try:
            data = parse_detailed_tool_breakdown(file)
            data['task_type'] = task_type
            results.append(data)
        except (PermissionError, OSError) as e:
            print(f"⚠️  Skipping {file.name}: {e}")
            continue
    
    return results

def aggregate_detailed_stats(results):
    """Aggregate detailed statistics across all tasks"""
    tool_times = defaultdict(list)
    subtask_times = defaultdict(lambda: defaultdict(list))
    mcp_init_times = []
    
    for result in results:
        if result['mcp_init_time'] > 0:
            mcp_init_times.append(result['mcp_init_time'])
        
        for tool_name, tool_data in result['tools'].items():
            tool_times[tool_name].append(tool_data['time'])
        
        for tool_name, subtasks in result['tool_subtasks'].items():
            for subtask_name, subtask_data in subtasks.items():
                subtask_times[tool_name][subtask_name].append(subtask_data['time'])
    
    # Calculate averages
    avg_tools = {name: np.mean(times) for name, times in tool_times.items()}
    avg_subtasks = {}
    for tool_name, subtasks in subtask_times.items():
        avg_subtasks[tool_name] = {
            subtask: np.mean(times) for subtask, times in subtasks.items()
        }
    avg_mcp_init = np.mean(mcp_init_times) if mcp_init_times else 0
    
    return avg_tools, avg_subtasks, avg_mcp_init

def create_detailed_visualizations(code_results, research_results):
    """Create extremely detailed visualizations"""
    
    code_tools, code_subtasks, code_mcp_init = aggregate_detailed_stats(code_results)
    research_tools, research_subtasks, research_mcp_init = aggregate_detailed_stats(research_results)
    
    output_dir = Path(__file__).parent
    
    print("=" * 80)
    print("EXTREMELY DETAILED TOOL BREAKDOWN ANALYSIS")
    print("=" * 80)
    
    print("\n📊 CODE TASKS - Detailed Breakdown:")
    print(f"  MCP Init: {code_mcp_init:.2f}s")
    for tool, time in sorted(code_tools.items(), key=lambda x: x[1], reverse=True):
        print(f"  {tool}: {time:.2f}s")
        if tool in code_subtasks:
            for subtask, sub_time in sorted(code_subtasks[tool].items(), key=lambda x: x[1], reverse=True):
                print(f"    └─ {subtask}: {sub_time:.3f}s")
    
    print("\n🔬 DEEP RESEARCH TASKS - Detailed Breakdown:")
    print(f"  MCP Init: {research_mcp_init:.2f}s")
    for tool, time in sorted(research_tools.items(), key=lambda x: x[1], reverse=True):
        print(f"  {tool}: {time:.2f}s")
        if tool in research_subtasks:
            for subtask, sub_time in sorted(research_subtasks[tool].items(), key=lambda x: x[1], reverse=True):
                print(f"    └─ {subtask}: {sub_time:.3f}s")
    
    # 1. Detailed breakdown for run_shell_command
    fig1, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    if 'run_shell_command' in code_subtasks and code_subtasks['run_shell_command']:
        subtasks = code_subtasks['run_shell_command']
        sorted_subtasks = sorted(subtasks.items(), key=lambda x: x[1], reverse=True)
        names = [s[0] for s in sorted_subtasks]
        times = [s[1] for s in sorted_subtasks]
        
        y_pos = np.arange(len(names))
        ax1.barh(y_pos, times, color='#3498db', alpha=0.7, edgecolor='black')
        ax1.set_yticks(y_pos)
        ax1.set_yticklabels(names, fontsize=9)
        ax1.set_xlabel('Average Time (seconds)', fontsize=11)
        ax1.set_title('Code Tasks - run_shell_command Breakdown', fontsize=12, fontweight='bold')
        ax1.grid(axis='x', alpha=0.3)
        
        for i, v in enumerate(times):
            ax1.text(v, i, f' {v:.3f}s', va='center', fontsize=8)
    else:
        ax1.text(0.5, 0.5, 'No run_shell_command data', ha='center', va='center', transform=ax1.transAxes)
    
    if 'run_shell_command' in research_subtasks and research_subtasks['run_shell_command']:
        subtasks = research_subtasks['run_shell_command']
        sorted_subtasks = sorted(subtasks.items(), key=lambda x: x[1], reverse=True)
        names = [s[0] for s in sorted_subtasks]
        times = [s[1] for s in sorted_subtasks]
        
        y_pos = np.arange(len(names))
        ax2.barh(y_pos, times, color='#e74c3c', alpha=0.7, edgecolor='black')
        ax2.set_yticks(y_pos)
        ax2.set_yticklabels(names, fontsize=9)
        ax2.set_xlabel('Average Time (seconds)', fontsize=11)
        ax2.set_title('Research Tasks - run_shell_command Breakdown', fontsize=12, fontweight='bold')
        ax2.grid(axis='x', alpha=0.3)
        
        for i, v in enumerate(times):
            ax2.text(v, i, f' {v:.3f}s', va='center', fontsize=8)
    else:
        ax2.text(0.5, 0.5, 'No run_shell_command data', ha='center', va='center', transform=ax2.transAxes)
    
    plt.tight_layout()
    output_path1 = output_dir / 'detailed_01_run_shell_command.png'
    plt.savefig(output_path1, dpi=300, bbox_inches='tight')
    print(f"\n✅ Chart 1 saved: {output_path1}")
    plt.close()
    
    # 2. Detailed breakdown for fetch_url (fetcher)
    fig2, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 8))
    
    if 'fetch_url (fetcher)' in code_subtasks and code_subtasks['fetch_url (fetcher)']:
        subtasks = code_subtasks['fetch_url (fetcher)']
        sorted_subtasks = sorted(subtasks.items(), key=lambda x: x[1], reverse=True)
        names = [s[0] for s in sorted_subtasks]
        times = [s[1] for s in sorted_subtasks]
        
        y_pos = np.arange(len(names))
        ax1.barh(y_pos, times, color='#2ecc71', alpha=0.7, edgecolor='black')
        ax1.set_yticks(y_pos)
        ax1.set_yticklabels(names, fontsize=8)
        ax1.set_xlabel('Average Time (seconds)', fontsize=11)
        ax1.set_title('Code Tasks - fetch_url Breakdown', fontsize=12, fontweight='bold')
        ax1.grid(axis='x', alpha=0.3)
        
        for i, v in enumerate(times):
            ax1.text(v, i, f' {v:.3f}s', va='center', fontsize=7)
    else:
        ax1.text(0.5, 0.5, 'No fetch_url data', ha='center', va='center', transform=ax1.transAxes)
    
    if 'fetch_url (fetcher)' in research_subtasks and research_subtasks['fetch_url (fetcher)']:
        subtasks = research_subtasks['fetch_url (fetcher)']
        sorted_subtasks = sorted(subtasks.items(), key=lambda x: x[1], reverse=True)
        names = [s[0] for s in sorted_subtasks]
        times = [s[1] for s in sorted_subtasks]
        
        y_pos = np.arange(len(names))
        ax2.barh(y_pos, times, color='#f39c12', alpha=0.7, edgecolor='black')
        ax2.set_yticks(y_pos)
        ax2.set_yticklabels(names, fontsize=8)
        ax2.set_xlabel('Average Time (seconds)', fontsize=11)
        ax2.set_title('Research Tasks - fetch_url Breakdown', fontsize=12, fontweight='bold')
        ax2.grid(axis='x', alpha=0.3)
        
        for i, v in enumerate(times):
            ax2.text(v, i, f' {v:.3f}s', va='center', fontsize=7)
    else:
        ax2.text(0.5, 0.5, 'No fetch_url data', ha='center', va='center', transform=ax2.transAxes)
    
    plt.tight_layout()
    output_path2 = output_dir / 'detailed_02_fetch_url.png'
    plt.savefig(output_path2, dpi=300, bbox_inches='tight')
    print(f"✅ Chart 2 saved: {output_path2}")
    plt.close()
    
    # 3. All tools with subtasks - Code Tasks
    fig3, ax = plt.subplots(figsize=(14, 10))
    
    all_items = []
    all_items.append(('MCP Init', code_mcp_init, '#9b59b6'))
    
    for tool_name, tool_time in sorted(code_tools.items(), key=lambda x: x[1], reverse=True):
        all_items.append((tool_name, tool_time, '#3498db'))
        if tool_name in code_subtasks:
            for subtask_name, subtask_time in sorted(code_subtasks[tool_name].items(), key=lambda x: x[1], reverse=True):
                display_name = f"  └─ {subtask_name}"
                all_items.append((display_name, subtask_time, '#95a5a6'))
    
    names = [item[0] for item in all_items]
    times = [item[1] for item in all_items]
    colors = [item[2] for item in all_items]
    
    y_pos = np.arange(len(names))
    ax.barh(y_pos, times, color=colors, alpha=0.7, edgecolor='black', linewidth=0.5)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(names, fontsize=7)
    ax.set_xlabel('Average Time (seconds)', fontsize=11)
    ax.set_title('Code Tasks - Complete Tool & Subtask Breakdown', fontsize=13, fontweight='bold')
    ax.grid(axis='x', alpha=0.3)
    
    for i, v in enumerate(times):
        if v > 0.01:
            ax.text(v, i, f' {v:.3f}s', va='center', fontsize=6)
    
    plt.tight_layout()
    output_path3 = output_dir / 'detailed_03_code_complete.png'
    plt.savefig(output_path3, dpi=300, bbox_inches='tight')
    print(f"✅ Chart 3 saved: {output_path3}")
    plt.close()
    
    # 4. All tools with subtasks - Research Tasks
    fig4, ax = plt.subplots(figsize=(14, 10))
    
    all_items = []
    all_items.append(('MCP Init', research_mcp_init, '#9b59b6'))
    
    for tool_name, tool_time in sorted(research_tools.items(), key=lambda x: x[1], reverse=True):
        all_items.append((tool_name, tool_time, '#e74c3c'))
        if tool_name in research_subtasks:
            for subtask_name, subtask_time in sorted(research_subtasks[tool_name].items(), key=lambda x: x[1], reverse=True):
                display_name = f"  └─ {subtask_name}"
                all_items.append((display_name, subtask_time, '#95a5a6'))
    
    names = [item[0] for item in all_items]
    times = [item[1] for item in all_items]
    colors = [item[2] for item in all_items]
    
    y_pos = np.arange(len(names))
    ax.barh(y_pos, times, color=colors, alpha=0.7, edgecolor='black', linewidth=0.5)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(names, fontsize=7)
    ax.set_xlabel('Average Time (seconds)', fontsize=11)
    ax.set_title('Research Tasks - Complete Tool & Subtask Breakdown', fontsize=13, fontweight='bold')
    ax.grid(axis='x', alpha=0.3)
    
    for i, v in enumerate(times):
        if v > 0.01:
            ax.text(v, i, f' {v:.3f}s', va='center', fontsize=6)
    
    plt.tight_layout()
    output_path4 = output_dir / 'detailed_04_research_complete.png'
    plt.savefig(output_path4, dpi=300, bbox_inches='tight')
    print(f"✅ Chart 4 saved: {output_path4}")
    plt.close()
    
    print(f"\n✨ All detailed visualizations saved successfully!")
    print(f"   Location: {output_dir}/detailed_*.png")

def main():
    script_dir = Path(__file__).parent
    
    code_dir = script_dir / 'code'
    code_results = analyze_directory(code_dir, 'code')
    
    research_dir = script_dir / 'deep_research'
    research_results = analyze_directory(research_dir, 'research')
    
    create_detailed_visualizations(code_results, research_results)

if __name__ == '__main__':
    main()
