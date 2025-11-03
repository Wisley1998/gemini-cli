# 自动化测试系统使用指南

## 📋 系统概述

本系统提供了完整的自动化测试流程，支持两种类型的测试：

- **DeepResearch**: 深度研究任务测试
- **SWE-bench**: 代码修复任务测试

## 🚀 快速开始

### 1. 生成测试 Prompts

```bash
# 生成 10 个 DeepResearch 和 10 个 SWE-bench prompts
python3 generate_prompts.py --deepresearch 10 --swebench 10

# 清理旧文件并重新生成
python3 generate_prompts.py --clean --deepresearch 10 --swebench 10

# 自定义数量
python3 generate_prompts.py --deepresearch 20 --swebench 15
```

### 2. 验证 Prompts 格式

```bash
# 验证生成的 prompts 是否符合要求
python3 verify_prompts.py
```

### 3. 运行测试

#### 测试所有类型

```bash
python3 run_automated_benchmark.py --type all
```

#### 只测试 DeepResearch

```bash
python3 run_automated_benchmark.py --type deepresearch
```

#### 只测试 SWE-bench

```bash
python3 run_automated_benchmark.py --type swebench
```

#### 限制测试数量

```bash
# 测试前 3 个 DeepResearch prompts
python3 run_automated_benchmark.py --type deepresearch --limit 3

# 测试前 5 个 SWE-bench prompts
python3 run_automated_benchmark.py --type swebench --limit 5

# 快速测试：每种类型各 1 个
python3 run_automated_benchmark.py --type deepresearch --limit 1
python3 run_automated_benchmark.py --type swebench --limit 1
```

### 4. 查看结果

```bash
# 查看 DeepResearch 测试结果
ls -lh results/deep_research/
cat results/deep_research/prompt_001_1_summary.txt

# 查看 SWE-bench 测试结果
ls -lh results/code/
cat results/code/prompt_001_astropy__astropy-12907_summary.txt
```

## 📁 目录结构

```
gemini-cli/
├── generate_prompts.py              # 生成 prompts 的脚本
├── verify_prompts.py                # 验证 prompts 格式
├── run_automated_benchmark.py       # 运行自动化测试
├── test-benchmark-quick.sh          # 快速测试指南
├── extract-deepresearch-bench-prompts.py  # DeepResearch prompt 生成器
├── extract-swe-bench-prompts.py     # SWE-bench prompt 生成器
├── deepresearch-bench-prompts/      # DeepResearch prompts
│   ├── prompt_001_1.txt
│   ├── prompt_002_2.txt
│   └── ...
├── swe-bench-prompts/               # SWE-bench prompts
│   ├── prompt_001_astropy__astropy-12907.txt
│   ├── prompt_002_astropy__astropy-14182.txt
│   └── ...
└── results/                         # 测试结果
    ├── deep_research/               # DeepResearch 结果
    │   ├── prompt_001_1_summary.txt
    │   └── ...
    └── code/                        # SWE-bench 结果
        ├── prompt_001_astropy__astropy-12907_summary.txt
        └── ...
```

## 🔧 脚本详解

### generate_prompts.py

自动生成测试 prompts

**参数:**

- `--deepresearch N`: 生成 N 个 DeepResearch prompts (默认: 10)
- `--swebench N`: 生成 N 个 SWE-bench prompts (默认: 10)
- `--clean`: 清理旧的 prompt 文件

**示例:**

```bash
python3 generate_prompts.py --deepresearch 15 --swebench 20 --clean
```

### verify_prompts.py

验证生成的 prompts 格式

**检查项:**

- 换行数（应为 0，确保单段式）
- 引号数（应为 0）
- 字符长度
- 是否包含问题描述原文（SWE-bench 应该不包含）

**示例:**

```bash
python3 verify_prompts.py
```

### run_automated_benchmark.py

运行自动化性能测试

**参数:**

- `--type {all|deepresearch|swebench}`: 测试类型 (默认: all)
- `--limit N`: 限制测试数量 (默认: 全部)

**示例:**

```bash
# 测试所有
python3 run_automated_benchmark.py

# 只测试 DeepResearch 前 5 个
python3 run_automated_benchmark.py --type deepresearch --limit 5

# 只测试 SWE-bench
python3 run_automated_benchmark.py --type swebench
```

### test-benchmark-quick.sh

交互式测试指南

**功能:**

- 显示所有使用示例
- 显示当前可用的 prompts
- 可选择运行快速测试

**示例:**

```bash
./test-benchmark-quick.sh
```

## 📝 Prompt 格式

### DeepResearch Prompt

```
DeepResearch Bench 任务 #X - 任务 ID: X - 领域: XXX. 研究目标: XXX. 🔧 MCP 工具使用要求（核心重点）：1. 必须使用 MCP 工具收集所有信息，严禁编造或凭记忆生成内容 2. 优先使用工具列表：Playwright MCP, Fetcher MCP, GitHub MCP. 📝 输出格式要求（极简原则）：1. 要点式输出：使用短句和列表，避免长段落 2. 禁止啰嗦：直接给出结论，不要过渡语和废话
```

### SWE-bench Prompt

```
SWE-bench 任务 #X - 任务 ID: XXX - GitHub 仓库: XXX - Issue链接: https://github.com/XXX/issues/XXX - 基础提交: XXX. 需要通过的测试: XXX. 🔧 MCP 工具使用要求（核心重点）：1. 必须使用 MCP 工具收集所有信息，严禁编造或凭记忆生成内容 2. 优先使用工具列表：Playwright MCP, Fetcher MCP, GitHub MCP. 📝 输出格式要求（极简原则）：1. 要点式输出：使用短句和列表，避免长段落 2. 禁止啰嗦：直接给出结论，不要过渡语和废话
```

**格式特点:**

- ✅ 单段式，无换行
- ✅ 无引号（" 和 '）
- ✅ 无分隔符（=== 和 ━━━）
- ✅ SWE-bench 只提供 Issue 链接，不包含问题描述原文

## 📊 测试结果

测试结果保存在 `results/` 目录下：

- `deep_research/`: DeepResearch 测试结果
- `code/`: SWE-bench 测试结果

每个结果文件包含：

- Prompt 文件名
- Prompt 类型
- 测试时间
- 性能统计数据（工具调用次数、token 使用等）

## 🎯 典型工作流程

### 完整测试流程

```bash
# 1. 生成 prompts
python3 generate_prompts.py --deepresearch 10 --swebench 10 --clean

# 2. 验证格式
python3 verify_prompts.py

# 3. 运行测试
python3 run_automated_benchmark.py --type all

# 4. 查看结果
ls -lh results/deep_research/
ls -lh results/code/
```

### 快速验证流程

```bash
# 1. 生成少量 prompts
python3 generate_prompts.py --deepresearch 2 --swebench 2 --clean

# 2. 快速测试
python3 run_automated_benchmark.py --type deepresearch --limit 1
python3 run_automated_benchmark.py --type swebench --limit 1

# 3. 查看结果
cat results/deep_research/prompt_001_1_summary.txt
cat results/code/prompt_001_*_summary.txt
```

### 单独测试某一类型

```bash
# 只测试 DeepResearch
python3 generate_prompts.py --deepresearch 5 --swebench 0
python3 run_automated_benchmark.py --type deepresearch

# 只测试 SWE-bench
python3 generate_prompts.py --deepresearch 0 --swebench 5
python3 run_automated_benchmark.py --type swebench
```

## 💡 提示与技巧

1. **首次使用**: 运行 `./test-benchmark-quick.sh` 查看完整指南
2. **快速测试**: 使用 `--limit 1` 进行单个测试验证
3. **分批测试**: 可以分别测试 DeepResearch 和 SWE-bench
4. **查看帮助**: 使用 `--help` 查看所有选项

## ⚠️ 注意事项

1. 确保已安装所需依赖：`pexpect`, `datasets`
2. 测试时间较长，建议先用 `--limit` 测试少量样本
3. 结果文件只保存性能摘要，不保存完整输出
4. 每次运行会覆盖同名的结果文件

## 🔗 相关文档

- [BENCHMARK_OPTIMIZATION.md](BENCHMARK_OPTIMIZATION.md) - 优化说明
- [PROMPT_FORMAT_UPDATE.md](PROMPT_FORMAT_UPDATE.md) - Prompt 格式更新说明
