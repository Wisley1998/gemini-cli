#!/usr/bin/env node

/**
 * @license
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

/**
 * MCP Server Timing 元数据检测工具
 *
 * 用途: 检查已配置的 MCP Server 是否在响应中包含 timing 信息
 * 使用: node scripts/detect-mcp-timing.js
 */

import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
import { SSEClientTransport } from '@modelcontextprotocol/sdk/client/sse.js';
import { StreamableHTTPClientTransport } from '@modelcontextprotocol/sdk/client/streamableHttp.js';
import { readFileSync } from 'node:fs';
import { homedir } from 'node:os';
import { join } from 'node:path';

// 读取用户的 MCP Server 配置
function loadMcpConfig() {
  try {
    const configPath = join(homedir(), '.gemini', 'settings.json');
    const config = JSON.parse(readFileSync(configPath, 'utf-8'));
    return config.mcpServers || {};
  } catch (error) {
    console.error('❌ 无法读取 MCP 配置:', error.message);
    console.log('💡 请确保已配置 MCP Server: ~/.gemini/settings.json');
    return {};
  }
}

// 创建 Transport
async function createTransport(serverName, config) {
  if (config.httpUrl) {
    return new StreamableHTTPClientTransport(new URL(config.httpUrl), {
      headers: config.headers || {},
    });
  } else if (config.url) {
    return new SSEClientTransport(new URL(config.url), {});
  } else if (config.command) {
    return new StdioClientTransport({
      command: config.command,
      args: config.args || [],
      env: { ...process.env, ...(config.env || {}) },
      stderr: 'ignore',
    });
  }
  throw new Error(`Server ${serverName}: 无法确定 transport 类型`);
}

// 检查响应中的 timing 元数据
function extractTimingMetadata(response) {
  if (!response || typeof response !== 'object') {
    return null;
  }

  // 检查多种可能的元数据位置
  const possiblePaths = [
    response._meta?.timing,
    response.meta?.timing,
    response.timing,
    response._timing,
    response._meta?.performance,
    response.meta?.performance,
    response.performance,
    // 有些 server 可能在 content 之外
    response._metadata?.timing,
    response.metadata?.timing,
  ];

  for (const timing of possiblePaths) {
    if (timing && typeof timing === 'object') {
      return timing;
    }
  }

  return null;
}

// 测试单个 MCP Server
async function testServer(serverName, serverConfig) {
  console.log(`\n${'='.repeat(70)}`);
  console.log(`🔍 测试服务器: ${serverName}`);
  console.log(`${'='.repeat(70)}`);

  const client = new Client({
    name: 'timing-detector',
    version: '1.0.0',
  });

  let transport;
  try {
    // 创建连接
    console.log('📡 连接中...');
    transport = await createTransport(serverName, serverConfig);
    await client.connect(transport, { timeout: 10000 });
    console.log('✅ 连接成功');

    // 列出可用工具
    console.log('\n📋 获取工具列表...');
    const toolsResult = await client.request(
      { method: 'tools/list' },
      { parse: (data) => data },
    );

    const tools = toolsResult.tools || [];
    console.log(
      `✅ 找到 ${tools.length} 个工具:`,
      tools.map((t) => t.name).join(', '),
    );

    if (tools.length === 0) {
      console.log('⚠️  服务器没有可用的工具,跳过 timing 检测');
      return { serverName, hasTools: false };
    }

    // 选择第一个工具进行测试
    const testTool = tools[0];
    console.log(`\n🧪 测试工具: ${testTool.name}`);

    // 构建最小参数
    const params = {};
    if (testTool.inputSchema?.properties) {
      for (const [key, schema] of Object.entries(
        testTool.inputSchema.properties,
      )) {
        if (schema.type === 'string') {
          params[key] = schema.default || 'test';
        } else if (schema.type === 'number') {
          params[key] = schema.default || 0;
        } else if (schema.type === 'boolean') {
          params[key] = schema.default || false;
        } else if (schema.type === 'array') {
          params[key] = schema.default || [];
        }
      }
    }

    console.log('📤 发送请求:', JSON.stringify(params, null, 2));

    // 调用工具
    const startTime = Date.now();
    let callResult;
    try {
      callResult = await client.request(
        {
          method: 'tools/call',
          params: {
            name: testTool.name,
            arguments: params,
          },
        },
        { parse: (data) => data },
      );
    } catch (error) {
      console.log(`⚠️  工具调用失败: ${error.message}`);
      console.log(
        '💡 这可能是因为参数不正确,但我们仍然可以检查错误响应中的 timing',
      );
      callResult = error.response || {};
    }
    const endTime = Date.now();
    const clientMeasuredTime = endTime - startTime;

    console.log(`⏱️  客户端测量时间: ${clientMeasuredTime}ms`);

    // 检查响应中的 timing 元数据
    console.log('\n🔎 检查 timing 元数据...');
    const timing = extractTimingMetadata(callResult);

    if (timing) {
      console.log('✅ 找到 timing 元数据!');
      console.log('📊 Timing 数据:');
      console.log(JSON.stringify(timing, null, 2));

      // 分析 timing 结构
      const keys = Object.keys(timing);
      console.log(`\n📈 可用的 timing 字段: ${keys.join(', ')}`);

      // 尝试识别总时间
      const totalFields = [
        'total',
        'totalMs',
        'duration',
        'durationMs',
        'elapsed',
      ];
      const totalField = totalFields.find((f) => timing[f] !== undefined);
      if (totalField) {
        const serverTime = timing[totalField];
        const overhead = clientMeasuredTime - serverTime;
        console.log(`\n⚡ 性能分析:`);
        console.log(`   服务器执行时间: ${serverTime}ms`);
        console.log(`   客户端测量时间: ${clientMeasuredTime}ms`);
        console.log(
          `   传输开销: ${overhead}ms (${((overhead / clientMeasuredTime) * 100).toFixed(1)}%)`,
        );
      }

      return {
        serverName,
        hasTools: true,
        supportsTiming: true,
        timingStructure: timing,
        testTool: testTool.name,
      };
    } else {
      console.log('❌ 未找到 timing 元数据');
      console.log('\n📄 完整响应结构:');
      console.log(JSON.stringify(callResult, null, 2).slice(0, 500) + '...');

      return {
        serverName,
        hasTools: true,
        supportsTiming: false,
        testTool: testTool.name,
      };
    }
  } catch (error) {
    console.error('❌ 测试失败:', error.message);
    return {
      serverName,
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
  console.log('🚀 MCP Server Timing 元数据检测工具\n');

  const mcpServers = loadMcpConfig();
  const serverNames = Object.keys(mcpServers);

  if (serverNames.length === 0) {
    console.log('❌ 未找到配置的 MCP Server');
    console.log('\n💡 请在 ~/.gemini/settings.json 中配置 MCP Server');
    console.log('示例:');
    console.log(`{
  "mcpServers": {
    "playwright": {
      "command": "npx",
      "args": ["-y", "@playwright/mcp@latest"]
    }
  }
}`);
    process.exit(1);
  }

  console.log(`📦 找到 ${serverNames.length} 个配置的服务器:\n`);
  serverNames.forEach((name, i) => {
    console.log(`${i + 1}. ${name}`);
  });

  // 测试所有服务器
  const results = [];
  for (const serverName of serverNames) {
    const result = await testServer(serverName, mcpServers[serverName]);
    results.push(result);
  }

  // 汇总报告
  console.log('\n\n' + '='.repeat(70));
  console.log('📊 汇总报告');
  console.log('='.repeat(70));

  const supportedServers = results.filter((r) => r.supportsTiming);
  const unsupportedServers = results.filter(
    (r) => r.hasTools && !r.supportsTiming,
  );
  const errorServers = results.filter((r) => r.error);

  console.log(`\n✅ 支持 Timing 元数据: ${supportedServers.length} 个`);
  supportedServers.forEach((r) => {
    console.log(`   - ${r.serverName} (测试工具: ${r.testTool})`);
    if (r.timingStructure) {
      const keys = Object.keys(r.timingStructure);
      console.log(`     可用字段: ${keys.join(', ')}`);
    }
  });

  console.log(`\n❌ 不支持 Timing 元数据: ${unsupportedServers.length} 个`);
  unsupportedServers.forEach((r) => {
    console.log(`   - ${r.serverName} (测试工具: ${r.testTool})`);
  });

  console.log(`\n⚠️  测试失败: ${errorServers.length} 个`);
  errorServers.forEach((r) => {
    console.log(`   - ${r.serverName}: ${r.error}`);
  });

  // 建议
  console.log('\n\n💡 建议:');
  if (supportedServers.length > 0) {
    console.log('✅ 你可以立即使用以下服务器的详细 timing 数据:');
    supportedServers.forEach((r) => console.log(`   - ${r.serverName}`));
  }

  if (unsupportedServers.length > 0) {
    console.log('\n⚠️  以下服务器不支持 timing 元数据,建议:');
    console.log('   1. 查看服务器文档,可能有配置选项');
    console.log('   2. 向服务器维护者提 issue 请求支持');
    console.log('   3. 如果是自己的服务器,可以添加 timing 支持');
    console.log('\n   不支持的服务器:');
    unsupportedServers.forEach((r) => console.log(`   - ${r.serverName}`));
  }

  console.log('\n📚 参考文档:');
  console.log('   - HOW_TO_MEASURE_MCP_SDK_INTERNALS.md (方法 4)');
  console.log('   - 为你的 MCP Server 添加 timing 支持');
}

// 运行
main().catch(console.error);
