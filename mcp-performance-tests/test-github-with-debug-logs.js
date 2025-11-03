#!/usr/bin/env node

/**
 * GitHub MCP Server with DEBUG Logging
 * 启用详细日志来分析 Server 内部执行时间
 */

import { MCPClient } from './mcp-client.js';
import { printSeparator, handleError, validateEnvVars } from './utils.js';
import fs from 'fs';
import path from 'path';

// 验证环境变量
if (!validateEnvVars(['GITHUB_PERSONAL_ACCESS_TOKEN'])) {
  process.exit(1);
}

async function testWithDebugLogging() {
  printSeparator('GitHub MCP Server - 详细日志分析');
  console.log('启用详细日志来分析内部执行时间\n');

  const logFile = path.join(process.cwd(), 'github-debug.log');

  // 清空之前的日志
  if (fs.existsSync(logFile)) {
    fs.unlinkSync(logFile);
  }

  const client = new MCPClient({
    command: 'docker',
    args: [
      'run',
      '-i',
      '--rm',
      '-e',
      'GITHUB_PERSONAL_ACCESS_TOKEN',
      '-e',
      'LOG_LEVEL=debug', // 启用 debug 日志
      'ghcr.io/github/github-mcp-server',
    ],
    env: {
      GITHUB_PERSONAL_ACCESS_TOKEN: process.env.GITHUB_PERSONAL_ACCESS_TOKEN,
      LOG_LEVEL: 'debug',
    },
  });

  try {
    console.log('📝 启动 MCP Server (DEBUG 模式)...\n');

    const startTime = Date.now();
    await client.connect();
    const connectTime = Date.now() - startTime;

    await client.listTools();

    console.log('\n🧪 执行测试工具...\n');
    console.log('─'.repeat(70));

    // 执行 search_repositories
    const toolStartTime = Date.now();
    const result = await client.callTool('search_repositories', {
      query: 'model context protocol',
      maxResults: 3,
    });
    const toolTime = Date.now() - toolStartTime;

    console.log('\n✅ 工具执行完成');
    console.log(`⏱️  连接时间: ${connectTime}ms`);
    console.log(`⏱️  工具执行时间: ${toolTime}ms`);

    await client.disconnect();

    // 分析日志
    console.log('\n' + '='.repeat(70));
    console.log('📊 分析 GitHub MCP Server 日志');
    console.log('='.repeat(70) + '\n');

    if (fs.existsSync(logFile)) {
      const logs = fs.readFileSync(logFile, 'utf8');
      console.log('📄 完整日志文件: ' + logFile);
      console.log('\n📋 日志内容:');
      console.log('-'.repeat(70));
      console.log(logs);
    } else {
      console.log('📝 GitHub MCP Server 将日志输出到 stderr');
      console.log('💡 日志已显示在控制台输出中\n');
    }

    console.log('\n✅ 测试完成!\n');
  } catch (error) {
    handleError(error, 'GitHub DEBUG 日志测试');
    process.exit(1);
  }
}

// 运行测试
testWithDebugLogging().catch(console.error);
