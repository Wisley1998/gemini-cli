# Gemini CLI 自动化性能测试

## 功能说明

这个自动化测试脚本会:

1. 从 `deepresearch-bench-prompts` 目录读取所有 prompt 文件
2. 对每个 prompt 自动启动 `gemini --yolo`
3. 自动输入 prompt 并等待完成(超时3分钟)
4. 自动发送 `/quit` 命令优雅退出
5. 提取完整的性能统计信息并保存到 `benchmark_results.txt`

## 使用方法

### 方法一: 直接运行 Python 脚本

```bash
python3 run_automated_benchmark.py
```

或者:

```bash
./run_automated_benchmark.py
```

### 方法二: 指定特定的 prompt 目录

编辑 `run_automated_benchmark.py` 文件,修改以下配置:

```python
PROMPTS_DIR = Path("/path/to/your/prompts")
OUTPUT_FILE = Path("/path/to/output.txt")
TIMEOUT_SECONDS = 180  # 修改超时时间(秒)
```

## 输出结果

测试结果会保存在 `benchmark_results.txt` 文件中,格式如下:

```
================================================================================
Prompt 文件: prompt_001_1.txt
测试时间: 2025-10-16 14:30:00
================================================================================

Performance
Wall Time:                  1m 40s
Agent Active:               1m 30s
  » API Time:               58.0s (64.3%)
    • gemini-2.5-flash:     58.0s (100.0%)
  » Tool Time:              32.2s (35.7%)
    ...

================================================================================
Prompt 文件: prompt_002_2.txt
测试时间: 2025-10-16 14:35:00
================================================================================

Performance
...
```

## 注意事项

1. **超时设置**: 默认每个 prompt 超时时间为 3 分钟,可以根据需要调整
2. **中断测试**: 按 Ctrl+C 可以随时中断测试
3. **实时输出**: 脚本会实时显示 gemini 的输出,方便监控进度
4. **失败处理**: 如果某个 prompt 测试失败,脚本会继续测试下一个
5. **结果追加**: 每次运行会创建新的结果文件(覆盖旧文件)

## 配置选项

在 `run_automated_benchmark.py` 中可以修改以下配置:

```python
# Prompt 文件目录
PROMPTS_DIR = Path("/Users/suiyifan/Desktop/multi-agnets/gemini-cli/deepresearch-bench-prompts")

# 结果输出文件
OUTPUT_FILE = Path("/Users/suiyifan/Desktop/multi-agnets/gemini-cli/benchmark_results.txt")

# 超时时间(秒)
TIMEOUT_SECONDS = 180

# Gemini 命令
GEMINI_CMD = "gemini"
GEMINI_ARGS = ["--yolo"]
```

## 示例

运行测试:

```bash
cd /Users/suiyifan/Desktop/multi-agnets/gemini-cli
python3 run_automated_benchmark.py
```

查看结果:

```bash
cat benchmark_results.txt
```

或者用你喜欢的编辑器打开:

```bash
code benchmark_results.txt
# 或
open benchmark_results.txt
```

## 故障排除

### 问题: 脚本无法启动 gemini

**解决**: 确保 gemini 命令在 PATH 中可用:

```bash
which gemini
```

### 问题: 提取不到 Performance 数据

**原因**: gemini 输出格式可能有变化

**解决**: 检查 `extract_performance_stats` 函数中的正则表达式

### 问题: 超时时间不够

**解决**: 增加 `TIMEOUT_SECONDS` 的值

### 问题: 想要测试单个 prompt

**解决**: 可以临时移动其他 prompt 文件到别的目录,或者修改 `get_prompt_files()` 函数来过滤特定文件
