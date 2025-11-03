#!/usr/bin/env python3
"""
事件-资源图分析示例
展示如何使用生成的图进行各种分析
"""

import networkx as nx
from pathlib import Path
from collections import defaultdict, Counter
from analyze_event_resource_graph import analyze_log, parse_log_file, build_event_graph


def analyze_graph_statistics(G: nx.MultiDiGraph, session_name: str):
    """分析图的基本统计信息"""
    print(f"\n{'='*60}")
    print(f"图统计分析: {session_name}")
    print(f"{'='*60}\n")
    
    # 基本统计
    print(f"节点总数: {G.number_of_nodes()}")
    print(f"边总数: {G.number_of_edges()}")
    print()
    
    # 节点类型分布
    print("节点类型分布:")
    node_types = defaultdict(int)
    for node, data in G.nodes(data=True):
        node_type = data.get('type', 'unknown')
        node_types[node_type] += 1
    
    for ntype, count in sorted(node_types.items()):
        print(f"  {ntype:20s}: {count:4d}")
    print()
    
    # 边类型分布
    print("边类型分布:")
    edge_types = defaultdict(int)
    for u, v, data in G.edges(data=True):
        edge_type = data.get('type', 'unknown')
        edge_types[edge_type] += 1
    
    for etype, count in sorted(edge_types.items()):
        print(f"  {etype:20s}: {count:4d}")
    print()


def analyze_domain_usage(G: nx.MultiDiGraph):
    """分析域名访问模式"""
    print(f"\n{'='*60}")
    print(f"域名访问分析")
    print(f"{'='*60}\n")
    
    # 收集所有域名节点
    domain_nodes = [
        (node, data) 
        for node, data in G.nodes(data=True) 
        if data.get('type') == 'domain'
    ]
    
    if not domain_nodes:
        print("未找到域名节点")
        return
    
    # 按类别分组
    by_category = defaultdict(list)
    for node, data in domain_nodes:
        category = data.get('domain_category', 'other')
        label = data.get('label', node)
        # 计算入度(被访问次数)
        in_degree = G.in_degree(node)
        by_category[category].append((label, in_degree))
    
    # 显示结果
    for category in sorted(by_category.keys()):
        domains = sorted(by_category[category], key=lambda x: x[1], reverse=True)
        print(f"\n{category.upper()}:")
        for domain, visits in domains:
            print(f"  {domain:40s} (访问 {visits} 次)")
    
    print()
    
    # 最常访问的域名
    all_domains = [
        (data.get('label', node), G.in_degree(node))
        for node, data in domain_nodes
    ]
    top_domains = sorted(all_domains, key=lambda x: x[1], reverse=True)[:5]
    
    print("\n最常访问的域名:")
    for i, (domain, visits) in enumerate(top_domains, 1):
        print(f"  {i}. {domain} ({visits} 次)")
    print()


def analyze_tool_usage(G: nx.MultiDiGraph):
    """分析工具使用模式"""
    print(f"\n{'='*60}")
    print(f"工具使用分析")
    print(f"{'='*60}\n")
    
    # 收集工具事件
    tool_events = [
        (node, data)
        for node, data in G.nodes(data=True)
        if data.get('type') == 'event' and data.get('subtype') == 'tool'
    ]
    
    if not tool_events:
        print("未找到工具事件")
        return
    
    # 统计工具使用
    tool_counter = Counter()
    tool_categories = defaultdict(set)
    
    for node, data in tool_events:
        tool_name = data.get('tool_name', 'unknown')
        category = data.get('category', 'unknown')
        tool_counter[tool_name] += 1
        tool_categories[category].add(tool_name)
    
    # 显示结果
    print(f"工具调用总数: {len(tool_events)}")
    print(f"不同工具数: {len(tool_counter)}\n")
    
    print("工具使用频率:")
    for tool, count in tool_counter.most_common():
        print(f"  {tool:30s}: {count:3d} 次")
    print()
    
    # 按类别显示
    print("\n按类别分组:")
    for category in sorted(tool_categories.keys()):
        tools = sorted(tool_categories[category])
        print(f"  {category}:")
        for tool in tools:
            count = tool_counter[tool]
            print(f"    - {tool} ({count} 次)")
    print()


def analyze_execution_flow(G: nx.MultiDiGraph):
    """分析执行流程"""
    print(f"\n{'='*60}")
    print(f"执行流程分析")
    print(f"{'='*60}\n")
    
    # 获取所有事件节点,按step排序
    event_nodes = [
        (node, data)
        for node, data in G.nodes(data=True)
        if data.get('type') == 'event'
    ]
    event_nodes.sort(key=lambda x: x[1].get('step', 0))
    
    if not event_nodes:
        print("未找到事件节点")
        return
    
    print(f"事件总数: {len(event_nodes)}\n")
    
    # 统计LLM和Tool事件
    llm_count = sum(1 for _, data in event_nodes if data.get('subtype') == 'llm')
    tool_count = sum(1 for _, data in event_nodes if data.get('subtype') == 'tool')
    
    print(f"LLM事件: {llm_count}")
    print(f"工具事件: {tool_count}")
    print()
    
    # 显示前10个事件
    print("执行序列 (前10个事件):")
    for i, (node, data) in enumerate(event_nodes[:10], 1):
        step = data.get('step', '?')
        subtype = data.get('subtype', 'unknown')
        label = data.get('label', node)[:60]
        timestamp = data.get('timestamp', '')[:19]
        
        if subtype == 'llm':
            print(f"  {step:3d}. [LLM] {label}")
        else:
            tool_name = data.get('tool_name', 'unknown')
            print(f"  {step:3d}. [TOOL:{tool_name}] {label}")
    
    if len(event_nodes) > 10:
        print(f"  ... (还有 {len(event_nodes) - 10} 个事件)")
    print()


def analyze_phase_distribution(G: nx.MultiDiGraph):
    """分析任务阶段分布"""
    print(f"\n{'='*60}")
    print(f"任务阶段分析")
    print(f"{'='*60}\n")
    
    # 收集阶段节点
    phase_nodes = [
        (node, data)
        for node, data in G.nodes(data=True)
        if data.get('type') == 'phase'
    ]
    
    if not phase_nodes:
        print("未找到阶段节点 (可能未启用阶段分析)")
        return
    
    # 统计每个阶段的事件数
    phase_events = defaultdict(list)
    
    for u, v, data in G.edges(data=True):
        if data.get('type') == 'in_phase':
            event_node = u
            phase_node = v
            
            # 获取事件信息
            event_data = G.nodes[event_node]
            phase_label = G.nodes[phase_node].get('label', phase_node)
            
            phase_events[phase_label].append(event_data)
    
    # 显示结果
    print(f"识别的阶段数: {len(phase_events)}\n")
    
    for phase in sorted(phase_events.keys()):
        events = phase_events[phase]
        llm_events = sum(1 for e in events if e.get('subtype') == 'llm')
        tool_events = sum(1 for e in events if e.get('subtype') == 'tool')
        
        print(f"{phase}:")
        print(f"  事件数: {len(events)} (LLM: {llm_events}, Tool: {tool_events})")
    print()


def analyze_url_patterns(G: nx.MultiDiGraph):
    """分析URL访问模式"""
    print(f"\n{'='*60}")
    print(f"URL访问模式分析")
    print(f"{'='*60}\n")
    
    # 收集URL节点
    url_nodes = [
        (node, data)
        for node, data in G.nodes(data=True)
        if data.get('type') == 'url'
    ]
    
    if not url_nodes:
        print("未找到URL节点")
        return
    
    print(f"访问的URL总数: {len(url_nodes)}\n")
    
    # 按scheme统计
    scheme_counter = Counter()
    for node, data in url_nodes:
        scheme = data.get('scheme', 'unknown')
        scheme_counter[scheme] += 1
    
    print("URL协议分布:")
    for scheme, count in scheme_counter.most_common():
        print(f"  {scheme}: {count}")
    print()
    
    # 显示部分URL
    print("示例URL (前10个):")
    for i, (node, data) in enumerate(url_nodes[:10], 1):
        label = data.get('label', node)
        in_degree = G.in_degree(node)
        print(f"  {i}. {label} (被访问 {in_degree} 次)")
    
    if len(url_nodes) > 10:
        print(f"  ... (还有 {len(url_nodes) - 10} 个URL)")
    print()


def analyze_query_params(G: nx.MultiDiGraph):
    """分析查询参数使用"""
    print(f"\n{'='*60}")
    print(f"查询参数分析")
    print(f"{'='*60}\n")
    
    # 收集查询参数节点
    param_nodes = [
        (node, data)
        for node, data in G.nodes(data=True)
        if data.get('type') == 'query_param'
    ]
    
    if not param_nodes:
        print("未找到查询参数节点 (可能未启用参数分析)")
        return
    
    print(f"查询参数总数: {len(param_nodes)}\n")
    
    # 按键统计
    key_counter = Counter()
    for node, data in param_nodes:
        key = data.get('key', 'unknown')
        key_counter[key] += 1
    
    print("查询参数键分布:")
    for key, count in key_counter.most_common(20):
        print(f"  {key:30s}: {count:3d}")
    
    if len(key_counter) > 20:
        print(f"  ... (还有 {len(key_counter) - 20} 个参数键)")
    print()


def generate_summary_report(log_path: str, output_dir: str = "output"):
    """生成完整的分析报告"""
    print(f"\n{'#'*60}")
    print(f"事件-资源图 完整分析报告")
    print(f"{'#'*60}")
    
    # 解析日志
    log_file = Path(log_path)
    session_name = log_file.stem
    
    print(f"\n日志文件: {log_path}")
    print(f"会话名称: {session_name}\n")
    
    # 构建图
    interactions = parse_log_file(log_path)
    G = build_event_graph(
        interactions,
        session_name=session_name,
        add_phase=True,
        add_query_params=True
    )
    
    # 运行所有分析
    analyze_graph_statistics(G, session_name)
    analyze_execution_flow(G)
    analyze_tool_usage(G)
    analyze_domain_usage(G)
    analyze_phase_distribution(G)
    analyze_url_patterns(G)
    analyze_query_params(G)
    
    print(f"\n{'#'*60}")
    print(f"报告完成")
    print(f"{'#'*60}\n")
    
    return G


def main():
    """主函数"""
    import sys
    
    if len(sys.argv) < 2:
        print("用法: python graph_analysis_examples.py <log_file>")
        print("示例: python graph_analysis_examples.py logs/10-22-18-1.log")
        sys.exit(1)
    
    log_path = sys.argv[1]
    
    if not Path(log_path).exists():
        print(f"错误: 日志文件不存在: {log_path}")
        sys.exit(1)
    
    generate_summary_report(log_path)


if __name__ == "__main__":
    main()
