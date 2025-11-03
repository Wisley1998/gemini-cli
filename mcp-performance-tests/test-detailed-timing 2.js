#!/usr/bin/env node

/**
 * Detailed MCP Timing Analysis
 * 详细分析多个 MCP 工具的内部时间分解
 */

import { MCPClient } from './mcp-client.js';
import { printSeparator, handleError } from './utils.js';

async function testDetailedTiming() {
  printSeparator('MCP 内部时间详细分析');
  console.log('测试多个工具,分析 MCP Call 内部各阶段的时间分布\n');

  const client = new MCPClient({
    command: 'npx',
    args: ['@playwright/mcp@latest'],
    env: {},
  });

  const testConfig = {
    testCases: [
      {
        name: '浏览器导航 (首次)',
        tool: 'browser_navigate',
        args: { url: 'https://example.com' },
        repeat: 1,
      },
      {
        name: '截图 (需要等待加载)',
        tool: 'browser_take_screenshot',
        args: {},
        repeat: 1,
      },
      {
        name: '获取控制台消息 (快速操作)',
        tool: 'browser_console_messages',
        args: {},
        repeat: 1,
      },
      {
        name: '再次导航 (缓存效果)',
        tool: 'browser_navigate',
        args: { url: 'https://example.com' },
        repeat: 1,
      },
    ],
  };

  try {
    await client.connect();
    await client.listTools();

    console.log('\n📊 开始执行测试用例...\n');

    const results = [];

    for (let i = 0; i < testConfig.testCases.length; i++) {
      const testCase = testConfig.testCases[i];
      console.log(`${'─'.repeat(70)}`);
      console.log(
        `🧪 测试 ${i + 1}/${testConfig.testCases.length}: ${testCase.name}`,
      );
      console.log(`${'─'.repeat(70)}`);

      const { result, duration, breakdown, serverTiming } =
        await client.callTool(testCase.tool, testCase.args);

      results.push({
        name: testCase.name,
        tool: testCase.tool,
        duration,
        breakdown,
        serverTiming,
      });

      console.log();
    }

    await client.disconnect();

    // 打印汇总对比
    console.log('\n' + '='.repeat(70));
    console.log('📊 MCP 内部时间对比分析');
    console.log('='.repeat(70) + '\n');

    console.log(
      '工具名称                          总耗时    请求准备  传输发送  服务器执行  传输接收  响应解析',
    );
    console.log('-'.repeat(100));

    results.forEach((r) => {
      const p = r.breakdown.phases;
      const name = r.name.padEnd(30);
      const total = r.duration.toString().padStart(6) + 'ms';
      const reqPrep = (p.requestPreparation || 0).toFixed(1).padStart(7) + 'ms';
      const transSend = (p.transportSend || 0).toFixed(1).padStart(7) + 'ms';
      const serverExec = (p.serverExecution || 0).toFixed(1).padStart(9) + 'ms';
      const transRecv = (p.transportReceive || 0).toFixed(1).padStart(7) + 'ms';
      const respParse = (p.responseParsing || 0).toFixed(1).padStart(7) + 'ms';

      console.log(
        `${name} ${total}  ${reqPrep}  ${transSend}  ${serverExec}  ${transRecv}  ${respParse}`,
      );
    });

    console.log('\n💡 分析结论:');
    console.log('   • 请求准备和响应解析: 通常 < 1ms (JSON 序列化/反序列化)');
    console.log('   • 传输发送和接收: 通常 < 1ms (Stdio 管道非常快)');
    console.log('   • 服务器执行: 占总时间的 99%+ (真实的工具操作)');
    console.log('\n✅ 测试完成!\n');
  } catch (error) {
    handleError(error, 'MCP 内部时间分析');
    process.exit(1);
  }
}

testDetailedTiming().catch(console.error);
