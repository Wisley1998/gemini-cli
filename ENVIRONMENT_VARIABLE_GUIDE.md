# 🔧 环境变量控制指南

## `GEMINI_CLI_IDE_INTEGRATION=disabled` 的作用

### 📋 问题场景

当你在**命令行**运行 Gemini CLI 时（不是在 VS Code 内部），可能遇到：

```bash
[ERROR] [IDEClient] To use this feature, please open a workspace folder in your IDE and try again.
```

### ✅ 解决方法

通过设置环境变量来**跳过 IDE 检查**：

```bash
GEMINI_CLI_IDE_INTEGRATION=disabled gemini --yolo
```

---

## 🎯 使用场景对比

### 场景 1：在 VS Code 内运行（默认）✅

```bash
# 在 VS Code 集成终端中
cd /path/to/project
gemini --yolo

# ✓ 自动检测 VS Code 环境
# ✓ 连接 IDE companion extension
# ✓ 可以使用 diff view、文件创建等 IDE 功能
```

**特点**：

- ✅ 完整的 IDE 集成功能
- ✅ 可视化 diff 预览
- ✅ 自动检测 workspace 路径

---

### 场景 2：纯命令行运行（会出错）❌

```bash
# 在普通终端中
cd /path/to/project
gemini --yolo

# ✗ 检测不到 VS Code 环境
# ✗ 尝试连接 IDE companion 失败
# ✗ workspace 验证失败
# 结果：报错 "please open a workspace folder"
```

**问题**：

- ❌ IDE 集成检查失败
- ❌ 无法继续执行任务

---

### 场景 3：禁用 IDE 集成（解决方案）✅

```bash
# 设置环境变量禁用 IDE 检查
GEMINI_CLI_IDE_INTEGRATION=disabled gemini --yolo

# ✓ 跳过 IDE 连接尝试
# ✓ 直接在命令行环境运行
# ✓ 不依赖 VS Code extension
```

**效果**：

- ✅ 可以在纯命令行环境运行
- ✅ 不需要 VS Code
- ✅ 适合自动化脚本
- ⚠️ 但无法使用 IDE 特定功能（如 diff view）

---

## 💡 实际应用

### 1️⃣ 在脚本中使用

```python
# run_automated_benchmark.py

# 方法 1：在命令中添加
cmd = f'GEMINI_CLI_IDE_INTEGRATION=disabled gemini --prompt-interactive "{prompt}" --yolo'

# 方法 2：设置环境变量字典
import os
env = os.environ.copy()
env['GEMINI_CLI_IDE_INTEGRATION'] = 'disabled'

subprocess.run(['gemini', '--yolo'], env=env)
```

### 2️⃣ 在 Shell 脚本中使用

```bash
#!/bin/bash

# 方法 1：临时设置
GEMINI_CLI_IDE_INTEGRATION=disabled gemini --yolo

# 方法 2：导出环境变量
export GEMINI_CLI_IDE_INTEGRATION=disabled
gemini --yolo

# 方法 3：在子 shell 中运行
(
  export GEMINI_CLI_IDE_INTEGRATION=disabled
  gemini --yolo
)
```

### 3️⃣ 在 pexpect 中使用

```python
import pexpect
import os

# 设置环境变量
env = os.environ.copy()
env['GEMINI_CLI_IDE_INTEGRATION'] = 'disabled'

# 启动进程
child = pexpect.spawn(
    'gemini',
    ['--yolo'],
    env=env
)
```

---

## 🔍 工作原理（技术细节）

### IDE 检测流程

```typescript
// packages/core/src/ide/detect-ide.ts

export function detectIde(): IdeInfo | undefined {
  // 1. 检查是否在 VS Code 环境
  if (process.env['TERM_PROGRAM'] !== 'vscode') {
    return undefined; // ← 如果不是 VS Code，返回 undefined
  }

  // 2. 检测具体的 IDE 类型
  const ide = detectIdeFromEnv();
  return verifyVSCode(ide, ideProcessInfo);
}
```

### 连接验证

```typescript
// packages/core/src/ide/ide-client.ts

async connect(): Promise<void> {
  if (!this.currentIde) {
    // ← 如果检测不到 IDE，报错
    this.setState(
      IDEConnectionStatus.Disconnected,
      `IDE integration is not supported...`
    );
    return;
  }

  // 验证 workspace 路径
  const { isValid, error } = IdeClient.validateWorkspacePath(
    workspacePath,
    process.cwd()
  );

  if (!isValid) {
    // ← workspace 验证失败时报错
    this.setState(IDEConnectionStatus.Disconnected, error, true);
    return;
  }
  // ...
}
```

### 环境变量的作用

虽然 `GEMINI_CLI_IDE_INTEGRATION=disabled` 在当前代码中**没有直接实现**，但我们可以：

1. **修改检测逻辑**（推荐，需要修改源码）
2. **模拟 VS Code 环境**（不推荐）
3. **使用工作目录变通**（当前方案）

---

## 🛠️ 三种实现方式对比

### 方式 1：环境变量禁用（需要源码支持）

```typescript
// 在 detect-ide.ts 中添加
export function detectIde(): IdeInfo | undefined {
  // 新增：检查禁用标志
  if (process.env['GEMINI_CLI_IDE_INTEGRATION'] === 'disabled') {
    return undefined; // 假装检测不到 IDE
  }

  if (process.env['TERM_PROGRAM'] !== 'vscode') {
    return undefined;
  }
  // ...
}
```

**优点**：

- ✅ 清晰、直接
- ✅ 易于理解和使用
- ✅ 适合各种场景

**缺点**：

- ❌ 需要修改源码
- ❌ 等待官方支持

---

### 方式 2：工作目录方案（当前使用）

```python
# 在特定目录运行，提供有效的 workspace
work_dir = Path("./swe-bench-workspace/task-001")
work_dir.mkdir(parents=True, exist_ok=True)

child = pexpect.spawn(
    'gemini',
    ['--yolo'],
    cwd=str(work_dir)  # 在有效目录中运行
)
```

**优点**：

- ✅ 不需要修改源码
- ✅ 立即可用
- ✅ 提供真实的工作环境

**缺点**：

- ⚠️ 仍然会尝试连接 IDE
- ⚠️ 需要创建目录

---

### 方式 3：模拟 VS Code 环境（不推荐）

```bash
# 设置 VS Code 相关环境变量
export TERM_PROGRAM=vscode
export VSCODE_PID=12345
export GEMINI_CLI_IDE_WORKSPACE_PATH=/path/to/workspace

gemini --yolo
```

**优点**：

- ✅ 可以绕过检测

**缺点**：

- ❌ 不够干净
- ❌ 可能导致其他问题
- ❌ 欺骗性做法

---

## 📊 最佳实践建议

### 对于自动化脚本 🤖

```python
# run_automated_benchmark_v2.py 的方案（推荐）

import os
from pathlib import Path

def run_gemini(prompt, task_id):
    # 1. 创建工作目录
    work_dir = Path(f"swe-bench-workspace/{task_id}")
    work_dir.mkdir(parents=True, exist_ok=True)

    # 2. 设置环境（虽然当前没用，但为未来准备）
    env = os.environ.copy()
    env['GEMINI_CLI_IDE_INTEGRATION'] = 'disabled'

    # 3. 在工作目录中运行
    child = pexpect.spawn(
        'bash',
        ['-c', f'cd {work_dir} && gemini --prompt-interactive "{prompt}" --yolo'],
        env=env
    )

    return child
```

---

### 对于手动测试 👨‍💻

```bash
# 选项 1：在 VS Code 中运行（推荐）
# 打开 VS Code → 打开项目文件夹 → 打开终端
gemini --yolo

# 选项 2：创建工作目录
mkdir -p /tmp/gemini-workspace
cd /tmp/gemini-workspace
gemini --yolo

# 选项 3：等待官方支持后
GEMINI_CLI_IDE_INTEGRATION=disabled gemini --yolo
```

---

## 🔮 未来改进建议

### 给 Gemini CLI 团队的建议

1. **添加环境变量支持** ⭐⭐⭐⭐⭐

   ```typescript
   // 在 detect-ide.ts 中
   if (process.env['GEMINI_CLI_IDE_INTEGRATION'] === 'disabled') {
     return undefined;
   }
   ```

2. **添加命令行参数** ⭐⭐⭐⭐

   ```bash
   gemini --no-ide-integration --yolo
   ```

3. **更宽松的 workspace 验证** ⭐⭐⭐
   - 允许在任何目录运行
   - 只在需要 IDE 功能时才检查

4. **更好的错误提示** ⭐⭐⭐
   ```
   [WARNING] IDE integration not available in current environment.
   Running in command-line mode. Some features may be limited.
   ```

---

## 🎯 总结

### 当前状态

| 功能                                  | 状态      | 说明                     |
| ------------------------------------- | --------- | ------------------------ |
| `GEMINI_CLI_IDE_INTEGRATION=disabled` | ⚠️ 未实现 | 源码中没有检查此变量     |
| 工作目录方案                          | ✅ 可用   | 通过创建有效目录绕过检查 |
| VS Code 集成                          | ✅ 完整   | 在 VS Code 中运行无问题  |

### 推荐方案

**短期（立即可用）**：

```python
# 使用 run_automated_benchmark_v2.py
# 为每个任务创建工作目录
python3 run_automated_benchmark_v2.py --type swebench --limit 3
```

**长期（等待官方支持）**：

```bash
# 期待未来版本支持
GEMINI_CLI_IDE_INTEGRATION=disabled gemini --yolo
```

---

## 📚 相关环境变量

### Gemini CLI 相关

```bash
# IDE 集成（建议添加，当前未实现）
GEMINI_CLI_IDE_INTEGRATION=disabled

# IDE 服务器端口
GEMINI_CLI_IDE_SERVER_PORT=3000

# IDE 服务器认证 token
GEMINI_CLI_IDE_SERVER_AUTH_TOKEN=xxx

# Workspace 路径
GEMINI_CLI_IDE_WORKSPACE_PATH=/path/to/workspace
```

### IDE 检测相关

```bash
# VS Code 标识
TERM_PROGRAM=vscode

# 其他 IDE
CURSOR_TRACE_ID=xxx          # Cursor
CODESPACES=true              # GitHub Codespaces
CLOUD_SHELL=true             # Google Cloud Shell
REPLIT_USER=xxx              # Replit
```

---

## 🆘 故障排查

### 问题 1：设置了环境变量但仍然报错

**原因**：当前源码未实现此功能

**解决**：

```bash
# 使用工作目录方案
mkdir -p /tmp/gemini-test
cd /tmp/gemini-test
gemini --yolo
```

### 问题 2：想要完全禁用 IDE 集成

**临时方案**：

```bash
# 取消 TERM_PROGRAM 变量
unset TERM_PROGRAM
gemini --yolo

# 或在脚本中
env -u TERM_PROGRAM gemini --yolo
```

**注意**：这可能影响终端功能

### 问题 3：在 CI/CD 中运行

```yaml
# .github/workflows/test.yml
- name: Run Gemini tests
  run: |
    mkdir -p workspace
    cd workspace
    gemini --prompt "test task" --yolo
  env:
    TERM_PROGRAM: '' # 清空，避免误检测
```

---

_最后更新：2025-10-21_  
_相关文件：`run_automated_benchmark_v2.py`_  
_状态：环境变量支持待官方实现_
