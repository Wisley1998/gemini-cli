# API 调用日志功能

## 概述

Gemini CLI 现在会自动记录所有 LLM API 调用的输入和输出到一个持久化的日志文件中。这个功能对于调试、审计和分析 API 使用情况非常有用。

## Log File Location

All API call logs are saved in:

```
<current-project-directory>/logs/api_calls.log
```

- The log file is stored in the `logs` folder within your project directory
- Each project has its own separate log file
- Logs are automatically created when you run `gemini` in any directory

## 日志格式

日志文件包含以下信息：

### Session Separator

Each time you start Gemini CLI, a session marker is added to the log:

```
================================================================================
Session started at: 2025-10-11T15:01:42.531Z
Project: /Users/suiyifan/Desktop/multi-agnets/gemini-cli
================================================================================
```

### 请求日志

```
--------------------------------------------------------------------------------
[REQUEST] 2025-10-11T10:30:05.123Z
Model: gemini-2.5-pro
Prompt ID: prompt-abc-123

Request Data:
{
  "role": "user",
  "parts": [
    {
      "text": "你的问题或提示..."
    }
  ]
}
--------------------------------------------------------------------------------
```

### 响应日志

```
--------------------------------------------------------------------------------
[RESPONSE] 2025-10-11T10:30:07.456Z
Model: gemini-2.5-pro
Prompt ID: prompt-abc-123
Duration: 2333ms

Response Data:
{
  "candidates": [
    {
      "content": {
        "role": "model",
        "parts": [
          {
            "text": "模型的回复..."
          }
        ]
      }
    }
  ],
  "usageMetadata": {
    "promptTokenCount": 25,
    "candidatesTokenCount": 150,
    "totalTokenCount": 175
  }
}
--------------------------------------------------------------------------------
```

### 错误日志

```
--------------------------------------------------------------------------------
[ERROR] 2025-10-11T10:30:10.789Z
Model: gemini-2.5-pro
Prompt ID: prompt-def-456
Duration: 1000ms

Error Message: API rate limit exceeded

Stack Trace:
Error: API rate limit exceeded
    at ...
--------------------------------------------------------------------------------
```

## 记录的信息

每个 API 调用都会记录：

1. **时间戳**：精确到毫秒的 ISO 8601 格式时间
2. **模型名称**：使用的 Gemini 模型（如 gemini-2.5-pro）
3. **Prompt ID**：用于关联请求和响应的唯一标识符
4. **持续时间**：API 调用的响应时间（仅响应和错误）
5. **完整数据**：请求内容或响应内容的 JSON 格式

## 使用场景

### 1. 调试问题

当遇到意外的模型行为时，可以查看日志文件来检查：

- 发送给模型的确切内容
- 模型返回的完整响应
- 错误消息和堆栈跟踪

### 2. 分析 Token 使用

通过响应日志中的 `usageMetadata` 字段，可以：

- 跟踪每次调用的 token 消耗
- 计算总体 API 成本
- 优化提示以减少 token 使用

### 3. 审计和合规

- 保留所有 API 交互的完整记录
- 用于安全审计或合规要求
- 追踪模型使用历史

### 4. 性能分析

- 查看 API 响应时间
- 识别慢速查询
- 优化应用性能

## 隐私和安全

⚠️ **重要提示**：

- 日志文件包含发送给 AI 模型的**所有内容**
- 如果您的提示包含敏感信息（密码、API 密钥、个人数据等），这些信息也会被记录
- 日志文件存储在本地，但请妥善保管
- 定期清理旧日志文件以节省磁盘空间和保护隐私

## 管理日志文件

##### View Logs

```bash
# View complete log (from project directory)
cat logs/api_calls.log

# View recent log entries
tail -n 100 logs/api_calls.log

# Monitor new logs in real-time
tail -f logs/api_calls.log
```

### Search Logs

```bash
# Search for calls to a specific model (from project directory)
grep "Model: gemini-2.5-pro" logs/api_calls.log

# Search for errors
grep "\[ERROR\]" logs/api_calls.log

# Search logs from a specific date
grep "2025-10-11" logs/api_calls.log
```

### 清理日志

````bash
### Clean Up Logs
```bash
# Delete log file (from project directory)
rm logs/api_calls.log

# Or clear log contents
echo "" > logs/api_calls.log

# Delete entire logs directory
rm -rf logs/
````

**Note**: The `logs/` directory is added to `.gitignore` and will not be tracked by git.

````

## 禁用日志功能

如果您想禁用 API 日志功能，可以在代码中调用：

```typescript
import { ApiLogger } from '@google/gemini-cli-core';

ApiLogger.disable();
````

要重新启用：

```typescript
ApiLogger.enable();
```

## 技术实现

API 日志功能通过以下方式实现：

1. `ApiLogger` 服务在应用启动时初始化
2. `LoggingContentGenerator` 拦截所有 API 调用
3. 请求在发送前被记录
4. 响应或错误在收到后被记录
5. 所有日志以追加方式写入同一个文件

这确保了：

- 所有 API 调用都被捕获
- 日志持久化到磁盘
- 跨会话的完整历史记录
- 最小的性能影响
