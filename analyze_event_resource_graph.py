#!/usr/bin/env python3
"""
事件-资源异构图生成工具
将Gemini Agent日志转换为复杂的事件-资源图结构
"""

import json
import re
import hashlib
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from datetime import datetime
import networkx as nx
from collections import defaultdict

try:
    import pydot
    HAS_PYDOT = True
except ImportError:
    HAS_PYDOT = False
    print("警告: pydot未安装,无法生成PNG图像。请运行: pip install pydot")

# ========== 配置 ==========

# 域名类别映射
DOMAIN_CATEGORY_MAP = {
    "google.com": "search",
    "duckduckgo.com": "search",
    "bing.com": "search",
    "reuters.com": "news",
    "bloomberg.com": "news",
    "wsj.com": "news",
    "ft.com": "news",
    "goldprice.org": "data_source",
    "stooq.com": "data_source",
    "fred.stlouisfed.org": "data_source",
    "finance.yahoo.com": "finance_portal",
    "query1.finance.yahoo.com": "api",
}

# 工具类别映射
TOOL_CATEGORY_MAP = {
    "fetch_url": "network",
    "browser_navigate": "browser",
    "playwright_navigate": "browser",
    "playwright_screenshot": "browser",
    "github_search": "api",
    "github_get_file": "api",
}

# 阶段识别关键词
PHASE_KEYWORDS = {
    "search": ["Google", "search", "searching", "查找", "搜索"],
    "direct_source": ["goldprice.org", "direct", "直接"],
    "yahoo_download": ["Yahoo", "GC=F", "download", "下载"],
    "news_fallback": ["Reuters", "Bloomberg", "news", "新闻"],
    "error": ["timeout", "blocked", "404", "authentication", "错误", "失败"],
}


# ========== URL处理 ==========

def normalize_url(raw_url: str) -> Tuple[str, Dict]:
    """
    URL规范化处理
    
    返回: (normalized_url, metadata)
    metadata包含: scheme, host, path, query_dict
    """
    # 去除特殊前缀
    url = raw_url.replace("URL_:", "").replace("URL_", "").strip()
    
    # 补充scheme
    if not url.startswith(("http://", "https://")):
        url = "https://" + url
    
    try:
        parsed = urlparse(url)
        
        # 解析查询参数
        query_dict = parse_qs(parsed.query)
        
        # 查询参数排序(用于规范化)
        sorted_query = urlencode(sorted(query_dict.items()), doseq=True)
        
        # 重建规范化URL
        normalized = urlunparse((
            parsed.scheme,
            parsed.netloc.lower(),
            parsed.path,
            parsed.params,
            sorted_query,
            ""  # 移除fragment
        ))
        
        metadata = {
            "scheme": parsed.scheme,
            "host": parsed.netloc.lower(),
            "path": parsed.path,
            "query_dict": query_dict,
        }
        
        return normalized, metadata
        
    except Exception as e:
        print(f"URL解析错误 {raw_url}: {e}")
        return raw_url, {
            "scheme": "unknown",
            "host": "unknown",
            "path": "",
            "query_dict": {},
        }


def get_domain_category(host: str) -> str:
    """获取域名类别"""
    for domain, category in DOMAIN_CATEGORY_MAP.items():
        if domain in host:
            return category
    return "other"


def get_tool_category(tool_name: str) -> str:
    """获取工具类别"""
    return TOOL_CATEGORY_MAP.get(tool_name, "unknown")


# ========== 日志解析 ==========

def parse_log_file(log_path: str) -> List[Dict]:
    """
    解析日志文件,提取交互事件
    
    返回: 交互事件列表,每个事件包含:
    - type: "llm_call" 或 "tool_call"
    - timestamp: ISO8601字符串
    - step: 整数索引
    - data: 原始数据
    """
    interactions = []
    step = 0
    
    with open(log_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 分割请求和响应块
    blocks = re.split(r'-{80,}', content)
    
    current_request = None
    
    for block in blocks:
        block = block.strip()
        if not block:
            continue
        
        # 解析请求
        if "[REQUEST]" in block:
            # 提取时间戳
            ts_match = re.search(r'\[REQUEST\]\s+(\S+)', block)
            if ts_match:
                timestamp = ts_match.group(1)
                current_request = {
                    "timestamp": timestamp,
                    "block": block
                }
        
        # 解析响应
        elif "[RESPONSE]" in block and current_request:
            ts_match = re.search(r'\[RESPONSE\]\s+(\S+)', block)
            if ts_match:
                timestamp = ts_match.group(1)
                
                # 查找functionCall
                if "functionCall" in block:
                    # 提取functionCall JSON - 改进正则以处理嵌套结构
                    fc_match = re.search(r'"functionCall":\s*(\{(?:[^{}]|(?:\{[^}]*\}))*\})', block, re.DOTALL)
                    if fc_match:
                        try:
                            fc_data = json.loads(fc_match.group(1))
                            tool_name = fc_data.get("name", "unknown")
                            args = fc_data.get("args", {})
                            
                            interactions.append({
                                "type": "tool_call",
                                "timestamp": timestamp,
                                "step": step,
                                "tool_name": tool_name,
                                "args": args,
                                "raw": block
                            })
                            step += 1
                        except json.JSONDecodeError:
                            # 静默处理JSON错误,避免大量输出
                            pass
                
                # 查找thought (LLM思考)
                if '"thought":' in block or '"text":' in block:
                    # 提取thoughts
                    thoughts = []
                    thought_matches = re.findall(r'"text":\s*"([^"]*)"', block)
                    thoughts.extend(thought_matches)
                    
                    if thoughts:
                        interactions.append({
                            "type": "llm_call",
                            "timestamp": timestamp,
                            "step": step,
                            "thoughts": thoughts,
                            "has_tool_calls": "functionCall" in block,
                            "raw": block[:500]  # 只保存前500字符
                        })
                        step += 1
                
                current_request = None
    
    return interactions


# ========== 阶段识别 ==========

def identify_phase(thoughts: List[str], prev_phase: Optional[str] = None) -> str:
    """
    从LLM思考内容识别任务阶段
    """
    text = " ".join(thoughts).lower()
    
    for phase, keywords in PHASE_KEYWORDS.items():
        for keyword in keywords:
            if keyword.lower() in text:
                return phase
    
    return prev_phase or "unknown"


# ========== 图构建 ==========

def build_event_graph(
    interactions: List[Dict],
    session_name: str = "session",
    add_phase: bool = True,
    add_query_params: bool = True
) -> nx.MultiDiGraph:
    """
    构建事件-资源异构图
    """
    G = nx.MultiDiGraph()
    
    # 记录节点和边
    url_nodes: Set[str] = set()
    domain_nodes: Set[str] = set()
    tool_nodes: Set[str] = set()
    phase_nodes: Set[str] = set()
    
    # 添加session节点
    session_id = f"session:{session_name}"
    G.add_node(session_id, type="session", label=session_name)
    
    # 记录最近的LLM事件(用于invokes边)
    last_llm_event = None
    current_phase = "unknown"
    
    # 遍历交互事件
    for i, interaction in enumerate(interactions):
        event_id = f"ev:{interaction['step']}"
        timestamp = interaction['timestamp']
        event_type = interaction['type']
        
        # 创建事件节点
        if event_type == "llm_call":
            thoughts = interaction.get('thoughts', [])
            thoughts_text = " ".join(thoughts)[:50]
            
            G.add_node(
                event_id,
                type="event",
                subtype="llm",
                step=interaction['step'],
                timestamp=timestamp,
                label=f"LLM-{interaction['step']} {thoughts_text}",
                has_tool_calls=interaction.get('has_tool_calls', False),
                category="llm"
            )
            
            last_llm_event = event_id
            
            # 识别阶段
            if add_phase:
                current_phase = identify_phase(thoughts, current_phase)
                phase_id = f"phase:{current_phase}"
                
                if phase_id not in phase_nodes:
                    G.add_node(phase_id, type="phase", label=current_phase)
                    phase_nodes.add(phase_id)
                
                G.add_edge(event_id, phase_id, type="in_phase")
        
        elif event_type == "tool_call":
            tool_name = interaction['tool_name']
            args = interaction.get('args', {})
            
            G.add_node(
                event_id,
                type="event",
                subtype="tool",
                step=interaction['step'],
                timestamp=timestamp,
                label=f"{tool_name}-{interaction['step']}",
                tool_name=tool_name,
                category=get_tool_category(tool_name),
                args=args
            )
            
            # 添加invokes边
            if last_llm_event:
                G.add_edge(last_llm_event, event_id, type="invokes")
            
            # 添加工具类型节点
            tool_id = f"tool:{tool_name}"
            if tool_id not in tool_nodes:
                G.add_node(
                    tool_id,
                    type="tool_type",
                    label=tool_name,
                    category=get_tool_category(tool_name)
                )
                tool_nodes.add(tool_id)
            
            G.add_edge(event_id, tool_id, type="uses_tool")
            
            # 处理URL参数
            url_arg = args.get('url') or args.get('URL')
            if url_arg:
                normalized_url, metadata = normalize_url(url_arg)
                url_id = f"url:{hashlib.md5(normalized_url.encode()).hexdigest()[:16]}"
                
                if url_id not in url_nodes:
                    G.add_node(
                        url_id,
                        type="url",
                        label=normalized_url[:60] + "..." if len(normalized_url) > 60 else normalized_url,
                        full_url=normalized_url,
                        scheme=metadata['scheme'],
                        path=metadata['path']
                    )
                    url_nodes.add(url_id)
                
                G.add_edge(event_id, url_id, type="accesses_url")
                
                # 添加域名节点
                host = metadata['host']
                domain_id = f"domain:{host}"
                
                if domain_id not in domain_nodes:
                    G.add_node(
                        domain_id,
                        type="domain",
                        label=host,
                        domain_category=get_domain_category(host)
                    )
                    domain_nodes.add(domain_id)
                
                G.add_edge(url_id, domain_id, type="targets_domain")
                
                # 添加查询参数节点
                if add_query_params and metadata['query_dict']:
                    for key, values in metadata['query_dict'].items():
                        for value in values:
                            value_hash = hashlib.md5(value.encode()).hexdigest()[:8]
                            qparam_id = f"qparam:{host}:{key}={value_hash}"
                            
                            short_val = value[:20] + "..." if len(value) > 20 else value
                            G.add_node(
                                qparam_id,
                                type="query_param",
                                label=f"{key}={short_val}",
                                key=key,
                                value=value
                            )
                            
                            G.add_edge(url_id, qparam_id, type="has_param")
        
        # 添加sequence边
        if i > 0:
            prev_event_id = f"ev:{interactions[i-1]['step']}"
            G.add_edge(prev_event_id, event_id, type="sequence")
        
        # 连接到session
        G.add_edge(event_id, session_id, type="in_session")
    
    return G


# ========== 样式和导出 ==========

def style_and_export(G: nx.MultiDiGraph, dot_path: str, png_path: Optional[str] = None):
    """
    为图添加样式并导出
    """
    # 设置节点样式
    for node, data in G.nodes(data=True):
        node_type = data.get("type", "unknown")
        
        if node_type == "event":
            subtype = data.get("subtype", "unknown")
            if subtype == "llm":
                data["shape"] = "box"
                data["fillcolor"] = "lightblue"
                data["style"] = "filled"
            else:
                data["shape"] = "hexagon"
                data["fillcolor"] = "orange"
                data["style"] = "filled"
        
        elif node_type == "tool_type":
            data["shape"] = "box"
            data["fillcolor"] = "lightgreen"
            data["style"] = "rounded,filled"
        
        elif node_type == "url":
            data["shape"] = "note"
            data["fillcolor"] = "lightgray"
            data["style"] = "filled"
        
        elif node_type == "domain":
            data["shape"] = "ellipse"
            category = data.get("domain_category", "other")
            colors = {
                "search": "plum",
                "news": "lightyellow",
                "data_source": "lightcyan",
                "finance_portal": "lightpink",
                "api": "lavender",
                "other": "white"
            }
            data["fillcolor"] = colors.get(category, "white")
            data["style"] = "filled"
        
        elif node_type == "query_param":
            data["shape"] = "diamond"
            data["fillcolor"] = "whitesmoke"
            data["style"] = "filled"
        
        elif node_type == "phase":
            data["shape"] = "folder"
            data["fillcolor"] = "lightgoldenrodyellow"
            data["style"] = "filled"
        
        elif node_type == "session":
            data["shape"] = "doubleoctagon"
            data["fillcolor"] = "gold"
            data["style"] = "filled"
    
    # 设置边样式
    for u, v, key, data in G.edges(data=True, keys=True):
        edge_type = data.get("type", "unknown")
        
        if edge_type == "sequence":
            data["color"] = "gray"
            data["style"] = "solid"
            data["penwidth"] = "1"
        
        elif edge_type in ["invokes", "returns_to"]:
            data["color"] = "black"
            data["style"] = "solid"
            data["penwidth"] = "2"
        
        elif edge_type in ["uses_tool", "accesses_url", "targets_domain", "has_param"]:
            data["color"] = "blue"
            data["style"] = "dashed"
        
        elif edge_type in ["in_session", "in_phase"]:
            data["color"] = "gray"
            data["style"] = "dotted"
    
    # 导出DOT
    write_dot(G, dot_path)
    print(f"✓ DOT文件已保存: {dot_path}")
    
    # 导出PNG (使用dot命令行工具更可靠)
    if png_path:
        try:
            import subprocess
            result = subprocess.run(
                ['dot', '-Tpng', dot_path, '-o', png_path],
                capture_output=True,
                text=True,
                timeout=30
            )
            if result.returncode == 0:
                print(f"✓ PNG图像已保存: {png_path}")
            else:
                # 如果dot命令失败,尝试使用pydot
                if HAS_PYDOT:
                    import pydot
                    graphs = pydot.graph_from_dot_file(dot_path)
                    if graphs:
                        graphs[0].write_png(png_path)
                        print(f"✓ PNG图像已保存: {png_path}")
                else:
                    print(f"✗ PNG导出失败: {result.stderr}")
        except FileNotFoundError:
            print(f"⚠ 未找到dot命令,跳过PNG生成")
            print(f"  提示: 安装Graphviz后可生成PNG")
            print(f"  macOS: brew install graphviz")
            print(f"  Ubuntu: sudo apt-get install graphviz")
        except subprocess.TimeoutExpired:
            print(f"✗ PNG生成超时(图可能太大)")
        except Exception as e:
            print(f"✗ PNG导出失败: {e}")


def write_dot(G: nx.MultiDiGraph, output_path: str):
    """手动写入DOT格式"""
    def escape_node_id(node_id: str) -> str:
        """转义节点ID,确保pydot兼容"""
        # 包含特殊字符的节点ID需要加引号
        if ':' in node_id or ' ' in node_id or '-' in node_id:
            return f'"{node_id}"'
        return f'"{node_id}"'  # 统一加引号最安全
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("digraph G {\n")
        f.write("  rankdir=LR;\n")
        f.write("  node [fontname=\"Arial\"];\n")
        f.write("  edge [fontname=\"Arial\"];\n\n")
        
        # 写入节点
        for node, data in G.nodes(data=True):
            attrs = []
            label = data.get('label', node).replace('"', '\\"').replace('\n', '\\n')
            attrs.append(f'label="{label}"')
            
            for key in ['shape', 'fillcolor', 'style']:
                if key in data:
                    attrs.append(f'{key}="{data[key]}"')
            
            node_id = escape_node_id(node)
            f.write(f'  {node_id} [{", ".join(attrs)}];\n')
        
        f.write("\n")
        
        # 写入边
        for u, v, key, data in G.edges(data=True, keys=True):
            attrs = []
            for attr_key in ['color', 'style', 'penwidth', 'label']:
                if attr_key in data:
                    attrs.append(f'{attr_key}="{data[attr_key]}"')
            
            attr_str = f' [{", ".join(attrs)}]' if attrs else ''
            u_id = escape_node_id(u)
            v_id = escape_node_id(v)
            f.write(f'  {u_id} -> {v_id}{attr_str};\n')
        
        f.write("}\n")


# ========== 主函数 ==========

def analyze_log(
    log_path: str,
    output_dir: str = "output",
    add_phase: bool = True,
    add_query_params: bool = True,
    generate_png: bool = True
):
    """
    分析单个日志文件并生成图
    """
    log_file = Path(log_path)
    if not log_file.exists():
        print(f"✗ 日志文件不存在: {log_path}")
        return
    
    # 创建输出目录
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    # 解析日志
    print(f"\n{'='*60}")
    print(f"分析日志: {log_file.name}")
    print(f"{'='*60}")
    
    interactions = parse_log_file(str(log_file))
    print(f"✓ 提取了 {len(interactions)} 个交互事件")
    
    # 构建图
    session_name = log_file.stem
    G = build_event_graph(
        interactions,
        session_name=session_name,
        add_phase=add_phase,
        add_query_params=add_query_params
    )
    
    print(f"✓ 构建了图: {G.number_of_nodes()} 个节点, {G.number_of_edges()} 条边")
    
    # 统计节点类型
    node_types = defaultdict(int)
    for node, data in G.nodes(data=True):
        node_types[data.get('type', 'unknown')] += 1
    
    print("\n节点类型分布:")
    for ntype, count in sorted(node_types.items()):
        print(f"  - {ntype}: {count}")
    
    # 导出
    dot_file = output_path / f"{session_name}.dot"
    png_file = output_path / f"{session_name}.png" if generate_png else None
    
    style_and_export(G, str(dot_file), str(png_file) if png_file else None)
    
    return G


def analyze_all_logs(
    logs_dir: str = "logs",
    output_dir: str = "output",
    add_phase: bool = True,
    add_query_params: bool = True,
    generate_png: bool = True
):
    """
    批量分析logs目录下的所有日志文件
    """
    logs_path = Path(logs_dir)
    if not logs_path.exists():
        print(f"✗ 日志目录不存在: {logs_dir}")
        return
    
    log_files = sorted(logs_path.glob("*.log"))
    
    if not log_files:
        print(f"✗ 在 {logs_dir} 中没有找到日志文件")
        return
    
    print(f"\n{'#'*60}")
    print(f"发现 {len(log_files)} 个日志文件")
    print(f"{'#'*60}")
    
    graphs = {}
    
    for log_file in log_files:
        try:
            G = analyze_log(
                str(log_file),
                output_dir=output_dir,
                add_phase=add_phase,
                add_query_params=add_query_params,
                generate_png=generate_png
            )
            graphs[log_file.stem] = G
        except Exception as e:
            print(f"\n✗ 处理 {log_file.name} 时出错: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'#'*60}")
    print(f"✓ 完成! 共处理 {len(graphs)} 个日志文件")
    print(f"输出目录: {output_dir}")
    print(f"{'#'*60}\n")
    
    return graphs


# ========== 命令行接口 ==========

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="将Gemini Agent日志转换为事件-资源异构图"
    )
    parser.add_argument(
        "input",
        nargs="?",
        default="logs",
        help="输入日志文件或目录 (默认: logs)"
    )
    parser.add_argument(
        "-o", "--output",
        default="output",
        help="输出目录 (默认: output)"
    )
    parser.add_argument(
        "--no-phase",
        action="store_true",
        help="不添加阶段节点"
    )
    parser.add_argument(
        "--no-query-params",
        action="store_true",
        help="不添加查询参数节点"
    )
    parser.add_argument(
        "--no-png",
        action="store_true",
        help="不生成PNG图像"
    )
    
    args = parser.parse_args()
    
    input_path = Path(args.input)
    
    if input_path.is_file():
        # 分析单个文件
        analyze_log(
            str(input_path),
            output_dir=args.output,
            add_phase=not args.no_phase,
            add_query_params=not args.no_query_params,
            generate_png=not args.no_png
        )
    elif input_path.is_dir():
        # 批量分析目录
        analyze_all_logs(
            logs_dir=str(input_path),
            output_dir=args.output,
            add_phase=not args.no_phase,
            add_query_params=not args.no_query_params,
            generate_png=not args.no_png
        )
    else:
        print(f"✗ 路径不存在: {input_path}")
        parser.print_help()
