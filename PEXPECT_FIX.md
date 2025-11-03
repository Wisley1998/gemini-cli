# 🔧 Pexpect 环境变量问题修复

## ❌ 错误信息

```
pexpect.exceptions.ExceptionPexpect: The command was not found or was not executable: GEMINI_CLI_IDE_INTEGRATION=disabled.
```

## 🔍 问题原因

`pexpect.spawn()` 不能直接解析 shell 的环境变量语法。

### 错误写法 ❌

```python
# 这样不行！pexpect 会把整个字符串当作命令名
cmd = f'GEMINI_CLI_IDE_INTEGRATION=disabled gemini --prompt-interactive "{prompt}" --yolo'
child = pexpect.spawn(cmd, encoding='utf-8', timeout=TIMEOUT_SECONDS)
```

## ✅ 解决方案

使用 `bash -c` 来执行命令：

### 正确写法 ✅

```python
# 方法 1: 使用 bash -c（推荐）
escaped_prompt = prompt_content.replace('"', '\\"').replace('$', '\\$')
cmd = f'bash -c "GEMINI_CLI_IDE_INTEGRATION=disabled gemini --prompt-interactive \\"{escaped_prompt}\\" --yolo"'
child = pexpect.spawn(cmd, encoding='utf-8', timeout=TIMEOUT_SECONDS)
```

### 替代方法

```python
# 方法 2: 使用 env 参数
import os
env = os.environ.copy()
env['GEMINI_CLI_IDE_INTEGRATION'] = 'disabled'

child = pexpect.spawn(
    'gemini',
    ['--prompt-interactive', prompt_content, '--yolo'],
    encoding='utf-8',
    timeout=TIMEOUT_SECONDS,
    env=env
)
```

## 🔑 关键要点

1. **转义处理**：
   - `"` → `\\"`（双引号需要转义）
   - `$` → `\\$`（美元符号需要转义，避免变量替换）

2. **嵌套引号**：

   ```python
   bash -c "GEMINI_CLI_IDE_INTEGRATION=disabled gemini --prompt-interactive \"...\" --yolo"
   #        ^外层引号                                                      ^内层引号需要转义
   ```

3. **pexpect.spawn() 的限制**：
   - 只接受可执行文件名作为第一个参数
   - 不会通过 shell 解析命令
   - 环境变量赋值语法是 shell 特性，不是命令

## 📝 完整修复代码

```python
def run_gemini_with_prompt(prompt_file, prompt_content):
    """运行 gemini CLI 并执行指定的 prompt"""
    output_buffer = []

    try:
        # 1. 转义特殊字符
        escaped_prompt = prompt_content.replace('"', '\\"').replace('$', '\\$')

        # 2. 使用 bash -c 执行命令
        cmd = f'bash -c "GEMINI_CLI_IDE_INTEGRATION=disabled gemini --prompt-interactive \\"{escaped_prompt}\\" --yolo"'

        # 3. 启动进程
        child = pexpect.spawn(cmd, encoding='utf-8', timeout=TIMEOUT_SECONDS)

        # 4. 捕获输出
        class OutputCapture:
            def __init__(self, buffer_list):
                self.buffer = buffer_list

            def write(self, data):
                self.buffer.append(data)
                sys.stdout.write(data)

            def flush(self):
                sys.stdout.flush()

        child.logfile_read = OutputCapture(output_buffer)

        # ... 其余代码

    except Exception as e:
        print(f"错误: {e}")
        return None
```

## 🧪 测试验证

```bash
# 测试修复后的脚本
cd /Users/suiyifan/Desktop/multi-agnets/gemini-cli
python3 run_automated_benchmark.py --type swebench --limit 1

# 应该看到：
# ✓ Gemini CLI 正常启动
# ✓ 显示 Gemini logo
# ✓ 开始执行任务
```

## 📊 修改位置

**文件**: `run_automated_benchmark.py`  
**行数**: 第 142-150 行

### 修改前

```python
escaped_prompt = prompt_content.replace('"', '\\"')
cmd = f'GEMINI_CLI_IDE_INTEGRATION=disabled gemini --prompt-interactive "{escaped_prompt}" --yolo'
print(f"启动命令: {cmd[:100]}...")
child = pexpect.spawn(cmd, encoding='utf-8', timeout=TIMEOUT_SECONDS)
```

### 修改后

```python
escaped_prompt = prompt_content.replace('"', '\\"').replace('$', '\\$')
cmd = f'bash -c "GEMINI_CLI_IDE_INTEGRATION=disabled gemini --prompt-interactive \\"{escaped_prompt}\\" --yolo"'
print(f"启动命令: bash -c \"GEMINI_CLI_IDE_INTEGRATION=disabled gemini --prompt-interactive ...\" --yolo")
child = pexpect.spawn(cmd, encoding='utf-8', timeout=TIMEOUT_SECONDS)
```

## 💡 为什么这样修复有效？

1. **`bash -c`** 启动一个 bash shell
2. **Shell** 解析并执行引号内的命令字符串
3. **环境变量** 在 shell 中被正确设置
4. **Gemini CLI** 在设置了环境变量的上下文中运行

### 执行流程

```
pexpect.spawn()
    ↓
启动 bash
    ↓
bash 解析: "GEMINI_CLI_IDE_INTEGRATION=disabled gemini ..."
    ↓
设置环境变量 GEMINI_CLI_IDE_INTEGRATION=disabled
    ↓
执行 gemini --prompt-interactive "..." --yolo
    ↓
成功！✅
```

## 🔗 相关文档

- **WORKSPACE_FIX_SUMMARY.md** - Workspace 问题总结
- **USE_SOLUTION_1.md** - 方案选择指南
- **FIX_WORKSPACE_ISSUE.md** - 完整修复文档

## ⚠️ 注意事项

### 转义陷阱

```python
# ❌ 错误：美元符号没有转义
escaped = prompt.replace('"', '\\"')
cmd = f'bash -c "... --prompt-interactive \\"{escaped}\\" ..."'
# 如果 prompt 包含 $variable，bash 会尝试替换它！

# ✅ 正确：同时转义引号和美元符号
escaped = prompt.replace('"', '\\"').replace('$', '\\$')
cmd = f'bash -c "... --prompt-interactive \\"{escaped}\\" ..."'
```

### 引号层级

```python
# 层级 1: Python f-string
cmd = f'bash -c "..."'
         #     ^Python 字符串引号

# 层级 2: bash -c 的参数
cmd = f'bash -c "GEMINI_CLI_IDE_INTEGRATION=disabled gemini ..."'
                ^bash 需要的引号

# 层级 3: prompt 内容
cmd = f'bash -c "... --prompt-interactive \\"...\\" ..."'
                                           ^转义的引号包裹 prompt
```

## 🎯 快速参考

| 场景         | 命令                                                     |
| ------------ | -------------------------------------------------------- |
| **直接运行** | `bash -c "ENV_VAR=value command"`                        |
| **pexpect**  | `pexpect.spawn('bash', ['-c', 'ENV_VAR=value command'])` |
| **带引号**   | 转义内层引号：`\\"`                                      |
| **带变量**   | 转义美元符号：`\\$`                                      |

---

_最后更新：2025-10-21_  
_问题：pexpect 无法解析环境变量语法_  
_解决：使用 bash -c 包装命令_  
_状态：✅ 已修复_
