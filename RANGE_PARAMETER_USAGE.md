# 📖 run_automated_benchmark.py 范围参数使用指南

## ✨ 新增功能

添加了 `--range` 参数，可以精确指定要执行的 prompt 范围。

## 🎯 使用方法

### 基本语法

```bash
python3 run_automated_benchmark.py --range START-END
```

- `START`: 起始索引（从 1 开始）
- `END`: 结束索引（包含）

### 📝 使用示例

#### 1. 执行前 5 个 DeepResearch prompts

```bash
python3 run_automated_benchmark.py --type deepresearch --range 1-5
```

#### 2. 执行第 10 到 20 个 prompts

```bash
python3 run_automated_benchmark.py --type deepresearch --range 10-20
```

#### 3. 执行单个 prompt（第 50 个）

```bash
python3 run_automated_benchmark.py --type deepresearch --range 50-50
```

#### 4. 执行最后 10 个 prompts（假设有 100 个）

```bash
python3 run_automated_benchmark.py --type deepresearch --range 91-100
```

#### 5. 不指定类型，执行所有类型的第 5-15 个

```bash
python3 run_automated_benchmark.py --range 5-15
```

#### 6. 使用 caffeinate 防止休眠

```bash
caffeinate -d python3 run_automated_benchmark.py --type deepresearch --range 1-10
```

## ⚙️ 参数优先级

- `--range` 参数**优先于** `--limit` 参数
- 如果同时指定，`--limit` 会被忽略

```bash
# 只会执行第 10-20 个，--limit 5 被忽略
python3 run_automated_benchmark.py --range 10-20 --limit 5
```

## 🛡️ 错误处理

### 1. 超出范围

如果结束索引超过可用 prompts 数量，会自动调整：

```bash
# 如果只有 100 个 prompts
python3 run_automated_benchmark.py --range 95-150
# 输出: 警告: 结束索引 150 超过了总数 100，将使用 100
# 实际执行: 第 95-100 个
```

### 2. 格式错误

```bash
# ❌ 错误格式
python3 run_automated_benchmark.py --range 10,20   # 应该用 - 不是 ,
python3 run_automated_benchmark.py --range 10      # 缺少结束索引
python3 run_automated_benchmark.py --range abc-20  # 必须是数字

# ✅ 正确格式
python3 run_automated_benchmark.py --range 10-20
```

### 3. 逻辑错误

```bash
# ❌ 起始索引 > 结束索引
python3 run_automated_benchmark.py --range 20-10
# 输出: 错误: 结束索引必须 >= 起始索引

# ❌ 起始索引 < 1
python3 run_automated_benchmark.py --range 0-10
# 输出: 错误: 起始索引必须 >= 1
```

## 📊 实际应用场景

### 场景 1: 分批处理大量 prompts

```bash
# 第一批: 1-25
caffeinate -d python3 run_automated_benchmark.py --type deepresearch --range 1-25

# 第二批: 26-50
caffeinate -d python3 run_automated_benchmark.py --type deepresearch --range 26-50

# 第三批: 51-75
caffeinate -d python3 run_automated_benchmark.py --type deepresearch --range 51-75

# 第四批: 76-100
caffeinate -d python3 run_automated_benchmark.py --type deepresearch --range 76-100
```

### 场景 2: 测试特定 prompt

```bash
# 只测试第 42 个 prompt
python3 run_automated_benchmark.py --type deepresearch --range 42-42
```

### 场景 3: 重新运行失败的 prompts

假设第 15-20 个失败了，可以单独重新运行：

```bash
python3 run_automated_benchmark.py --type deepresearch --range 15-20
```

### 场景 4: 并行处理（多终端）

在不同终端中同时运行不同范围：

```bash
# 终端 1
caffeinate -d python3 run_automated_benchmark.py --range 1-25

# 终端 2
caffeinate -d python3 run_automated_benchmark.py --range 26-50

# 终端 3
caffeinate -d python3 run_automated_benchmark.py --range 51-75

# 终端 4
caffeinate -d python3 run_automated_benchmark.py --range 76-100
```

## 🔍 查看可用的 prompts

在执行前，可以先查看有哪些 prompts：

```bash
# 查看 DeepResearch prompts
ls deepresearch-bench-prompts/prompt_*.txt | wc -l

# 查看详细列表
ls -1 deepresearch-bench-prompts/prompt_*.txt | head -20

# 查看索引文件
cat deepresearch-bench-prompts/INDEX.md
```

## 📈 性能建议

1. **小批量测试**：先用 `--range 1-5` 测试，确保一切正常
2. **分批处理**：每批 20-25 个 prompts，便于管理和错误恢复
3. **使用 caffeinate**：防止系统休眠影响长时间运行
4. **监控结果**：定期检查 `results/deep_research/` 目录

## 🆚 对比其他参数

| 参数                | 用途              | 示例                          |
| ------------------- | ----------------- | ----------------------------- |
| `--limit N`         | 从头开始执行 N 个 | `--limit 10` → 第 1-10 个     |
| `--range START-END` | 执行指定范围      | `--range 10-20` → 第 10-20 个 |
| `--type`            | 指定 prompt 类型  | `--type deepresearch`         |

## 📝 完整示例

```bash
# 1. 查看帮助
python3 run_automated_benchmark.py --help

# 2. 执行前 5 个作为测试
python3 run_automated_benchmark.py --type deepresearch --range 1-5

# 3. 确认无误后，分批执行全部
caffeinate -d python3 run_automated_benchmark.py --type deepresearch --range 1-25
caffeinate -d python3 run_automated_benchmark.py --type deepresearch --range 26-50
caffeinate -d python3 run_automated_benchmark.py --type deepresearch --range 51-75
caffeinate -d python3 run_automated_benchmark.py --type deepresearch --range 76-100

# 4. 查看结果
ls -lh results/deep_research/
```

## 🎉 总结

- ✅ `--range` 参数让你**精确控制**执行哪些 prompts
- ✅ 支持**分批处理**，便于管理大量任务
- ✅ 可以**重试失败**的特定 prompts
- ✅ **自动处理**超出范围的情况
- ✅ **优先级高于** `--limit` 参数

Happy testing! 🚀
