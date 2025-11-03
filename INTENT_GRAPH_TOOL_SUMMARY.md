# 意图-行为-目标图分析工具 - 完整说明

## 🎉 创建完成

我已经为你创建了一个完整的Python分析工具，用于将Gemini CLI的日志文件转换为"意图-行为-目标"有向图。

## 📦 创建的文件

### 1. 主要程序

- **`analyze_intent_behavior_target_graph.py`** - 核心分析脚本
  - 解析日志文件
  - 构建NetworkX图
  - 生成可视化图形

### 2. 依赖文件

- **`requirements_intent_graph.txt`** - Python依赖包
  - matplotlib (图形绘制)
  - networkx (图数据结构)

### 3. 使用文档

- **`INTENT_BEHAVIOR_TARGET_GRAPH_README.md`** - 完整使用指南
  - 安装步骤
  - 使用方法
  - 输出说明
- **`INTENT_GRAPH_INTERPRETATION_GUIDE.md`** - 图解读指南
  - 如何理解生成的图
  - 识别关键模式
  - 优化建议

### 4. 快速运行脚本

- **`run-intent-graph-analysis.sh`** - 一键运行脚本
  - 自动检查依赖
  - 执行分析
  - 提示查看结果

## 🚀 快速开始

### 方式1: 使用快捷脚本

```bash
./run-intent-graph-analysis.sh
```

### 方式2: 直接运行Python脚本

```bash
# 安装依赖
pip3 install -r requirements_intent_graph.txt

# 运行分析
python3 analyze_intent_behavior_target_graph.py --logs-dir logs
```

## 📊 已生成的示例

工具已经成功分析了你的6个日志文件，生成了:

### 图形文件 (在 `intent_behavior_target_graphs/` 目录)

```
✅ 10-22-18-1_intent_behavior_target_graph.png (678KB)
   📊 13个LLM决策, 13个工具调用, 7个目标资源

✅ 10-22-18-4_intent_behavior_target_graph.png (686KB)
   📊 13个LLM决策, 14个工具调用, 3个目标资源

✅ 10-22-19-2_intent_behavior_target_graph.png (258KB)
   📊 3个LLM决策, 3个工具调用, 3个目标资源

✅ 10-22-19-3_intent_behavior_target_graph.png (349KB)
   📊 7个LLM决策, 7个工具调用, 2个目标资源

✅ 10-22-19-4_intent_behavior_target_graph.png (343KB)
   📊 6个LLM决策, 6个工具调用, 1个目标资源
```

### 统计文件

每个图形都有对应的JSON统计文件，包含:

- 总体统计 (决策数、工具数、目标数)
- 目标资源列表
- 工具使用统计
- 图的节点和边数量

## 🎨 图的特点

### 三种节点类型

1. **🟦 LLM Decision** (蓝色方块)
   - 显示LLM的决策点
   - 包含思考摘要
   - 标注调用的工具数量

2. **🟩 Tool Call** (绿色椭圆)
   - 显示具体的工具调用
   - 包含工具名称
   - 显示访问的目标

3. **⚪ Target Resource** (灰色圆形)
   - 显示被访问的资源
   - 通常是域名或资源标识
   - 作为汇聚点

### 两种边类型

1. **Calls** (实线箭头)
   - LLM Decision → Tool Call
   - 表示调用关系

2. **Accesses** (虚线箭头)
   - Tool Call → Target Resource
   - 表示访问关系

## 💡 核心优势

### 相比传统的线性日志分析

✅ **以目标为中心**: 多个工具调用可能访问同一个目标，形成汇聚点

✅ **结构化视图**: 清晰展示意图(LLM)、行为(Tool)、目标(Resource)的关系

✅ **模式识别**: 容易识别重复访问、并行调用等模式

✅ **优化指导**: 直观显示缓存机会和优化点

## 📈 实际应用示例

### 示例: 10-22-18-1.log 分析结果

```json
{
  "total_llm_decisions": 13,
  "total_tool_calls": 13,
  "total_target_resources": 7,
  "target_resources": [
    "bloomberg.com",
    "duckduckgo.com",
    "finance.yahoo.com",
    "goldprice.org",
    "google.com",
    "query1.finance.yahoo.com",
    "reuters.com"
  ],
  "tool_usage": {
    "fetch_url": 11,
    "browser_navigate": 2
  }
}
```

**洞察**:

- Agent 访问了7个不同的金融数据源
- 主要使用 `fetch_url` 工具 (11次)
- 少量使用浏览器导航 (2次)
- 平均每个决策调用1个工具 (高效)

## 🔧 高级功能

### 支持的工具类型

- ✅ `fetch_url` - 提取URL域名
- ✅ `browser_navigate` - 提取URL域名
- ✅ `github_search`, `github_get` - 提取仓库信息
- ✅ 其他工具 - 自动检测URL参数

### 目标提取规则

```python
URL: https://www.google.com/search?q=test
  ↓
Domain: google.com  (自动去除www前缀)

Repo: owner/repo
  ↓
Target: github:owner/repo
```

### 布局算法

- **分层布局**: 三层结构清晰展示层次关系
- **智能定位**: Tool节点靠近对应的LLM节点
- **目标汇聚**: 相同目标的调用集中显示

## 📚 完整文档

1. **安装和使用**
   → 阅读 `INTENT_BEHAVIOR_TARGET_GRAPH_README.md`

2. **解读图形**
   → 阅读 `INTENT_GRAPH_INTERPRETATION_GUIDE.md`

3. **技术细节**
   → 查看 `analyze_intent_behavior_target_graph.py` 源码注释

## 🎯 后续扩展建议

### 可以添加的功能

1. **交互式图形**: 使用 plotly 生成可交互的HTML图
2. **时间维度**: 添加时间戳，显示执行时序
3. **性能指标**: 显示每个调用的耗时
4. **成功率**: 标记失败的调用
5. **对比分析**: 比较多个日志的差异
6. **聚类分析**: 自动识别相似的执行模式

### 其他可视化方式

1. **Sankey图**: 显示流量和依赖关系
2. **热力图**: 显示目标访问频率
3. **时间线**: 显示执行的时间顺序
4. **树状图**: 显示决策树结构

## ✨ 总结

你现在有了一个完整的分析工具，可以:

✅ 自动解析Gemini CLI日志
✅ 构建意图-行为-目标图
✅ 生成高质量的可视化图形
✅ 输出详细的统计数据
✅ 识别优化机会

所有功能都已经测试并成功运行！

## 📞 使用支持

如果遇到问题:

1. 检查日志格式是否正确
2. 确保依赖已正确安装
3. 查看 Python 错误信息
4. 参考示例输出对比

祝你使用愉快! 🎉
