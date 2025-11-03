# DeepResearch Bench 快速开始

使用 gemini-cli 完成 DeepResearch Bench 研究任务的简明指南。

## 🎯 什么是 DeepResearch Bench?

DeepResearch Bench 是一个包含 100 个 PhD 级别研究任务的基准测试，涵盖 22 个领域：

- 🔬 科学技术（物理、化学、生物、工程等）
- 💼 金融商业（投资、市场营销等）
- 💻 软件技术
- 🌍 其他领域（艺术、历史、旅游等）

官方资源：

- 📚 [论文](https://arxiv.org/abs/2506.11763)
- 💻 [GitHub](https://github.com/Ayanami0730/deep_research_bench)
- 🏆 [排行榜](https://huggingface.co/spaces/Ayanami0730/DeepResearch-Leaderboard)

## 📥 步骤 1: 提取任务

```bash
# 提取前 5 个任务（测试）
python extract-deepresearch-bench-prompts.py --limit 5

# 提取所有 100 个任务
python extract-deepresearch-bench-prompts.py

# 自定义输出目录
python extract-deepresearch-bench-prompts.py --output-dir ./my-prompts --limit 10
```

这将创建 `deepresearch-bench-prompts/` 目录，包含：

```
deepresearch-bench-prompts/
├── prompt_001_task_xxx.txt    # 任务 1
├── prompt_002_task_xxx.txt    # 任务 2
├── ...
├── INDEX.md                   # 任务索引
├── README.md                  # 说明文档
└── query.jsonl                # 原始数据
```

## 🔍 步骤 2: 查看任务

```bash
# 查看任务列表
cat deepresearch-bench-prompts/INDEX.md

# 查看某个具体任务
cat deepresearch-bench-prompts/prompt_001_*.txt

# 查看前 20 行
head -20 deepresearch-bench-prompts/prompt_001_*.txt
```

## 🚀 步骤 3: 执行任务

### 方法 A: 单个任务（推荐开始时使用）

```bash
# 直接执行并保存结果
gemini --prompt "$(cat deepresearch-bench-prompts/prompt_001_*.txt)" \
    > my-research-report.md

# 或者在交互模式中执行
gemini
# 然后粘贴任务内容
```

### 方法 B: 批量执行

```bash
# 赋予脚本执行权限
chmod +x run-deepresearch-bench.sh

# 运行前 5 个任务
./run-deepresearch-bench.sh --limit 5

# 使用特定模型
./run-deepresearch-bench.sh --model gemini-2.5-pro --limit 3

# 查看将要执行的命令（演习模式）
./run-deepresearch-bench.sh --dry-run --limit 10

# 运行所有任务
./run-deepresearch-bench.sh
```

批量执行的结果保存在 `deepresearch-bench-results/` 目录：

```
deepresearch-bench-results/
├── result_001_task_xxx.md     # 研究报告 1
├── result_002_task_xxx.md     # 研究报告 2
├── log_001_task_xxx.txt       # 日志 1
├── log_002_task_xxx.txt       # 日志 2
└── ...
```

## 📊 任务示例

提取的任务 prompt 格式如下：

```
================================================================================
DeepResearch Bench 任务 #1
================================================================================

任务 ID: task_001
领域: 物理学 (Physics)
来源: DeepResearch Bench

================================================================================
研究任务
================================================================================

[具体的研究问题描述...]

================================================================================
任务要求
================================================================================

请完成一份全面的深度研究报告，要求：

1. 📚 全面性：充分覆盖主题的各个重要方面
2. 🔍 深度：提供深入的分析和有价值的洞察
3. 📋 准确性：所有事实性陈述需要可靠来源支持
4. 📖 可读性：清晰的结构、逻辑连贯的论述

建议报告结构：
- 执行摘要
- 背景介绍
- 主要内容（分节论述）
- 关键发现
- 结论
- 参考文献
```

## 💡 使用技巧

### 1. 利用 MCP 工具

在执行研究任务时，gemini-cli 可以使用各种 MCP 工具：

- **fetch_webpage**: 获取网页内容
- **搜索工具**: 查找相关资料
- **文档工具**: 访问官方文档
- **文件操作**: 保存中间结果

### 2. 优化研究流程

```bash
# 阶段 1: 理解任务
gemini --prompt "请分析这个研究任务的核心问题和关键概念：
$(cat deepresearch-bench-prompts/prompt_001_*.txt)"

# 阶段 2: 信息收集
# 让 AI 使用 MCP 工具搜索和收集信息

# 阶段 3: 完整报告
# 生成完整的研究报告
```

### 3. 分批处理

如果任务较多，建议分批处理：

```bash
# 第一批：前 10 个
./run-deepresearch-bench.sh --limit 10

# 第二批：11-20
# 手动选择任务或修改脚本
```

## 📖 报告结构建议

一份优秀的研究报告应包含：

```markdown
# [研究主题]

## 执行摘要

- 研究背景
- 主要发现
- 关键结论

## 背景介绍

- 主题背景
- 为什么重要
- 研究范围

## 主要内容

### 方面 1

[详细分析]

### 方面 2

[详细分析]

### 方面 3

[详细分析]

## 关键发现

- 发现 1
- 发现 2
- 发现 3

## 结论

- 总结
- 启示
- 建议

## 参考文献

[1] 来源标题 - URL
[2] 来源标题 - URL
...
```

## ⚙️ 脚本选项

### extract-deepresearch-bench-prompts.py

```bash
--limit N              # 提取前 N 个任务
--output-dir DIR       # 输出目录（默认: ./deepresearch-bench-prompts）
--data-file FILE       # 使用本地数据文件
--data-url URL         # 从 URL 下载数据
```

### run-deepresearch-bench.sh

```bash
-h, --help             # 显示帮助
-l, --limit N          # 运行前 N 个任务
-p, --prompts-dir DIR  # prompt 目录
-r, --results-dir DIR  # 结果目录
-m, --model MODEL      # 指定模型
-v, --verbose          # 详细输出
-d, --dry-run          # 演习模式
--gemini-cmd CMD       # gemini 命令路径
```

## ❓ 常见问题

### Q: 任务太多，从哪里开始？

**A**: 先提取 5 个任务测试：

```bash
python extract-deepresearch-bench-prompts.py --limit 5
# 查看任务，选择感兴趣的领域
cat deepresearch-bench-prompts/INDEX.md
```

### Q: 如何选择感兴趣的任务？

**A**: 查看 INDEX.md，它按领域分类了所有任务：

```bash
cat deepresearch-bench-prompts/INDEX.md | grep "Physics\|化学\|软件"
```

### Q: 执行失败怎么办？

**A**: 查看日志文件：

```bash
cat deepresearch-bench-results/log_001_*.txt
# 常见问题：API 限流、网络问题、Token 超限
```

### Q: 可以自定义 prompt 吗？

**A**: 可以！修改生成的 txt 文件或直接编辑 `extract-deepresearch-bench-prompts.py` 中的 `format_research_task_prompt` 函数。

### Q: 如何查看已完成的任务？

**A**: 查看结果目录：

```bash
ls -lh deepresearch-bench-results/result_*.md
# 或
find deepresearch-bench-results -name "result_*.md" -exec wc -w {} \; | sort -n
```

## 🔗 相关资源

- [DeepResearch Bench GitHub](https://github.com/Ayanami0730/deep_research_bench)
- [论文](https://arxiv.org/abs/2506.11763)
- [排行榜](https://huggingface.co/spaces/Ayanami0730/DeepResearch-Leaderboard)
- [项目网站](https://deepresearch-bench.github.io/)

## 📝 下一步

1. **提取你的第一个任务**

   ```bash
   python extract-deepresearch-bench-prompts.py --limit 1
   ```

2. **执行它**

   ```bash
   gemini --prompt "$(cat deepresearch-bench-prompts/prompt_001_*.txt)"
   ```

3. **查看更多任务**

   ```bash
   python extract-deepresearch-bench-prompts.py --limit 10
   cat deepresearch-bench-prompts/INDEX.md
   ```

4. **批量执行**
   ```bash
   ./run-deepresearch-bench.sh --limit 5
   ```

祝研究顺利！🎉
