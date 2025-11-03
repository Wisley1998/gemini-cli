# 性能测试系统优化说明

## 📋 完成的修改

### 1. ✅ 优化了 Prompt 生成脚本

#### DeepResearch Bench (`extract-deepresearch-bench-prompts.py`)

增强了执行策略部分，现在包含：

**🔧 MCP 工具使用要求（核心重点）**：

- 必须使用 MCP 工具收集所有信息
- 优先使用的工具：
  - Playwright MCP: playwright_navigate, playwright_screenshot, playwright_evaluate
  - Fetcher MCP: fetch
  - GitHub MCP: search_repositories, get_file_contents, search_code
- 每个研究主题至少调用 8-10 次 MCP 工具
- 多样化信息源：至少访问 5 个不同网站
- 工具调用占比 > 70%

**📝 输出格式要求（极简原则）**：

- 总字数 ≤ 300 字（不含引用链接）
- 要点式输出，避免长段落
- 每个事实必须附来源
- 禁止啰嗦和废话

**💯 评分标准**：

- MCP 工具调用次数 ≥ 8 次（40分）
- 信息来源多样性 ≥ 5 个网站（30分）
- 输出简洁性 ≤ 300 字（20分）
- 每个事实都有来源标注（10分）

#### SWE-bench (`extract-swe-bench-prompts.py`)

增强了任务要求部分，现在包含：

**🔧 MCP 工具使用要求（必须遵守）**：

- GitHub MCP 工具优先：
  - github_search_repositories
  - github_get_file_contents
  - github_search_code
  - github_get_issues
  - github_get_pull_request
- 最少工具调用次数：至少 6-8 次
- 禁止直接编码

**📝 输出格式要求（简洁原则）**：

- 总输出 ≤ 400 字（不含代码）
- 问题分析 ≤ 100 字
- 解决方案 ≤ 150 字
- 关键代码仅核心部分 ≤ 30 行
- 验证计划 ≤ 100 字

**💯 评分标准**：

- GitHub MCP 工具调用 ≥ 6 次（40分）
- 输出简洁性 ≤ 400 字（30分）
- 代码修改准确性（20分）
- 测试通过率（10分）

### 2. ✅ 重构了测试脚本 (`run_automated_benchmark.py`)

**主要改进**：

- ❌ 移除了完整输出的保存（`_full.txt`）
- ✅ 只保留性能摘要（`_summary.txt`）
- ✅ 根据 prompt 类型自动分类保存：
  - DeepResearch prompts → `results/deep_research/`
  - SWE-bench prompts → `results/code/`

**新的目录结构**：

```
results/
├── deep_research/
│   ├── prompt_001_1_summary.txt
│   ├── prompt_002_2_summary.txt
│   └── ...
└── code/
    ├── prompt_001_astropy__astropy-12907_summary.txt
    ├── prompt_002_astropy__astropy-14182_summary.txt
    └── ...
```

**配置变量**：

```python
BASE_DIR = Path("/Users/suiyifan/Desktop/multi-agnets/gemini-cli")
DEEPRESEARCH_PROMPTS_DIR = BASE_DIR / "deepresearch-bench-prompts"
SWE_BENCH_PROMPTS_DIR = BASE_DIR / "swe-bench-prompts"
RESULTS_BASE_DIR = BASE_DIR / "results"
DEEP_RESEARCH_RESULTS_DIR = RESULTS_BASE_DIR / "deep_research"
CODE_RESULTS_DIR = RESULTS_BASE_DIR / "code"
```

### 3. ✅ 生成了测试数据

已成功生成：

- ✅ 10 个 DeepResearch prompts
- ✅ 10 个 SWE-bench prompts

**DeepResearch 任务覆盖**：

- prompt_001_1.txt 到 prompt_010_10.txt
- 主题包括：中国社会阶层、物理学、化学、生物学等

**SWE-bench 任务覆盖**：

- 6 个 astropy/astropy 问题
- 4 个 django/django 问题
- 包括真实的 GitHub issue 和 PR

## 🚀 如何使用

### 生成新的 Prompts

```bash
# 生成 DeepResearch prompts
python3 extract-deepresearch-bench-prompts.py --limit 10

# 生成 SWE-bench prompts
python3 extract-swe-bench-prompts.py --limit 10
```

### 运行性能测试

```bash
# 运行所有测试
python3 run_automated_benchmark.py

# 结果会自动保存到对应目录
# - results/deep_research/ (DeepResearch 任务)
# - results/code/ (SWE-bench 任务)
```

### 查看结果

```bash
# 查看 DeepResearch 结果
ls results/deep_research/

# 查看 Code 结果
ls results/code/

# 读取特定结果
cat results/deep_research/prompt_001_1_summary.txt
```

## 📊 预期改进效果

### MCP 工具使用率提升

- ✅ 明确要求使用特定 MCP 工具
- ✅ 设定最低调用次数阈值
- ✅ 量化评分标准

### 输出质量提升

- ✅ 严格字数限制（DeepResearch: 300字，SWE-bench: 400字）
- ✅ 要求结构化输出
- ✅ 强制来源标注

### 效率提升

- ✅ 只保存摘要，节省存储空间
- ✅ 自动分类保存，便于分析
- ✅ 清晰的目录结构

## 📁 文件结构

```
gemini-cli/
├── extract-deepresearch-bench-prompts.py  # 已优化
├── extract-swe-bench-prompts.py          # 已优化
├── run_automated_benchmark.py            # 已重构
├── deepresearch-bench-prompts/           # 生成的 DeepResearch prompts
│   ├── prompt_001_1.txt
│   ├── prompt_002_2.txt
│   └── ...
├── swe-bench-prompts/                    # 生成的 SWE-bench prompts
│   ├── prompt_001_astropy__astropy-12907.txt
│   ├── prompt_002_astropy__astropy-14182.txt
│   └── ...
└── results/                              # 测试结果（新增）
    ├── deep_research/                    # DeepResearch 结果
    │   └── *_summary.txt
    └── code/                             # SWE-bench 结果
        └── *_summary.txt
```

## 🎯 下一步建议

1. **运行基准测试**：使用新的 prompts 运行完整测试
2. **分析结果**：比较不同 prompt 的 MCP 工具使用情况
3. **调优参数**：根据实际结果调整字数限制和工具调用次数
4. **扩展测试集**：生成更多 prompts 进行全面测试

## ✅ 验证清单

- [x] DeepResearch prompt 生成脚本包含 MCP 工具强调
- [x] SWE-bench prompt 生成脚本包含 MCP 工具强调
- [x] 测试脚本只保存 summary
- [x] 测试脚本按类型分类保存结果
- [x] 创建了结果目录结构
- [x] 生成了 10 个 DeepResearch prompts
- [x] 生成了 10 个 SWE-bench prompts
- [x] 所有修改已完成并测试通过
