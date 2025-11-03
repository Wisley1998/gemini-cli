# Gemini CLI 性能测试结果说明

## 文件结构

批量测试运行后会生成以下文件:

### 1. 汇总文件

- **benchmark_results.txt** - 所有测试的索引和状态汇总

### 2. 单个任务的完整输出

每个prompt会生成一个完整输出文件:

- **benchmark_output_prompt_XXX_full.txt** - 包含完整的gemini运行日志(已清理ANSI码)
- 文件大小: ~200-500KB
- 包含: 启动信息、任务执行过程、工具调用、最终输出、性能统计等

### 3. 单个任务的性能摘要 ⭐

每个prompt会生成一个精简的性能摘要:

- **benchmark_output_prompt_XXX_summary.txt** - 仅包含性能统计部分
- 文件大小: ~3-10KB (压缩了95-98%)
- 包含:
  - Interaction Summary (会话摘要)
  - Performance (性能指标)
    - Wall Time (总时间)
    - Agent Active (活跃时间)
    - API Time (API调用时间)
    - Tool Time (工具执行时间)
  - Detailed Timing Breakdown (详细时间分解)
    - 各个MCP服务器的连接和发现时间
  - Model Usage (模型使用统计)
    - Token使用量
    - 缓存节省

## 快速查看结果

### 查看单个任务的性能

```bash
cat benchmark_output_prompt_001_1_summary.txt
```

### 查看所有任务的索引

```bash
cat benchmark_results.txt
```

### 对比多个任务的Wall Time

```bash
grep "Wall Time:" benchmark_output_*_summary.txt
```

### 统计平均性能

```bash
grep "Wall Time:" benchmark_output_*_summary.txt | \
  awk '{print $3}' | \
  sed 's/s//' | \
  awk '{sum+=$1; count++} END {print "平均时间:", sum/count, "秒"}'
```

## 运行测试

### 测试单个prompt (调试用)

```bash
python3 test_single_benchmark.py
```

生成文件:

- test_output_raw.txt (原始输出)
- test_output.txt (清理后完整输出)
- test_output_summary.txt (性能摘要)

### 批量测试所有prompts

```bash
python3 run_automated_benchmark.py
```

自动处理 `deepresearch-bench-prompts/` 目录下的所有 `prompt_*.txt` 文件

## 文件命名规则

文件名中的 `prompt_XXX` 对应源prompt文件名,例如:

- 源文件: `deepresearch-bench-prompts/prompt_001_1.txt`
- 完整输出: `benchmark_output_prompt_001_1_full.txt`
- 性能摘要: `benchmark_output_prompt_001_1_summary.txt`

## 性能指标说明

### 关键时间指标

- **Wall Time**: 从开始到结束的总时间(包括空闲等待)
- **Agent Active**: Agent实际工作的时间
- **API Time**: 调用Gemini API的时间
- **Tool Time**: 执行工具(如MCP服务)的时间
- **MCP Init**: MCP服务器初始化时间

### 效率分析

- **API Time占比**: 反映模型调用效率
- **Tool Time占比**: 反映工具执行效率
- **MCP服务器时间**: 可以找出最慢的服务来优化

### Token使用

- **Input Tokens**: 输入token数量
- **Output Tokens**: 输出token数量
- **Cache Savings**: 缓存节省的token(降低成本)

## 推荐工作流

1. **运行批量测试**

   ```bash
   python3 run_automated_benchmark.py
   ```

2. **查看汇总**

   ```bash
   cat benchmark_results.txt
   ```

3. **查看感兴趣的任务性能**

   ```bash
   cat benchmark_output_prompt_001_1_summary.txt
   ```

4. **如需调试,查看完整输出**
   ```bash
   cat benchmark_output_prompt_001_1_full.txt
   ```

## 清理旧结果

```bash
# 删除所有测试结果
rm -f benchmark_output_*.txt benchmark_results.txt

# 只删除完整输出,保留摘要
rm -f benchmark_output_*_full.txt
```

## 故障排查

如果某个测试失败:

1. 查看 `benchmark_results.txt` 中的错误信息
2. 单独运行该prompt:
   ```bash
   # 修改 test_single_benchmark.py 中的 test_prompt 变量
   python3 test_single_benchmark.py
   ```
3. 查看 `test_output.txt` 获取详细日志

## 性能优化建议

根据测试结果,可以优化:

- 如果 **MCP Init** 时间长 → 考虑禁用不需要的MCP服务
- 如果 **API Time** 占比高 → 考虑优化prompt或使用更快的模型
- 如果 **Tool Time** 占比高 → 检查工具调用是否必要
- 如果 **Cache未命中** → 考虑调整上下文以提高缓存命中率
