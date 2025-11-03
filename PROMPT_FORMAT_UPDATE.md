# Prompt 格式优化说明

## ✅ 完成的修改

### 主要改进

1. **移除所有分隔线**：删除了 `===` 和 `━━━` 等分隔符
2. **一段式输出**：所有内容合并为一个连续段落，无换行
3. **简化要求部分**：只保留最核心的 MCP 工具和输出格式要求

### 新的 Prompt 格式

#### DeepResearch Bench Prompt

```
DeepResearch Bench 任务 #X - 任务 ID: X - 领域: XXX. 研究目标: XXX. 🔧 MCP 工具使用要求（核心重点）：1. **必须使用 MCP 工具收集所有信息**，严禁编造或凭记忆生成内容 2. **优先使用工具列表**：Playwright MCP, Fetcher MCP, GitHub MCP. 📝 输出格式要求（极简原则）：1. **要点式输出**：使用短句和列表，避免长段落 2. **禁止啰嗦**：直接给出结论，不要过渡语和废话
```

#### SWE-bench Prompt

```
SWE-bench 任务 #X - 任务 ID: XXX - GitHub 仓库: XXX (链接) - 基础提交: XXX. 问题描述: [完整问题描述，所有换行都被压缩成空格] 需要通过的测试: XXX. 🔧 MCP 工具使用要求（核心重点）：1. **必须使用 MCP 工具收集所有信息**，严禁编造或凭记忆生成内容 2. **优先使用工具列表**：Playwright MCP, Fetcher MCP, GitHub MCP. 📝 输出格式要求（极简原则）：1. **要点式输出**：使用短句和列表，避免长段落 2. **禁止啰嗦**：直接给出结论，不要过渡语和废话
```

### 技术实现

#### extract-deepresearch-bench-prompts.py

```python
# 构建一段式 prompt - 无分隔符
research_prompt = f"""DeepResearch Bench 任务 #{task_number} - 任务 ID: {task_id} - 领域: {topic}. 研究目标: {prompt}. 🔧 MCP 工具使用要求（核心重点）：1. **必须使用 MCP 工具收集所有信息**，严禁编造或凭记忆生成内容 2. **优先使用工具列表**：Playwright MCP, Fetcher MCP, GitHub MCP. 📝 输出格式要求（极简原则）：1. **要点式输出**：使用短句和列表，避免长段落 2. **禁止啰嗦**：直接给出结论，不要过渡语和废话"""
```

#### extract-swe-bench-prompts.py

```python
# 将问题描述压缩成一行，去掉所有换行
problem_statement = ' '.join(problem_statement.split())

# 构建一段式 prompt，无分隔符，无换行
prompt = f"""SWE-bench 任务 #{task_number} - 任务 ID: {instance_id} - GitHub 仓库: {repo} ({issue_pr_link}) - 基础提交: {base_commit}. 问题描述: {problem_statement} 需要通过的测试: {fail_tests}. 🔧 MCP 工具使用要求（核心重点）：1. **必须使用 MCP 工具收集所有信息**，严禁编造或凭记忆生成内容 2. **优先使用工具列表**：Playwright MCP, Fetcher MCP, GitHub MCP. 📝 输出格式要求（极简原则）：1. **要点式输出**：使用短句和列表，避免长段落 2. **禁止啰嗦**：直接给出结论，不要过渡语和废话"""
```

### 优势

1. **无分段问题**：Gemini 不会因为分段而产生理解偏差
2. **更简洁**：去掉了冗余的格式化元素
3. **专注核心**：只保留最重要的 MCP 工具要求和输出格式要求
4. **一致性好**：两种类型的 prompt 格式统一

### 文件示例

#### prompt_001_1.txt (DeepResearch)

```
DeepResearch Bench 任务 #1 - 任务 ID: 1 - 领域: 通用研究 (General Research). 研究目标: 收集整理目前中国9阶层实际收入和财务状况，特别研究得出中国的中产有哪些特点，实际中产人数，财力等等. 🔧 MCP 工具使用要求（核心重点）：1. **必须使用 MCP 工具收集所有信息**，严禁编造或凭记忆生成内容 2. **优先使用工具列表**：Playwright MCP, Fetcher MCP, GitHub MCP. 📝 输出格式要求（极简原则）：1. **要点式输出**：使用短句和列表，避免长段落 2. **禁止啰嗦**：直接给出结论，不要过渡语和废话
```

#### prompt_001_astropy\_\_astropy-12907.txt (SWE-bench)

所有代码块和换行都被压缩到一行，便于 Gemini 处理。

### 已生成文件

✅ 10 个 DeepResearch prompts (deepresearch-bench-prompts/)
✅ 10 个 SWE-bench prompts (swe-bench-prompts/)

所有 prompts 都已按照新格式重新生成！
