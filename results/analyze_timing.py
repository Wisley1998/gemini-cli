#!/usr/bin/env python3
import re
import os
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np

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

def parse_summary_file(filepath):
    """Parse a summary file and extract timing information"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    data = {}
    
    # Extract Wall Time
    wall_time_match = re.search(r'Wall Time:\s+(.+?)\s+│', content)
    if wall_time_match:
        data['wall_time'] = parse_time_string(wall_time_match.group(1))
    
    # Extract Agent Active Time
    agent_active_match = re.search(r'Agent Active:\s+(.+?)\s+│', content)
    if agent_active_match:
        data['agent_active'] = parse_time_string(agent_active_match.group(1))
    
    # Extract API Time with percentage
    api_time_match = re.search(r'» API Time:\s+(.+?)\s+\((.+?)%\)', content)
    if api_time_match:
        data['api_time'] = parse_time_string(api_time_match.group(1))
        data['api_percentage'] = float(api_time_match.group(2))
    
    # Extract Tool Time with percentage
    tool_time_match = re.search(r'» Tool Time:\s+(.+?)\s+\((.+?)%\)', content)
    if tool_time_match:
        data['tool_time'] = parse_time_string(tool_time_match.group(1))
        data['tool_percentage'] = float(tool_time_match.group(2))
    
    # Extract MCP Init Time
    mcp_init_match = re.search(r'• MCP Init:\s+(.+?)\s+\((.+?)%\)', content)
    if mcp_init_match:
        data['mcp_init'] = parse_time_string(mcp_init_match.group(1))
        data['mcp_init_percentage'] = float(mcp_init_match.group(2))
    
    # Extract other tool times (excluding MCP Init)
    data['other_tool_time'] = data.get('tool_time', 0) - data.get('mcp_init', 0)
    if data.get('tool_time', 0) > 0:
        data['other_tool_percentage'] = (data['other_tool_time'] / data.get('tool_time', 1)) * 100
    
    return data

def analyze_directory(directory_path, task_type):
    """Analyze all summary files in a directory"""
    results = []
    
    for file in sorted(Path(directory_path).glob('*_summary.txt')):
        data = parse_summary_file(file)
        data['filename'] = file.name
        data['task_type'] = task_type
        results.append(data)
    
    return results

def calculate_averages(results):
    """Calculate average timing for a task type"""
    if not results:
        return {}
    
    avg = {}
    keys = ['wall_time', 'agent_active', 'api_time', 'tool_time', 'mcp_init', 'other_tool_time',
            'api_percentage', 'tool_percentage', 'mcp_init_percentage', 'other_tool_percentage']
    
    for key in keys:
        values = [r[key] for r in results if key in r]
        if values:
            avg[key] = np.mean(values)
    
    return avg

def create_visualization(code_results, research_results):
    """Create visualization comparing code and deep research tasks"""
    
    # Calculate averages
    code_avg = calculate_averages(code_results)
    research_avg = calculate_averages(research_results)
    
    # Print summary statistics
    print("=" * 80)
    print("TIMING ANALYSIS SUMMARY")
    print("=" * 80)
    
    print("\n📊 CODE TASKS (SWE-Bench)")
    print(f"  Number of tasks: {len(code_results)}")
    print(f"  Average wall time: {code_avg.get('wall_time', 0):.1f}s")
    print(f"  Average agent active time: {code_avg.get('agent_active', 0):.1f}s")
    print(f"  Average API time: {code_avg.get('api_time', 0):.1f}s ({code_avg.get('api_percentage', 0):.1f}%)")
    print(f"  Average Tool time: {code_avg.get('tool_time', 0):.1f}s ({code_avg.get('tool_percentage', 0):.1f}%)")
    print(f"    - MCP Init: {code_avg.get('mcp_init', 0):.1f}s ({code_avg.get('mcp_init_percentage', 0):.1f}% of tool time)")
    print(f"    - Other tools: {code_avg.get('other_tool_time', 0):.1f}s ({code_avg.get('other_tool_percentage', 0):.1f}% of tool time)")
    
    print("\n🔬 DEEP RESEARCH TASKS")
    print(f"  Number of tasks: {len(research_results)}")
    print(f"  Average wall time: {research_avg.get('wall_time', 0):.1f}s")
    print(f"  Average agent active time: {research_avg.get('agent_active', 0):.1f}s")
    print(f"  Average API time: {research_avg.get('api_time', 0):.1f}s ({research_avg.get('api_percentage', 0):.1f}%)")
    print(f"  Average Tool time: {research_avg.get('tool_time', 0):.1f}s ({research_avg.get('tool_percentage', 0):.1f}%)")
    print(f"    - MCP Init: {research_avg.get('mcp_init', 0):.1f}s ({research_avg.get('mcp_init_percentage', 0):.1f}% of tool time)")
    print(f"    - Other tools: {research_avg.get('other_tool_time', 0):.1f}s ({research_avg.get('other_tool_percentage', 0):.1f}% of tool time)")
    
    output_dir = Path(__file__).parent
    categories = ['Code Tasks\n(SWE-Bench)', 'Deep Research\nTasks']
    
    # 1. Agent Active Time Comparison
    fig1, ax1 = plt.subplots(figsize=(8, 6))
    agent_times = [code_avg.get('agent_active', 0), research_avg.get('agent_active', 0)]
    bars1 = ax1.bar(categories, agent_times, color=['#3498db', '#e74c3c'], alpha=0.7, edgecolor='black')
    ax1.set_ylabel('Time (seconds)', fontsize=12)
    ax1.set_title('Average Agent Active Time', fontsize=14, fontweight='bold')
    ax1.grid(axis='y', alpha=0.3)
    
    # Add value labels on bars
    for bar in bars1:
        height = bar.get_height()
        ax1.text(bar.get_x() + bar.get_width()/2., height,
                f'{height:.1f}s', ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    plt.tight_layout()
    output_path1 = output_dir / 'timing_01_agent_active_time.png'
    plt.savefig(output_path1, dpi=300, bbox_inches='tight')
    print(f"\n✅ Chart 1 saved: {output_path1}")
    plt.close()
    
    # 2. API vs Tool Time
    fig2, ax2 = plt.subplots(figsize=(8, 6))
    x = np.arange(len(categories))
    width = 0.35
    
    api_times = [code_avg.get('api_time', 0), research_avg.get('api_time', 0)]
    tool_times = [code_avg.get('tool_time', 0), research_avg.get('tool_time', 0)]
    
    bars2 = ax2.bar(x - width/2, api_times, width, label='API Time', color='#2ecc71', alpha=0.7, edgecolor='black')
    bars3 = ax2.bar(x + width/2, tool_times, width, label='Tool Time', color='#f39c12', alpha=0.7, edgecolor='black')
    
    ax2.set_ylabel('Time (seconds)', fontsize=12)
    ax2.set_title('Average API Time vs Tool Time', fontsize=14, fontweight='bold')
    ax2.set_xticks(x)
    ax2.set_xticklabels(categories)
    ax2.legend(fontsize=11)
    ax2.grid(axis='y', alpha=0.3)
    
    # Add value labels
    for bars in [bars2, bars3]:
        for bar in bars:
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}s', ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    output_path2 = output_dir / 'timing_02_api_vs_tool_time.png'
    plt.savefig(output_path2, dpi=300, bbox_inches='tight')
    print(f"✅ Chart 2 saved: {output_path2}")
    plt.close()
    
    # 3. Percentage Breakdown
    fig3, ax3 = plt.subplots(figsize=(8, 6))
    
    code_percentages = [code_avg.get('api_percentage', 0), code_avg.get('tool_percentage', 0)]
    research_percentages = [research_avg.get('api_percentage', 0), research_avg.get('tool_percentage', 0)]
    
    x = np.arange(len(categories))
    width = 0.35
    
    bars4 = ax3.bar(x - width/2, [code_percentages[0], research_percentages[0]], width, 
                    label='API Time %', color='#2ecc71', alpha=0.7, edgecolor='black')
    bars5 = ax3.bar(x + width/2, [code_percentages[1], research_percentages[1]], width, 
                    label='Tool Time %', color='#f39c12', alpha=0.7, edgecolor='black')
    
    ax3.set_ylabel('Percentage (%)', fontsize=12)
    ax3.set_title('Time Distribution (% of Agent Active Time)', fontsize=14, fontweight='bold')
    ax3.set_xticks(x)
    ax3.set_xticklabels(categories)
    ax3.legend(fontsize=11)
    ax3.grid(axis='y', alpha=0.3)
    ax3.set_ylim(0, 100)
    
    # Add value labels
    for bars in [bars4, bars5]:
        for bar in bars:
            height = bar.get_height()
            ax3.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}%', ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    output_path3 = output_dir / 'timing_03_percentage_breakdown.png'
    plt.savefig(output_path3, dpi=300, bbox_inches='tight')
    print(f"✅ Chart 3 saved: {output_path3}")
    plt.close()
    
    # 4. Tool Time Breakdown
    fig4, ax4 = plt.subplots(figsize=(8, 6))
    
    x = np.arange(len(categories))
    width = 0.35
    
    mcp_times = [code_avg.get('mcp_init', 0), research_avg.get('mcp_init', 0)]
    other_times = [code_avg.get('other_tool_time', 0), research_avg.get('other_tool_time', 0)]
    
    bars6 = ax4.bar(x - width/2, mcp_times, width, label='MCP Init', color='#9b59b6', alpha=0.7, edgecolor='black')
    bars7 = ax4.bar(x + width/2, other_times, width, label='Other Tools', color='#1abc9c', alpha=0.7, edgecolor='black')
    
    ax4.set_ylabel('Time (seconds)', fontsize=12)
    ax4.set_title('Tool Time Breakdown', fontsize=14, fontweight='bold')
    ax4.set_xticks(x)
    ax4.set_xticklabels(categories)
    ax4.legend(fontsize=11)
    ax4.grid(axis='y', alpha=0.3)
    
    # Add value labels
    for bars in [bars6, bars7]:
        for bar in bars:
            height = bar.get_height()
            ax4.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.1f}s', ha='center', va='bottom', fontsize=9)
    
    plt.tight_layout()
    output_path4 = output_dir / 'timing_04_tool_breakdown.png'
    plt.savefig(output_path4, dpi=300, bbox_inches='tight')
    print(f"✅ Chart 4 saved: {output_path4}")
    plt.close()
    
    print(f"\n✨ All visualizations saved successfully!")
    print(f"   Location: {output_dir}/timing_*.png")

def main():
    script_dir = Path(__file__).parent
    
    # Analyze code tasks
    code_dir = script_dir / 'code'
    code_results = analyze_directory(code_dir, 'code')
    
    # Analyze deep research tasks
    research_dir = script_dir / 'deep_research'
    research_results = analyze_directory(research_dir, 'research')
    
    # Create visualization
    create_visualization(code_results, research_results)

if __name__ == '__main__':
    main()
