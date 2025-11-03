#!/usr/bin/env node

/**
 * 分析 Fetcher Debug 日志
 * 从时间戳中计算各阶段的执行时间
 */

import fs from 'fs';
import path from 'path';

const logFile = path.join(process.cwd(), 'fetcher-debug.log');

console.log('='.repeat(80));
console.log('📊 Fetcher MCP Server 内部执行时间分析');
console.log('='.repeat(80) + '\n');

if (!fs.existsSync(logFile)) {
  console.log('❌ 未找到日志文件: ' + logFile);
  console.log('💡 请先运行: node test-fetcher-with-debug-logs.js\n');
  process.exit(1);
}

const logs = fs.readFileSync(logFile, 'utf8');
const lines = logs.split('\n').filter((line) => line.trim());

// 提取所有带时间戳的事件
const events = [];
lines.forEach((line) => {
  const match = line.match(
    /^(\d{4}-\d{2}-\d{2}T[\d:.]+Z)\s+pw:(api|browser)\s+(.+)$/,
  );
  if (match) {
    events.push({
      timestamp: new Date(match[1]),
      category: match[2],
      message: match[3],
    });
  }
});

if (events.length === 0) {
  console.log('❌ 日志中没有找到时间戳事件');
  console.log('📄 日志内容:\n');
  console.log(logs);
  process.exit(1);
}

console.log(`🔍 找到 ${events.length} 个事件\n`);

// 定义关键事件 (类似 Playwright，因为 Fetcher 也使用 Playwright)
const keyEvents = [
  {
    name: '🚀 启动浏览器',
    start: /=> browserType\.launch/,
    end: /<= browserType\.launch.*succeeded/,
  },
  {
    name: '🌐 导航到 URL',
    start: /=> page\.goto started/,
    end: /"commit" event fired/,
  },
  {
    name: '⏳ 等待 DOMContentLoaded',
    start: /"commit" event fired/,
    end: /"domcontentloaded" event fired/,
  },
  {
    name: '📦 等待页面加载完成',
    start: /"domcontentloaded" event fired/,
    end: /"load" event fired/,
  },
  {
    name: '📄 提取页面内容',
    start: /=> page\.content started/,
    end: /<= page\.content succeeded/,
  },
  {
    name: '✅ page.goto 总耗时',
    start: /=> page\.goto started/,
    end: /<= page\.goto succeeded/,
  },
];

// 计算每个阶段的时间
console.log('⏱️  各阶段执行时间:\n');
console.log('-'.repeat(80));

const timing = {};
let totalServerTime = 0;

keyEvents.forEach(({ name, start, end }) => {
  const startEvent = events.find((e) => start.test(e.message));
  const endEvent = events.find((e) => end.test(e.message));

  if (startEvent && endEvent) {
    const duration = endEvent.timestamp - startEvent.timestamp;
    timing[name] = duration;

    console.log(`${name.padEnd(40)} ${duration.toString().padStart(6)}ms`);
  }
});

// 计算总的服务器执行时间
const firstEvent = events[0];
const lastEvent = events[events.length - 1];
totalServerTime = lastEvent.timestamp - firstEvent.timestamp;

console.log('-'.repeat(80));
console.log(
  `${'📊 服务器总执行时间'.padEnd(40)} ${totalServerTime.toString().padStart(6)}ms`,
);
console.log();

// 计算百分比
if (Object.keys(timing).length > 0) {
  console.log('📈 时间占比分析:\n');
  Object.entries(timing).forEach(([name, duration]) => {
    const percentage = ((duration / totalServerTime) * 100).toFixed(1);
    const bar = '█'.repeat(Math.round(percentage / 2));
    console.log(`${name.padEnd(40)} ${percentage.padStart(5)}% ${bar}`);
  });
}

// 详细事件时间线
console.log('\n' + '='.repeat(80));
console.log('📅 详细事件时间线 (相对时间)');
console.log('='.repeat(80) + '\n');

const baseTime = events[0].timestamp;
events.slice(0, 50).forEach((event, index) => {
  // 限制显示前50个事件
  const relativeTime = event.timestamp - baseTime;
  const delta = index > 0 ? event.timestamp - events[index - 1].timestamp : 0;

  const timeStr = `+${relativeTime}ms`.padStart(10);
  const deltaStr = delta > 0 ? `(+${delta}ms)`.padStart(12) : ''.padStart(12);
  const category = event.category === 'api' ? '🔷 API' : '🔶 Browser';
  const message = event.message.substring(0, 60);

  console.log(`${timeStr} ${deltaStr}  ${category}  ${message}`);
});

if (events.length > 50) {
  console.log(`\n... (还有 ${events.length - 50} 个事件)`);
}

console.log('\n✅ 分析完成!\n');
console.log('💡 提示:');
console.log('   • Fetcher 使用 Playwright 来抓取网页');
console.log('   • "启动浏览器" 包括启动进程和 WebSocket 连接');
console.log('   • "导航到 URL" 是发起请求到收到第一个字节');
console.log('   • "提取页面内容" 是从 DOM 中提取文本内容');
console.log();
