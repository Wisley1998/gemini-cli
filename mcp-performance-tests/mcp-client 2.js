/**
 * MCP Client Wrapper
 * 封装MCP客户端连接和操作
 */

import { Client } from '@modelcontextprotocol/sdk/client/index.js';
import { StdioClientTransport } from '@modelcontextprotocol/sdk/client/stdio.js';
import { spawn } from 'child_process';
import { logWithTimestamp, measureTime, safeWaitForExit } from './utils.js';
import { PerformanceMonitor, formatBreakdown } from './performance-monitor.js';
import { randomUUID } from 'crypto';

export class MCPClient {
  constructor(config) {
    this.config = config;
    this.client = null;
    this.transport = null;
    this.process = null;
    this.perfMonitor = new PerformanceMonitor();
  }

  /**
   * 启动MCP服务器并建立连接（包含初始化握手）
   */
  async connect() {
    const { result: connectResult, duration: connectDuration } =
      await measureTime(async () => {
        logWithTimestamp(
          '🚀',
          `启动MCP服务器: ${this.config.command} ${this.config.args.join(' ')}`,
        );

        // 创建传输层
        this.transport = new StdioClientTransport({
          command: this.config.command,
          args: this.config.args,
          env: {
            ...process.env,
            ...this.config.env,
          },
        });

        // 监听stderr以便调试
        this.transport.onerror = (error) => {
          console.error(`   [transport error] ${error}`);
        };

        // 创建客户端
        this.client = new Client(
          {
            name: 'mcp-performance-test',
            version: '1.0.0',
          },
          {
            capabilities: {},
          },
        );

        // 连接（自动执行初始化握手）
        await this.client.connect(this.transport);

        // 获取服务器信息
        const serverVersion = this.client.getServerVersion();
        const serverCapabilities = this.client.getServerCapabilities();

        logWithTimestamp('✓', '连接成功并完成协议握手');
        logWithTimestamp('✓', `服务器名称: ${serverVersion?.name || 'N/A'}`);
        logWithTimestamp('✓', `服务器版本: ${serverVersion?.version || 'N/A'}`);

        return { serverVersion, serverCapabilities };
      }, '启动、连接和握手总耗时');

    return connectDuration;
  }

  /**
   * 获取可用工具列表
   */
  async listTools() {
    const { result, duration } = await measureTime(async () => {
      logWithTimestamp('📦', '获取可用工具列表...');
      const listResult = await this.client.listTools();
      const tools = listResult.tools || [];
      logWithTimestamp('✓', `发现 ${tools.length} 个可用工具`);

      if (tools.length > 0) {
        console.log('\n   可用工具:');
        tools.forEach((tool, index) => {
          console.log(`   ${index + 1}. ${tool.name}`);
          if (tool.description) {
            console.log(
              `      ${tool.description.substring(0, 60)}${tool.description.length > 60 ? '...' : ''}`,
            );
          }
        });
        console.log();
      }

      return tools;
    }, '工具列表获取耗时');

    return { tools: result, duration };
  }

  /**
   * 调用工具 (带详细性能监控)
   */
  async callTool(toolName, args = {}) {
    // 创建唯一的调用 ID
    const callId = randomUUID();

    // 开始性能监控
    this.perfMonitor.start(callId);

    const { result, duration } = await measureTime(async () => {
      logWithTimestamp('⚡', `执行工具: ${toolName}`);
      if (Object.keys(args).length > 0) {
        console.log(
          `   参数: ${JSON.stringify(args, null, 2).split('\n').join('\n   ')}`,
        );
      }

      // 标记: 请求准备完成
      this.perfMonitor.mark(callId, 'request-ready');

      // 标记: 开始调用
      this.perfMonitor.mark(callId, 'call-started');

      // 实际的 MCP Call (这是黑盒)
      const callResult = await this.client.callTool({
        name: toolName,
        arguments: args,
      });

      // 标记: 收到响应
      this.perfMonitor.mark(callId, 'response-received');

      logWithTimestamp('✓', `工具执行完成`);

      // 检查 Server 是否返回了 timing 元数据
      const serverTiming = this.extractServerTiming(callResult);

      // 打印结果摘要
      if (callResult.content && Array.isArray(callResult.content)) {
        console.log(`   返回内容数: ${callResult.content.length}`);
        callResult.content.forEach((item, index) => {
          if (item.type === 'text') {
            const preview = item.text?.substring(0, 100) || '';
            console.log(
              `   [${index}] text: ${preview}${preview.length >= 100 ? '...' : ''}`,
            );
          } else if (item.type === 'image') {
            console.log(
              `   [${index}] image: ${item.data?.substring(0, 50) || 'N/A'}...`,
            );
          } else {
            console.log(`   [${index}] ${item.type}`);
          }
        });
      }

      // 标记: 响应解析完成
      this.perfMonitor.mark(callId, 'response-parsed');

      return { callResult, serverTiming };
    }, `工具 "${toolName}" 执行耗时`);

    // 获取详细的时间分解
    const breakdown = this.perfMonitor.end(callId);

    // 打印详细的性能信息
    console.log(formatBreakdown(breakdown));

    // 如果 Server 支持 timing,也打印出来
    if (result.serverTiming) {
      console.log('\n📊 服务器端 Timing (Server 报告):');
      console.log(JSON.stringify(result.serverTiming, null, 2));
    }

    return {
      result: result.callResult,
      duration,
      breakdown,
      serverTiming: result.serverTiming,
    };
  }

  /**
   * 从响应中提取 Server Timing 元数据
   */
  extractServerTiming(callResult) {
    // 检查多个可能的位置
    const locations = [
      callResult._meta?.timing,
      callResult.meta?.timing,
      callResult.timing,
    ];

    for (const timing of locations) {
      if (timing && typeof timing === 'object') {
        return timing;
      }
    }

    return null;
  }

  /**
   * 关闭连接
   */
  async disconnect() {
    const { duration } = await measureTime(async () => {
      logWithTimestamp('🛑', '关闭MCP连接...');

      if (this.client) {
        try {
          await this.client.close();
        } catch (error) {
          console.error(`   关闭客户端出错: ${error.message}`);
        }
      }

      if (this.process && !this.process.killed) {
        this.process.kill('SIGTERM');
        await safeWaitForExit(this.process, 3000);
      }

      logWithTimestamp('✓', 'MCP连接已关闭');
    }, '关闭耗时');

    return duration;
  }

  /**
   * 完整的性能测试流程
   */
  async runPerformanceTest(testConfig) {
    const stats = {
      startup: 0,
      listTools: 0,
      toolCount: 0,
      executions: [],
      shutdown: 0,
      total: 0,
    };

    const startTime = Date.now();

    try {
      // 1. 启动、连接和握手（connect 自动完成初始化）
      stats.startup = await this.connect();

      // 2. 获取工具列表
      const toolsResult = await this.listTools();
      stats.listTools = toolsResult.duration;
      stats.toolCount = toolsResult.tools.length;

      // 3. 执行测试用例
      if (testConfig.testCases && testConfig.testCases.length > 0) {
        for (let i = 0; i < testConfig.testCases.length; i++) {
          const testCase = testConfig.testCases[i];
          console.log(`\n${'─'.repeat(60)}`);
          logWithTimestamp(
            '🧪',
            `测试用例 ${i + 1}/${testConfig.testCases.length}: ${testCase.name}`,
          );
          console.log(`${'─'.repeat(60)}`);

          const execution = await this.callTool(testCase.tool, testCase.args);
          stats.executions.push({
            name: testCase.name,
            tool: testCase.tool,
            duration: execution.duration,
            success: true,
          });

          // 如果配置了多次执行，测试缓存效果
          if (testCase.repeat) {
            for (let r = 1; r < testCase.repeat; r++) {
              console.log(`\n   🔄 第 ${r + 1} 次执行...`);
              const repeatExecution = await this.callTool(
                testCase.tool,
                testCase.args,
              );
              stats.executions.push({
                name: `${testCase.name} (第${r + 1}次)`,
                tool: testCase.tool,
                duration: repeatExecution.duration,
                success: true,
              });
            }
          }
        }
      }

      // 4. 关闭连接
      stats.shutdown = await this.disconnect();
    } catch (error) {
      console.error(`\n❌ 测试失败: ${error.message}`);
      console.error(error.stack);

      // 尝试清理
      try {
        await this.disconnect();
      } catch (cleanupError) {
        console.error(`清理资源失败: ${cleanupError.message}`);
      }

      throw error;
    }

    stats.total = Date.now() - startTime;
    return stats;
  }
}
