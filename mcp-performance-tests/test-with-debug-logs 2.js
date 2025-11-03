#!/usr/bin/env node

/**
 * Playwright MCP Server with DEBUG Logging
 * 启用详细日志来分析 Server 内部执行时间
 */

import { MCPClient } from './mcp-client.js';
import { printSeparator, handleError } from './utils.js';
import fs from 'fs';
import path from 'path';

async function testWithDebugLogging() {
  printSeparator('Playwright MCP Server - 详细日志分析');
  console.log('启用 Playwright DEBUG 日志来分析内部执行时间\n');

  const logFile = path.join(process.cwd(), 'playwright-debug.log');

  // 清空之前的日志
  if (fs.existsSync(logFile)) {
    fs.unlinkSync(logFile);
  }

  const client = new MCPClient({
    command: 'npx',
    args: ['@playwright/mcp@latest'],
    env: {
      DEBUG: 'pw:api,pw:browser', // 启用 Playwright API 和浏览器日志
      DEBUG_FILE: logFile, // 日志输出到文件
      DEBUG_COLORS: '0', // 禁用颜色,方便解析
    },
  });

  try {
    console.log('📝 启动 MCP Server (DEBUG 模式)...\n');

    await client.connect();
    await client.listTools();

    console.log('\n🧪 执行测试工具...\n');
    console.log('─'.repeat(70));

    // 执行 browser_navigate
    await client.callTool('browser_navigate', {
      url: 'https://example.com',
    });

    await client.disconnect();

    // 分析日志
    console.log('\n' + '='.repeat(70));
    console.log('📊 分析 Playwright DEBUG 日志');
    console.log('='.repeat(70) + '\n');

    if (fs.existsSync(logFile)) {
      const logs = fs.readFileSync(logFile, 'utf8');
      const timing = parsePlaywrightLogs(logs);

      console.log('🔍 从日志中提取的时间信息:\n');

      if (Object.keys(timing).length > 0) {
        Object.entries(timing).forEach(([operation, time]) => {
          console.log(`   ${operation.padEnd(40)} ${time}`);
        });
      } else {
        console.log('   ⚠️  未找到详细的时间信息');
        console.log('   💡 Playwright 可能没有输出足够的 DEBUG 日志');
      }

      console.log('\n📄 完整日志文件: ' + logFile);
      console.log('💡 你可以手动检查日志文件来查看更多细节\n');

      // 显示日志摘要
      console.log('📋 日志摘要 (前30行):');
      console.log('-'.repeat(70));
      const lines = logs.split('\n').slice(0, 30);
      lines.forEach((line) => {
        if (line.trim()) {
          console.log('   ' + line.substring(0, 100));
        }
      });
      if (logs.split('\n').length > 30) {
        console.log(`   ... (还有 ${logs.split('\n').length - 30} 行)`);
      }
    } else {
      console.log('❌ 未找到日志文件');
      console.log('💡 Playwright 可能没有写入日志,或者不支持 DEBUG_FILE');
    }

    console.log('\n✅ 测试完成!\n');
  } catch (error) {
    handleError(error, 'Playwright DEBUG 日志测试');
    process.exit(1);
  }
}

/**
 * 解析 Playwright 日志提取时间信息
 */
function parsePlaywrightLogs(logs) {
  const timing = {};
  const lines = logs.split('\n');

  // 查找常见的时间戳模式
  const patterns = [
    // pw:api chromium.launch() 开始/结束
    {
      regex: /pw:api.*chromium\.launch\(\).*\((\d+)ms\)/,
      key: 'Browser Launch',
    },
    // pw:api page.goto()
    {
      regex: /pw:api.*page\.goto\(.*\).*\((\d+)ms\)/,
      key: 'Page Navigation',
    },
    // pw:api page.waitForLoadState()
    {
      regex: /pw:api.*waitForLoadState.*\((\d+)ms\)/,
      key: 'Wait For Load',
    },
    // pw:api page.screenshot()
    {
      regex: /pw:api.*screenshot.*\((\d+)ms\)/,
      key: 'Screenshot',
    },
    // 通用的 finished 模式
    {
      regex: /pw:api.*([\w.]+)\(\).*finished.*\((\d+)ms\)/,
      extract: (match) => [match[1], match[2] + 'ms'],
    },
  ];

  lines.forEach((line) => {
    patterns.forEach((pattern) => {
      const match = line.match(pattern.regex);
      if (match) {
        if (pattern.extract) {
          const [key, value] = pattern.extract(match);
          timing[key] = value;
        } else {
          timing[pattern.key] = match[1] + 'ms';
        }
      }
    });
  });

  // 查找时间戳并计算间隔
  const timestamps = [];
  lines.forEach((line, index) => {
    const tsMatch = line.match(/\[(.+?)\]/);
    if (tsMatch) {
      timestamps.push({
        line: index,
        time: new Date(tsMatch[1]),
        content: line,
      });
    }
  });

  // 如果找到时间戳,计算关键操作的间隔
  if (timestamps.length > 1) {
    for (let i = 1; i < timestamps.length; i++) {
      const duration = timestamps[i].time - timestamps[i - 1].time;
      if (duration > 10) {
        // 只显示 >10ms 的间隔
        const prevLine = timestamps[i - 1].content.substring(0, 60);
        timing[`Interval ${i} (${prevLine}...)`] = duration + 'ms';
      }
    }
  }

  return timing;
}

testWithDebugLogging().catch(console.error);
