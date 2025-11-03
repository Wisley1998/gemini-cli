# MCP 内部时间分析改进

## 问题发现

在分析 Gemini CLI 的性能输出时，发现 Playwright MCP 和 Fetcher MCP 的内部时间分解存在以下问题：

### 原始输出示例

```
│      • fetch_url:            24.0s (31.8%)
│        ‣ MCP Call:           21.0s (87.5%)
│          - DOMContentLoaded: 1.8s (8.4%)
│          - Other:            869ms (4.1%)
│          - Page Load:        847ms (4.0%)
│          - Navigation:       434ms (2.1%)
│          - Browser Launch:   96ms (0.5%)
│          - Get Content:      22ms (0.1%)
│          - Context Creation: 2ms (0.0%)
│          - Page Close:       2ms (0.0%)
│
│      • browser_navigate:     4.0s (5.4%)
│        ‣ MCP Call:           3.5s (87.6%)
│          - DOMContentLoaded: 1.8s (52.2%)
│          - Browser Launch:   1.2s (33.9%)
│          - Navigation:       461ms (13.0%)
│          - Page Load:        1ms (0.0%)
│
│      • browser_click:        2.0s (2.6%)
│        ‣ MCP Call:           1.5s (74.4%)
│        [无内部分解]
│
│      • browser_type:         1.6s (2.1%)
│        ‣ MCP Call:           1.1s (67.7%)
│        [无内部分解]
│
│      • browser_snapshot:     1.1s (1.4%)
│        ‣ MCP Call:           63ms (5.9%)
│        [无内部分解]
```

### 问题分析

1. **`browser_navigate` 和 `fetch_url` 有详细分解** ✅
   - 这两个工具都涉及页面导航，触发了完整的页面加载生命周期
   - 包括：Browser Launch、Navigation、DOMContentLoaded、Page Load 等

2. **`browser_click`、`browser_type`、`browser_snapshot` 缺少分解** ❌
   - 这些工具执行不同的 Playwright API 调用
   - 但解析器没有捕获这些特定操作的内部时间

3. **根本原因**
   - `parsePlaywrightLogs()` 函数只捕获了页面导航相关的阶段
   - 缺少对 `page.click`、`page.type`/`page.fill`、`page.screenshot` 等操作的时间解析

## 改进方案

### 新增的时间阶段

在 `packages/core/src/tools/mcp-debug-parser.ts` 中添加以下阶段：

```typescript
// 1. 元素定位 (Locator)
const locator = findDuration(
  events,
  /=> locator\.(click|fill|type|check|uncheck|selectOption) started/,
  /<= locator\.(click|fill|type|check|uncheck|selectOption) succeeded/,
  'Locator Action',
);

// 2. 点击操作 (Click)
const click = findDuration(
  events,
  /=> (page|locator|elementHandle)\.click started/,
  /<= (page|locator|elementHandle)\.click succeeded/,
  'Click',
);

// 3. 输入操作 (Type/Fill)
const typeOrFill = findDuration(
  events,
  /=> (page|locator|elementHandle)\.(type|fill|press) started/,
  /<= (page|locator|elementHandle)\.(type|fill|press) succeeded/,
  'Type/Fill',
);

// 4. 等待加载状态 (Wait Load State)
const waitForLoadState = findDuration(
  events,
  /=> page\.waitForLoadState started/,
  /<= page\.waitForLoadState succeeded/,
  'Wait Load State',
);
```

### 完整的阶段列表

改进后，`parsePlaywrightLogs()` 将捕获以下所有阶段：

| 阶段名称               | 对应 API                | 适用工具            | 说明               |
| ---------------------- | ----------------------- | ------------------- | ------------------ |
| Browser Launch         | `browserType.launch`    | 所有工具（首次）    | 浏览器启动时间     |
| Context Creation       | `browser.newContext`    | 所有工具            | 浏览器上下文创建   |
| Page Creation          | `browser.newPage`       | 所有工具            | 页面对象创建       |
| Navigation             | `page.goto`             | navigate, fetch_url | 导航到 URL         |
| DOMContentLoaded       | 事件                    | navigate, fetch_url | DOM 解析完成       |
| Page Load              | 事件                    | navigate, fetch_url | 页面完全加载       |
| **Locator Action** ✨  | `locator.*`             | click, type         | **新增：元素定位** |
| **Click** ✨           | `page.click`            | browser_click       | **新增：点击操作** |
| **Type/Fill** ✨       | `page.type/fill`        | browser_type        | **新增：输入操作** |
| **Wait Load State** ✨ | `page.waitForLoadState` | 多个工具            | **新增：等待加载** |
| Screenshot             | `page.screenshot`       | browser_snapshot    | 截图操作           |
| Get Content            | `page.content`          | fetch_url           | 获取页面内容       |
| Page Close             | `page.close`            | 所有工具（结束）    | 关闭页面           |

## 预期效果

改进后的输出示例：

```
│      • browser_click:        2.0s (2.6%)
│        ‣ MCP Call:           1.5s (74.4%)
│          - Locator Action:   800ms (53.3%)   ← 新增
│          - Click:            500ms (33.3%)   ← 新增
│          - Other:            200ms (13.3%)
│
│      • browser_type:         1.6s (2.1%)
│        ‣ MCP Call:           1.1s (67.7%)
│          - Locator Action:   400ms (36.4%)   ← 新增
│          - Type/Fill:        600ms (54.5%)   ← 新增
│          - Other:            100ms (9.1%)
│
│      • browser_snapshot:     1.1s (1.4%)
│        ‣ MCP Call:           63ms (5.9%)
│          - Screenshot:       50ms (79.4%)    ← 原有，现在能显示
│          - Other:            13ms (20.6%)
```

## 验证方法

### 1. 使用 DEBUG 模式测试

```bash
# 启用 Playwright DEBUG 日志
DEBUG="pw:api,pw:browser" gemini --yolo

# 或使用性能测试脚本
cd mcp-performance-tests
./quick-test.sh playwright-debug
```

### 2. 检查日志输出

查看生成的 `playwright-debug.log`，确认包含：

```
pw:api => locator.click started
pw:api <= locator.click succeeded
pw:api => page.type started
pw:api <= page.type succeeded
pw:api => page.screenshot started
pw:api <= page.screenshot succeeded
```

### 3. 分析性能报告

运行 Gemini CLI 后，在最终的性能统计中检查是否显示了新的内部时间阶段。

## 技术细节

### Playwright Debug 日志格式

Playwright 使用一致的日志格式：

```
<timestamp> pw:api => <method> started [<params>]
<timestamp> pw:api <= <method> succeeded [<result>]
```

### 时间计算方法

`findDuration()` 函数通过匹配日志的开始和结束模式来计算持续时间：

```typescript
function findDuration(
  events: TimestampedEvent[],
  startPattern: RegExp, // 开始模式
  endPattern: RegExp, // 结束模式
  name: string, // 阶段名称
): McpInternalPhase | null;
```

### "Other" 时间

如果解析的阶段时间总和小于 MCP Call 总时间，会自动添加 "Other" 阶段：

```typescript
const accountedTimeMs = phases.reduce((sum, phase) => sum + phase.timeMs, 0);
const otherTimeMs = totalTimeMs - accountedTimeMs;

// 只有当"其他"时间超过 100ms 或超过总时间的 5% 时才添加
if (otherTimeMs > 100 && otherTimeMs / totalTimeMs > 0.05) {
  phases.push({ name: 'Other', timeMs: otherTimeMs });
}
```

## 后续改进

### 1. 支持更多 Playwright API

- `page.hover` - 鼠标悬停
- `page.select` - 下拉选择
- `page.check/uncheck` - 复选框操作
- `page.focus` - 聚焦元素

### 2. 区分同步/异步操作

某些操作可能有同步和异步版本，可以进一步细分。

### 3. 网络请求详情

捕获 Playwright 的网络请求时间：

- `page.route` - 路由拦截
- `page.waitForResponse` - 等待响应

### 4. 资源加载分析

解析资源加载时间：

- JavaScript 文件
- CSS 文件
- 图片资源
- 字体文件

## 相关文档

- [MCP Performance Testing](../mcp-performance-tests/README.md)
- [MCP Internal Timing](../docs/mcp-internal-timing.md)
- [API Logging Guide](./api-logging.md)

## 更新日期

- **创建**: 2025-10-16
- **作者**: Gemini CLI Team
- **版本**: 1.0.0
