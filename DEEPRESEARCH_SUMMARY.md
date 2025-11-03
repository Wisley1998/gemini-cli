# DeepResearch Bench 集成总结

## ✅ 已创建的文件

### 1. 核心脚本

#### `extract-deepresearch-bench-prompts.py`

**用途**: 从 DeepResearch Bench 下载并提取研究任务 prompt

**功能**:

- 自动从 GitHub 下载任务数据（100 个研究任务）
- 将每个任务格式化为独立的 prompt 文件
- 生成任务索引和说明文档

**使用方法**:

```bash
# 提取前 5 个任务（测试）
python extract-deepresearch-bench-prompts.py --limit 5

# 提取所有 100 个任务
python extract-deepresearch-bench-prompts.py

# 自定义输出目录
python extract-deepresearch-bench-prompts.py --output-dir ./my-tasks
```

**输出**:

- `deepresearch-bench-prompts/prompt_001_*.txt` - 任务 prompt 文件
- `deepresearch-bench-prompts/INDEX.md` - 任务索引
- `deepresearch-bench-prompts/README.md` - 使用说明
- `deepresearch-bench-prompts/query.jsonl` - 原始数据

---

#### `run-deepresearch-bench.sh`

**用途**: 批量执行 DeepResearch Bench 任务

**功能**:

- 自动扫描并执行所有或指定数量的任务
- 保存研究报告和日志
- 显示执行进度和统计

**使用方法**:

```bash
# 赋予执行权限
chmod +x run-deepresearch-bench.sh

# 运行前 5 个任务
./run-deepresearch-bench.sh --limit 5

# 使用特定模型
./run-deepresearch-bench.sh --model gemini-2.5-pro --limit 3

# 演习模式（不实际执行）
./run-deepresearch-bench.sh --dry-run

# 详细输出
./run-deepresearch-bench.sh --verbose --limit 10
```

**输出**:

- `deepresearch-bench-results/result_001_*.md` - 研究报告
- `deepresearch-bench-results/log_001_*.txt` - 执行日志

---

### 2. 文档

#### `DEEPRESEARCH_QUICK_START.md`

**用途**: 快速开始指南

**内容**:

- DeepResearch Bench 简介
- 完整的使用流程（提取、查看、执行）
- 实用技巧和常见问题
- 报告结构建议

**适合**:

- 首次使用者
- 需要快速上手的用户

---

## 📋 完整工作流程

### 第一步：提取任务

```bash
# 提取少量任务测试
python extract-deepresearch-bench-prompts.py --limit 5
```

**生成的文件**:

```
deepresearch-bench-prompts/
├── prompt_001_1.txt          # 任务 1
├── prompt_002_2.txt          # 任务 2
├── prompt_003_3.txt          # 任务 3
├── ...
├── INDEX.md                  # 任务列表和索引
├── README.md                 # 说明文档
└── query.jsonl               # 原始数据（从 GitHub 下载）
```

### 第二步：查看任务

```bash
# 查看所有任务的索引
cat deepresearch-bench-prompts/INDEX.md

# 查看具体某个任务
cat deepresearch-bench-prompts/prompt_001_*.txt
```

**任务 prompt 格式**:

```
================================================================================
DeepResearch Bench 任务 #1
================================================================================

任务 ID: 1
领域: [自动识别的领域]
来源: DeepResearch Bench

================================================================================
研究任务
================================================================================

[具体的研究问题...]

================================================================================
任务要求
================================================================================

请完成一份全面的深度研究报告，要求：
1. 全面性
2. 深度
3. 准确性
4. 可读性

[建议的报告结构...]
```

### 第三步：执行任务

**方式 A: 单个任务**

```bash
# 直接执行
gemini --prompt "$(cat deepresearch-bench-prompts/prompt_001_*.txt)"

# 保存到文件
gemini --prompt "$(cat deepresearch-bench-prompts/prompt_001_*.txt)" > my-report.md
```

**方式 B: 批量执行**

```bash
# 执行多个任务
./run-deepresearch-bench.sh --limit 5
```

**生成的结果**:

```
deepresearch-bench-results/
├── result_001_task_xxx.md    # 研究报告 1
├── result_002_task_xxx.md    # 研究报告 2
├── log_001_task_xxx.txt      # 执行日志 1
├── log_002_task_xxx.txt      # 执行日志 2
└── ...
```

---

## 🎯 与 SWE-bench 的对比

| 特性            | SWE-bench                      | DeepResearch Bench                      |
| --------------- | ------------------------------ | --------------------------------------- |
| **任务类型**    | 软件工程（修复 bug）           | 深度研究                                |
| **任务数量**    | 数千个                         | 100 个                                  |
| **领域**        | 编程                           | 22 个不同领域                           |
| **难度**        | 工程实现                       | PhD 级别研究                            |
| **输出**        | 代码补丁                       | 研究报告                                |
| **评估**        | 测试通过率                     | RACE + FACT 框架                        |
| **提取脚本**    | `extract-swe-bench-prompts.py` | `extract-deepresearch-bench-prompts.py` |
| **执行脚本**    | `run-swe-bench-v2.sh`          | `run-deepresearch-bench.sh`             |
| **Prompt 目录** | `swe-bench-prompts/`           | `deepresearch-bench-prompts/`           |

---

## 💡 使用建议

### 1. 从小规模开始

```bash
# 先提取 3-5 个任务测试
python extract-deepresearch-bench-prompts.py --limit 5

# 执行 1 个任务看看效果
gemini --prompt "$(cat deepresearch-bench-prompts/prompt_001_*.txt)"
```

### 2. 选择感兴趣的领域

```bash
# 查看所有任务的领域分类
cat deepresearch-bench-prompts/INDEX.md

# 根据兴趣选择任务执行
```

### 3. 利用 MCP 工具

在执行研究任务时，gemini-cli 会自动使用可用的 MCP 工具：

- `fetch_webpage` - 获取网页内容
- `mcp_microsoft_doc_microsoft_docs_search` - 搜索 Microsoft 文档
- 其他搜索和文档工具

### 4. 批量处理策略

```bash
# 分批执行，避免一次性处理太多
./run-deepresearch-bench.sh --limit 10  # 第一批
./run-deepresearch-bench.sh --limit 20  # 累计 20 个
```

---

## 📊 DeepResearch Bench 评估标准（仅供参考）

虽然您只需要任务 prompt，但了解评估标准有助于写出更好的研究报告：

### RACE 框架（报告质量）

- **全面性**: 覆盖主题的广度和深度
- **洞察力**: 分析质量和独特见解
- **指令遵循**: 满足任务要求
- **可读性**: 结构清晰、表达专业

### FACT 框架（引用质量）

- **引用准确性**: 引用源真实支持所述内容
- **有效引用数**: 可靠引用的数量

---

## 🔗 相关资源

- **DeepResearch Bench**: https://github.com/Ayanami0730/deep_research_bench
- **论文**: https://arxiv.org/abs/2506.11763
- **排行榜**: https://huggingface.co/spaces/Ayanami0730/DeepResearch-Leaderboard
- **项目网站**: https://deepresearch-bench.github.io/

---

## 📝 快速开始命令

```bash
# 1. 提取 5 个任务
python extract-deepresearch-bench-prompts.py --limit 5

# 2. 查看任务列表
cat deepresearch-bench-prompts/INDEX.md

# 3. 执行第一个任务
gemini --prompt "$(cat deepresearch-bench-prompts/prompt_001_*.txt)"

# 或批量执行
chmod +x run-deepresearch-bench.sh
./run-deepresearch-bench.sh --limit 5
```

---

## ❓ 常见问题

**Q: 任务数据从哪里来？**  
A: 自动从 DeepResearch Bench 的 GitHub 仓库下载（100 个任务的 JSONL 文件）

**Q: 可以只提取特定领域的任务吗？**  
A: 目前按顺序提取，但提取后可以通过 `INDEX.md` 查看并选择感兴趣的任务

**Q: 如何查看已经执行了哪些任务？**  
A: 查看 `deepresearch-bench-results/` 目录中的文件

**Q: 执行失败怎么办？**  
A: 查看对应的 `log_*.txt` 文件，检查错误信息

**Q: 可以自定义 prompt 格式吗？**  
A: 可以！编辑 `extract-deepresearch-bench-prompts.py` 中的 `format_research_task_prompt` 函数

---

## ✨ 总结

现在您拥有完整的 DeepResearch Bench 集成：

✅ **提取脚本** - 下载并格式化 100 个研究任务  
✅ **执行脚本** - 批量运行任务并保存结果  
✅ **文档** - 完整的使用指南  
✅ **简洁的 Prompt** - 专注于任务本身，无评估相关内容

开始您的深度研究之旅吧！🚀
