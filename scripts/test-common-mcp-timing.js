#!/usr/bin/env node

/**
 * @license
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

/**
 * 快速测试常见 MCP Server 的 timing 支持
 *
 * 直接测试几个常见的公开 MCP Server,不需要配置文件
 */

import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';

// 常见的 MCP Server 配置
const COMMON_SERVERS = [
  {
    name: 'Playwright',
    command: 'npx',
    args: ['-y', '@playwright/mcp@latest'],
    testTool: 'playwright_navigate',
    testParams: { url: 'https://example.com' },
  },
  {
    name: 'Filesystem (bundled)',
    command: 'node',
    args: ['packages/core/dist/mcp-servers/filesystem.js'],
    testTool: 'list_directory',
    testParams: { path: '.' },
  },
];

// 提取 timing 元数据
function extractTimingMetadata(response) {
  if (!response || typeof response !== 'object') {
    return null;
  }

  const paths = [
    response._meta?.timing,
    response.meta?.timing,
    response.timing,
    response._timing,
    response._meta?.performance,
    response.performance,
  ];

  for (const timing of paths) {
    if (timing && typeof timing === 'object') {
      return timing;
    }
  }

  return null;
}

// 测试单个 Server
async function testServer(config) {
  console.log(`\n${'='.repeat(70)}`);
  console.log(`🔍 测试: ${config.name}`);
  console.log(`📦 命令: ${config.command} ${config.args.join(' ')}`);
  console.log(`${'='.repeat(70)}`);

  const client = new Client({
    name: 'timing-tester',
    version: '1.0.0',
  });

  let transport;
  try {
    console.log('📡 启动服务器并连接...');
    transport = new StdioClientTransport({
      command: config.command,
      args: config.args,
      env: process.env,
      stderr: 'pipe',
    });

    // 监听 stderr 以查看可能的错误
    let stderrOutput = '';
    if (transport.stderr) {
      transport.stderr.on('data', (data) => {
        stderrOutput += data.toString();
      });
    }

    await client.connect(transport, { timeout: 30000 });
    console.log('✅ 连接成功');

    // 列出工具
    console.log('\n📋 获取工具列表...');
    const toolsResult = await client.request(
      { method: 'tools/list' },
      { parse: (data) => data },
    );

    const tools = toolsResult.tools || [];
    console.log(`✅ 找到 ${tools.length} 个工具`);

    if (tools.length > 0) {
      console.log(
        '   工具列表:',
        tools
          .slice(0, 5)
          .map((t) => t.name)
          .join(', '),
        tools.length > 5 ? '...' : '',
      );
    }

    // 查找测试工具
    const testTool = tools.find((t) => t.name === config.testTool) || tools[0];
    if (!testTool) {
      console.log('⚠️  没有可用的工具');
      return { name: config.name, status: 'no_tools' };
    }

    console.log(`\n🧪 测试工具: ${testTool.name}`);
    console.log(`📝 描述: ${testTool.description || 'N/A'}`);

    // 调用工具
    console.log(`📤 发送请求...`);
    const startTime = Date.now();

    let callResult;
    try {
      callResult = await client.request(
        {
          method: 'tools/call',
          params: {
            name: testTool.name,
            arguments: config.testParams,
          },
        },
        { parse: (data) => data },
      );
    } catch (error) {
      console.log(`⚠️  工具调用出错: ${error.message}`);
      console.log('📋 这可能是正常的(参数问题),继续检查响应...');
      callResult = {};
    }

    const endTime = Date.now();
    const clientTime = endTime - startTime;
    console.log(`⏱️  客户端测量时间: ${clientTime}ms`);

    // 检查 timing 元数据
    console.log('\n🔎 检查响应中的 timing 元数据...');

    // 先检查完整响应
    const timing = extractTimingMetadata(callResult);

    if (timing) {
      console.log('✅ ✅ ✅ 找到 timing 元数据! ✅ ✅ ✅');
      console.log('\n📊 Timing 数据:');
      console.log(JSON.stringify(timing, null, 2));

      // 分析结构
      const keys = Object.keys(timing);
      console.log(`\n📈 可用字段: ${keys.join(', ')}`);

      // 尝试计算开销
      const totalFields = ['total', 'totalMs', 'duration', 'durationMs'];
      const totalField = totalFields.find((f) => timing[f] !== undefined);
      if (totalField) {
        const serverTime = timing[totalField];
        const overhead = clientTime - serverTime;
        console.log(`\n⚡ 性能对比:`);
        console.log(`   服务器报告时间: ${serverTime}ms`);
        console.log(`   客户端测量时间: ${clientTime}ms`);
        console.log(
          `   传输开销: ${overhead}ms (${((overhead / clientTime) * 100).toFixed(1)}%)`,
        );
      }

      return {
        name: config.name,
        status: 'supported',
        timing: timing,
        testTool: testTool.name,
      };
    } else {
      console.log('❌ 未找到 timing 元数据');

      // 显示响应结构以便分析
      console.log('\n📄 响应结构预览:');
      const preview = JSON.stringify(callResult, null, 2);
      if (preview.length > 800) {
        console.log(preview.slice(0, 800) + '\n... (truncated)');
      } else {
        console.log(preview);
      }

      return {
        name: config.name,
        status: 'not_supported',
        testTool: testTool.name,
      };
    }
  } catch (error) {
    console.error(`❌ 测试失败: ${error.message}`);
    if (error.stack) {
      console.error(
        '📋 错误堆栈:',
        error.stack.split('\n').slice(0, 3).join('\n'),
      );
    }
    return {
      name: config.name,
      status: 'error',
      error: error.message,
    };
  } finally {
    try {
      await client.close();
      if (transport) {
        await transport.close();
      }
    } catch (e) {
      // Ignore cleanup errors
    }
  }
}

// 主函数
async function main() {
  console.log('🚀 MCP Server Timing 支持快速测试');
  console.log('📦 测试常见的公开 MCP Server\n');

  const results = [];

  for (const serverConfig of COMMON_SERVERS) {
    const result = await testServer(serverConfig);
    results.push(result);

    // 等待一下,避免并发问题
    await new Promise((resolve) => setTimeout(resolve, 1000));
  }

  // 汇总报告
  console.log('\n\n' + '='.repeat(70));
  console.log('📊 测试汇总');
  console.log('='.repeat(70));

  const supported = results.filter((r) => r.status === 'supported');
  const notSupported = results.filter((r) => r.status === 'not_supported');
  const errors = results.filter((r) => r.status === 'error');
  const noTools = results.filter((r) => r.status === 'no_tools');

  console.log(`\n总测试数: ${results.length}`);
  console.log(`✅ 支持 timing: ${supported.length}`);
  console.log(`❌ 不支持 timing: ${notSupported.length}`);
  console.log(`⚠️  测试失败: ${errors.length}`);
  console.log(`⚪ 无可用工具: ${noTools.length}`);

  if (supported.length > 0) {
    console.log('\n🎉 支持 timing 元数据的服务器:');
    supported.forEach((r) => {
      console.log(`   ✅ ${r.name} (工具: ${r.testTool})`);
      if (r.timing) {
        const keys = Object.keys(r.timing);
        console.log(`      字段: ${keys.join(', ')}`);
      }
    });
  }

  if (notSupported.length > 0) {
    console.log('\n❌ 不支持 timing 元数据的服务器:');
    notSupported.forEach((r) => {
      console.log(`   - ${r.name} (工具: ${r.testTool})`);
    });
  }

  if (errors.length > 0) {
    console.log('\n⚠️  测试失败的服务器:');
    errors.forEach((r) => {
      console.log(`   - ${r.name}: ${r.error}`);
    });
  }

  // 结论
  console.log('\n\n💡 结论:');
  if (supported.length === 0) {
    console.log('❌ 测试的 MCP Server 都不支持 timing 元数据');
    console.log('📝 这是预期的,因为大多数公开 Server 都没有实现这个功能');
    console.log('\n✅ 推荐方案:');
    console.log(
      '   1. 使用客户端测量 (Performance Hooks) - 见 HOW_TO_MEASURE_MCP_SDK_INTERNALS.md',
    );
    console.log('   2. 如果是自己的 Server,可以添加 timing 支持');
    console.log('   3. 向上游 Server 项目提 PR 添加 timing 功能');
  } else {
    console.log('✅ 发现了支持 timing 的 Server!');
    console.log('📝 你可以直接使用这些 Server 的详细性能数据');
  }
}

// 运行
main().catch(console.error);
