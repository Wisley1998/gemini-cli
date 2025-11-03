#!/usr/bin/env node

/**
 * Huggingface MCP Server Performance Test
 * 测试Huggingface MCP服务器的完整性能
 */

import { MCPClient } from './mcp-client.js';
import {
  printSeparator,
  printPerformanceSummary,
  validateEnvVars,
  handleError,
} from './utils.js';

// 验证环境变量
if (!validateEnvVars(['HF_TOKEN'])) {
  process.exit(1);
}

async function testHuggingfaceMCP() {
  printSeparator('Huggingface MCP Server Performance Test');
  console.log('测试 Huggingface MCP Server 的完整执行时间');
  console.log('包括: npx启动、模型加载、协议握手、工具执行等\n');

  const client = new MCPClient({
    command: 'npx',
    args: ['@llmindset/hf-mcp-server'],
    env: {
      HF_TOKEN: process.env.HF_TOKEN,
    },
  });

  const testConfig = {
    testCases: [
      {
        name: '情感分析（简单测试）',
        tool: 'analyze_sentiment',
        args: {
          text: 'I love this product! It works great.',
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

    console.log('✅ Huggingface MCP Server 测试完成!\n');
  } catch (error) {
    handleError(error, 'Huggingface MCP Server 测试');
    process.exit(1);
  }
}

// 运行测试
testHuggingfaceMCP().catch(console.error);
