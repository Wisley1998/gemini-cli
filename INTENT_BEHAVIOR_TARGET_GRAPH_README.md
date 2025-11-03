# 意图-行为-目标图分析器

## 📖 简介

该工具用于分析 Gemini CLI 日志文件，将每次 LLM 执行任务的过程可视化为一个"意图-行为-目标"的有向图。

## 🎯 核心概念

该分析方案不仅将 LLM 和工具调用视为线性步骤，而是根据工具调用的"目标"（如访问的网址域名）将它们分组和关联，形成一个更具结构性的图。

### 图的节点类型

1. **LLM_Decision (LLM决策节点)** 🟦
   - **何时创建**: 当日志中出现工具调用时
   - **节点属性**:
     - `id`: 唯一标识符 (例如 `llm_step_1`)
     - `type`: `LLM_Decision`
     - `label`: 包含步骤编号、工具数量和思考摘要
     - `step`: 步骤编号
     - `tool_count`: 工具调用数量

2. **Tool_Call (工具调用节点)** 🟩
   - **何时创建**: 每次工具调用时
   - **节点属性**:
     - `id`: 唯一标识符 (例如 `tool_step_2`)
     - `type`: `Tool_Call`
     - `label`: 包含工具名称和目标参数
     - `tool_name`: 工具名称 (如 `fetch_url`)
     - `target`: 目标资源

3. **Target_Resource (目标资源节点)** ⚪
   - **何时创建**: 根据工具调用的 `target` 字段
   - **节点属性**:
     - `id`: 目标值 (例如 `google.com`)
     - `type`: `Target_Resource`
     - `label`: 目标资源名称

### 图的边类型

1. **Calls (调用关系边)** — 实线
   - 从 `LLM_Decision` 节点指向 `Tool_Call` 节点
   - 表示 LLM 决定调用某个工具

2. **Accesses (访问关系边)** ⋯ 虚线
   - 从 `Tool_Call` 节点指向 `Target_Resource` 节点
   - 表示工具访问某个目标资源

## 🚀 使用方法

### 1. 安装依赖

```bash
pip install -r requirements_intent_graph.txt
```

### 2. 分析所有日志文件

```bash
python3 analyze_intent_behavior_target_graph.py --logs-dir logs
```

### 3. 分析单个日志文件或指定输出目录

```bash
python3 analyze_intent_behavior_target_graph.py \
    --logs-dir logs \
    --output-dir custom_output_dir
```

## 📊 输出文件

脚本会在 `intent_behavior_target_graphs/` 目录下生成以下文件：

### 1. 图形文件 (PNG)

- 文件名: `{日志名}_intent_behavior_target_graph.png`
- 内容: 可视化的意图-行为-目标图
- 特点:
  - 🟦 蓝色方块 = LLM Decision
  - 🟩 绿色椭圆 = Tool Call
  - ⚪ 灰色圆形 = Target Resource
  - 实线箭头 = Calls 关系
  - 虚线箭头 = Accesses 关系

### 2. 统计文件 (JSON)

- 文件名: `{日志名}_stats.json`
- 内容: 详细的图统计信息

示例统计文件:

```json
{
  "log_file": "10-22-18-1",
  "total_llm_decisions": 13,
  "total_tool_calls": 13,
  "total_target_resources": 7,
  "unique_tools": 2,
  "graph_nodes": 33,
  "graph_edges": 26,
  "target_resources": ["bloomberg.com", "google.com", "reuters.com"],
  "tool_usage": {
    "fetch_url": 11,
    "browser_navigate": 2
  }
}
```

## 📐 图的布局

脚本使用**分层布局**来组织节点:

- **第1层** (顶部): LLM Decision 节点
- **第2层** (中间): Tool Call 节点
- **第3层** (底部): Target Resource 节点

多个 Tool Call 可能指向同一个 Target Resource，形成汇聚点，这样可以清晰地看到哪些目标被重复访问。

## 🔍 分析示例

### 示例输出

```
🔍 找到 6 个日志文件

============================================================
📝 分析日志: 10-22-18-1.log
============================================================
✓ 图形已保存: intent_behavior_target_graphs/10-22-18-1_intent_behavior_target_graph.png
✓ 统计信息已保存: intent_behavior_target_graphs/10-22-18-1_stats.json

📊 分析摘要 - 10-22-18-1:
  LLM决策次数: 13
  工具调用次数: 13
  目标资源数: 7
  唯一工具数: 2
```

### 关键洞察

通过查看生成的图，你可以:

1. **识别热点目标**: 哪些域名/资源被频繁访问
2. **理解决策模式**: LLM 如何组织和分配工具调用
3. **发现依赖关系**: 哪些工具调用访问相同的资源
4. **优化机会**: 识别重复访问和潜在的缓存机会

## 🛠️ 技术细节

### 支持的工具类型

脚本目前支持以下工具的目标提取:

- `fetch_url`: 提取 URL 域名
- `browser_navigate`: 提取 URL 域名
- `github_search`, `github_get`: 提取仓库名称 (格式: `github:repo`)

对于其他工具，脚本会尝试从参数中查找 URL。

### 域名提取

URL `https://www.google.com/search?q=test` 会被提取为域名 `google.com` (自动移除 `www.` 前缀)

## 🐛 故障排除

### 中文字符显示问题

如果生成的图形中中文字符显示为方块，这是因为 matplotlib 默认字体不支持中文。你可以忽略警告，图形仍然可用，或者安装支持中文的字体。

### 空图

如果某个日志文件没有工具调用，生成的图将是空的。这是正常的 - 表示该任务没有使用任何工具。

## 📝 日志文件格式

该工具解析 Gemini CLI 生成的日志文件，期望以下格式:

- REQUEST 块包含请求数据
- RESPONSE 块包含响应数据 (包括 `functionCall` 字段)

## 🔄 与其他分析工具的区别

该工具专注于:

- ✅ **目标为中心**: 以访问的资源为汇聚点
- ✅ **意图可视化**: 显示 LLM 的决策思路
- ✅ **关系映射**: 清晰展示调用和访问关系

与简单的调用链分析不同，这个工具能够揭示更深层的模式和结构。

## 📄 许可

与 Gemini CLI 项目保持一致。
