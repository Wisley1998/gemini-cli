# 事件-资源异构图分析工具

## 概述

这个工具将Gemini Agent的日志文件转换为**事件-资源异构图**,把原本线性的LLM→Tool调用流程转换为复杂的多维图结构,便于分析和可视化Agent的执行过程。

## 特性

### 图建模架构

采用"事件节点 + 资源节点"的异构图设计:

- **事件节点 (Event)**: 每个LLM调用或工具调用
- **资源节点 (Resource)**: 工具类型、URL、域名、查询参数等
- **多重连接**: 相同资源被多次访问时形成汇聚点,自然产生复杂图结构

### 节点类型

1. **Event节点** (`event`)
   - `llm`: LLM思考事件
   - `tool`: 工具调用事件

2. **ToolType节点** (`tool_type`)
   - 工具类型聚合点 (如 `fetch_url`, `browser_navigate`)

3. **URL节点** (`url`)
   - 规范化的URL

4. **Domain节点** (`domain`)
   - 域名节点,按类别着色:
     - `search`: 搜索引擎 (Google, Bing等)
     - `news`: 新闻网站 (Reuters, Bloomberg等)
     - `data_source`: 数据源 (goldprice.org等)
     - `finance_portal`: 金融门户 (Yahoo Finance等)
     - `api`: API接口

5. **QueryParam节点** (`query_param`)
   - URL查询参数节点

6. **Phase节点** (`phase`)
   - 任务阶段节点 (search, direct_source, yahoo_download等)

7. **Session节点** (`session`)
   - 会话根节点

### 边类型

- `sequence`: 事件时间顺序边
- `invokes`: LLM → Tool (调用关系)
- `uses_tool`: Tool → ToolType
- `accesses_url`: Tool → URL
- `targets_domain`: URL → Domain
- `has_param`: URL → QueryParam
- `in_phase`: Event → Phase
- `in_session`: Event → Session

## 安装依赖

```bash
# 安装Python依赖
pip install networkx pydot

# macOS安装Graphviz (用于生成PNG)
brew install graphviz

# 或者Ubuntu/Debian
sudo apt-get install graphviz
```

## 使用方法

### 基本用法

```bash
# 分析logs目录下的所有日志文件
python analyze_event_resource_graph.py

# 分析单个日志文件
python analyze_event_resource_graph.py logs/10-22-18-1.log

# 指定输出目录
python analyze_event_resource_graph.py -o graphs/

# 不生成PNG图像(只生成DOT文件)
python analyze_event_resource_graph.py --no-png

# 不添加阶段节点
python analyze_event_resource_graph.py --no-phase

# 不添加查询参数节点
python analyze_event_resource_graph.py --no-query-params
```

### 命令行参数

```
positional arguments:
  input                 输入日志文件或目录 (默认: logs)

optional arguments:
  -h, --help            显示帮助信息
  -o OUTPUT, --output OUTPUT
                        输出目录 (默认: output)
  --no-phase            不添加阶段节点
  --no-query-params     不添加查询参数节点
  --no-png              不生成PNG图像
```

## 输出文件

对于每个日志文件 `10-22-18-1.log`,会生成:

- `output/10-22-18-1.dot` - Graphviz DOT格式图文件
- `output/10-22-18-1.png` - PNG可视化图像 (如果安装了Graphviz)

## 日志格式要求

工具会解析包含以下内容的日志:

1. **REQUEST/RESPONSE块**: 用`---`分隔
2. **时间戳**: `[REQUEST] 2025-10-22T10:49:29.265Z`
3. **LLM思考**: JSON中的`"thought": true`和`"text"`字段
4. **工具调用**: JSON中的`"functionCall"`字段,包含`name`和`args`

示例:

```json
{
  "functionCall": {
    "name": "fetch_url",
    "args": {
      "url": "https://goldprice.org/gold-price-history.html"
    }
  }
}
```

## 图结构示例

生成的图会包含以下结构:

```
LLM-0 → Tool-1 (fetch_url) → URL (google.com/search) → Domain (google.com)
                           ↓
                      ToolType (fetch_url) ← Tool-3, Tool-5, ...
                                          ↓
                                    多个事件汇聚
```

同时:

- URL节点可能连接多个QueryParam节点
- Domain节点会聚合多个URL访问
- ToolType节点会聚合所有该工具的使用
- Phase节点会聚合相关阶段的事件

## 扩展和定制

### 添加新的域名类别

在 `DOMAIN_CATEGORY_MAP` 中添加:

```python
DOMAIN_CATEGORY_MAP = {
    "example.com": "custom_category",
    # ...
}
```

### 添加新的工具类别

在 `TOOL_CATEGORY_MAP` 中添加:

```python
TOOL_CATEGORY_MAP = {
    "custom_tool": "custom_category",
    # ...
}
```

### 添加新的阶段识别规则

在 `PHASE_KEYWORDS` 中添加:

```python
PHASE_KEYWORDS = {
    "custom_phase": ["keyword1", "keyword2"],
    # ...
}
```

## 作为Python模块使用

```python
from analyze_event_resource_graph import analyze_log, build_event_graph, parse_log_file

# 解析日志
interactions = parse_log_file("logs/10-22-18-1.log")

# 构建图
G = build_event_graph(interactions, session_name="my_session")

# 分析图
print(f"节点数: {G.number_of_nodes()}")
print(f"边数: {G.number_of_edges()}")

# 查找特定类型的节点
domain_nodes = [n for n, d in G.nodes(data=True) if d.get('type') == 'domain']
print(f"访问的域名: {domain_nodes}")

# 完整分析并导出
analyze_log("logs/10-22-18-1.log", output_dir="my_graphs")
```

## 图分析示例

生成的NetworkX图对象可以进行各种分析:

```python
import networkx as nx
from analyze_event_resource_graph import analyze_log

G = analyze_log("logs/10-22-18-1.log")

# 找出度最高的节点(最常访问的资源)
in_degrees = dict(G.in_degree())
top_nodes = sorted(in_degrees.items(), key=lambda x: x[1], reverse=True)[:10]
print("最常访问的节点:", top_nodes)

# 找出所有域名节点
domains = [n for n, d in G.nodes(data=True) if d.get('type') == 'domain']
print(f"访问了 {len(domains)} 个不同的域名")

# 计算事件之间的路径
events = [n for n, d in G.nodes(data=True) if d.get('type') == 'event']
if len(events) >= 2:
    try:
        path = nx.shortest_path(G, events[0], events[-1])
        print(f"第一个到最后一个事件的路径: {path}")
    except nx.NetworkXNoPath:
        print("无路径连接")

# 统计不同类型的边
edge_types = {}
for u, v, data in G.edges(data=True):
    edge_type = data.get('type', 'unknown')
    edge_types[edge_type] = edge_types.get(edge_type, 0) + 1
print("边类型分布:", edge_types)
```

## 可视化建议

使用Graphviz查看大图:

```bash
# 使用dot布局
dot -Tpng output/10-22-18-1.dot -o output/10-22-18-1.png

# 使用fdp布局(力导向)
fdp -Tpng output/10-22-18-1.dot -o output/10-22-18-1-fdp.png

# 使用circo布局(圆形)
circo -Tpng output/10-22-18-1.dot -o output/10-22-18-1-circo.png

# 使用neato布局
neato -Tpng output/10-22-18-1.dot -o output/10-22-18-1-neato.png

# 生成SVG(可缩放)
dot -Tsvg output/10-22-18-1.dot -o output/10-22-18-1.svg
```

使用在线工具:

- [Graphviz Online](http://www.webgraphviz.com/) - 粘贴DOT文件内容
- [Viz.js](http://viz-js.com/) - 浏览器中渲染

## 故障排除

### 问题: 无法生成PNG

**原因**: 未安装Graphviz或pydot

**解决**:

```bash
# macOS
brew install graphviz
pip install pydot

# Ubuntu/Debian
sudo apt-get install graphviz
pip install pydot
```

### 问题: JSON解析错误

**原因**: 日志格式不完整或损坏

**解决**: 检查日志文件是否完整,特别是JSON结构是否闭合

### 问题: 图太大无法查看

**解决**:

1. 使用 `--no-query-params` 减少节点
2. 使用 `--no-phase` 减少节点
3. 使用SVG格式并在浏览器中查看
4. 使用Gephi等专业图可视化工具导入DOT文件

## 性能优化

对于大型日志文件:

1. **只分析关键部分**: 提前过滤日志文件
2. **禁用查询参数**: 使用 `--no-query-params`
3. **批处理**: 使用脚本批量处理多个文件

```bash
# 批量处理并只生成DOT文件
for log in logs/*.log; do
    python analyze_event_resource_graph.py "$log" --no-png
done
```

## 贡献

欢迎提交Issue和Pull Request!

## 许可

遵循项目主许可协议。
