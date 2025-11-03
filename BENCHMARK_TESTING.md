# 测试和调试说明

## 快速测试

在运行完整的基准测试之前,建议先运行单个测试来验证配置:

```bash
# 运行单个简单测试
python3 test_single_benchmark.py
```

这个测试脚本会:

1. 启动 `gemini --yolo`
2. 发送一个简单的计算问题 "计算 123 + 456"
3. 等待 5 秒
4. 发送 `/quit` 命令退出
5. 显示完整输出和提取的性能统计

## 检查点

运行测试时,检查以下内容:

### ✓ 成功的标志

- 看到 "Interaction Summary" 输出
- 看到 "Performance" 部分
- 看到 "Wall Time", "Agent Active" 等指标
- 提取的性能统计不为空

### ✗ 可能的问题

**问题 1: 未找到性能统计**

- 原因: `/quit` 命令可能没有正确发送
- 解决: 检查终端输出,看是否有 "Agent powering down" 消息

**问题 2: 进程超时**

- 原因: gemini 可能还在等待输入
- 解决: 增加 `/quit` 前的等待时间

**问题 3: 输出被截断**

- 原因: communicate() 超时太短
- 解决: 增加 `communicate(timeout=10)` 的超时值

## 调试步骤

### 1. 手动测试 /quit 命令

在终端中手动运行:

```bash
gemini --yolo
# 输入一个问题
计算 1+1
# 等待回答
# 输入 /quit
/quit
# 观察是否输出性能统计
```

### 2. 检查输出格式

运行测试脚本后,查看 "完整输出" 部分:

```bash
python3 test_single_benchmark.py | tee test_output.log
```

查看输出日志:

```bash
cat test_output.log
```

### 3. 调整提取逻辑

如果性能统计的格式有变化,修改 `extract_performance_stats()` 函数中的正则表达式。

当前支持的模式:

- 优先查找 "Interaction Summary"
- 备选查找 "Performance"
- 最后查找 "Wall Time"

## 运行完整基准测试

确认单个测试成功后,再运行完整测试:

```bash
python3 run_automated_benchmark.py
```

## 实时监控

在另一个终端窗口中实时查看结果:

```bash
tail -f benchmark_results.txt
```

## 中断和恢复

如果需要中断测试:

1. 按 `Ctrl+C` 停止脚本
2. 检查 `benchmark_results.txt` 查看已完成的测试
3. 可以手动移除已测试的 prompt 文件或修改脚本跳过它们

## 常见问题

**Q: 为什么改用 /quit 而不是 Ctrl+C?**

A: 因为:

1. `/quit` 是 gemini 的内置命令,会触发正常的退出流程
2. Ctrl+C (SIGINT) 可能会中断进程,不保证输出统计信息
3. `/quit` 更可靠,能确保输出完整的性能报告

**Q: 为什么需要等待时间?**

A:

- `time.sleep(2)`: 等待 gemini 启动完成
- `time.sleep(5)`: 等待 gemini 处理 prompt (可根据任务复杂度调整)
- `time.sleep(2)`: 等待 gemini 输出性能统计

**Q: 如何调整超时时间?**

A: 修改脚本中的 `TIMEOUT_SECONDS` 变量:

```python
TIMEOUT_SECONDS = 300  # 改为 5 分钟
```
