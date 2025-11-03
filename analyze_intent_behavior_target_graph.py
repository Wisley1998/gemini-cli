#!/usr/bin/env python3
"""
意图-行为-目标图分析器

该脚本从Gemini CLI日志文件中提取LLM决策、工具调用和目标资源，
并构建一个有向图来可视化它们之间的关系。

图的节点类型:
- LLM_Decision: LLM决策节点（蓝色方块）
- Tool_Call: 工具调用节点（绿色椭圆）
- Target_Resource: 目标资源节点（灰色圆形）

图的边类型:
- Calls: 从LLM_Decision到Tool_Call的调用关系（实线）
- Accesses: 从Tool_Call到Target_Resource的访问关系（虚线）
"""

import json
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple
from urllib.parse import urlparse

import matplotlib.pyplot as plt
import networkx as nx

# 配置matplotlib支持中文显示
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题


class IntentBehaviorTargetAnalyzer:
    """分析日志并构建意图-行为-目标图"""

    def __init__(self, log_file_path: str):
        self.log_file_path = log_file_path
        self.log_name = Path(log_file_path).stem
        
        # 图相关
        self.graph = nx.DiGraph()
        
        # 存储节点信息
        self.llm_decisions: List[Dict] = []
        self.tool_calls: List[Dict] = []
        self.target_resources: Set[str] = set()
        
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
    
    def parse_log_file(self):
        """解析日志文件，提取所有REQUEST和RESPONSE块"""
        with open(self.log_file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 分割日志为各个请求-响应块
        blocks = re.split(r'-{80,}', content)
        
        current_request = None
        
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
                except json.JSONDecodeError:
                    pass
            
            # 检测RESPONSE
            elif '[RESPONSE]' in block and current_request:
                try:
                    # 提取JSON部分
                    json_match = re.search(r'Response Data:\n(\[[\s\S]+)', block)
                    if json_match:
                        response_data = json.loads(json_match.group(1))
                        self.process_interaction(current_request, response_data)
                except json.JSONDecodeError:
                    pass
                finally:
                    current_request = None
    
    def process_interaction(self, request_data: List, response_data: List):
        """处理一次完整的请求-响应交互"""
        # 遍历response中的所有候选响应
        for response_item in response_data:
            candidates = response_item.get('candidates', [])
            
            for candidate in candidates:
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
                    # 提取思考过程（如果有）
                    thoughts = []
                    for part in parts:
                        if part.get('thought', False) and 'text' in part:
                            thought_text = part['text'].strip()
                            # 提取思考的第一行作为摘要
                            first_line = thought_text.split('\n')[0][:100]
                            thoughts.append(first_line)
                    
                    self.llm_counter += 1
                    llm_node_id = f"llm_step_{self.llm_counter}"
                    
                    llm_decision = {
                        'id': llm_node_id,
                        'type': 'LLM_Decision',
                        'step': self.llm_counter,
                        'tool_count': len(tool_calls_in_response),
                        'thoughts': thoughts[:1] if thoughts else ['决策'],  # 只取第一个思考
                        'tools': []
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
                    
                    self.llm_decisions.append(llm_decision)
    
    def extract_target_from_args(self, tool_name: str, args: Dict) -> str | None:
        """从工具参数中提取目标资源"""
        # 对于不同的工具，提取不同的目标标识
        if tool_name in ['fetch_url', 'browser_navigate']:
            url = args.get('url', '')
            return self.extract_domain(url)
        elif tool_name in ['github_search', 'github_get']:
            repo = args.get('repo', args.get('repository', ''))
            return f"github:{repo}" if repo else None
        else:
            # 对于其他工具，尝试找到任何URL或标识符
            for value in args.values():
                if isinstance(value, str) and ('http://' in value or 'https://' in value):
                    return self.extract_domain(value)
        
        return None
    
    def build_graph(self):
        """构建NetworkX图"""
        # 添加LLM_Decision节点
        for llm_decision in self.llm_decisions:
            label = f"LLM-{llm_decision['step']}\n"
            label += f"决策: {llm_decision['tool_count']}个工具\n"
            if llm_decision['thoughts']:
                # 截断过长的思考文本
                thought = llm_decision['thoughts'][0]
                if len(thought) > 40:
                    thought = thought[:37] + "..."
                label += f"思考: {thought}"
            
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
            if tool_call['target']:
                # 截断过长的目标
                target = tool_call['target']
                if len(target) > 30:
                    target = target[:27] + "..."
                label += f"\n→ {target}"
            
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
        
        # 添加Target_Resource节点和Accesses边
        for target in self.target_resources:
            if target:
                self.graph.add_node(
                    target,
                    type='Target_Resource',
                    label=target
                )
        
        # 添加Tool到Target的访问边
        for tool_call in self.tool_calls:
            if tool_call['target'] and tool_call['target'] in self.target_resources:
                self.graph.add_edge(
                    tool_call['id'],
                    tool_call['target'],
                    type='Accesses'
                )
    
    def visualize_graph(self, output_dir: str | None = None):
        """可视化图并保存"""
        if not output_dir:
            output_dir_path = Path(self.log_file_path).parent.parent / "intent_behavior_target_graphs"
        else:
            output_dir_path = Path(output_dir)
        
        output_dir_path.mkdir(exist_ok=True)
        
        # 创建图形 - 进一步增大尺寸以避免重叠
        plt.figure(figsize=(24, 18), dpi=100)
        
        # 使用分层布局
        pos = self._create_hierarchical_layout()
        
        # 分别绘制不同类型的节点
        llm_nodes = [n for n, d in self.graph.nodes(data=True) if d['type'] == 'LLM_Decision']
        tool_nodes = [n for n, d in self.graph.nodes(data=True) if d['type'] == 'Tool_Call']
        target_nodes = [n for n, d in self.graph.nodes(data=True) if d['type'] == 'Target_Resource']
        
        # 绘制节点 - 适度增大节点尺寸
        nx.draw_networkx_nodes(self.graph, pos, nodelist=llm_nodes, 
                               node_color='#4A90E2', node_shape='s', 
                               node_size=6000, alpha=0.9, label='LLM Decision')
        
        nx.draw_networkx_nodes(self.graph, pos, nodelist=tool_nodes, 
                               node_color='#50E3C2', node_shape='o', 
                               node_size=5000, alpha=0.9, label='Tool Call')
        
        nx.draw_networkx_nodes(self.graph, pos, nodelist=target_nodes, 
                               node_color='#B8B8B8', node_shape='o', 
                               node_size=4000, alpha=0.9, label='Target Resource')
        
        # 分别绘制不同类型的边
        calls_edges = [(u, v) for u, v, d in self.graph.edges(data=True) if d['type'] == 'Calls']
        accesses_edges = [(u, v) for u, v, d in self.graph.edges(data=True) if d['type'] == 'Accesses']
        
        nx.draw_networkx_edges(self.graph, pos, edgelist=calls_edges,
                               edge_color='#4A90E2', style='solid', 
                               width=2, alpha=0.7, arrows=True, 
                               arrowsize=20, arrowstyle='->')
        
        nx.draw_networkx_edges(self.graph, pos, edgelist=accesses_edges,
                               edge_color='#50E3C2', style='dashed', 
                               width=2, alpha=0.6, arrows=True, 
                               arrowsize=20, arrowstyle='->')
        
        # 绘制标签 - 增大字体
        labels = nx.get_node_attributes(self.graph, 'label')
        nx.draw_networkx_labels(self.graph, pos, labels, font_size=10, 
                                font_family='sans-serif', font_weight='normal',
                                verticalalignment='center', horizontalalignment='center')
        
        # 设置图例和标题
        plt.legend(loc='upper left', fontsize=12, framealpha=0.9)
        plt.title(f'意图-行为-目标图: {self.log_name}', 
                  fontsize=16, fontweight='bold', pad=30)
        
        plt.axis('off')
        plt.tight_layout(pad=2.0)
        
        # 保存图形 - 提高DPI和质量
        output_file = output_dir_path / f"{self.log_name}_intent_behavior_target_graph.png"
        plt.savefig(output_file, dpi=200, bbox_inches='tight', 
                    facecolor='white', edgecolor='none', pad_inches=0.5)
        plt.close()
        
        print(f"✓ 图形已保存: {output_file}")
        
        # 保存图的统计信息
        self._save_graph_stats(output_dir_path)
    
    def _create_hierarchical_layout(self) -> Dict:
        """创建分层布局 - 优化布局避免重叠"""
        pos = {}
        
        # 第一层: LLM Decisions - 增加水平间距
        llm_nodes = [n for n, d in self.graph.nodes(data=True) if d['type'] == 'LLM_Decision']
        for i, node in enumerate(sorted(llm_nodes, key=lambda x: self.graph.nodes[x].get('step', 0))):
            pos[node] = (i * 4.0, 2)  # 从3.5增加到4.0
        
        # 第二层: Tool Calls - 增加间距
        tool_nodes = [n for n, d in self.graph.nodes(data=True) if d['type'] == 'Tool_Call']
        tool_x_offset = 0
        for node in sorted(tool_nodes, key=lambda x: self.graph.nodes[x].get('step', 0)):
            # 找到对应的LLM节点
            llm_predecessors = [p for p in self.graph.predecessors(node)]
            if llm_predecessors:
                llm_x = pos[llm_predecessors[0]][0]
                pos[node] = (llm_x + tool_x_offset * 1.0, 1)  # 从0.8增加到1.0
                tool_x_offset += 1
            else:
                pos[node] = (tool_x_offset * 4.0, 1)
                tool_x_offset += 1
        
        # 第三层: Target Resources - 智能布局避免重叠，使用多个高度层
        target_nodes = [n for n, d in self.graph.nodes(data=True) if d['type'] == 'Target_Resource']
        
        if target_nodes:
            # 收集所有目标的理想位置（基于其前驱工具节点）
            target_ideal_positions = {}
            for node in target_nodes:
                tool_predecessors = [p for p in self.graph.predecessors(node)]
                if tool_predecessors:
                    avg_x = sum(pos[p][0] for p in tool_predecessors) / len(tool_predecessors)
                    target_ideal_positions[node] = avg_x
                else:
                    target_ideal_positions[node] = 0
            
            # 按理想位置排序目标节点
            sorted_targets = sorted(target_ideal_positions.items(), key=lambda x: x[1])
            
            # 使用贪心算法分配位置，相邻节点交替使用不同高度
            min_spacing = 1.2  # 减小最小水平间距，因为有垂直错开
            used_positions = []
            height_levels = [-0.15, 0, 0.15]  # 三个高度层：下、中、上
            current_height_idx = 0
            
            for node, ideal_x in sorted_targets:
                # 尝试在理想位置放置
                best_x = ideal_x
                
                # 检查是否与已有位置冲突
                conflict_count = 0
                while any(abs(best_x - used_x) < min_spacing for used_x in used_positions):
                    # 如果冲突，稍微向右移动
                    best_x += 0.25
                    conflict_count += 1
                    # 如果移动次数过多，切换到下一个高度层
                    if conflict_count > 2:
                        current_height_idx = (current_height_idx + 1) % len(height_levels)
                        break
                
                # 分配位置，使用当前高度层
                y_position = height_levels[current_height_idx]
                pos[node] = (best_x, y_position)
                used_positions.append(best_x)
                
                # 交替使用不同高度
                current_height_idx = (current_height_idx + 1) % len(height_levels)
        
        return pos
    
    def _save_graph_stats(self, output_dir: Path):
        """保存图的统计信息"""
        stats = {
            'log_file': self.log_name,
            'total_llm_decisions': len(self.llm_decisions),
            'total_tool_calls': len(self.tool_calls),
            'total_target_resources': len(self.target_resources),
            'unique_tools': len(set(tc['tool_name'] for tc in self.tool_calls)),
            'graph_nodes': self.graph.number_of_nodes(),
            'graph_edges': self.graph.number_of_edges(),
            'target_resources': sorted(list(self.target_resources)),
            'tool_usage': self._get_tool_usage_stats()
        }
        
        stats_file = output_dir / f"{self.log_name}_stats.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, indent=2, ensure_ascii=False)
        
        print(f"✓ 统计信息已保存: {stats_file}")
        
        # 打印摘要
        print(f"\n📊 分析摘要 - {self.log_name}:")
        print(f"  LLM决策次数: {stats['total_llm_decisions']}")
        print(f"  工具调用次数: {stats['total_tool_calls']}")
        print(f"  目标资源数: {stats['total_target_resources']}")
        print(f"  唯一工具数: {stats['unique_tools']}")
    
    def _get_tool_usage_stats(self) -> Dict[str, int]:
        """获取工具使用统计"""
        tool_usage = defaultdict(int)
        for tc in self.tool_calls:
            tool_usage[tc['tool_name']] += 1
        return dict(tool_usage)


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
            analyzer = IntentBehaviorTargetAnalyzer(str(log_file))
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
        description='分析Gemini CLI日志并生成意图-行为-目标图'
    )
    parser.add_argument(
        '--logs-dir',
        default='logs',
        help='日志文件目录 (默认: logs)'
    )
    parser.add_argument(
        '--output-dir',
        default=None,
        help='输出目录 (默认: intent_behavior_target_graphs)'
    )
    
    args = parser.parse_args()
    
    analyze_all_logs(args.logs_dir, args.output_dir)


if __name__ == '__main__':
    main()
