# MCP 工具内部时间统计 - 完整文档

## 📋 目录

- [功能概述](#功能概述)
- [快速开始](#快速开始)
- [实现思路](#实现思路)
- [核心架构](#核心架构)
- [实现流程](#实现流程)
- [技术细节](#技术细节)
- [使用指南](#使用指南)
- [扩展指南](#扩展指南)
- [常见问题](#常见问题)
- [实现总结](#实现总结)

---

## 功能概述

### 目标

为 MCP (Model Context Protocol) 工具调用添加内部执行时间的详细统计,帮助用户和开发者:

- 🔍 识别性能瓶颈
- 📊 了解时间分布
- ⚡ 优化工具调用
- 🎯 精确定位慢速阶段

### 支持的 MCP 服务器

- **Playwright/Fetcher**: 网页抓取工具 (14+ 阶段)
- **GitHub**: GitHub API 工具 (3 阶段)
- **扩展性**: 易于添加新的服务器支持

### 显示的时间阶段

#### Playwright/Fetcher (14+ 阶段)

| 阶段              | 含义                     | 典型时间    | 优化建议               |
| ----------------- | ------------------------ | ----------- | ---------------------- |
| Browser Launch    | 浏览器启动               | 1-3s        | 复用浏览器实例         |
| Context Creation  | 浏览器上下文创建         | 100-300ms   | 使用持久化上下文       |
| Page Creation     | 页面对象创建             | 50-150ms    | 复用页面对象           |
| Navigation        | 网络请求到页面提交       | 200-1000ms  | 检查网络速度、CDN      |
| DNS Lookup        | DNS 解析                 | 10-100ms    | 使用 DNS 缓存          |
| TCP Connection    | TCP 连接建立             | 20-200ms    | 使用 HTTP/2            |
| DOMContentLoaded  | HTML解析+同步脚本        | 500-3000ms  | 减少同步脚本、优化HTML |
| Page Load         | 所有资源加载完成         | 1000-5000ms | 延迟加载、压缩资源     |
| JS Execution      | JavaScript 代码执行      | 100-2000ms  | 优化 JS 代码           |
| Wait for Selector | 等待特定元素出现         | 100-5000ms  | 简化选择器             |
| Screenshot        | 页面截图                 | 100-500ms   | 降低分辨率             |
| Get Content       | 获取页面内容             | 50-500ms    | 优化提取逻辑           |
| Page Close        | 关闭页面                 | 10-100ms    | -                      |
| **Other**         | **未分类时间(自动计算)** | **变动**    | -                      |

#### GitHub (3 阶段)

- **API Request** - API 请求时间
- **Authentication** - 认证时间
- **Response Parsing** - 响应解析时间

---

## 快速开始

### 一分钟上手

```bash
# 1. 启用详细日志
export DEBUG="pw:api,pw:browser"

# 2. 运行 gemini
gemini --yolo

# 3. 使用 MCP 工具
> 请使用 fetch_url 获取 https://example.com

# 4. 查看统计
> /stats
```

### 输出示例

```
│    » Tool Time:              33.7s (68.3%)
│      • fetch_url:            11.5s (34.0%)
│        ‣ MCP Call:           10.4s (91.2%)  ← MCP 调用总时间
│          - Browser Launch:   2.1s (20.2%)   ← 浏览器启动
│          - Navigation:       450ms (4.3%)   ← 网络请求
│          - DOMContentLoaded: 2.4s (22.8%)   ← HTML解析+同步JS
│          - Page Load:        1.9s (18.5%)   ← 资源加载完成
│          - Get Content:      850ms (8.2%)   ← 内容提取
│          - Other:            2.7s (26.0%)   ← 未分类时间
│        ‣ Serialization:      0s (0.0%)      ← 参数序列化
│        ‣ Processing:         0s (0.0%)      ← 结果处理
```

### 理解百分比

- 子阶段的百分比是**相对于 MCP Call** 计算的
- 例如: Browser Launch 20.2% = 2.1s / 10.4s
- 所有子阶段应该接近(但不必等于) 100%
- "Other" 时间补齐未被精确测量的部分

---

## 实现思路

### 核心思想

```
MCP 工具调用
    ↓
捕获 DEBUG 日志 (stderr)
    ↓
解析时间戳事件
    ↓
计算阶段时间
    ↓
添加"其他"时间
    ↓
聚合到统计数据
    ↓
在 /stats 中显示
```

### 关键挑战与解决方案

| 挑战              | 解决方案                          |
| ----------------- | --------------------------------- |
| 如何获取内部时间? | 利用 Playwright 的 DEBUG 日志输出 |
| 如何捕获日志?     | 拦截 stderr 输出或使用 DEBUG_FILE |
| 日志格式不统一    | 使用灵活的正则表达式匹配          |
| 时间不相加到 100% | 自动计算"其他"时间补齐            |
| 多次调用日志混淆  | 使用服务器名称隔离日志            |

### 核心创新

1. **自动计算"其他"时间**
   - 总时间减去所有已知阶段
   - 智能显示:只在超过 100ms 且 > 5% 时显示
   - 帮助识别遗漏的阶段

2. **零侵入性设计**
   - 不需要修改 MCP 服务器代码
   - 只解析现有的 DEBUG 日志
   - 完全透明,不影响正常功能

3. **灵活的日志匹配**
   - 支持多种 Playwright 日志格式
   - 适配不同版本
   - 易于扩展新格式

4. **模块化架构**
   - 日志捕获、解析、显示分离
   - 易于测试和维护
   - 易于扩展新的 MCP 服务器

---

## 核心架构

### 文件结构

```
packages/core/src/tools/
├── mcp-debug-parser.ts          # 日志解析核心 (新增)
└── mcp-tool.ts                  # 日志捕获与集成 (修改)

packages/core/src/telemetry/
└── uiTelemetry.ts               # 数据结构定义 (修改)

packages/cli/src/ui/
├── utils/computeStats.ts        # 统计计算 (修改)
└── components/StatsDisplay.tsx  # UI 显示 (修改)
```

### 数据流向

```typescript
// 1. 数据结构定义 (uiTelemetry.ts)
interface McpToolExecutionPhases {
  serializationTimeMs: number;
  mcpCallTimeMs: number;
  processingTimeMs: number;
  totalTimeMs: number;
  internalPhases?: Array<{    // ← 内部阶段
    name: string;
    timeMs: number;
  }>;
}

// 2. 日志捕获 (mcp-tool.ts)
const stderrLogs = captureStderrLogs();

// 3. 日志解析 (mcp-debug-parser.ts)
const phases = parseDebugLogs(stderrLogs, serverName);
const phasesWithOther = addOtherPhase(phases, mcpCallTime);

// 4. 数据聚合 (mcp-tool.ts)
updateMcpToolMetrics(serverName, toolName, {
  internalPhases: phasesWithOther
});

// 5. 统计计算 (computeStats.ts)
const subPhases = phases.map(phase => ({
  name: phase.name,
  timeMs: phase.totalTimeMs,
  percent: (phase.totalTimeMs / mcpCallTime) * 100
}));

// 6. UI 显示 (StatsDisplay.tsx)
{subPhases.map(subPhase => (
  <Text>{subPhase.name}: {formatDuration(subPhase.timeMs)} ({subPhase.percent}%)</Text>
))}
```

---

## 实现流程

### 步骤 1: 定义数据结构

**文件**: `packages/core/src/telemetry/uiTelemetry.ts`

```typescript
export interface McpToolExecutionPhases {
  serializationTimeMs: number;
  mcpCallTimeMs: number;
  processingTimeMs: number;
  totalTimeMs: number;
  // 新增：内部阶段
  internalPhases?: Array<{
    name: string;
    timeMs: number;
  }>;
}

export interface McpToolMetrics {
  toolName: string;
  executionCount: number;
  totalSerializationTimeMs: number;
  totalMcpCallTimeMs: number;
  totalProcessingTimeMs: number;
  totalExecutionTimeMs: number;
  // 新增：累积的内部阶段
  internalPhases?: Array<{
    name: string;
    totalTimeMs: number; // 所有执行的累加
    count: number; // 出现次数
  }>;
}
```

### 步骤 2: 创建日志解析器

**文件**: `packages/core/src/tools/mcp-debug-parser.ts`

#### 2.1 定义接口

```typescript
export interface McpInternalPhase {
  name: string;
  timeMs: number;
}

interface TimestampedEvent {
  timestamp: Date;
  category: string;
  message: string;
}
```

#### 2.2 提取时间戳事件

```typescript
function extractTimestampedEvents(logs: string[]): TimestampedEvent[] {
  const events: TimestampedEvent[] = [];

  for (const log of logs) {
    // Playwright format: 2025-01-15T10:30:45.123Z pw:api => page.goto started
    const pwMatch = log.match(
      /^(\d{4}-\d{2}-\d{2}T[\d:.]+Z)\s+pw:(api|browser|protocol)\s+(.+)$/,
    );
    if (pwMatch) {
      events.push({
        timestamp: new Date(pwMatch[1]),
        category: pwMatch[2],
        message: pwMatch[3],
      });
    }
    // ... 其他格式匹配
  }

  return events;
}
```

#### 2.3 计算阶段时间

```typescript
function findDuration(
  events: TimestampedEvent[],
  startPattern: RegExp,
  endPattern: RegExp,
  name: string,
): McpInternalPhase | null {
  const startEvent = events.find((e) => startPattern.test(e.message));
  const endEvent = events.find((e) => endPattern.test(e.message));

  if (startEvent && endEvent) {
    const timeMs =
      endEvent.timestamp.getTime() - startEvent.timestamp.getTime();
    return { name, timeMs };
  }

  return null;
}
```

#### 2.4 解析 Playwright 日志

```typescript
function parsePlaywrightLogs(events: TimestampedEvent[]): McpInternalPhase[] {
  const phases: McpInternalPhase[] = [];

  // 浏览器启动
  const browserLaunch = findDuration(
    events,
    /=> browserType\.launch|launchPersistentContext started/,
    /<= browserType\.launch|launchPersistentContext succeeded/,
    'Browser Launch',
  );
  if (browserLaunch) phases.push(browserLaunch);

  // DOMContentLoaded
  const domReady = findDuration(
    events,
    /"commit" event fired/,
    /"domcontentloaded" event fired/,
    'DOMContentLoaded',
  );
  if (domReady) phases.push(domReady);

  // ... 其他阶段 (共 14+ 个)

  return phases;
}
```

#### 2.5 添加"其他"时间

```typescript
export function addOtherPhase(
  phases: McpInternalPhase[],
  totalTimeMs: number,
): McpInternalPhase[] {
  if (phases.length === 0 || totalTimeMs <= 0) {
    return phases;
  }

  const accountedTimeMs = phases.reduce((sum, phase) => sum + phase.timeMs, 0);
  const otherTimeMs = totalTimeMs - accountedTimeMs;

  // 只有当"其他"时间超过 100ms 或超过总时间的 5% 时才添加
  if (otherTimeMs > 100 && otherTimeMs / totalTimeMs > 0.05) {
    return [...phases, { name: 'Other', timeMs: otherTimeMs }];
  }

  return phases;
}
```

### 步骤 3: 集成到 MCP 工具

**文件**: `packages/core/src/tools/mcp-tool.ts`

```typescript
// Phase 2: MCP communication (actual tool call)
const mcpCallStartTime = Date.now();
// ... MCP 调用 ...
const mcpCallTime = Date.now() - mcpCallStartTime;

// 等待 stderr 数据处理
await new Promise((resolve) => setTimeout(resolve, 500));

// 获取并解析日志
const stderrLogs = DiscoveredMCPTool.getServerStderrLogs(this.serverName);
if (stderrLogs && stderrLogs.length > 0) {
  const { parseDebugLogs: parseDebugLogsFunc, addOtherPhase } = await import(
    './mcp-debug-parser.js'
  );

  let internalPhases = parseDebugLogsFunc(stderrLogs, this.serverName);

  // 添加"其他"时间
  if (internalPhases && internalPhases.length > 0 && mcpCallTime > 0) {
    internalPhases = addOtherPhase(internalPhases, mcpCallTime);
  }
}

// 记录统计数据
uiTelemetryService.recordMcpToolExecutionPhases(
  this.serverName,
  this.serverToolName,
  {
    serializationTimeMs: serializationTime,
    mcpCallTimeMs: mcpCallTime,
    processingTimeMs: processingTime,
    totalTimeMs: totalTime,
    internalPhases: internalPhases,
  },
);
```

---

## 技术细节

### 日志格式支持

#### Playwright 日志格式

```
2025-01-15T10:30:45.123Z pw:api => page.goto started
2025-01-15T10:30:47.456Z pw:browser "commit" event fired
2025-01-15T10:30:49.789Z pw:api <= page.goto succeeded
```

**匹配正则**:

```typescript
/^(\d{4}-\d{2}-\d{2}T[\d:.]+Z)\s+pw:(api|browser|protocol)\s+(.+)$/;
```

#### GitHub 日志格式

```
[DEBUG] 2025-01-15 10:30:45 - API request started
[DEBUG] 2025-01-15 10:30:47 - API request completed
```

**匹配正则**:

```typescript
/^\[DEBUG\]\s+(\d{4}-\d{2}-\d{2}\s+[\d:]+)\s+-\s+(.+)$/;
```

### 时间计算逻辑

```typescript
// 1. 单个阶段时间
phaseTime = endEventTimestamp - startEventTimestamp;

// 2. 已记录时间总和
accountedTime = Σ(phaseTime);

// 3. "其他"时间
otherTime = totalMcpCallTime - accountedTime;

// 4. 百分比计算
phasePercent = (phaseTime / totalMcpCallTime) * 100;
```

### 数据聚合

当工具被多次调用时:

```typescript
// 累积内部阶段时间
for (const phase of newPhases) {
  const existing = internalPhases.find((p) => p.name === phase.name);
  if (existing) {
    existing.totalTimeMs += phase.timeMs;
    existing.count += 1;
  } else {
    internalPhases.push({
      name: phase.name,
      totalTimeMs: phase.timeMs,
      count: 1,
    });
  }
}
```

---

## 使用指南

### 基本使用

```bash
# 1. 启用 DEBUG 日志
export DEBUG="pw:api,pw:browser"

# 2. 运行 gemini
gemini --yolo

# 3. 使用 MCP 工具
> 请使用 fetch_url 获取 https://example.com

# 4. 查看统计
> /stats
```

### 永久启用

添加到 `~/.zshrc` 或 `~/.bashrc`:

```bash
echo 'export DEBUG="pw:api,pw:browser"' >> ~/.zshrc
source ~/.zshrc
```

### 调试技巧

#### 1. 检查日志是否被捕获

查找控制台输出:

```
[MCP Debug] Retrieved 45 log lines from static Map for fetcher/fetch_url
[MCP Debug] Sample logs (first 3):
  1. 2025-01-15T10:30:45.123Z pw:api => page.goto started...
[MCP Debug] Parsed 5 internal phases: [...]
```

#### 2. 查看原始日志

```bash
DEBUG="pw:api,pw:browser" gemini --yolo 2>&1 | grep "pw:" | head -20
```

#### 3. 强制重新启动浏览器

```bash
# 清除浏览器进程
pkill -9 chromium  # 或 chrome/firefox

# 重新运行
gemini --yolo
```

#### 4. 增加日志级别

```bash
# 更详细的日志
export DEBUG="pw:*"

# 或只看 API 调用
export DEBUG="pw:api"
```

### 禁用统计

```bash
# 取消设置 DEBUG
unset DEBUG

# 运行 gemini (不会显示内部时间)
gemini --yolo
```

---

## 扩展指南

### 添加新的 MCP 服务器支持

#### 步骤 1: 识别日志格式

研究目标 MCP 服务器的日志输出:

```bash
DEBUG="*" your-mcp-server 2>&1 | tee server-logs.txt
```

#### 步骤 2: 添加日志格式匹配

编辑 `mcp-debug-parser.ts`:

```typescript
function extractTimestampedEvents(logs: string[]): TimestampedEvent[] {
  const events: TimestampedEvent[] = [];

  for (const log of logs) {
    // ... 现有匹配 ...

    // 新的服务器格式
    const customMatch = log.match(/YOUR_REGEX_PATTERN/);
    if (customMatch) {
      events.push({
        timestamp: new Date(customMatch[1]),
        category: customMatch[2],
        message: customMatch[3],
      });
    }
  }

  return events;
}
```

#### 步骤 3: 创建解析函数

```typescript
function parseCustomServerLogs(events: TimestampedEvent[]): McpInternalPhase[] {
  const phases: McpInternalPhase[] = [];

  // 定义关键阶段
  const initialization = findDuration(
    events,
    /initialization started/,
    /initialization completed/,
    'Initialization',
  );
  if (initialization) phases.push(initialization);

  // ... 添加更多阶段 ...

  return phases;
}
```

#### 步骤 4: 注册服务器

```typescript
export function parseDebugLogs(
  logs: string[],
  serverName: string,
): McpInternalPhase[] {
  const events = extractTimestampedEvents(logs);
  const serverLower = serverName.toLowerCase();

  // ... 现有服务器 ...

  // 新服务器
  if (serverLower.includes('your-server-name')) {
    return parseCustomServerLogs(events);
  }

  return [];
}
```

### 添加新的时间阶段

在相应的解析函数中:

```typescript
// 新阶段示例: 数据库查询
const dbQuery = findDuration(
  events,
  /database query started/, // 开始事件
  /database query completed/, // 结束事件
  'Database Query', // 显示名称
);
if (dbQuery) phases.push(dbQuery);
```

### 自定义"其他"时间阈值

编辑 `addOtherPhase()` 函数:

```typescript
export function addOtherPhase(
  phases: McpInternalPhase[],
  totalTimeMs: number,
  minTimeMs = 100, // 最小时间阈值
  minPercent = 0.05, // 最小百分比阈值
): McpInternalPhase[] {
  const accountedTimeMs = phases.reduce((sum, phase) => sum + phase.timeMs, 0);
  const otherTimeMs = totalTimeMs - accountedTimeMs;

  if (otherTimeMs > minTimeMs && otherTimeMs / totalTimeMs > minPercent) {
    return [...phases, { name: 'Other', timeMs: otherTimeMs }];
  }

  return phases;
}
```

---

## 常见问题

### Q1: 为什么看不到 Browser Launch?

**A**: 可能原因:

1. 浏览器已经启动,不需要重新启动
2. DEBUG 环境变量未设置
3. 使用的是已存在的浏览器上下文

**解决**:

```bash
pkill -9 chromium && DEBUG="pw:api,pw:browser" gemini --yolo
```

### Q2: "Other" 时间很大怎么办?

**A**: "Other" 时间包含:

- 浏览器内部处理
- 系统级延迟
- 未被特定事件标记的操作

通常占比 20-40% 是正常的。如果超过 60%,可能需要:

1. 检查日志是否完整
2. 添加更多阶段解析
3. 调查是否有性能问题

### Q3: 阶段时间不准确?

**A**: 检查:

1. 系统时钟是否正确
2. 是否有其他程序干扰
3. 网络是否稳定
4. DEBUG 日志是否完整

### Q4: 如何禁用内部时间统计?

**A**: 不设置 DEBUG 环境变量即可:

```bash
unset DEBUG
gemini --yolo
```

### Q5: 支持哪些浏览器?

**A**: Playwright 支持:

- Chromium (推荐)
- Firefox
- WebKit

日志格式相同,都可以正常解析。

### Q6: 为什么阶段不相加到 100%?

**A**: 这是设计行为:

1. **选择性测量**: 只显示关键的、可测量的阶段
2. **并行执行**: 某些阶段可能重叠
3. **其他时间**: "Other" 补齐未分类的时间

### Q7: 如何查看更详细的日志?

**A**: 使用更详细的 DEBUG 级别:

```bash
DEBUG="pw:*" gemini --yolo 2>&1 | tee debug.log
```

---

## 实现总结

### 已完成功能

✅ **核心功能**

- 创建日志解析器 (`mcp-debug-parser.ts`)
- 实现 14+ 个时间阶段支持
- 自动计算"其他"时间
- 集成到 MCP 工具调用流程
- 更新统计计算逻辑
- 更新 UI 显示组件

✅ **文档**

- 完整实现文档
- 快速使用指南
- 扩展开发指南

### 核心文件

#### 实现文件

1. `packages/core/src/tools/mcp-debug-parser.ts` - 日志解析器 (新增)
2. `packages/core/src/tools/mcp-tool.ts` - 日志捕获 (修改)
3. `packages/core/src/telemetry/uiTelemetry.ts` - 数据结构 (修改)
4. `packages/cli/src/ui/utils/computeStats.ts` - 统计计算 (修改)
5. `packages/cli/src/ui/components/StatsDisplay.tsx` - UI 显示 (修改)

### 技术亮点

🎯 **日志捕获**: 拦截 stderr 输出,无需修改 MCP 服务器
🎯 **灵活解析**: 正则匹配多种日志格式
🎯 **精确计时**: 基于时间戳,毫秒级精度
🎯 **智能聚合**: 多次调用自动累积统计
🎯 **优雅降级**: 无日志时不影响正常功能

### 使用建议

💡 **开发调试**: 使用 `DEBUG="pw:*"` 获取最详细日志
💡 **性能分析**: 重点关注占比超过 20% 的阶段
💡 **持续监控**: 定期查看 `/stats` 了解性能趋势
💡 **优化方向**: 针对耗时最长的阶段进行优化

### 核心优势

- ✅ **详细可见**: 14+ 个内部阶段,全面了解执行过程
- ✅ **自动计算**: "其他"时间自动补齐,无需手动计算
- ✅ **易于扩展**: 模块化设计,轻松添加新服务器/阶段
- ✅ **性能友好**: 惰性解析,最小化性能开销
- ✅ **用户友好**: 清晰的 UI 显示,直观的百分比

### 效果对比

#### 之前

```
‣ MCP Call: 10.4s (91.2%)
  - DOMContentLoaded: 2.4s (22.8%)
  - Page Load: 1.9s (18.5%)
  - Navigation: 450ms (4.3%)
  (54.4% 未被记录) ❌
```

#### 现在

```
‣ MCP Call: 10.4s (91.2%)
  - Browser Launch: 2.1s (20.2%)    ← 新增
  - Context Creation: 150ms (1.4%)  ← 新增
  - Page Creation: 80ms (0.8%)      ← 新增
  - Navigation: 450ms (4.3%)
  - DOMContentLoaded: 2.4s (22.8%)
  - Page Load: 1.9s (18.5%)
  - Get Content: 850ms (8.2%)       ← 新增
  - Page Close: 50ms (0.5%)         ← 新增
  - Other: 2.5s (24.0%)             ← 自动计算
  (所有时间都被记录) ✅
```

---

## 参考资源

- **Playwright Debug 文档**: https://playwright.dev/docs/debug
- **MCP 协议规范**: https://modelcontextprotocol.io/
- **核心实现**: `packages/core/src/tools/mcp-debug-parser.ts`

---

**文档版本**: v1.0  
**最后更新**: 2025-10-16  
**作者**: Gemini CLI Team  
**状态**: ✅ 已完成并投入使用
