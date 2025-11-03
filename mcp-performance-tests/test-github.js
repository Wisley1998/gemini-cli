#!/usr/bin/env node

/**
 * GitHub MCP Server Performance Test
 * 测试GitHub MCP服务器的完整性能
 */

import { MCPClient } from './mcp-client.js';
import {
  printSeparator,
  printPerformanceSummary,
  validateEnvVars,
  handleError,
} from './utils.js';

// 验证环境变量
if (!validateEnvVars(['GITHUB_PERSONAL_ACCESS_TOKEN'])) {
  process.exit(1);
}

async function testGitHubMCP() {
  printSeparator('GitHub MCP Server Performance Test');
  console.log('测试 GitHub MCP Server 的完整执行时间');
  console.log('包括: Docker启动、协议握手、工具执行等所有阶段\n');

  const client = new MCPClient({
    command: 'docker',
    args: [
      'run',
      '-i',
      '--rm',
      '-e',
      'GITHUB_PERSONAL_ACCESS_TOKEN',
      'ghcr.io/github/github-mcp-server',
    ],
    env: {
      GITHUB_PERSONAL_ACCESS_TOKEN: process.env.GITHUB_PERSONAL_ACCESS_TOKEN,
    },
  });

  const testConfig = {
    testCases: [
      {
        name: '搜索仓库',
        tool: 'search_repositories',
        args: {
          query: 'model context protocol',
          maxResults: 5,
        },
        repeat: 2, // 执行2次，测试缓存效果
      },
      {
        name: '获取用户信息',
        tool: 'get_me',
        args: {},
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

    console.log('✅ GitHub MCP Server 测试完成!\n');
  } catch (error) {
    handleError(error, 'GitHub MCP Server 测试');
    process.exit(1);
  }
}

// 运行测试
testGitHubMCP().catch(console.error);
