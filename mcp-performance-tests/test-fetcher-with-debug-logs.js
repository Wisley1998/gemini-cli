#!/usr/bin/env node

/**
 * Fetcher MCP Server with DEBUG Logging
 * 启用详细日志来分析 Server 内部执行时间
 */

import { MCPClient } from './mcp-client.js';
import { printSeparator, handleError } from './utils.js';
import fs from 'fs';
import path from 'path';

async function testWithDebugLogging() {
  printSeparator('Fetcher MCP Server - 详细日志分析');
  console.log('启用 Playwright DEBUG 日志来分析内部执行时间\n');

  const logFile = path.join(process.cwd(), 'fetcher-debug.log');

  // 清空之前的日志
  if (fs.existsSync(logFile)) {
    fs.unlinkSync(logFile);
  }

  const client = new MCPClient({
    command: 'npx',
    args: ['-y', 'fetcher-mcp'],
    env: {
      DEBUG: 'pw:api,pw:browser', // Fetcher 使用 Playwright，启用相同的 DEBUG
      DEBUG_FILE: logFile,
      DEBUG_COLORS: '0',
    },
  });

  try {
    console.log('📝 启动 MCP Server (DEBUG 模式)...\n');

    await client.connect();
    await client.listTools();

    console.log('\n🧪 执行测试工具...\n');
    console.log('─'.repeat(70));

    // 执行 fetch_url
    await client.callTool('fetch_url', {
      url: 'https://example.com',
      timeout: 30000,
      extractContent: true,
      disableMedia: true,
    });

    await client.disconnect();

    // 分析日志
    console.log('\n' + '='.repeat(70));
    console.log('📊 分析 Fetcher MCP Server 日志');
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
        console.log('   💡 Fetcher 可能没有输出足够的 DEBUG 日志');
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
      console.log('💡 Fetcher 可能没有写入日志,或者不支持 DEBUG_FILE');
    }

    console.log('\n✅ 测试完成!\n');
  } catch (error) {
    handleError(error, 'Fetcher DEBUG 日志测试');
    process.exit(1);
  }
}

/**
 * 解析 Playwright 日志提取时间信息
 */
function parsePlaywrightLogs(logs) {
  const timing = {};
  const lines = logs.split('\n');

  // 寻找关键的时间标记
  const patterns = [
    { name: 'Browser Launch', pattern: /browserType\.launch/ },
    { name: 'Page Navigation', pattern: /page\.goto/ },
    { name: 'Content Extraction', pattern: /page\.content/ },
  ];

  patterns.forEach(({ name, pattern }) => {
    const matches = lines.filter((line) => pattern.test(line));
    if (matches.length > 0) {
      timing[name] = `Found ${matches.length} operations`;
    }
  });

  return timing;
}

// 运行测试
testWithDebugLogging().catch(console.error);
