#!/usr/bin/env python3
"""
意图-行为-目标图分析器 V2

该脚本从Gemini CLI日志文件中提取LLM决策、工具调用和目标资源，
并构建一个有向图来可视化它们之间的关系。

V2 新增功能:
1. 从LLM思考过程中提取候选资源（被考虑但未被选择）
2. 显示候选资源与最终选择资源的对比
3. 分析同一主域名下的不同页面关系
4. 可视化LLM的决策演化过程

图的节点类型:
- LLM_Decision: LLM决策节点（蓝色方块）
- Tool_Call: 工具调用节点（绿色椭圆）
- Target_Resource: 最终选择的目标资源节点（深灰色圆形，加粗边框）
- Candidate_Resource: 候选资源节点（浅灰色圆形，虚线边框）

图的边类型:
- Calls: 从LLM_Decision到Tool_Call的调用关系（实线，蓝色）
- Accesses: 从Tool_Call到Target_Resource的访问关系（实线，绿色）
- Considers: 从LLM_Decision到Candidate_Resource的考虑关系（虚线，橙色）
- Groups_With: 同一主域名下资源的分组关系（点线，紫色）
"""

import json
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple
from urllib.parse import urlparse

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.colors as mcolors
import networkx as nx

# 配置matplotlib支持中文显示
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题

# 定义颜色调色板（用于区分不同域名）
# 选择色环上均匀分布、对比度高的颜色
DOMAIN_COLOR_PALETTE = [
    '#E74C3C',  # 鲜红色 (0°)
    '#3498DB',  # 明亮蓝 (210°)
    '#2ECC71',  # 翠绿色 (120°)
    '#F39C12',  # 金橙色 (40°)
    '#9B59B6',  # 紫罗兰 (280°)
    '#1ABC9C',  # 青绿色 (170°)
    '#E91E63',  # 玫瑰红 (340°)
    '#34495E',  # 深灰蓝 (210°暗)
    '#16A085',  # 深青色 (170°暗)
    '#D35400',  # 深橙色 (30°)
]


class IntentBehaviorTargetAnalyzerV2:
    """分析日志并构建意图-行为-目标图（增强版）"""

    def __init__(self, log_file_path: str):
        self.log_file_path = log_file_path
        self.log_name = Path(log_file_path).stem
        
        # 图相关
        self.graph = nx.DiGraph()
        
        # 存储节点信息
        self.llm_decisions: List[Dict] = []
        self.tool_calls: List[Dict] = []
        self.target_resources: Set[str] = set()  # 最终选择的资源
        self.candidate_resources: Dict[str, Set[str]] = {}  # LLM_ID -> 候选资源集合
        
        # 域名分组
        self.domain_groups: Dict[str, Set[str]] = defaultdict(set)  # 主域名 -> 完整URL集合
        
        # 域名到颜色的映射
        self.domain_colors: Dict[str, str] = {}
        
        # 用于生成唯一ID
        self.llm_counter = 0
        self.tool_counter = 0
        
    def extract_domain(self, url: str) -> str:
        """从URL中提取域名作为目标资源"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            # 移除www前缀
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain if domain else url
        except Exception:
            return url
    
    def extract_main_domain(self, url: str) -> str:
        """提取主域名（用于分组）"""
        domain = self.extract_domain(url)
        # 对于多级域名，只保留最后两级
        parts = domain.split('.')
        if len(parts) >= 2:
            return '.'.join(parts[-2:])
        return domain
    
    def extract_urls_from_text(self, text: str) -> Set[str]:
        """从文本中提取所有URL"""
        if not text:
            return set()
        
        candidates = set()
        
        # 提取URL
        url_pattern = r'https?://[^\s\)\]\'"<>\,]+'
        urls = re.findall(url_pattern, text)
        for url in urls:
            # 清理末尾可能的标点符号
            url = url.rstrip('.,;:!?')
            # 只保留有效的URL
            if len(url) > 10:  # 基本验证
                candidates.add(url)
        
        return candidates
    
    def parse_log_file(self):
        """解析日志文件，提取所有REQUEST和RESPONSE块"""
        with open(self.log_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 分割日志为各个请求-响应块
        blocks = re.split(r'-{80,}', content)
        
        current_request = None
        previous_tool_responses = []  # 存储上一轮的工具返回结果
        
        for block in blocks:
            block = block.strip()
            if not block:
                continue
            
            # 检测REQUEST
            if '[REQUEST]' in block:
                try:
                    # 提取JSON部分
                    json_match = re.search(r'Request Data:\n(\[[\s\S]+)', block)
                    if json_match:
                        current_request = json.loads(json_match.group(1))
                        
                        # 从请求中提取上一轮的工具响应
                        previous_tool_responses = self.extract_tool_responses_from_request(current_request)
                except json.JSONDecodeError:
                    pass
            
            # 检测RESPONSE
            elif '[RESPONSE]' in block and current_request:
                try:
                    # 提取JSON部分
                    json_match = re.search(r'Response Data:\n(\[[\s\S]+)', block)
                    if json_match:
                        response_data = json.loads(json_match.group(1))
                        self.process_interaction(current_request, response_data, previous_tool_responses)
                except json.JSONDecodeError:
                    pass
                finally:
                    current_request = None
    
    
    def extract_tool_responses_from_request(self, request_data: List) -> List[str]:
        """从请求数据中提取上一轮工具调用的响应内容（用于提取候选URL）"""
        tool_response_contents = []
        
        for item in request_data:
            if item.get('role') == 'user':
                parts = item.get('parts', [])
                for part in parts:
                    # 检查是否是工具响应
                    if 'functionResponse' in part:
                        function_response = part['functionResponse']
                        response = function_response.get('response', {})
                        output = response.get('output', '')
                        
                        if output:
                            tool_response_contents.append(output)
        
        return tool_response_contents
    
    def process_interaction(self, request_data: List, response_data: List, previous_tool_responses: List[str]):
        """处理一次完整的请求-响应交互"""
        # 从上一轮工具响应中提取所有候选URL
        candidates_from_previous = set()
        for response_content in previous_tool_responses:
            candidates_from_previous.update(self.extract_urls_from_text(response_content))
        
        # 遍历response中的所有候选响应
        for response_item in response_data:
            candidates_list = response_item.get('candidates', [])
            
            for candidate in candidates_list:
                content = candidate.get('content', {})
                parts = content.get('parts', [])
                
                # 检查是否有工具调用
                has_tool_calls = False
                tool_calls_in_response = []
                
                for part in parts:
                    if 'functionCall' in part:
                        has_tool_calls = True
                        function_call = part['functionCall']
                        tool_name = function_call.get('name', '')
                        args = function_call.get('args', {})
                        
                        # 提取目标URL或其他标识
                        target = self.extract_target_from_args(tool_name, args)
                        
                        tool_calls_in_response.append({
                            'tool_name': tool_name,
                            'args': args,
                            'target': target
                        })
                
                # 如果这个响应包含工具调用，创建LLM_Decision节点
                if has_tool_calls:
                    self.llm_counter += 1
                    llm_node_id = f"llm_step_{self.llm_counter}"
                    
                    # 使用从上一轮工具响应中提取的候选URL
                    self.candidate_resources[llm_node_id] = candidates_from_previous
                    
                    llm_decision = {
                        'id': llm_node_id,
                        'type': 'LLM_Decision',
                        'step': self.llm_counter,
                        'tool_count': len(tool_calls_in_response),
                        'thoughts': [],
                        'full_thoughts': [],
                        'tools': [],
                        'candidates': candidates_from_previous
                    }
                    
                    # 为每个工具调用创建Tool_Call节点
                    for tool_info in tool_calls_in_response:
                        self.tool_counter += 1
                        tool_node_id = f"tool_step_{self.tool_counter}"
                        
                        tool_call = {
                            'id': tool_node_id,
                            'type': 'Tool_Call',
                            'step': self.tool_counter,
                            'tool_name': tool_info['tool_name'],
                            'target': tool_info['target'],
                            'llm_id': llm_node_id
                        }
                        
                        self.tool_calls.append(tool_call)
                        llm_decision['tools'].append(tool_node_id)
                        
                        # 记录目标资源
                        if tool_info['target']:
                            self.target_resources.add(tool_info['target'])
                            # 记录域名分组
                            main_domain = self.extract_main_domain(tool_info['target'])
                            self.domain_groups[main_domain].add(tool_info['target'])
                    
                    self.llm_decisions.append(llm_decision)
    
    def extract_target_from_args(self, tool_name: str, args: Dict) -> str | None:
        """从工具参数中提取目标资源"""
        # 对于不同的工具，提取不同的目标标识
        if tool_name in ['fetch_url', 'browser_navigate']:
            url = args.get('url', '')
            return url  # 保留完整URL而不只是域名
        elif tool_name in ['github_search', 'github_get']:
            repo = args.get('repo', args.get('repository', ''))
            return f"github:{repo}" if repo else None
        else:
            # 对于其他工具，尝试找到任何URL或标识符
            for value in args.values():
                if isinstance(value, str) and ('http://' in value or 'https://' in value):
                    return value
        
        return None
    
    def build_graph(self):
        """构建NetworkX图"""
        # 首先分配颜色给所有域名
        self._assign_domain_colors()
        
        # 添加LLM_Decision节点
        for llm_decision in self.llm_decisions:
            label = f"LLM-{llm_decision['step']}\n"
            label += f"决策: {llm_decision['tool_count']}个工具\n"
            label += f"候选: {len(llm_decision['candidates'])}个资源"
            
            self.graph.add_node(
                llm_decision['id'],
                type='LLM_Decision',
                label=label,
                step=llm_decision['step']
            )
        
        # 添加Tool_Call节点和Calls边
        for tool_call in self.tool_calls:
            # 构建工具调用标签
            label = f"Tool-{tool_call['step']}\n"
            label += f"{tool_call['tool_name']}"
            
            self.graph.add_node(
                tool_call['id'],
                type='Tool_Call',
                label=label,
                tool_name=tool_call['tool_name'],
                target=tool_call['target']
            )
            
            # 添加LLM到Tool的调用边
            self.graph.add_edge(
                tool_call['llm_id'],
                tool_call['id'],
                type='Calls'
            )
        
        # 添加Target_Resource节点（最终选择的资源）
        for target in self.target_resources:
            if target:
                # 缩短显示标签
                display_label = self._shorten_url_label(target)
                self.graph.add_node(
                    target,
                    type='Target_Resource',
                    label=display_label,
                    full_url=target
                )
        
        # 添加Tool到Target的访问边
        for tool_call in self.tool_calls:
            if tool_call['target'] and tool_call['target'] in self.target_resources:
                self.graph.add_edge(
                    tool_call['id'],
                    tool_call['target'],
                    type='Accesses'
                )
        
        # 添加Candidate_Resource节点（候选但未选择的资源）
        for llm_id, candidates in self.candidate_resources.items():
            for candidate in candidates:
                # 只添加那些不是最终选择的候选
                if candidate not in self.target_resources:
                    candidate_id = f"candidate_{candidate}"
                    display_label = self._shorten_url_label(candidate)
                    
                    self.graph.add_node(
                        candidate_id,
                        type='Candidate_Resource',
                        label=display_label,
                        full_url=candidate
                    )
                    
                    # 添加Considers边
                    self.graph.add_edge(
                        llm_id,
                        candidate_id,
                        type='Considers'
                    )
                    
                    # 记录域名分组
                    main_domain = self.extract_main_domain(candidate)
                    self.domain_groups[main_domain].add(candidate)
        
        # 添加域名分组边（Groups_With）
        for main_domain, urls in self.domain_groups.items():
            if len(urls) > 1:
                # 为同一主域名下的资源添加分组边
                url_list = list(urls)
                for i in range(len(url_list)):
                    for j in range(i + 1, len(url_list)):
                        url1, url2 = url_list[i], url_list[j]
                        
                        # 查找对应的节点ID
                        node1 = url1 if url1 in self.target_resources else f"candidate_{url1}"
                        node2 = url2 if url2 in self.target_resources else f"candidate_{url2}"
                        
                        if self.graph.has_node(node1) and self.graph.has_node(node2):
                            self.graph.add_edge(
                                node1,
                                node2,
                                type='Groups_With',
                                domain=main_domain
                            )
    
    def _shorten_url_label(self, url: str, max_len: int = 40) -> str:
        """缩短URL用于显示"""
        if len(url) <= max_len:
            return url
        
        # 尝试只显示域名+路径的一部分
        try:
            parsed = urlparse(url)
            domain = parsed.netloc
            path = parsed.path
            
            if len(domain) + len(path) <= max_len:
                return f"{domain}{path}"
            else:
                # 截断路径
                available = max_len - len(domain) - 3
                if available > 0:
                    return f"{domain}{path[:available]}..."
                else:
                    return domain[:max_len-3] + "..."
        except:
            return url[:max_len-3] + "..."
    
    def _assign_domain_colors(self):
        """为每个主域名分配颜色"""
        # 收集所有主域名
        all_domains = set()
        
        # 从目标资源中提取域名
        for url in self.target_resources:
            domain = self.extract_main_domain(url)
            all_domains.add(domain)
        
        # 从候选资源中提取域名
        for candidates in self.candidate_resources.values():
            for url in candidates:
                domain = self.extract_main_domain(url)
                all_domains.add(domain)
        
        # 为每个域名分配颜色
        sorted_domains = sorted(all_domains)
        for i, domain in enumerate(sorted_domains):
            color_idx = i % len(DOMAIN_COLOR_PALETTE)
            self.domain_colors[domain] = DOMAIN_COLOR_PALETTE[color_idx]
    
    def _get_node_color(self, url: str, is_selected: bool) -> str:
        """获取节点颜色（根据域名和是否被选中）"""
        domain = self.extract_main_domain(url)
        base_color = self.domain_colors.get(domain, '#999999')
        
        if is_selected:
            # 被选中：使用原色（深色）
            return base_color
        else:
            # 未被选中：使用淡化版本（浅色）
            # 将颜色转换为RGB并淡化
            rgb = mcolors.hex2color(base_color)
            # 与白色混合，淡化70%
            lightened = tuple(c * 0.3 + 0.7 for c in rgb)
            return mcolors.to_hex(lightened)
    
    def _export_graph_topology(self, output_path: Path):
        """导出图的拓扑结构（数学图论表示）
        
        导出格式为JSON，包含：
        1. 节点列表：每个节点的ID、类型和属性
        2. 边列表：区分真实边和虚拟边
           - 真实边: LLM→Tool (Calls), Tool→LLM (Returns), Tool→Resource (Accesses)
           - 虚拟边: LLM→Candidate (Considers)
        3. LLM决策链：表示完整的 LLM1→Tool→LLM2 连接关系
        
        这是标准的图论表示，可用于：
        - 图算法分析（最短路径、连通性等）
        - 导入到其他图分析工具
        - 程序化处理和查询
        """
        import json
        
        # 构建节点列表
        nodes = []
        for node_id, data in self.graph.nodes(data=True):
            node_info = {
                'id': node_id,
                'type': data['type'],
                'label': data.get('label', ''),
            }
            
            # 添加特定类型的额外信息
            if data['type'] in ['Target_Resource', 'Candidate_Resource']:
                node_info['full_url'] = data.get('full_url', '')
                node_info['domain'] = self.extract_main_domain(data.get('full_url', ''))
                node_info['is_selected'] = (data['type'] == 'Target_Resource')
            elif data['type'] == 'Tool_Call':
                node_info['tool_name'] = data.get('tool_name', '')
            
            nodes.append(node_info)
        
        # 构建边列表 - 分为真实边和虚拟边
        real_edges = []  # 真实的数据流和控制流
        virtual_edges = []  # 虚拟的"考虑"关系
        
        # 从图中提取现有的边
        for u, v, data in self.graph.edges(data=True):
            edge_info = {
                'source': u,
                'target': v,
                'type': data['type']
            }
            
            if data['type'] == 'Considers':
                # 虚拟边：LLM考虑某个候选资源
                virtual_edges.append(edge_info)
            else:
                # 真实边：Calls (LLM→Tool) 或 Accesses (Tool→Resource)
                real_edges.append(edge_info)
        
        # 构建LLM决策链：添加 Tool→NextLLM 的返回边
        # 逻辑：每个Tool节点后面如果有LLM节点，说明工具返回触发了下一个LLM决策
        llm_nodes = sorted([n for n, d in self.graph.nodes(data=True) if d['type'] == 'LLM_Decision'])
        tool_nodes = [n for n, d in self.graph.nodes(data=True) if d['type'] == 'Tool_Call']
        
        # 为每个工具找到它返回给哪个LLM
        for i, llm_node in enumerate(llm_nodes):
            # 找到这个LLM调用的工具
            tool_called = None
            for edge_u, edge_v, edge_data in self.graph.edges(data=True):
                if edge_u == llm_node and edge_data['type'] == 'Calls':
                    tool_called = edge_v
                    break
            
            # 如果找到了工具，且后面还有LLM，添加 Tool→NextLLM 边
            if tool_called and i + 1 < len(llm_nodes):
                next_llm = llm_nodes[i + 1]
                real_edges.append({
                    'source': tool_called,
                    'target': next_llm,
                    'type': 'Returns'  # 工具返回给下一个LLM
                })
        
        # 构建邻接表表示（便于图算法）
        adjacency_list = {}
        for node in nodes:
            adjacency_list[node['id']] = {
                'real_neighbors': [],
                'virtual_neighbors': []
            }
        
        for edge in real_edges:
            if edge['source'] in adjacency_list:
                adjacency_list[edge['source']]['real_neighbors'].append({
                    'target': edge['target'],
                    'edge_type': edge['type']
                })
        
        for edge in virtual_edges:
            if edge['source'] in adjacency_list:
                adjacency_list[edge['source']]['virtual_neighbors'].append({
                    'target': edge['target'],
                    'edge_type': edge['type']
                })
        
        # 构建完整的拓扑结构
        topology = {
            'metadata': {
                'log_name': self.log_name,
                'node_count': len(nodes),
                'real_edge_count': len(real_edges),
                'virtual_edge_count': len(virtual_edges),
                'description': '意图-行为-目标图的数学图论表示'
            },
            'nodes': nodes,
            'edges': {
                'real': real_edges,  # 真实连接：Calls, Accesses, Returns
                'virtual': virtual_edges  # 虚拟连接：Considers
            },
            'adjacency_list': adjacency_list,
            'statistics': {
                'llm_decisions': len([n for n in nodes if n['type'] == 'LLM_Decision']),
                'tool_calls': len([n for n in nodes if n['type'] == 'Tool_Call']),
                'selected_resources': len([n for n in nodes if n['type'] == 'Target_Resource']),
                'candidate_resources': len([n for n in nodes if n['type'] == 'Candidate_Resource']),
            }
        }
        
        # 写入JSON文件
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(topology, f, ensure_ascii=False, indent=2)
    
    def _export_dot(self, output_path: Path):
        """导出DOT格式供Graphviz使用
        
        DOT格式的优势:
        - 可以使用不同的布局算法 (dot, neato, fdp, sfdp, circo)
        - 可以导出为SVG/PDF等矢量格式
        - 可以在其他图形工具中进一步编辑
        
        使用方法:
        dot -Tpng -o output.png input.dot
        dot -Tsvg -o output.svg input.dot
        dot -Tpdf -o output.pdf input.dot
        neato -Tpng -o output.png input.dot  # 不同的布局算法
        """
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("digraph IntentBehaviorTargetGraph {\n")
            f.write("  // 图的基本设置\n")
            f.write("  rankdir=TB;  // 从上到下布局\n")
            f.write("  node [fontname=\"Arial\", fontsize=10];\n")
            f.write("  edge [fontname=\"Arial\", fontsize=8];\n")
            f.write("  bgcolor=\"white\";\n")
            f.write("  dpi=200;\n\n")
            
            # 写入LLM Decision节点
            f.write("  // LLM Decision 节点\n")
            llm_nodes = [n for n, d in self.graph.nodes(data=True) if d['type'] == 'LLM_Decision']
            for node in llm_nodes:
                data = self.graph.nodes[node]
                label = data['label'].replace('\n', '\\n').replace('"', '\\"')
                f.write(f'  "{node}" [shape=box, style=filled, fillcolor="#4A90E2", '
                       f'fontcolor=white, label="{label}", penwidth=2.5];\n')
            
            f.write("\n  // Tool Call 节点\n")
            tool_nodes = [n for n, d in self.graph.nodes(data=True) if d['type'] == 'Tool_Call']
            for node in tool_nodes:
                data = self.graph.nodes[node]
                label = data['label'].replace('\n', '\\n').replace('"', '\\"')
                f.write(f'  "{node}" [shape=ellipse, style=filled, fillcolor="#50E3C2", '
                       f'label="{label}", penwidth=2.5];\n')
            
            f.write("\n  // Target Resource 节点 (被选中的资源)\n")
            target_nodes = [n for n, d in self.graph.nodes(data=True) if d['type'] == 'Target_Resource']
            for node in target_nodes:
                data = self.graph.nodes[node]
                url = data.get('full_url', node)
                label = data['label'].replace('\n', '\\n').replace('"', '\\"')
                color = self._get_node_color(url, is_selected=True)
                f.write(f'  "{node}" [shape=note, style=filled, fillcolor="{color}", '
                       f'label="{label}", penwidth=3, color=black];\n')
            
            f.write("\n  // Candidate Resource 节点 (候选但未选中的资源)\n")
            candidate_nodes = [n for n, d in self.graph.nodes(data=True) if d['type'] == 'Candidate_Resource']
            for node in candidate_nodes:
                data = self.graph.nodes[node]
                url = data.get('full_url', node).replace('candidate_', '')
                color = self._get_node_color(url, is_selected=False)
                domain = self.extract_main_domain(url)
                # 候选节点不显示完整URL，只显示域名
                f.write(f'  "{node}" [shape=ellipse, style=filled, fillcolor="{color}", '
                       f'label="{domain}", penwidth=2, color=gray];\n')
            
            # 写入边
            f.write("\n  // 边: Calls (LLM → Tool)\n")
            for u, v, data in self.graph.edges(data=True):
                if data['type'] == 'Calls':
                    f.write(f'  "{u}" -> "{v}" [color="#4A90E2", penwidth=3.5, '
                           f'style=solid, arrowsize=1.2];\n')
            
            f.write("\n  // 边: Accesses (Tool → Target)\n")
            for u, v, data in self.graph.edges(data=True):
                if data['type'] == 'Accesses':
                    f.write(f'  "{u}" -> "{v}" [color="#50E3C2", penwidth=2.5, '
                           f'style=solid, arrowsize=1.0];\n')
            
            f.write("\n  // 边: Considers (LLM → Candidate) - 虚线\n")
            for u, v, data in self.graph.edges(data=True):
                if data['type'] == 'Considers':
                    f.write(f'  "{u}" -> "{v}" [color="#FF9500", penwidth=1.0, '
                           f'style=dashed, arrowsize=0.8];\n')
            
            f.write("\n  // 图例和标题\n")
            f.write(f'  labelloc="t";\n')
            f.write(f'  label="意图-行为-目标图 V2: {self.log_name}\\n'
                   f'颜色编码: 同域名同色系 | 深色=选中 | 浅色=候选未选";\n')
            f.write(f'  fontsize=16;\n')
            
            f.write("}\n")
    
    def visualize_graph(self, output_dir: str | None = None):
        """可视化图并保存"""
        if not output_dir:
            output_dir_path = Path(self.log_file_path).parent.parent / "intent_behavior_target_graphs_v2"
        else:
            output_dir_path = Path(output_dir)
        
        output_dir_path.mkdir(exist_ok=True)
        
        # 导出图论拓扑表示（JSON格式）
        topology_file = output_dir_path / f"{self.log_name}_graph_topology.json"
        self._export_graph_topology(topology_file)
        print(f"✓ 图拓扑已导出: {topology_file}")
        
        # 创建图形 - 超大尺寸以容纳更多节点
        plt.figure(figsize=(32, 26), dpi=100)
        
        # 使用分层布局
        pos = self._create_hierarchical_layout()
        
        # 分别绘制不同类型的节点
        llm_nodes = [n for n, d in self.graph.nodes(data=True) if d['type'] == 'LLM_Decision']
        tool_nodes = [n for n, d in self.graph.nodes(data=True) if d['type'] == 'Tool_Call']
        target_nodes = [n for n, d in self.graph.nodes(data=True) if d['type'] == 'Target_Resource']
        candidate_nodes = [n for n, d in self.graph.nodes(data=True) if d['type'] == 'Candidate_Resource']
        
        # 绘制LLM Decision节点
        nx.draw_networkx_nodes(self.graph, pos, nodelist=llm_nodes, 
                               node_color='#4A90E2', node_shape='s', 
                               node_size=7000, alpha=0.95, linewidths=2.5, edgecolors='#2E5C8A')
        
        # 绘制Tool Call节点
        nx.draw_networkx_nodes(self.graph, pos, nodelist=tool_nodes, 
                               node_color='#50E3C2', node_shape='o', 
                               node_size=6000, alpha=0.95, linewidths=2.5, edgecolors='#2A8B74')
        
        # 绘制Target资源 - 使用域名颜色（深色）
        for node in target_nodes:
            url = self.graph.nodes[node].get('full_url', node)
            color = self._get_node_color(url, is_selected=True)
            nx.draw_networkx_nodes(self.graph, pos, nodelist=[node], 
                                   node_color=color, node_shape='o', 
                                   node_size=5500, alpha=0.95, linewidths=3, 
                                   edgecolors='#000000')
        
        # 绘制Candidate资源 - 使用域名颜色（浅色）
        for node in candidate_nodes:
            url = self.graph.nodes[node].get('full_url', node).replace('candidate_', '')
            color = self._get_node_color(url, is_selected=False)
            nx.draw_networkx_nodes(self.graph, pos, nodelist=[node], 
                                   node_color=color, node_shape='o', 
                                   node_size=4500, alpha=0.85, linewidths=2, 
                                   edgecolors='#AAAAAA')
        
        # 分别绘制不同类型的边 - 使用线宽表示重要性
        calls_edges = [(u, v) for u, v, d in self.graph.edges(data=True) if d['type'] == 'Calls']
        accesses_edges = [(u, v) for u, v, d in self.graph.edges(data=True) if d['type'] == 'Accesses']
        considers_edges = [(u, v) for u, v, d in self.graph.edges(data=True) if d['type'] == 'Considers']
        groups_edges = [(u, v) for u, v, d in self.graph.edges(data=True) if d['type'] == 'Groups_With']
        
        # Calls边 - 蓝色实线，最粗（最重要：LLM的决策链）
        nx.draw_networkx_edges(self.graph, pos, edgelist=calls_edges,
                               edge_color='#4A90E2', style='solid', 
                               width=3.5, alpha=0.8, arrows=True, 
                               arrowsize=28, arrowstyle='->', connectionstyle='arc3,rad=0.1')
        
        # Accesses边 - 绿色实线，中等（次重要：实际访问）
        nx.draw_networkx_edges(self.graph, pos, edgelist=accesses_edges,
                               edge_color='#50E3C2', style='solid', 
                               width=2.5, alpha=0.75, arrows=True, 
                               arrowsize=25, arrowstyle='->', connectionstyle='arc3,rad=0.1')
        
        # Considers边 - 橙色虚线，最细（次要：仅考虑未执行）
        nx.draw_networkx_edges(self.graph, pos, edgelist=considers_edges,
                               edge_color='#FF9500', style='dashed', 
                               width=1.0, alpha=0.2, arrows=True, 
                               arrowsize=15, arrowstyle='->', connectionstyle='arc3,rad=0.1')
        
        # Groups_With边 - 不绘制，太多了会很乱
        # nx.draw_networkx_edges(self.graph, pos, edgelist=groups_edges,
        #                        edge_color='#9B59B6', style='dotted', 
        #                        width=1, alpha=0.2, arrows=False)
        
        # 只为选中的节点和关键节点绘制标签
        labels_to_draw = {}
        
        # LLM和Tool节点的标签
        for node in llm_nodes + tool_nodes:
            labels_to_draw[node] = self.graph.nodes[node]['label']
        
        # Target节点的标签（被选中的资源）
        for node in target_nodes:
            url = self.graph.nodes[node].get('full_url', node)
            labels_to_draw[node] = self._shorten_url_label(url, max_len=35)
        
        # Candidate节点不显示标签，只用颜色区分
        
        nx.draw_networkx_labels(self.graph, pos, labels_to_draw, font_size=9, 
                                font_family='sans-serif', font_weight='normal',
                                verticalalignment='center', horizontalalignment='center')
        
        # 创建图例 - 包含域名颜色说明
        legend_elements = [
            mpatches.Rectangle((0, 0), 1, 1, fc='#4A90E2', ec='#2E5C8A', linewidth=2, label='LLM Decision'),
            mpatches.Circle((0, 0), 1, fc='#50E3C2', ec='#2A8B74', linewidth=2, label='Tool Call'),
        ]
        
        # 添加主要域名的颜色图例
        main_domains = sorted(self.domain_colors.items(), key=lambda x: len(self.domain_groups.get(x[0], [])), reverse=True)[:6]
        for domain, color in main_domains:
            # 深色版本（被选中）
            legend_elements.append(
                mpatches.Circle((0, 0), 1, fc=color, ec='#000000', linewidth=2, 
                               label=f'{domain} (选中)')
            )
            # 浅色版本（候选）
            light_color = self._get_node_color(f"http://{domain}", is_selected=False)
            legend_elements.append(
                mpatches.Circle((0, 0), 1, fc=light_color, ec='#AAAAAA', linewidth=1.5, 
                               label=f'{domain} (候选)')
            )
        
        legend_elements.extend([
            mpatches.Patch(color='#4A90E2', label='Calls (LLM→Tool)'),
            mpatches.Patch(color='#50E3C2', label='Accesses (Tool→Target)'),
            mpatches.Patch(color='#FF9500', label='Considers (LLM→Candidate)', alpha=0.3),
        ])
        
        plt.legend(handles=legend_elements, loc='upper left', fontsize=10, 
                   framealpha=0.95, ncol=2, columnspacing=1)
        
        plt.title(f'意图-行为-目标图 V2: {self.log_name}\n颜色编码: 同域名同色系 | 深色=选中 | 浅色=候选未选', 
                  fontsize=18, fontweight='bold', pad=40)
        
        plt.axis('off')
        plt.tight_layout(pad=3.0)
        
        # 保存图形
        output_file = output_dir_path / f"{self.log_name}_intent_behavior_target_graph_v2.png"
        plt.savefig(output_file, dpi=200, bbox_inches='tight', 
                    facecolor='white', edgecolor='none', pad_inches=0.5)
        plt.close()
        
        print(f"✓ 图形已保存: {output_file}")
        
        # 导出DOT格式供Graphviz使用
        dot_file = output_dir_path / f"{self.log_name}_intent_behavior_target_graph_v2.dot"
        self._export_dot(dot_file)
        print(f"✓ DOT文件已导出: {dot_file}")
        
        # 保存图的统计信息
        self._save_graph_stats(output_dir_path)
    
    def _create_hierarchical_layout(self) -> Dict:
        """创建分层布局 - 4层结构"""
        pos = {}
        
        # 第一层: LLM Decisions
        llm_nodes = [n for n, d in self.graph.nodes(data=True) if d['type'] == 'LLM_Decision']
        for i, node in enumerate(sorted(llm_nodes, key=lambda x: self.graph.nodes[x].get('step', 0))):
            pos[node] = (i * 5.0, 3)
        
        # 第二层: Tool Calls
        tool_nodes = [n for n, d in self.graph.nodes(data=True) if d['type'] == 'Tool_Call']
        tool_x_offset = 0
        for node in sorted(tool_nodes, key=lambda x: self.graph.nodes[x].get('step', 0)):
            # 找到对应的LLM节点
            llm_predecessors = [p for p in self.graph.predecessors(node)]
            if llm_predecessors:
                llm_x = pos[llm_predecessors[0]][0]
                pos[node] = (llm_x + tool_x_offset * 1.2, 2)
                tool_x_offset += 1
            else:
                pos[node] = (tool_x_offset * 5.0, 2)
                tool_x_offset += 1
        
        # 第三层: Target Resources（被选择的）
        target_nodes = [n for n, d in self.graph.nodes(data=True) if d['type'] == 'Target_Resource']
        self._layout_resource_nodes(pos, target_nodes, y_position=1.0)
        
        # 第四层: Candidate Resources（候选但未选择的）
        candidate_nodes = [n for n, d in self.graph.nodes(data=True) if d['type'] == 'Candidate_Resource']
        self._layout_resource_nodes(pos, candidate_nodes, y_position=0.0)
        
        return pos
    
    def _layout_resource_nodes(self, pos: Dict, nodes: List, y_position: float):
        """布局资源节点（Target或Candidate）"""
        if not nodes:
            return
        
        # 收集所有节点的理想位置（基于其前驱节点）
        node_ideal_positions = {}
        for node in nodes:
            predecessors = list(self.graph.predecessors(node))
            if predecessors:
                # 计算所有前驱节点的平均x位置
                avg_x = sum(pos[p][0] for p in predecessors if p in pos) / len([p for p in predecessors if p in pos])
                node_ideal_positions[node] = avg_x
            else:
                node_ideal_positions[node] = 0
        
        # 按理想位置排序
        sorted_nodes = sorted(node_ideal_positions.items(), key=lambda x: x[1])
        
        # 使用贪心算法分配位置，避免重叠
        min_spacing = 1.5
        used_positions = []
        height_levels = [y_position - 0.2, y_position, y_position + 0.2]
        current_height_idx = 0
        
        for node, ideal_x in sorted_nodes:
            best_x = ideal_x
            conflict_count = 0
            
            # 检查是否与已有位置冲突
            while any(abs(best_x - used_x) < min_spacing for used_x in used_positions):
                best_x += 0.3
                conflict_count += 1
                if conflict_count > 3:
                    current_height_idx = (current_height_idx + 1) % len(height_levels)
                    break
            
            # 分配位置
            y = height_levels[current_height_idx]
            pos[node] = (best_x, y)
            used_positions.append(best_x)
            
            # 交替高度
            current_height_idx = (current_height_idx + 1) % len(height_levels)
    
    def _save_graph_stats(self, output_dir: Path):
        """保存图的统计信息"""
        # 统计候选资源信息
        total_candidates = sum(len(candidates) for candidates in self.candidate_resources.values())
        candidates_not_selected = total_candidates - len([c for c in self.candidate_resources.values() 
                                                           for candidate in c if candidate in self.target_resources])
        
        # 统计域名分组
        domain_group_stats = {
            domain: len(urls) for domain, urls in self.domain_groups.items() if len(urls) > 1
        }
        
        stats = {
            'log_file': self.log_name,
            'total_llm_decisions': len(self.llm_decisions),
            'total_tool_calls': len(self.tool_calls),
            'total_target_resources': len(self.target_resources),
            'total_candidate_resources': total_candidates,
            'candidates_not_selected': candidates_not_selected,
            'unique_tools': len(set(tc['tool_name'] for tc in self.tool_calls)),
            'graph_nodes': self.graph.number_of_nodes(),
            'graph_edges': self.graph.number_of_edges(),
            'target_resources': sorted(list(self.target_resources)),
            'domain_groups': domain_group_stats,
            'tool_usage': self._get_tool_usage_stats(),
            'decision_details': self._get_decision_details()
        }
        
        stats_file = output_dir / f"{self.log_name}_stats_v2.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        
        print(f"✓ 统计信息已保存: {stats_file}")
        
        # 打印摘要
        print(f"\n📊 分析摘要 - {self.log_name}:")
        print(f"  LLM决策次数: {stats['total_llm_decisions']}")
        print(f"  工具调用次数: {stats['total_tool_calls']}")
        print(f"  最终选择资源: {stats['total_target_resources']}")
        print(f"  候选资源总数: {stats['total_candidate_resources']}")
        print(f"  未被选择候选: {stats['candidates_not_selected']}")
        print(f"  域名分组数: {len(domain_group_stats)}")
        print(f"  唯一工具数: {stats['unique_tools']}")
    
    def _get_tool_usage_stats(self) -> Dict[str, int]:
        """获取工具使用统计"""
        tool_usage = defaultdict(int)
        for tc in self.tool_calls:
            tool_usage[tc['tool_name']] += 1
        return dict(tool_usage)
    
    def _get_decision_details(self) -> List[Dict]:
        """获取每个决策的详细信息"""
        details = []
        for llm_decision in self.llm_decisions:
            detail = {
                'step': llm_decision['step'],
                'tools_called': len(llm_decision['tools']),
                'candidates_considered': len(llm_decision['candidates']),
                'candidates_list': sorted(list(llm_decision['candidates'])),
                'thought_summary': llm_decision['thoughts'][0] if llm_decision['thoughts'] else ''
            }
            details.append(detail)
        return details


def analyze_all_logs(logs_dir: str, output_dir: str | None = None):
    """分析logs目录下的所有日志文件"""
    logs_path = Path(logs_dir)
    
    if not logs_path.exists():
        print(f"❌ 日志目录不存在: {logs_dir}")
        return
    
    log_files = sorted(logs_path.glob("*.log"))
    
    if not log_files:
        print(f"❌ 未找到日志文件: {logs_dir}")
        return
    
    print(f"🔍 找到 {len(log_files)} 个日志文件\n")
    
    for log_file in log_files:
        print(f"\n{'='*60}")
        print(f"📝 分析日志: {log_file.name}")
        print(f"{'='*60}")
        
        try:
            analyzer = IntentBehaviorTargetAnalyzerV2(str(log_file))
            analyzer.parse_log_file()
            analyzer.build_graph()
            analyzer.visualize_graph(output_dir)
        except Exception as e:
            print(f"❌ 分析失败: {e}")
            import traceback
            traceback.print_exc()


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='分析Gemini CLI日志并生成意图-行为-目标图 V2（增强版）'
    )
    parser.add_argument(
        '--logs-dir',
        default='logs',
        help='日志文件目录 (默认: logs)'
    )
    parser.add_argument(
        '--output-dir',
        default=None,
        help='输出目录 (默认: intent_behavior_target_graphs_v2)'
    )
    
    args = parser.parse_args()
    
    analyze_all_logs(args.logs_dir, args.output_dir)


if __name__ == '__main__':
    main()
