#!/usr/bin/env node

/**
 * Playwright MCP Server Performance Test
 * 测试Playwright MCP服务器的完整性能
 */

import { MCPClient } from './mcp-client.js';
import {
  printSeparator,
  printPerformanceSummary,
  handleError,
} from './utils.js';

async function testPlaywrightMCP() {
  printSeparator('Playwright MCP Server Performance Test');
  console.log('测试 Playwright MCP Server 的完整执行时间');
  console.log('包括: npx启动、浏览器初始化、协议握手、工具执行等\n');

  const client = new MCPClient({
    command: 'npx',
    args: ['@playwright/mcp@latest'],
    env: {},
  });

  const testConfig = {
    testCases: [
      {
        name: '打开网页并截图',
        tool: 'browser_navigate',
        args: {
          url: 'https://example.com',
        },
        repeat: 2, // 执行2次，测试缓存效果
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

    console.log('✅ Playwright MCP Server 测试完成!\n');
  } catch (error) {
    handleError(error, 'Playwright MCP Server 测试');
    process.exit(1);
  }
}

// 运行测试
testPlaywrightMCP().catch(console.error);
