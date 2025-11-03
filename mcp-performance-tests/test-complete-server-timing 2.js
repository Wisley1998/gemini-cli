#!/usr/bin/env node

/**
 * 完整的 Server 内部时间分析
 * 测试不同网页的加载时间并分析 DEBUG 日志
 */

import { MCPClient } from './mcp-client.js';
import { printSeparator, handleError } from './utils.js';
import fs from 'fs';
import path from 'path';
import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

const testCases = [
  { name: 'Example.com (极简)', url: 'https://example.com' },
  { name: 'Google 首页', url: 'https://www.google.com' },
  { name: 'GitHub 首页', url: 'https://github.com' },
];

async function runCompleteAnalysis() {
  printSeparator('MCP Server 内部时间完整分析');
  console.log('测试不同网页并分析服务器内部执行时间\n');

  const results = [];

  for (let i = 0; i < testCases.length; i++) {
    const testCase = testCases[i];
    const logFile = path.join(process.cwd(), `playwright-debug-${i}.log`);

    // 清空之前的日志
    if (fs.existsSync(logFile)) {
      fs.unlinkSync(logFile);
    }

    console.log('='.repeat(80));
    console.log(`🧪 测试 ${i + 1}/${testCases.length}: ${testCase.name}`);
    console.log('='.repeat(80) + '\n');

    const client = new MCPClient({
      command: 'npx',
      args: ['@playwright/mcp@latest'],
      env: {
        DEBUG: 'pw:api,pw:browser',
        DEBUG_FILE: logFile,
        DEBUG_COLORS: '0',
      },
    });

    try {
      await client.connect();

      const { duration, breakdown } = await client.callTool(
        'browser_navigate',
        {
          url: testCase.url,
        },
      );

      await client.disconnect();

      // 分析日志
      console.log('\n📊 分析 DEBUG 日志...\n');

      const timing = await analyzeLog(logFile);

      results.push({
        name: testCase.name,
        url: testCase.url,
        totalDuration: duration,
        breakdown: breakdown,
        serverTiming: timing,
      });

      console.log();
    } catch (error) {
      console.error(`❌ 测试失败: ${error.message}\n`);
      results.push({
        name: testCase.name,
        url: testCase.url,
        error: error.message,
      });
    }
  }

  // 打印汇总对比
  console.log('\n' + '='.repeat(100));
  console.log('📊 所有测试结果对比');
  console.log('='.repeat(100) + '\n');

  console.log(
    '网页                  总耗时    浏览器启动  导航   DOM加载  完全加载  其他',
  );
  console.log('-'.repeat(100));

  results.forEach((r) => {
    if (r.error) {
      console.log(`${r.name.padEnd(20)} ERROR: ${r.error}`);
      return;
    }

    const name = r.name.padEnd(20);
    const total = (r.totalDuration + 'ms').padStart(8);
    const launch = ((r.serverTiming?.browserLaunch || 0) + 'ms').padStart(10);
    const nav = ((r.serverTiming?.navigation || 0) + 'ms').padStart(6);
    const dom = ((r.serverTiming?.domLoad || 0) + 'ms').padStart(7);
    const load = ((r.serverTiming?.pageLoad || 0) + 'ms').padStart(8);
    const other = ((r.serverTiming?.other || 0) + 'ms').padStart(6);

    console.log(
      `${name} ${total}  ${launch}  ${nav}  ${dom}  ${load}  ${other}`,
    );
  });

  console.log('\n💡 结论:');
  console.log('   • 浏览器启动是最大开销 (首次访问时)');
  console.log('   • 复杂网页的导航和加载时间更长');
  console.log('   • 第二次访问同一网页时,只需导航时间 (浏览器已启动)');
  console.log('\n✅ 完整分析完成!\n');
}

async function analyzeLog(logFile) {
  if (!fs.existsSync(logFile)) {
    return null;
  }

  const logs = fs.readFileSync(logFile, 'utf8');
  const lines = logs.split('\n').filter((line) => line.trim());

  // 提取事件
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
    return null;
  }

  const timing = {};

  // 浏览器启动
  const launchStart = events.find((e) =>
    /=> browserType\.launch/.test(e.message),
  );
  const launchEnd = events.find((e) =>
    /<= browserType\.launch.*succeeded/.test(e.message),
  );
  if (launchStart && launchEnd) {
    timing.browserLaunch = launchEnd.timestamp - launchStart.timestamp;
  }

  // 导航
  const navStart = events.find((e) => /=> page\.goto started/.test(e.message));
  const commitEvent = events.find((e) =>
    /"commit" event fired/.test(e.message),
  );
  if (navStart && commitEvent) {
    timing.navigation = commitEvent.timestamp - navStart.timestamp;
  }

  // DOM 加载
  const domEvent = events.find((e) =>
    /"domcontentloaded" event fired/.test(e.message),
  );
  if (commitEvent && domEvent) {
    timing.domLoad = domEvent.timestamp - commitEvent.timestamp;
  }

  // 完全加载
  const loadEvent = events.find((e) => /"load" event fired/.test(e.message));
  if (domEvent && loadEvent) {
    timing.pageLoad = loadEvent.timestamp - domEvent.timestamp;
  }

  // 其他操作
  const firstEvent = events[0];
  const lastEvent = events[events.length - 1];
  const total = lastEvent.timestamp - firstEvent.timestamp;
  const accounted =
    (timing.browserLaunch || 0) +
    (timing.navigation || 0) +
    (timing.domLoad || 0) +
    (timing.pageLoad || 0);
  timing.other = total - accounted;

  // 打印详细信息
  console.log('⏱️  Server 内部时间分解:');
  console.log(`   🚀 浏览器启动: ${timing.browserLaunch || 0}ms`);
  console.log(`   🌐 导航到 URL: ${timing.navigation || 0}ms`);
  console.log(`   ⏳ DOM 加载: ${timing.domLoad || 0}ms`);
  console.log(`   📦 完全加载: ${timing.pageLoad || 0}ms`);
  console.log(`   🔧 其他操作: ${timing.other || 0}ms`);
  console.log(`   📊 总计: ${total}ms`);

  return timing;
}

runCompleteAnalysis().catch(console.error);
