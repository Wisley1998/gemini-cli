/**
 * @license
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

/**
 * 示例:如何为 MCP Docker 容器追踪时间
 *
 * 此文件展示了如何在 MCP 服务器启动过程中追踪 Docker 相关的时间。
 * 虽然基本的连接和发现时间会自动追踪,但 Docker 特定的操作需要手动追踪。
 */

import { uiTelemetryService } from '@google/gemini-cli-core';
import { spawn } from 'node:child_process';

/**
 * 追踪 Docker 镜像拉取时间的辅助函数
 */
async function pullDockerImageWithTiming(imageName: string): Promise<number> {
  const startTime = Date.now();

  return new Promise((resolve, reject) => {
    const pullProcess = spawn('docker', ['pull', imageName]);

    pullProcess.on('close', (code) => {
      const pullTimeMs = Date.now() - startTime;

      if (code === 0) {
        console.log(`Docker 镜像 ${imageName} 拉取完成,耗时 ${pullTimeMs}ms`);
        resolve(pullTimeMs);
      } else {
        reject(new Error(`Docker 镜像拉取失败,退出码: ${code}`));
      }
    });

    pullProcess.on('error', (error) => {
      reject(error);
    });
  });
}

/**
 * 追踪 Docker 容器启动时间的辅助函数
 */
async function startDockerContainerWithTiming(
  containerName: string,
  imageName: string,
  args: string[] = [],
): Promise<number> {
  const startTime = Date.now();

  return new Promise((resolve, reject) => {
    const runArgs = ['run', '--name', containerName, ...args, imageName];
    const runProcess = spawn('docker', runArgs);

    // 等待容器就绪(可以通过检查健康检查或端口来实现)
    const checkHealth = setInterval(() => {
      const inspectProcess = spawn('docker', [
        'inspect',
        '--format',
        '{{.State.Health.Status}}',
        containerName,
      ]);

      inspectProcess.stdout.on('data', (data) => {
        const status = data.toString().trim();

        if (status === 'healthy' || status === 'none') {
          clearInterval(checkHealth);
          const startTimeMs = Date.now() - startTime;
          console.log(
            `Docker 容器 ${containerName} 启动完成,耗时 ${startTimeMs}ms`,
          );
          resolve(startTimeMs);
        }
      });
    }, 500);

    runProcess.on('error', (error) => {
      clearInterval(checkHealth);
      reject(error);
    });
  });
}

/**
 * 完整示例:启动 MCP Docker 服务器并追踪所有时间
 */
export async function startMcpDockerServerWithFullTiming(
  serverName: string,
  imageName: string,
  containerName: string,
): Promise<void> {
  console.log(`正在启动 MCP 服务器: ${serverName}`);

  // 1. 拉取 Docker 镜像(如果需要)
  let dockerPullTimeMs: number | undefined;
  try {
    console.log(`检查 Docker 镜像: ${imageName}`);
    dockerPullTimeMs = await pullDockerImageWithTiming(imageName);
  } catch (error) {
    console.warn('Docker 镜像已存在或拉取失败:', error);
  }

  // 2. 启动 Docker 容器
  const containerStartTimeMs = await startDockerContainerWithTiming(
    containerName,
    imageName,
    ['-d', '-p', '8080:8080'],
  );

  // 3. 连接到 MCP 服务器(这部分在 McpClient 中自动追踪)
  // 这里只是模拟
  const connectionStartTime = Date.now();
  // ... 实际连接逻辑 ...
  const connectionTimeMs = Date.now() - connectionStartTime;

  // 4. 发现工具(这部分在 McpClient 中自动追踪)
  const discoveryStartTime = Date.now();
  // ... 实际发现逻辑 ...
  const discoveryTimeMs = Date.now() - discoveryStartTime;
  const toolsDiscovered = 5; // 示例值
  const promptsDiscovered = 2; // 示例值

  // 5. 记录所有时间到遥测系统
  uiTelemetryService.recordMcpServerInit(
    serverName,
    connectionTimeMs,
    discoveryTimeMs,
    toolsDiscovered,
    promptsDiscovered,
    dockerPullTimeMs, // 可选:Docker 拉取时间
    containerStartTimeMs, // 可选:容器启动时间
  );

  console.log(`\nMCP 服务器 ${serverName} 启动完成:`);
  console.log(`  Docker 拉取时间: ${dockerPullTimeMs || 0}ms`);
  console.log(`  容器启动时间: ${containerStartTimeMs}ms`);
  console.log(`  连接时间: ${connectionTimeMs}ms`);
  console.log(`  发现时间: ${discoveryTimeMs}ms`);
  console.log(
    `  总时间: ${(dockerPullTimeMs || 0) + containerStartTimeMs + connectionTimeMs + discoveryTimeMs}ms`,
  );
}

/**
 * 简化版本:仅在 McpClient 中集成
 *
 * 如果要集成到现有的 McpClient 代码中,可以这样做:
 */
export class EnhancedMcpClient {
  private dockerPullTimeMs?: number;
  private containerStartTimeMs?: number;

  async setupDockerContainer(
    imageName: string,
    containerName: string,
  ): Promise<void> {
    // 拉取镜像
    try {
      this.dockerPullTimeMs = await pullDockerImageWithTiming(imageName);
    } catch (error) {
      console.warn('使用现有 Docker 镜像');
    }

    // 启动容器
    this.containerStartTimeMs = await startDockerContainerWithTiming(
      containerName,
      imageName,
    );
  }

  async connect(): Promise<void> {
    const connectionStartTime = Date.now();
    // ... 实际连接逻辑 ...
    const connectionTimeMs = Date.now() - connectionStartTime;

    // 存储以备后用
    (this as any).connectionTimeMs = connectionTimeMs;
  }

  async discover(): Promise<void> {
    const discoveryStartTime = Date.now();
    // ... 实际发现逻辑 ...
    const discoveryTimeMs = Date.now() - discoveryStartTime;
    const toolsDiscovered = 5;
    const promptsDiscovered = 2;

    // 记录所有时间,包括 Docker 时间
    const connectionTimeMs = (this as any).connectionTimeMs || 0;

    uiTelemetryService.recordMcpServerInit(
      'my-server',
      connectionTimeMs,
      discoveryTimeMs,
      toolsDiscovered,
      promptsDiscovered,
      this.dockerPullTimeMs, // 包含 Docker 拉取时间
      this.containerStartTimeMs, // 包含容器启动时间
    );
  }
}

/**
 * 使用示例
 */
async function example() {
  const client = new EnhancedMcpClient();

  // 设置 Docker 容器(追踪拉取和启动时间)
  await client.setupDockerContainer('my-mcp-server:latest', 'my-mcp-container');

  // 连接(追踪连接时间)
  await client.connect();

  // 发现工具(追踪发现时间,并记录所有时间)
  await client.discover();

  // 现在所有时间都已记录到 uiTelemetryService
  // 可以在 /stats 命令中看到完整的分解
}
