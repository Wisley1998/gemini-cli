#!/usr/bin/env node

/**
 * Docker MCP Server Performance Test
 * 测试 Docker MCP 服务器的完整性能
 */

import { MCPClient } from './mcp-client.js';
import {
  printSeparator,
  printPerformanceSummary,
  handleError,
} from './utils.js';

async function testDockerMCP() {
  printSeparator('Docker MCP Server Performance Test');
  console.log('测试 Docker MCP Server 的完整执行时间');
  console.log('包括: uvx启动、Docker SDK初始化、协议握手、容器管理操作等\n');

  const client = new MCPClient({
    command: 'uvx',
    args: ['mcp-server-docker'],
    env: {},
  });

  const testConfig = {
    testCases: [
      {
        name: '列出所有容器',
        tool: 'list_containers',
        args: {
          all: true,
        },
      },
      {
        name: '列出所有镜像',
        tool: 'list_images',
        args: {},
      },
      {
        name: '列出 Docker 网络',
        tool: 'list_networks',
        args: {},
      },
      {
        name: '列出 Docker 卷',
        tool: 'list_volumes',
        args: {},
      },
      {
        name: '拉取轻量镜像',
        tool: 'pull_image',
        args: {
          image: 'alpine:latest',
        },
      },
      {
        name: '创建测试容器',
        tool: 'create_container',
        args: {
          image: 'alpine:latest',
          name: 'mcp-test-alpine',
          command: ['echo', 'Hello from MCP Docker test!'],
        },
      },
      {
        name: '启动测试容器',
        tool: 'start_container',
        args: {
          container_id: 'mcp-test-alpine',
        },
      },
      {
        name: '获取容器日志',
        tool: 'fetch_container_logs',
        args: {
          container_id: 'mcp-test-alpine',
          tail: 50,
        },
      },
      {
        name: '停止测试容器',
        tool: 'stop_container',
        args: {
          container_id: 'mcp-test-alpine',
        },
      },
      {
        name: '删除测试容器',
        tool: 'remove_container',
        args: {
          container_id: 'mcp-test-alpine',
          force: true,
        },
      },
      {
        name: '删除测试镜像',
        tool: 'remove_image',
        args: {
          image: 'alpine:latest',
          force: false,
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
        const status = exec.success ? '✓' : '✗';
        const errorInfo = exec.success
          ? ''
          : ` (${exec.error?.split('\n')[0]})`;
        console.log(
          `   ${index + 1}. ${exec.name}: ${exec.duration}ms ${status}${errorInfo}`,
        );
      });
      console.log();
    }

    // 统计成功/失败
    const successCount = stats.executions.filter((e) => e.success).length;
    const failCount = stats.executions.filter((e) => !e.success).length;

    console.log(
      `📊 测试结果: ${successCount} 成功 / ${failCount} 失败 / ${stats.executions.length} 总计`,
    );
    console.log();
    console.log('✅ Docker MCP Server 测试完成!\n');
  } catch (error) {
    handleError(error, 'Docker MCP Server 测试');
    process.exit(1);
  }
}

// 运行测试
testDockerMCP().catch((error) => {
  console.error('Unhandled error:', error);
  process.exit(1);
});
