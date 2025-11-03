#!/usr/bin/env node

/**
 * Fetcher MCP Server Performance Test
 * 测试 Fetcher MCP 服务器的完整性能
 */

import { MCPClient } from './mcp-client.js';
import {
  printSeparator,
  printPerformanceSummary,
  handleError,
} from './utils.js';

async function testFetcherMCP() {
  printSeparator('Fetcher MCP Server Performance Test');
  console.log('测试 Fetcher MCP Server 的完整执行时间');
  console.log('包括: npx启动、Playwright浏览器初始化、协议握手、网页抓取等\n');

  const client = new MCPClient({
    command: 'npx',
    args: ['-y', 'fetcher-mcp'],
    env: {},
  });

  const testConfig = {
    testCases: [
      {
        name: '抓取简单网页',
        tool: 'fetch_url',
        args: {
          url: 'https://example.com',
          timeout: 30000,
          extractContent: true,
          disableMedia: true,
        },
        repeat: 2, // 执行2次，测试缓存效果
      },
      {
        name: '抓取并返回HTML',
        tool: 'fetch_url',
        args: {
          url: 'https://example.com',
          timeout: 30000,
          extractContent: false,
          returnHtml: true,
          disableMedia: true,
        },
      },
      {
        name: '批量抓取多个网页',
        tool: 'fetch_urls',
        args: {
          urls: ['https://example.com', 'https://example.org'],
          timeout: 30000,
          extractContent: true,
          disableMedia: true,
        },
      },
    ],
  };

  try {
    const stats = await client.runPerformanceTest(testConfig);

    // 打印详细统计
    printPerformanceSummary({
      startup: stats.startup,
      listTools: stats.listTools,
      toolCount: stats.toolCount,
      firstExecution: stats.executions[0]?.duration || 0,
      secondExecution: stats.executions[1]?.duration,
      shutdown: stats.shutdown,
      total: stats.total,
    });

    // 打印每个测试用例的执行时间
    if (stats.executions.length > 0) {
      console.log('\n📋 测试用例详细耗时:');
      stats.executions.forEach((exec, index) => {
        console.log(
          `   ${index + 1}. ${exec.name}: ${exec.duration}ms ${exec.success ? '✓' : '✗'}`,
        );
      });
      console.log();
    }

    console.log('✅ Fetcher MCP Server 测试完成!\n');
  } catch (error) {
    handleError(error, 'Fetcher MCP Server 测试');
    process.exit(1);
  }
}

// 运行测试
testFetcherMCP().catch(console.error);
