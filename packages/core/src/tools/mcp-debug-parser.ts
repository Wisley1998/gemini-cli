/**
 * @license
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

/**
 * MCP Debug Log Parser
 *
 * 解析 MCP 工具的 DEBUG 日志，提取内部执行阶段的时间统计。
 * 支持 Playwright、Fetcher、GitHub 等 MCP 服务器。
 */

export interface McpInternalPhase {
  name: string;
  timeMs: number;
}

interface TimestampedEvent {
  timestamp: Date;
  category: string;
  message: string;
}

/**
 * 从 DEBUG 日志中提取时间戳事件
 */
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
      continue;
    }

    // Playwright 简化格式 (可能没有 pw: 前缀)
    const pwSimpleMatch = log.match(/^(\d{4}-\d{2}-\d{2}T[\d:.]+Z)\s+(.+)$/);
    if (
      pwSimpleMatch &&
      (pwSimpleMatch[2].includes('=>') || pwSimpleMatch[2].includes('<='))
    ) {
      events.push({
        timestamp: new Date(pwSimpleMatch[1]),
        category: 'api',
        message: pwSimpleMatch[2],
      });
      continue;
    }

    // GitHub format: [DEBUG] 2025-01-15 10:30:45 - API request started
    const ghMatch = log.match(
      /^\[DEBUG\]\s+(\d{4}-\d{2}-\d{2}\s+[\d:]+)\s+-\s+(.+)$/,
    );
    if (ghMatch) {
      events.push({
        timestamp: new Date(ghMatch[1]),
        category: 'debug',
        message: ghMatch[2],
      });
    }
  }

  return events;
}

/**
 * 查找两个事件之间的时间差
 */
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

/**
 * 解析 Playwright DEBUG 日志
 */
function parsePlaywrightLogs(events: TimestampedEvent[]): McpInternalPhase[] {
  const phases: McpInternalPhase[] = [];

  // 浏览器启动 - 更宽松的匹配模式
  const browserLaunch = findDuration(
    events,
    /=> browserType\.launch|launchPersistentContext started/,
    /<= browserType\.launch|launchPersistentContext succeeded/,
    'Browser Launch',
  );
  if (browserLaunch) phases.push(browserLaunch);

  // 创建上下文
  const contextCreation = findDuration(
    events,
    /=> browser\.newContext started/,
    /<= browser\.newContext succeeded/,
    'Context Creation',
  );
  if (contextCreation) phases.push(contextCreation);

  // 创建页面
  const pageCreation = findDuration(
    events,
    /=> browser\.newPage|context\.newPage started/,
    /<= browser\.newPage|context\.newPage succeeded/,
    'Page Creation',
  );
  if (pageCreation) phases.push(pageCreation);

  // 导航开始到提交 (主要是网络请求时间)
  const navigation = findDuration(
    events,
    /=> page\.goto started/,
    /"commit" event fired/,
    'Navigation',
  );
  if (navigation) phases.push(navigation);

  // DNS解析 + TCP连接 (如果有单独的日志)
  const dns = findDuration(
    events,
    /DNS lookup started/,
    /DNS lookup completed/,
    'DNS Lookup',
  );
  if (dns) phases.push(dns);

  const tcpConnection = findDuration(
    events,
    /TCP connection started/,
    /TCP connection established/,
    'TCP Connection',
  );
  if (tcpConnection) phases.push(tcpConnection);

  // DOMContentLoaded (HTML解析 + 同步脚本执行)
  const domReady = findDuration(
    events,
    /"commit" event fired/,
    /"domcontentloaded" event fired/,
    'DOMContentLoaded',
  );
  if (domReady) phases.push(domReady);

  // Page Load (所有资源加载完成,包括图片、CSS、异步脚本)
  const pageLoad = findDuration(
    events,
    /"domcontentloaded" event fired/,
    /"load" event fired/,
    'Page Load',
  );
  if (pageLoad) phases.push(pageLoad);

  // JavaScript 执行 (如果有 console API 调用)
  const jsExecution = findDuration(
    events,
    /=> page\.evaluate started/,
    /<= page\.evaluate succeeded/,
    'JS Execution',
  );
  if (jsExecution) phases.push(jsExecution);

  // 等待特定元素
  const waitForSelector = findDuration(
    events,
    /=> page\.waitForSelector started/,
    /<= page\.waitForSelector succeeded/,
    'Wait for Selector',
  );
  if (waitForSelector) phases.push(waitForSelector);

  // 元素定位 (locator)
  const locator = findDuration(
    events,
    /=> locator\.(click|fill|type|check|uncheck|selectOption) started/,
    /<= locator\.(click|fill|type|check|uncheck|selectOption) succeeded/,
    'Locator Action',
  );
  if (locator) phases.push(locator);

  // 点击操作
  const click = findDuration(
    events,
    /=> (page|locator|elementHandle)\.click started/,
    /<= (page|locator|elementHandle)\.click succeeded/,
    'Click',
  );
  if (click) phases.push(click);

  // 输入操作 (type/fill)
  const typeOrFill = findDuration(
    events,
    /=> (page|locator|elementHandle)\.(type|fill|press) started/,
    /<= (page|locator|elementHandle)\.(type|fill|press) succeeded/,
    'Type/Fill',
  );
  if (typeOrFill) phases.push(typeOrFill);

  // 等待加载状态
  const waitForLoadState = findDuration(
    events,
    /=> page\.waitForLoadState started/,
    /<= page\.waitForLoadState succeeded/,
    'Wait Load State',
  );
  if (waitForLoadState) phases.push(waitForLoadState);

  // 截图（如果有）
  const screenshot = findDuration(
    events,
    /=> page\.screenshot started/,
    /<= page\.screenshot succeeded/,
    'Screenshot',
  );
  if (screenshot) phases.push(screenshot);

  // 获取内容
  const getContent = findDuration(
    events,
    /=> page\.content started/,
    /<= page\.content succeeded/,
    'Get Content',
  );
  if (getContent) phases.push(getContent);

  // 关闭页面
  const pageClose = findDuration(
    events,
    /=> page\.close started/,
    /<= page\.close succeeded/,
    'Page Close',
  );
  if (pageClose) phases.push(pageClose);

  return phases;
}

/**
 * 计算"其他"时间 - 即总时间减去所有已知阶段的时间
 * @param phases 已解析的阶段
 * @param totalTimeMs 总时间(MCP Call 的总时间)
 * @returns 包含"其他"阶段的完整阶段列表
 */
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

/**
 * 解析 GitHub DEBUG 日志
 */
function parseGitHubLogs(events: TimestampedEvent[]): McpInternalPhase[] {
  const phases: McpInternalPhase[] = [];

  // API 请求
  const apiRequest = findDuration(
    events,
    /API request started/,
    /API request completed/,
    'API Request',
  );
  if (apiRequest) phases.push(apiRequest);

  // 认证
  const auth = findDuration(
    events,
    /Authentication started/,
    /Authentication completed/,
    'Authentication',
  );
  if (auth) phases.push(auth);

  // 数据解析
  const parsing = findDuration(
    events,
    /Parsing response started/,
    /Parsing response completed/,
    'Response Parsing',
  );
  if (parsing) phases.push(parsing);

  return phases;
}

/**
 * 主解析函数：根据服务器类型选择合适的解析器
 */
export function parseDebugLogs(
  logs: string[],
  serverName: string,
): McpInternalPhase[] {
  if (!logs || logs.length === 0) {
    return [];
  }

  const events = extractTimestampedEvents(logs);
  if (events.length === 0) {
    return [];
  }

  const serverLower = serverName.toLowerCase();

  // Playwright 或 Fetcher（Fetcher 内部使用 Playwright）
  if (serverLower.includes('playwright') || serverLower.includes('fetch')) {
    return parsePlaywrightLogs(events);
  }

  // GitHub
  if (serverLower.includes('github')) {
    return parseGitHubLogs(events);
  }

  // 未知服务器类型，返回空数组
  return [];
}

/**
 * 捕获 stderr 输出的辅助类
 */
export class StderrCapture {
  private logs: string[] = [];
  private originalWrite: typeof process.stderr.write;

  constructor() {
    this.originalWrite = process.stderr.write;
  }

  start(): void {
    this.logs = [];
    const self = this;

    process.stderr.write = function (
      chunk: any,
      encodingOrCallback?: any,
      callback?: any,
    ): boolean {
      const str = chunk.toString();
      // 只捕获 DEBUG 日志
      if (
        str.includes('pw:api') ||
        str.includes('pw:browser') ||
        str.includes('[DEBUG]')
      ) {
        self.logs.push(str);
      }
      // 仍然输出到原始 stderr（可选，用于调试）
      if (callback) {
        return self.originalWrite.call(
          process.stderr,
          chunk,
          encodingOrCallback,
          callback,
        );
      } else if (encodingOrCallback) {
        return self.originalWrite.call(
          process.stderr,
          chunk,
          encodingOrCallback,
        );
      } else {
        return self.originalWrite.call(process.stderr, chunk);
      }
    };
  }

  stop(): string[] {
    process.stderr.write = this.originalWrite;
    return this.logs;
  }

  getLogs(): string[] {
    return this.logs;
  }
}
