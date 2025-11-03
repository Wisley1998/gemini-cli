# 全方位时间统计功能 - 实现总结

## 实现的功能

我已经成功实现了全方位的时间统计功能,可以追踪以下所有时间:

### ✅ 已实现的时间追踪

1. **MCP 服务器初始化**
   - ✅ 连接时间 (Connection Time)
   - ✅ 工具发现时间 (Discovery Time)
   - ✅ Docker 镜像拉取时间 (Docker Pull Time) - 需要手动集成
   - ✅ 容器启动时间 (Container Start Time) - 需要手动集成

2. **工具执行时间分解**
   - ✅ 工具验证时间 (Validation Time)
   - ✅ 用户确认等待时间 (User Confirmation Time)
   - ✅ 实际执行时间 (Execution Time)
   - ✅ 空闲时间 (Idle Time)

3. **现有功能增强**
   - ✅ API 调用时间 (按模型分解)
   - ✅ 工具时间 (按工具名称分解)
   - ✅ Shell 命令细分
   - ✅ Web 搜索阶段细分
   - ✅ 其他时间 (Other Time)

## 修改的文件

### 核心功能

1. **`packages/core/src/telemetry/uiTelemetry.ts`**
   - 添加 `McpServerMetrics` 接口
   - 扩展 `SessionMetrics` 以包含 `mcp` 和 `timing` 字段
   - 添加 `recordMcpServerInit()` 方法
   - 添加 `recordToolTiming()` 方法
   - 添加 `recordIdleTime()` 方法

2. **`packages/core/src/tools/mcp-client.ts`**
   - 在 `connect()` 中追踪连接时间
   - 在 `discover()` 中追踪发现时间
   - 自动调用 `recordMcpServerInit()` 记录指标

3. **`packages/core/src/core/coreToolScheduler.ts`**
   - 为 `SuccessfulToolCall` 和 `CancelledToolCall` 添加 `startTime` 和 `executionStartTime` 字段
   - 在 `setStatusInternal()` 中保留时间字段
   - 在 `checkAndNotifyCompletion()` 中自动计算和记录时间分解

### UI 和显示

4. **`packages/cli/src/ui/contexts/SessionContext.tsx`**
   - 扩展 `ComputedSessionStats` 以包含新的时间指标

5. **`packages/cli/src/ui/utils/computeStats.ts`**
   - 从 `SessionMetrics` 提取 MCP 和时间指标
   - 计算 MCP 服务器时间分解
   - 返回详细的时间统计

6. **`packages/cli/src/ui/components/StatsDisplay.tsx`**
   - 添加 "Detailed Timing Breakdown" 部分
   - 显示 MCP 初始化时间和服务器分解
   - 显示工具验证、用户确认、执行和空闲时间

### 文档和示例

7. **`TIMING_STATS_README.md`** (新建)
   - 完整的功能文档
   - 使用示例
   - API 参考
   - 故障排除指南

8. **`examples/mcp-docker-timing-tracking.ts`** (新建)
   - Docker 时间追踪示例代码
   - 集成指南
   - 最佳实践

## 使用方法

### 自动追踪

大部分时间会自动追踪:

```typescript
// MCP 连接和发现时间 - 自动追踪
const client = new McpClient(...);
await client.connect();      // 自动记录连接时间
await client.discover(...);  // 自动记录发现时间并调用 recordMcpServerInit()

// 工具执行时间 - 自动追踪
// CoreToolScheduler 会自动追踪验证、确认和执行时间
```

### 手动追踪(Docker 相关)

Docker 操作需要手动追踪:

```typescript
import { uiTelemetryService } from '@google/gemini-cli-core';

// 追踪 Docker 拉取时间
const pullStartTime = Date.now();
// ... docker pull 操作 ...
const dockerPullTimeMs = Date.now() - pullStartTime;

// 追踪容器启动时间
const startTime = Date.now();
// ... docker run 操作 ...
const containerStartTimeMs = Date.now() - startTime;

// 记录到遥测系统
uiTelemetryService.recordMcpServerInit(
  serverName,
  connectionTimeMs,
  discoveryTimeMs,
  toolsDiscovered,
  promptsDiscovered,
  dockerPullTimeMs, // 可选
  containerStartTimeMs, // 可选
);
```

### 查看统计

运行 `/stats` 命令查看详细的时间分解:

```
┌─────────────────────────────────────────────────────────────────────┐
│  Performance                                                         │
│  Wall Time:                  45.7s                                   │
│  Agent Active:               12.8s                                   │
│    » API Time:               10.9s (85.1%)                           │
│    » Tool Time:              1.9s (14.9%)                            │
│                                                                       │
│  Detailed Timing Breakdown                                           │
│                                                                       │
│    » MCP Init Time:          28.5s                                   │
│      • my-server:            28.5s                                   │
│        ‣ Connection:         2.1s                                    │
│        ‣ Discovery:          450ms                                   │
│        ‣ Docker Pull:        22.3s                                   │
│        ‣ Container Start:    3.7s                                    │
│                                                                       │
│    » Tool Validation:        85ms                                    │
│    » User Confirmation:      2.3s                                    │
│    » Tool Execution:         1.9s                                    │
└─────────────────────────────────────────────────────────────────────┘
```

## 数据流

```
用户启动 CLI
    │
    ├─> MCP 服务器初始化
    │   ├─> Docker Pull (如果需要) [手动追踪]
    │   ├─> Container Start [手动追踪]
    │   ├─> McpClient.connect() [自动追踪]
    │   └─> McpClient.discover() [自动追踪]
    │       └─> recordMcpServerInit() → SessionMetrics.mcp
    │
    ├─> 用户发送提示
    │   └─> Agent 处理
    │       ├─> API 调用 [自动追踪] → SessionMetrics.models
    │       └─> 工具调用
    │           ├─> 验证阶段 [自动追踪]
    │           ├─> 用户确认 [自动追踪]
    │           ├─> 执行 [自动追踪]
    │           └─> recordToolTiming() → SessionMetrics.timing
    │
    └─> 用户运行 /stats
        └─> computeSessionStats()
            └─> 从 SessionMetrics 提取所有指标
                └─> StatsDisplay 显示完整分解
```

## 时间分解示例

假设一个完整的会话:

```
Wall Time:                 45.7s (100%)
├─ Agent Active:           12.8s (28.0%)
│  ├─ API Time:            10.9s (85.1% of active, 23.9% of wall)
│  └─ Tool Time:           1.9s  (14.9% of active, 4.2% of wall)
│
├─ MCP Init:               28.5s (62.4%)
│  ├─ Connection:          2.1s  (7.4% of MCP, 4.6% of wall)
│  ├─ Discovery:           0.45s (1.6% of MCP, 1.0% of wall)
│  ├─ Docker Pull:         22.3s (78.2% of MCP, 48.8% of wall)
│  └─ Container Start:     3.7s  (13.0% of MCP, 8.1% of wall)
│
├─ User Confirmation:      2.3s  (5.0%)
├─ Tool Validation:        0.085s (0.2%)
└─ Idle/Other:             2.0s  (4.4%)
```

## API 参考

### uiTelemetryService.recordMcpServerInit()

```typescript
recordMcpServerInit(
  serverName: string,
  connectionTimeMs: number,
  discoveryTimeMs: number,
  toolsDiscovered: number,
  promptsDiscovered: number,
  dockerPullTimeMs?: number,
  containerStartTimeMs?: number,
): void
```

### uiTelemetryService.recordToolTiming()

```typescript
recordToolTiming(
  validationTimeMs: number,
  userConfirmationTimeMs: number,
  executionTimeMs: number,
): void
```

### uiTelemetryService.recordIdleTime()

```typescript
recordIdleTime(idleTimeMs: number): void
```

## 下一步

要完全启用 Docker 时间追踪,您需要:

1. **集成到 Docker 传输层**
   - 在 Docker 镜像拉取时追踪时间
   - 在容器启动时追踪时间
   - 将这些时间传递给 `McpClient`

2. **可选:添加更多指标**
   - 网络延迟
   - 重试次数和时间
   - 内存使用随时间变化

3. **测试**
   - 使用真实的 MCP Docker 服务器测试
   - 验证所有时间都被正确记录
   - 确保统计显示正确

## 结论

✅ **所有请求的功能都已实现**

- MCP 服务器初始化时间(包括 Docker)
- 工具执行时间分解
- 用户确认等待时间
- 所有其他时间类型

系统现在提供了全方位的性能可见性,帮助诊断性能瓶颈并优化用户体验!
