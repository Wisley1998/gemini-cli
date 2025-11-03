# 意图-行为-目标图分析器 V2 (增强版)

## 📖 简介

V2版本在原有基础上进行了重大升级，**不仅显示LLM最终选择的资源，还展示了决策过程中考虑但未选择的候选资源**。这使得我们能够更深入地理解LLM的决策逻辑和选择理由。

## 🆕 V2 版本的核心改进

### 1. **候选资源提取** 🎯

- 从**上一轮工具调用的返回结果**中提取所有URL作为候选资源
- 识别LLM看到但最终**未选择**访问的候选网站
- 对比展示"候选集"vs"最终选择"

**工作原理示例**:

1. LLM调用 `fetch_url("google.com/search?q=gold")`
2. 工具返回包含链接: `goldprice.org`, `kitco.com`, `bloomberg.com`等
3. LLM在下一步选择访问 `goldprice.org`
4. → `kitco.com`和`bloomberg.com`成为"候选但未选择"的资源

### 2. **决策过程可视化** 🔍

- 显示LLM在每次决策中考虑了多少个候选资源
- 用不同的视觉样式区分"被选择"和"未被选择"的资源
- 通过边的类型清晰表达"考虑"vs"访问"的关系

### 3. **域名关系分析** 🌐

- 自动识别同一主域名下的不同页面(如 `goldprice.org` 的不同子页面)
- 用分组边(Groups_With)连接相关资源
- 揭示LLM在同一网站不同页面间的选择模式

### 4. **决策演化追踪** 📈

- 展示相邻决策之间候选资源的变化
- 识别被反复考虑的资源
- 分析LLM的资源探索策略

## 🎨 图的节点类型与颜色编码

### 节点类型

| 节点类型                      | 视觉样式                          | 含义                            |
| ----------------------------- | --------------------------------- | ------------------------------- |
| **LLM_Decision** 🟦           | 蓝色方块，加粗边框                | LLM的决策点，显示考虑的候选数量 |
| **Tool_Call** 🟩              | 绿色椭圆                          | 工具调用实例                    |
| **Target_Resource** 🔴🔵🟠    | **深色**圆形，黑色粗边框，显示URL | **最终被选择并访问**的资源      |
| **Candidate_Resource** 🌸🌊🍊 | **浅色**圆形，灰色细边框，无文字  | **被考虑但未被选择**的资源      |

### 颜色编码系统 🎨

**核心设计理念**: 用颜色代替文字，减少视觉混乱

1. **域名分组着色**
   - 同一主域名（如 `goldprice.org`）下的所有URL使用同一色系
   - 例如：`goldprice.org` 的所有页面都用红色系

2. **深浅度表示选择**
   - **深色** = 被LLM选择并访问的URL
   - **浅色** = 被考虑但未选择的URL（深色的淡化70%版本）

3. **示例**

   ```
   goldprice.org/history     🔴 深红色 (被选中)
   goldprice.org/charts      🌸 浅红色 (候选)
   goldprice.org/prices      🌸 浅红色 (候选)

   bloomberg.com/markets     🔵 深蓝色 (被选中)
   bloomberg.com/news        🌊 浅蓝色 (候选)
   ```

4. **图例显示**
   - 图例会显示主要域名的颜色对应关系
   - 每个域名显示深浅两个版本

## 🔗 图的边类型

| 边类型          | 样式         | 含义                            |
| --------------- | ------------ | ------------------------------- |
| **Calls**       | 蓝色实线箭头 | LLM决定调用某个工具             |
| **Accesses**    | 绿色实线箭头 | 工具实际访问某个资源            |
| **Considers**   | 橙色虚线箭头 | LLM考虑（但可能未选择）某个资源 |
| **Groups_With** | 紫色点线     | 同一主域名下的资源关系          |

## 🚀 使用方法

### 1. 安装依赖

```bash
pip install -r requirements_intent_graph.txt
```

### 2. 分析所有日志文件

```bash
python3 analyze_intent_behavior_target_graph_v2.py --logs-dir logs
```

### 3. 指定输出目录

```bash
python3 analyze_intent_behavior_target_graph_v2.py \
    --logs-dir logs \
    --output-dir custom_output_v2
```

## 📊 输出文件

脚本会在 `intent_behavior_target_graphs_v2/` 目录下生成以下文件:

### 1. 图形文件 (PNG)

- 文件名: `{日志名}_intent_behavior_target_graph_v2.png`
- 内容: 增强版的意图-行为-目标图
- 视觉特点:
  - 🟦 蓝色方块 = LLM Decision (显示候选数量)
  - 🟩 绿色椭圆 = Tool Call
  - 🔴🔵🟠 **深色**圆形(粗黑边框，带URL标签) = 最终选择的资源
  - 🌸🌊🍊 **浅色**圆形(细灰边框，无标签) = 候选但未选择的资源
  - 实线箭头 = 实际执行的调用/访问
  - 虚线箭头(淡化) = 考虑但未执行
  - **颜色分组**: 同域名同色系，深浅区分选择

### 2. 统计文件 (JSON)

- 文件名: `{日志名}_stats_v2.json`
- 内容: 增强的统计信息

示例统计文件:

```json
{
  "log_file": "10-22-18-1",
  "total_llm_decisions": 13,
  "total_tool_calls": 13,
  "total_target_resources": 7,
  "total_candidate_resources": 25,
  "candidates_not_selected": 18,
  "domain_groups": {
    "goldprice.org": 4,
    "kitco.com": 3,
    "bloomberg.com": 2
  },
  "decision_details": [
    {
      "step": 1,
      "tools_called": 1,
      "candidates_considered": 5,
      "candidates_list": [
        "https://goldprice.org/gold-price-history.html",
        "https://goldprice.org/30-year-gold-price-history.html",
        "https://kitco.com/charts/livegold.html",
        "https://www.investing.com/commodities/gold",
        "https://www.bloomberg.com/markets/commodities"
      ],
      "thought_summary": "Planning Data Acquisition Strategies"
    }
  ]
}
```

## 🔍 V2 版本的关键洞察

通过V2版本的图，你可以回答以下问题:

### 1. **选择理由分析**

- LLM为什么选择网站A而不是网站B？
- 被选择的资源有什么共同特征？
- 未被选择的候选为什么被排除？

### 2. **决策模式识别**

- LLM倾向于选择权威网站还是专业网站？
- 是否存在"先探索后聚焦"的模式？
- 同一域名的不同页面如何被选择？

### 3. **资源覆盖度评估**

- LLM考虑的资源是否足够多样化？
- 是否存在被忽略的重要信息源？
- 候选集的质量如何？

### 4. **优化机会发现**

- 哪些候选资源值得优先访问？
- 是否存在重复考虑但从未选择的资源？
- 候选生成策略是否需要改进？

## 📐 图的布局策略

V2版本使用**4层分层布局**:

- **第1层** (最顶部): LLM Decision 节点
- **第2层**: Tool Call 节点
- **第3层**: Target Resource 节点 (被选择的)
- **第4层** (最底部): Candidate Resource 节点 (未被选择的)

这种布局清晰地将"最终选择"和"未选择"分开，便于对比分析。

## 🆚 与 V1 版本的对比

| 特性               | V1 版本 | V2 版本 |
| ------------------ | ------- | ------- |
| 显示最终选择的资源 | ✅      | ✅      |
| 显示候选资源       | ❌      | ✅      |
| 从thought提取信息  | 部分    | 完整    |
| 域名关系分析       | ❌      | ✅      |
| 决策过程可视化     | ❌      | ✅      |
| 选择vs考虑对比     | ❌      | ✅      |
| 统计候选资源数量   | ❌      | ✅      |

## 💡 使用建议

### 对于研究人员

- 分析LLM的决策偏好和选择模式
- 评估信息检索的覆盖度和质量
- 识别决策过程中的潜在偏见

### 对于系统优化者

- 发现被低估的候选资源
- 优化候选生成策略
- 改进资源排序算法

### 对于用户

- 理解为什么得到特定的回答
- 评估信息来源的多样性
- 了解LLM的思考过程

## 🛠️ 技术细节

### 候选资源提取方法

**V2版本的关键创新**: 从工具返回结果中提取候选,而非从思考过程中猜测

1. **监听工具响应**: 解析每个REQUEST中的`functionResponse`字段
2. **URL提取**: 使用正则表达式从响应文本中提取所有HTTP(S) URL
3. **候选累积**: 将所有提取的URL作为下一次决策的候选集
4. **对比分析**: 比较候选集和LLM实际调用的URL,识别未选择项

**示例流程**:

```
Step 1: LLM调用 fetch_url("google.com/search?q=gold")
  ↓
Step 2: 工具返回包含:
  - goldprice.org/history
  - goldprice.org/30-year
  - kitco.com
  - bloomberg.com
  ↓
Step 3: LLM看到这4个候选,选择调用 fetch_url("goldprice.org/30-year")
  ↓
结果: 3个候选资源(未选择) + 1个目标资源(选择)

### 支持的资源类型

- Web URL (完整显示路径，不只是域名)
- GitHub仓库 (格式: `github:owner/repo`)
- 金融数据网站 (Bloomberg, Reuters, Kitco等)
- 新闻网站 (Forbes, WSJ, CNBC等)

## 📝 示例输出

```

🔍 找到 6 个日志文件

============================================================
📝 分析日志: 10-22-18-1.log
============================================================
✓ 图形已保存: intent_behavior_target_graphs_v2/10-22-18-1_intent_behavior_target_graph_v2.png
✓ 统计信息已保存: intent_behavior_target_graphs_v2/10-22-18-1_stats_v2.json

📊 分析摘要 - 10-22-18-1:
LLM决策次数: 13
工具调用次数: 13
最终选择资源: 7
候选资源总数: 25
未被选择候选: 18
域名分组数: 5
唯一工具数: 2

```

## 🔬 深入分析示例

假设在某个决策步骤中:

**候选资源** (浅色圆形，无文字):
- 🌸 `goldprice.org/gold-price-history.html` (浅红色)
- 🔴 `goldprice.org/30-year-gold-price-history.html` (深红色) ✅ **被选中**
- 🌊 `kitco.com/charts/livegold.html` (浅蓝色)
- 🌊 `bloomberg.com/markets/commodities` (浅蓝色)

**视觉效果**:
- 一眼就能看到 `goldprice.org` 的两个页面（同为红色系）
- 深红色的节点带有URL标签，浅红色的没有标签
- `kitco.com` 和 `bloomberg.com` 是另外的蓝色系
- 候选节点用浅色+无标签减少视觉干扰

**分析**:
- LLM考虑了4个候选，来自3个不同的网站
- 最终选择了 `goldprice.org` 的30年历史页面
- 可能的选择理由: 更长的历史数据 (30年 vs 默认)
- 同域名的其他页面也被考虑但未选择
- `kitco.com` 和 `bloomberg.com` 被认为是备选方案

## 🐛 故障排除

### 中文字符显示问题
忽略matplotlib的中文字体警告，图形仍然可用。

### 候选资源提取不准确
V2版本使用启发式方法从思考文本提取候选。如果提取不准确:
1. 检查思考文本格式
2. 添加更多关键词到 `financial_sites` 列表
3. 改进URL正则表达式

### 图形过于复杂
如果节点过多导致重叠:
1. 增加图形尺寸 (修改 `figsize` 参数)
2. 调整节点间距 (修改布局参数)
3. 分批分析日志文件

## 🔄 与其他工具的集成

V2版本可以与以下工具配合使用:

- **V1版本**: 对比简化图和详细图
- **Event Resource Graph**: 分析资源访问的时间序列
- **LLM Tool Usage Analyzer**: 分析工具使用模式

## 📄 许可

与 Gemini CLI 项目保持一致。

## 🙏 反馈

如果你发现V2版本的改进有用，或有进一步的建议，欢迎反馈！
```
