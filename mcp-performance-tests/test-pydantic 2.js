#!/usr/bin/env node

/**
 * Pydantic MCP Run Python Server Performance Test
 * 测试 Pydantic MCP Run Python 服务器的完整性能
 */

import { MCPClient } from './mcp-client.js';
import {
  printSeparator,
  printPerformanceSummary,
  handleError,
} from './utils.js';

async function testPydanticMCP() {
  printSeparator('Pydantic MCP Run Python Performance Test');
  console.log('测试 Pydantic MCP Run Python 的完整执行时间');
  console.log('包括: uvx启动、Deno初始化、协议握手、Python代码执行等\n');

  const client = new MCPClient({
    command: 'uvx',
    args: ['mcp-run-python@latest', 'stdio'],
    env: {},
  });

  const testConfig = {
    testCases: [
      {
        name: '执行简单Python代码',
        tool: 'run_python_code',
        args: {
          python_code: 'print("Hello from Python!")\nresult = 2 + 2\nresult',
        },
        repeat: 2, // 执行2次,测试缓存效果
      },
      {
        name: '执行带依赖的Python代码',
        tool: 'run_python_code',
        args: {
          python_code:
            'import datetime\ntoday = datetime.date.today()\nprint(f"Today is {today}")\ntoday.isoformat()',
        },
      },
      {
        name: '执行数学计算',
        tool: 'run_python_code',
        args: {
          python_code:
            'import math\nresult = math.sqrt(16) + math.pi\nprint(f"Result: {result}")\nresult',
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

    console.log('✅ Pydantic MCP Run Python 测试完成!\n');
  } catch (error) {
    handleError(error, 'Pydantic MCP Run Python 测试');
    process.exit(1);
  }
}

// 运行测试
testPydanticMCP().catch(console.error);
