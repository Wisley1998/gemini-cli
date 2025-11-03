# 事件-资源图分析工具 - 快速开始指南

## 📋 目录

1. [概述](#概述)
2. [安装](#安装)
3. [快速开始](#快速开始)
4. [使用示例](#使用示例)
5. [高级分析](#高级分析)
6. [文件说明](#文件说明)

---

## 概述

这套工具将Gemini Agent的线性日志转换为**事件-资源异构图**,实现:

✅ **复杂图结构**: 多对多关系,资源汇聚点,自然分层  
✅ **多维度分析**: 域名、工具、阶段、查询参数等  
✅ **可视化**: DOT/PNG格式,支持Graphviz渲染  
✅ **可编程**: NetworkX图对象,支持自定义分析

---

## 安装

### 方法1: 自动安装 (推荐)

```bash
./setup-graph-analyzer.sh
```

### 方法2: 手动安装

```bash
# 安装Python依赖
pip3 install networkx pydot

# 安装Graphviz (可选,用于生成PNG)
# macOS
brew install graphviz

# Ubuntu/Debian
sudo apt-get install graphviz

# 创建输出目录
mkdir -p output
```

---

## 快速开始

### 1. 分析所有日志文件

```bash
python3 analyze_event_resource_graph.py
```

这会分析 `logs/` 目录下的所有 `.log` 文件,并在 `output/` 目录生成图文件。

### 2. 分析单个日志文件

```bash
python3 analyze_event_resource_graph.py logs/10-22-18-1.log
```

### 3. 运行快速测试

```bash
./test-graph-analyzer.sh
```

这会:

- 自动选择第一个日志文件
- 生成图到 `test_output/` 目录
- 显示统计信息
- 在macOS上自动打开PNG图像

---

## 使用示例

### 基本用法

```bash
# 默认: 分析logs/目录,输出到output/
python3 analyze_event_resource_graph.py

# 指定输出目录
python3 analyze_event_resource_graph.py -o graphs/

# 分析特定文件
python3 analyze_event_resource_graph.py logs/session1.log -o session1_graphs/
```

### 控制图的复杂度

```bash
# 不添加阶段节点 (减少节点数)
python3 analyze_event_resource_graph.py --no-phase

# 不添加查询参数节点 (大幅减少节点数)
python3 analyze_event_resource_graph.py --no-query-params

# 只生成DOT文件,不生成PNG
python3 analyze_event_resource_graph.py --no-png

# 最简化图
python3 analyze_event_resource_graph.py --no-phase --no-query-params
```

### 批量处理

```bash
# 处理所有日志
for log in logs/*.log; do
    python3 analyze_event_resource_graph.py "$log" -o output/
done

# 只生成DOT文件(快速)
for log in logs/*.log; do
    python3 analyze_event_resource_graph.py "$log" --no-png
done
```

---

## 高级分析

### 1. 生成详细分析报告

```bash
python3 graph_analysis_examples.py logs/10-22-18-1.log
```

这会生成包含以下内容的完整报告:

- 图统计信息 (节点数、边数、类型分布)
- 执行流程分析 (事件序列)
- 工具使用分析 (频率、类别)
- 域名访问分析 (分类、频率)
- 阶段分布分析 (任务阶段)
- URL模式分析
- 查询参数分析

### 2. Python API使用

```python
from analyze_event_resource_graph import analyze_log, build_event_graph
import networkx as nx

# 分析日志并获取图对象
G = analyze_log("logs/10-22-18-1.log")

# 查询节点
domains = [n for n, d in G.nodes(data=True) if d.get('type') == 'domain']
print(f"访问了 {len(domains)} 个域名")

# 查询边
tool_calls = [(u, v) for u, v, d in G.edges(data=True) if d.get('type') == 'invokes']
print(f"有 {len(tool_calls)} 次工具调用")

# 计算度中心性
in_degrees = dict(G.in_degree())
top_nodes = sorted(in_degrees.items(), key=lambda x: x[1], reverse=True)[:5]
print("最重要的节点:", top_nodes)
```

### 3. 自定义分析脚本

创建 `my_analysis.py`:

```python
from analyze_event_resource_graph import parse_log_file, build_event_graph

# 解析日志
interactions = parse_log_file("logs/my_session.log")

# 构建图
G = build_event_graph(interactions)

# 自定义分析
# 例如: 找出所有访问失败的URL
for node, data in G.nodes(data=True):
    if data.get('type') == 'url':
        # 检查是否有错误标记
        # ...你的分析逻辑
        pass
```

---

## 输出文件

对于日志文件 `logs/10-22-18-1.log`,会生成:

```
output/
├── 10-22-18-1.dot    # Graphviz DOT格式
└── 10-22-18-1.png    # PNG图像 (如果安装了Graphviz)
```

### DOT文件格式

DOT是文本格式,可以:

- 用任何文本编辑器查看
- 上传到在线Graphviz工具
- 用Graphviz命令行工具转换

```bash
# 转换为不同格式
dot -Tpng output/10-22-18-1.dot -o output/10-22-18-1.png
dot -Tsvg output/10-22-18-1.dot -o output/10-22-18-1.svg
dot -Tpdf output/10-22-18-1.dot -o output/10-22-18-1.pdf

# 尝试不同布局算法
fdp -Tpng output/10-22-18-1.dot -o output/10-22-18-1-fdp.png
circo -Tpng output/10-22-18-1.dot -o output/10-22-18-1-circo.png
neato -Tpng output/10-22-18-1.dot -o output/10-22-18-1-neato.png
```

---

## 文件说明

### 核心文件

| 文件                              | 说明                      |
| --------------------------------- | ------------------------- |
| `analyze_event_resource_graph.py` | 主分析脚本,解析日志生成图 |
| `graph_analysis_examples.py`      | 高级分析示例,生成详细报告 |
| `EVENT_RESOURCE_GRAPH_README.md`  | 完整文档                  |
| `GRAPH_QUICK_START.md`            | 本文件,快速开始指南       |

### 辅助脚本

| 文件                      | 说明         |
| ------------------------- | ------------ |
| `setup-graph-analyzer.sh` | 自动安装依赖 |
| `test-graph-analyzer.sh`  | 快速测试分析 |

---

## 可视化建议

### 在线工具

对于简单查看,可以使用在线工具:

1. **Graphviz Online**: http://www.webgraphviz.com/
   - 复制DOT文件内容
   - 粘贴到网页
   - 在线渲染

2. **Viz.js**: http://viz-js.com/
   - 上传DOT文件
   - 浏览器中查看

### 本地工具

对于大图,推荐使用专业工具:

1. **Gephi** (推荐)
   - 下载: https://gephi.org/
   - 导入DOT文件
   - 强大的布局和分析功能

2. **yEd**
   - 下载: https://www.yworks.com/products/yed
   - 导入GraphML格式 (需转换)

3. **Graphviz命令行**

   ```bash
   # 交互式查看 (需要GUI)
   dot -Tx11 output/10-22-18-1.dot

   # 生成高分辨率图像
   dot -Tpng -Gdpi=300 output/10-22-18-1.dot -o output/high-res.png
   ```

---

## 常见问题

### Q: 图太大无法查看?

**A**: 有几个选项:

1. 减少节点:

   ```bash
   python3 analyze_event_resource_graph.py --no-query-params --no-phase
   ```

2. 使用SVG格式(可缩放):

   ```bash
   dot -Tsvg output/10-22-18-1.dot -o output/10-22-18-1.svg
   ```

3. 使用Gephi等工具进行交互式浏览

### Q: 无法生成PNG?

**A**: 检查Graphviz安装:

```bash
# 检查是否安装
dot -V

# macOS安装
brew install graphviz

# Ubuntu/Debian安装
sudo apt-get install graphviz
```

### Q: 如何修改节点颜色?

**A**: 编辑 `analyze_event_resource_graph.py` 中的 `style_and_export` 函数,修改 `fillcolor` 值。

### Q: 如何添加自定义节点类型?

**A**: 参考 `build_event_graph` 函数,添加新的节点创建逻辑。

---

## 示例输出

运行 `python3 analyze_event_resource_graph.py logs/10-22-18-1.log` 后:

```
============================================================
分析日志: 10-22-18-1.log
============================================================
✓ 提取了 42 个交互事件
✓ 构建了图: 156 个节点, 243 条边

节点类型分布:
  - domain: 12
  - event: 42
  - phase: 4
  - query_param: 38
  - session: 1
  - tool_type: 3
  - url: 56

✓ DOT文件已保存: output/10-22-18-1.dot
✓ PNG图像已保存: output/10-22-18-1.png
```

---

## 下一步

1. ✅ 运行快速测试: `./test-graph-analyzer.sh`
2. ✅ 分析你的日志: `python3 analyze_event_resource_graph.py logs/your-log.log`
3. ✅ 查看完整文档: `cat EVENT_RESOURCE_GRAPH_README.md`
4. ✅ 尝试高级分析: `python3 graph_analysis_examples.py logs/your-log.log`

---

## 支持

- 📖 详细文档: `EVENT_RESOURCE_GRAPH_README.md`
- 💻 代码注释: 查看Python源文件
- 🐛 问题反馈: 提交Issue

---

**祝分析愉快! 🎉**
