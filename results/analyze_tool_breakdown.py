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
    # Match pattern like "308ms" but NOT "22.4s" 
    ms_match = re.search(r'(\d+)ms\b', time_str)
    if ms_match:
        total_seconds += int(ms_match.group(1)) / 1000
        return total_seconds  # If it's milliseconds, return immediately
    
    # Handle seconds (e.g., "22.4s" or "1m 2s")
    # This matches decimal seconds or integer seconds not followed by 'm'
    sec_match = re.search(r'([\d.]+)s\b', time_str)
    if sec_match:
        total_seconds += float(sec_match.group(1))
    
    return total_seconds

def parse_tool_breakdown(filepath):
    """Parse a summary file and extract detailed tool breakdown"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    data = {
        'filename': Path(filepath).name,
        'tools': {},
        'mcp_servers': {},
        'total_tool_time': 0,
        'mcp_init_time': 0
    }
    
    # Extract total tool time
    tool_time_match = re.search(r'» Tool Time:\s+(.+?)\s+\(', content)
    if tool_time_match:
        data['total_tool_time'] = parse_time_string(tool_time_match.group(1))
    
    # Extract MCP Init time
    mcp_init_match = re.search(r'• MCP Init:\s+(.+?)\s+\((.+?)%\)', content)
    if mcp_init_match:
        data['mcp_init_time'] = parse_time_string(mcp_init_match.group(1))
        data['mcp_init_percentage'] = float(mcp_init_match.group(2))
    
    # Extract individual tool times (after Tool Time section, before Detailed Timing Breakdown)
    tool_section = re.search(r'» Tool Time:.*?(?=Detailed Timing Breakdown)', content, re.DOTALL)
    if tool_section:
        tool_text = tool_section.group(0)
        
        # Parse each tool (excluding MCP Init which we already have)
        tool_pattern = r'• ([^:]+):\s+(.+?)\s+\((.+?)%\)'
        for match in re.finditer(tool_pattern, tool_text):
            tool_name = match.group(1).strip()
            if tool_name != 'MCP Init':
                time_str = match.group(2).strip()
                percentage = float(match.group(3))
                data['tools'][tool_name] = {
                    'time': parse_time_string(time_str),
                    'percentage': percentage
                }
    
    # Extract MCP Server breakdown
    mcp_section = re.search(r'» MCP Servers:.*?(?=» Tool|$)', content, re.DOTALL)
    if mcp_section:
        mcp_text = mcp_section.group(0)
        
        # Parse each MCP server
        server_pattern = r'• ([^:]+):\s+(.+?)\s+\((.+?)%\)'
        for match in re.finditer(server_pattern, mcp_text):
            server_name = match.group(1).strip()
            time_str = match.group(2).strip()
            percentage = float(match.group(3))
            
            # Extract connection and discovery times
            server_start = match.start()
            next_match = re.search(r'• ', mcp_text[server_start + 1:])
            if next_match:
                server_detail = mcp_text[server_start:server_start + 1 + next_match.start()]
            else:
                server_detail = mcp_text[server_start:]
            
            connection_match = re.search(r'‣ Connection:\s+(.+?)\s+\((.+?)%\)', server_detail)
            discovery_match = re.search(r'‣ Discovery:\s+(.+?)\s+\((.+?)%\)', server_detail)
            
            data['mcp_servers'][server_name] = {
                'total_time': parse_time_string(time_str),
                'total_percentage': percentage,
                'connection_time': 0,
                'discovery_time': 0
            }
            
            if connection_match:
                data['mcp_servers'][server_name]['connection_time'] = parse_time_string(connection_match.group(1))
            if discovery_match:
                data['mcp_servers'][server_name]['discovery_time'] = parse_time_string(discovery_match.group(1))
    
    return data

def analyze_directory(directory_path, task_type):
    """Analyze all summary files in a directory"""
    results = []
    
    for file in sorted(Path(directory_path).glob('*_summary.txt')):
        # Skip files that are not regular files or have read permission issues
        if not file.is_file():
            continue
        try:
            data = parse_tool_breakdown(file)
            data['task_type'] = task_type
            results.append(data)
        except (PermissionError, OSError) as e:
            print(f"⚠️  Skipping {file.name}: {e}")
            continue
    
    return results

def aggregate_tool_stats(results):
    """Aggregate tool statistics across all tasks"""
    tool_times = defaultdict(list)
    mcp_server_times = defaultdict(list)
    mcp_init_times = []
    
    for result in results:
        # Collect MCP Init times
        if result['mcp_init_time'] > 0:
            mcp_init_times.append(result['mcp_init_time'])
        
        # Collect individual tool times
        for tool_name, tool_data in result['tools'].items():
            tool_times[tool_name].append(tool_data['time'])
        
        # Collect MCP server times
        for server_name, server_data in result['mcp_servers'].items():
            mcp_server_times[server_name].append(server_data['total_time'])
    
    # Calculate averages
    avg_tools = {}
    for tool_name, times in tool_times.items():
        avg_tools[tool_name] = np.mean(times)
    
    avg_mcp_servers = {}
    for server_name, times in mcp_server_times.items():
        avg_mcp_servers[server_name] = np.mean(times)
    
    avg_mcp_init = np.mean(mcp_init_times) if mcp_init_times else 0
    
    return avg_tools, avg_mcp_servers, avg_mcp_init

def create_tool_breakdown_visualizations(code_results, research_results):
    """Create detailed tool breakdown visualizations"""
    
    # Aggregate statistics
    code_tools, code_mcp_servers, code_mcp_init = aggregate_tool_stats(code_results)
    research_tools, research_mcp_servers, research_mcp_init = aggregate_tool_stats(research_results)
    
    output_dir = Path(__file__).parent
    
    # Print summary
    print("=" * 80)
    print("DETAILED TOOL BREAKDOWN ANALYSIS")
    print("=" * 80)
    
    print("\n📊 CODE TASKS - Tool Usage:")
    print(f"  MCP Init: {code_mcp_init:.2f}s")
    for tool, time in sorted(code_tools.items(), key=lambda x: x[1], reverse=True):
        print(f"  {tool}: {time:.2f}s")
    
    print("\n📊 CODE TASKS - MCP Servers:")
    for server, time in sorted(code_mcp_servers.items(), key=lambda x: x[1], reverse=True):
        print(f"  {server}: {time:.2f}s")
    
    print("\n🔬 DEEP RESEARCH TASKS - Tool Usage:")
    print(f"  MCP Init: {research_mcp_init:.2f}s")
    for tool, time in sorted(research_tools.items(), key=lambda x: x[1], reverse=True):
        print(f"  {tool}: {time:.2f}s")
    
    print("\n🔬 DEEP RESEARCH TASKS - MCP Servers:")
    for server, time in sorted(research_mcp_servers.items(), key=lambda x: x[1], reverse=True):
        print(f"  {server}: {time:.2f}s")
    
    # 1. Tool Usage Comparison (excluding MCP Init)
    fig1, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Code tasks
    if code_tools:
        sorted_code_tools = sorted(code_tools.items(), key=lambda x: x[1], reverse=True)
        tools_names = [t[0] for t in sorted_code_tools]
        tools_times = [t[1] for t in sorted_code_tools]
        
        y_pos = np.arange(len(tools_names))
        ax1.barh(y_pos, tools_times, color='#3498db', alpha=0.7, edgecolor='black')
        ax1.set_yticks(y_pos)
        ax1.set_yticklabels(tools_names)
        ax1.set_xlabel('Average Time (seconds)', fontsize=11)
        ax1.set_title('Code Tasks - Tool Usage', fontsize=13, fontweight='bold')
        ax1.grid(axis='x', alpha=0.3)
        
        # Add value labels
        for i, v in enumerate(tools_times):
            ax1.text(v, i, f' {v:.2f}s', va='center', fontsize=9)
    
    # Deep research tasks
    if research_tools:
        sorted_research_tools = sorted(research_tools.items(), key=lambda x: x[1], reverse=True)
        tools_names = [t[0] for t in sorted_research_tools]
        tools_times = [t[1] for t in sorted_research_tools]
        
        y_pos = np.arange(len(tools_names))
        ax2.barh(y_pos, tools_times, color='#e74c3c', alpha=0.7, edgecolor='black')
        ax2.set_yticks(y_pos)
        ax2.set_yticklabels(tools_names)
        ax2.set_xlabel('Average Time (seconds)', fontsize=11)
        ax2.set_title('Deep Research Tasks - Tool Usage', fontsize=13, fontweight='bold')
        ax2.grid(axis='x', alpha=0.3)
        
        # Add value labels
        for i, v in enumerate(tools_times):
            ax2.text(v, i, f' {v:.2f}s', va='center', fontsize=9)
    
    plt.tight_layout()
    output_path1 = output_dir / 'tool_detail_01_tool_usage.png'
    plt.savefig(output_path1, dpi=300, bbox_inches='tight')
    print(f"\n✅ Chart 1 saved: {output_path1}")
    plt.close()
    
    # 2. MCP Server Initialization Breakdown
    fig2, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6))
    
    # Code tasks
    if code_mcp_servers:
        sorted_code_servers = sorted(code_mcp_servers.items(), key=lambda x: x[1], reverse=True)
        server_names = [s[0] for s in sorted_code_servers]
        server_times = [s[1] for s in sorted_code_servers]
        
        y_pos = np.arange(len(server_names))
        ax1.barh(y_pos, server_times, color='#9b59b6', alpha=0.7, edgecolor='black')
        ax1.set_yticks(y_pos)
        ax1.set_yticklabels(server_names)
        ax1.set_xlabel('Average Time (seconds)', fontsize=11)
        ax1.set_title('Code Tasks - MCP Server Init', fontsize=13, fontweight='bold')
        ax1.grid(axis='x', alpha=0.3)
        
        # Add value labels
        for i, v in enumerate(server_times):
            ax1.text(v, i, f' {v:.2f}s', va='center', fontsize=9)
    
    # Deep research tasks
    if research_mcp_servers:
        sorted_research_servers = sorted(research_mcp_servers.items(), key=lambda x: x[1], reverse=True)
        server_names = [s[0] for s in sorted_research_servers]
        server_times = [s[1] for s in sorted_research_servers]
        
        y_pos = np.arange(len(server_names))
        ax2.barh(y_pos, server_times, color='#e67e22', alpha=0.7, edgecolor='black')
        ax2.set_yticks(y_pos)
        ax2.set_yticklabels(server_names)
        ax2.set_xlabel('Average Time (seconds)', fontsize=11)
        ax2.set_title('Deep Research Tasks - MCP Server Init', fontsize=13, fontweight='bold')
        ax2.grid(axis='x', alpha=0.3)
        
        # Add value labels
        for i, v in enumerate(server_times):
            ax2.text(v, i, f' {v:.2f}s', va='center', fontsize=9)
    
    plt.tight_layout()
    output_path2 = output_dir / 'tool_detail_02_mcp_servers.png'
    plt.savefig(output_path2, dpi=300, bbox_inches='tight')
    print(f"✅ Chart 2 saved: {output_path2}")
    plt.close()
    
    # 3. Combined Tool Time Distribution (Pie Charts)
    fig3, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7))
    
    # Code tasks - pie chart
    code_combined = {'MCP Init': code_mcp_init}
    code_combined.update(code_tools)
    
    if code_combined:
        # Filter out very small values and group them as "Other"
        threshold = 0.5  # seconds
        main_items = {k: v for k, v in code_combined.items() if v >= threshold}
        other_sum = sum(v for k, v in code_combined.items() if v < threshold)
        
        if other_sum > 0:
            main_items['Other'] = other_sum
        
        sorted_items = sorted(main_items.items(), key=lambda x: x[1], reverse=True)
        labels = [item[0] for item in sorted_items]
        sizes = [item[1] for item in sorted_items]
        
        colors = plt.cm.Set3(np.linspace(0, 1, len(labels)))
        
        wedges, texts, autotexts = ax1.pie(sizes, labels=labels, autopct='%1.1f%%',
                                            colors=colors, startangle=90,
                                            textprops={'fontsize': 10})
        
        # Make percentage text bold
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(9)
        
        ax1.set_title('Code Tasks - Tool Time Distribution', fontsize=13, fontweight='bold', pad=20)
    
    # Deep research tasks - pie chart
    research_combined = {'MCP Init': research_mcp_init}
    research_combined.update(research_tools)
    
    if research_combined:
        # Filter out very small values and group them as "Other"
        threshold = 0.5  # seconds
        main_items = {k: v for k, v in research_combined.items() if v >= threshold}
        other_sum = sum(v for k, v in research_combined.items() if v < threshold)
        
        if other_sum > 0:
            main_items['Other'] = other_sum
        
        sorted_items = sorted(main_items.items(), key=lambda x: x[1], reverse=True)
        labels = [item[0] for item in sorted_items]
        sizes = [item[1] for item in sorted_items]
        
        colors = plt.cm.Set3(np.linspace(0, 1, len(labels)))
        
        wedges, texts, autotexts = ax2.pie(sizes, labels=labels, autopct='%1.1f%%',
                                            colors=colors, startangle=90,
                                            textprops={'fontsize': 10})
        
        # Make percentage text bold
        for autotext in autotexts:
            autotext.set_color('white')
            autotext.set_fontweight('bold')
            autotext.set_fontsize(9)
        
        ax2.set_title('Deep Research Tasks - Tool Time Distribution', fontsize=13, fontweight='bold', pad=20)
    
    plt.tight_layout()
    output_path3 = output_dir / 'tool_detail_03_time_distribution.png'
    plt.savefig(output_path3, dpi=300, bbox_inches='tight')
    print(f"✅ Chart 3 saved: {output_path3}")
    plt.close()
    
    # 4. Top Tools Comparison
    fig4, ax = plt.subplots(figsize=(12, 8))
    
    # Get top 10 tools from both task types
    all_tools = set(code_tools.keys()) | set(research_tools.keys())
    all_tools.add('MCP Init')
    
    tool_comparison = []
    for tool in all_tools:
        code_time = code_mcp_init if tool == 'MCP Init' else code_tools.get(tool, 0)
        research_time = research_mcp_init if tool == 'MCP Init' else research_tools.get(tool, 0)
        total_time = code_time + research_time
        tool_comparison.append((tool, code_time, research_time, total_time))
    
    # Sort by total time and take top 10
    tool_comparison.sort(key=lambda x: x[3], reverse=True)
    top_tools = tool_comparison[:10]
    
    tools = [t[0] for t in top_tools]
    code_times = [t[1] for t in top_tools]
    research_times = [t[2] for t in top_tools]
    
    x = np.arange(len(tools))
    width = 0.35
    
    bars1 = ax.bar(x - width/2, code_times, width, label='Code Tasks', 
                   color='#3498db', alpha=0.7, edgecolor='black')
    bars2 = ax.bar(x + width/2, research_times, width, label='Deep Research Tasks', 
                   color='#e74c3c', alpha=0.7, edgecolor='black')
    
    ax.set_ylabel('Average Time (seconds)', fontsize=12)
    ax.set_title('Top 10 Tools - Comparison', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(tools, rotation=45, ha='right')
    ax.legend(fontsize=11)
    ax.grid(axis='y', alpha=0.3)
    
    # Add value labels
    for bars in [bars1, bars2]:
        for bar in bars:
            height = bar.get_height()
            if height > 0:
                ax.text(bar.get_x() + bar.get_width()/2., height,
                       f'{height:.1f}s', ha='center', va='bottom', fontsize=8)
    
    plt.tight_layout()
    output_path4 = output_dir / 'tool_detail_04_top_tools_comparison.png'
    plt.savefig(output_path4, dpi=300, bbox_inches='tight')
    print(f"✅ Chart 4 saved: {output_path4}")
    plt.close()
    
    print(f"\n✨ All detailed tool breakdown visualizations saved successfully!")
    print(f"   Location: {output_dir}/tool_detail_*.png")

def main():
    script_dir = Path(__file__).parent
    
    # Analyze code tasks
    code_dir = script_dir / 'code'
    code_results = analyze_directory(code_dir, 'code')
    
    # Analyze deep research tasks
    research_dir = script_dir / 'deep_research'
    research_results = analyze_directory(research_dir, 'research')
    
    # Create visualizations
    create_tool_breakdown_visualizations(code_results, research_results)

if __name__ == '__main__':
    main()
