/**
 * @license
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { safeJsonStringify } from '../utils/safeJsonStringify.js';
import type {
  ToolCallConfirmationDetails,
  ToolInvocation,
  ToolMcpConfirmationDetails,
  ToolResult,
} from './tools.js';
import {
  BaseDeclarativeTool,
  BaseToolInvocation,
  Kind,
  ToolConfirmationOutcome,
} from './tools.js';
import type { CallableTool, FunctionCall, Part } from '@google/genai';
import { ToolErrorType } from './tool-error.js';
import type { Config } from '../config/config.js';

type ToolParams = Record<string, unknown>;

// Discriminated union for MCP Content Blocks to ensure type safety.
type McpTextBlock = {
  type: 'text';
  text: string;
};

type McpMediaBlock = {
  type: 'image' | 'audio';
  mimeType: string;
  data: string;
};

type McpResourceBlock = {
  type: 'resource';
  resource: {
    text?: string;
    blob?: string;
    mimeType?: string;
  };
};

type McpResourceLinkBlock = {
  type: 'resource_link';
  uri: string;
  title?: string;
  name?: string;
};

type McpContentBlock =
  | McpTextBlock
  | McpMediaBlock
  | McpResourceBlock
  | McpResourceLinkBlock;

class DiscoveredMCPToolInvocation extends BaseToolInvocation<
  ToolParams,
  ToolResult
> {
  private static readonly allowlist: Set<string> = new Set();

  constructor(
    private readonly mcpTool: CallableTool,
    readonly serverName: string,
    readonly serverToolName: string,
    readonly displayName: string,
    readonly trust?: boolean,
    params: ToolParams = {},
    private readonly cliConfig?: Config,
  ) {
    super(params);
  }

  override async shouldConfirmExecute(
    _abortSignal: AbortSignal,
  ): Promise<ToolCallConfirmationDetails | false> {
    const serverAllowListKey = this.serverName;
    const toolAllowListKey = `${this.serverName}.${this.serverToolName}`;

    if (this.cliConfig?.isTrustedFolder() && this.trust) {
      return false; // server is trusted, no confirmation needed
    }

    if (
      DiscoveredMCPToolInvocation.allowlist.has(serverAllowListKey) ||
      DiscoveredMCPToolInvocation.allowlist.has(toolAllowListKey)
    ) {
      return false; // server and/or tool already allowlisted
    }

    const confirmationDetails: ToolMcpConfirmationDetails = {
      type: 'mcp',
      title: 'Confirm MCP Tool Execution',
      serverName: this.serverName,
      toolName: this.serverToolName, // Display original tool name in confirmation
      toolDisplayName: this.displayName, // Display global registry name exposed to model and user
      onConfirm: async (outcome: ToolConfirmationOutcome) => {
        if (outcome === ToolConfirmationOutcome.ProceedAlwaysServer) {
          DiscoveredMCPToolInvocation.allowlist.add(serverAllowListKey);
        } else if (outcome === ToolConfirmationOutcome.ProceedAlwaysTool) {
          DiscoveredMCPToolInvocation.allowlist.add(toolAllowListKey);
        }
      },
    };
    return confirmationDetails;
  }

  // Determine if the response contains tool errors
  // This is needed because CallToolResults should return errors inside the response.
  // ref: https://modelcontextprotocol.io/specification/2025-06-18/schema#calltoolresult
  isMCPToolError(rawResponseParts: Part[]): boolean {
    const functionResponse = rawResponseParts?.[0]?.functionResponse;
    const response = functionResponse?.response;

    interface McpError {
      isError?: boolean | string;
    }

    if (response) {
      const error = (response as { error?: McpError })?.error;
      const isError = error?.isError;

      if (error && (isError === true || isError === 'true')) {
        return true;
      }
    }
    return false;
  }

  async execute(signal: AbortSignal): Promise<ToolResult> {
    // Track execution phases
    const executionStartTime = Date.now();

    const functionCalls: FunctionCall[] = [
      {
        name: this.serverToolName,
        args: this.params,
      },
    ];

    // Phase 1: Prepare and serialize request
    const serializationTime = Date.now() - executionStartTime;

    // Phase 2: MCP communication (actual tool call)
    const mcpCallStartTime = Date.now();

    // Race MCP tool call with abort signal to respect cancellation
    const rawResponseParts = await new Promise<Part[]>((resolve, reject) => {
      if (signal.aborted) {
        const error = new Error('Tool call aborted');
        error.name = 'AbortError';
        reject(error);
        return;
      }
      const onAbort = () => {
        cleanup();
        const error = new Error('Tool call aborted');
        error.name = 'AbortError';
        reject(error);
      };
      const cleanup = () => {
        signal.removeEventListener('abort', onAbort);
      };
      signal.addEventListener('abort', onAbort, { once: true });

      this.mcpTool
        .callTool(functionCalls)
        .then((res) => {
          cleanup();
          resolve(res);
        })
        .catch((err) => {
          cleanup();
          reject(err);
        });
    });

    const mcpCallTime = Date.now() - mcpCallStartTime;

    // 等待一小段时间确保所有 stderr 数据都已被处理
    // Playwright 的 DEBUG 日志是异步输出的，可能在 MCP 调用完成后才到达
    // 使用 50ms 的短暂等待平衡性能和日志捕获完整性
    await new Promise((resolve) => setTimeout(resolve, 50));

    // 从静态 Map 中获取 MCP 服务器的 stderr 日志并解析内部阶段
    let internalPhases: Array<{ name: string; timeMs: number }> | undefined;

    // 首先尝试从 DEBUG_FILE 读取日志（如果存在）
    const debugLogFile = DiscoveredMCPTool.getServerDebugLogFile(
      this.serverName,
    );

    let stderrLogs: string[] = [];

    if (debugLogFile) {
      // 从文件读取 DEBUG 日志
      try {
        const { readFileSync, unlinkSync } = await import('node:fs');
        const logContent = readFileSync(debugLogFile, 'utf8');
        stderrLogs = logContent.split('\n').filter((line) => line.trim());
        console.error(
          `[MCP Debug] Read ${stderrLogs.length} log lines from DEBUG_FILE: ${debugLogFile}`,
        );
        try {
          unlinkSync(debugLogFile);
        } catch (unlinkErr) {
          console.error(
            `[MCP Debug] Failed to remove DEBUG_FILE ${debugLogFile}:`,
            unlinkErr,
          );
        }
        DiscoveredMCPTool.clearServerDebugLogFile(this.serverName);
      } catch (err) {
        console.error(
          `[MCP Debug] Failed to read DEBUG_FILE ${debugLogFile}:`,
          err,
        );
      }
    }

    // 如果文件中没有日志，再尝试从 stderr 获取
    if (stderrLogs.length === 0) {
      stderrLogs = DiscoveredMCPTool.getServerStderrLogs(this.serverName);
      console.error(
        `[MCP Debug] Retrieved ${stderrLogs.length} log lines from static Map for ${this.serverName}/${this.serverToolName}`,
      );
    }

    if (stderrLogs && stderrLogs.length > 0) {
      // 打印前几行日志样本用于调试
      console.error(`[MCP Debug] Sample logs (first 3):`);
      stderrLogs.slice(0, 3).forEach((log, i) => {
        console.error(`  ${i + 1}. ${log.substring(0, 150).trim()}...`);
      });

      // 解析日志获取内部阶段
      const { parseDebugLogs: parseDebugLogsFunc, addOtherPhase } =
        await import('./mcp-debug-parser.js');
      internalPhases = parseDebugLogsFunc(stderrLogs, this.serverName);

      // 添加"其他"时间(如果需要)
      if (internalPhases && internalPhases.length > 0 && mcpCallTime > 0) {
        internalPhases = addOtherPhase(internalPhases, mcpCallTime);
      }

      console.error(
        `[MCP Debug] Parsed ${internalPhases?.length || 0} internal phases:`,
        internalPhases,
      );

      // 清空日志数组，为下次调用做准备
      // 注意：这里只清空已解析的部分，保留新的日志
      // 简单起见，我们不清空，让日志累积（后续可以优化）
    } else {
      console.error(
        `[MCP Debug] No DEBUG logs captured for ${this.serverName}. Internal timing breakdown unavailable.`,
      );
    }

    // Phase 3: Response processing
    const processingStartTime = Date.now();

    // Ensure the response is not an error
    if (this.isMCPToolError(rawResponseParts)) {
      const errorMessage = `MCP tool '${
        this.serverToolName
      }' reported tool error for function call: ${safeJsonStringify(
        functionCalls[0],
      )} with response: ${safeJsonStringify(rawResponseParts)}`;
      return {
        llmContent: errorMessage,
        returnDisplay: `Error: MCP tool '${this.serverToolName}' reported an error.`,
        error: {
          message: errorMessage,
          type: ToolErrorType.MCP_TOOL_ERROR,
        },
      };
    }

    const transformedParts = transformMcpContentToParts(rawResponseParts);
    const processingTime = Date.now() - processingStartTime;

    // Record MCP execution phases (包括内部阶段)
    const totalExecutionTime = Date.now() - executionStartTime;
    const { uiTelemetryService } = await import('../telemetry/uiTelemetry.js');
    uiTelemetryService.recordMcpToolExecution(
      this.serverName,
      this.serverToolName,
      {
        serializationTimeMs: serializationTime,
        mcpCallTimeMs: mcpCallTime,
        processingTimeMs: processingTime,
        totalTimeMs: totalExecutionTime,
        internalPhases, // 传递内部阶段数据
      },
    );

    return {
      llmContent: transformedParts,
      returnDisplay: getStringifiedResultForDisplay(rawResponseParts),
    };
  }

  getDescription(): string {
    return safeJsonStringify(this.params);
  }
}

export class DiscoveredMCPTool extends BaseDeclarativeTool<
  ToolParams,
  ToolResult
> {
  // 静态 Map 用于存储每个 MCP 服务器的 stderr 日志
  private static serverStderrLogs = new Map<string, string[]>();
  private static serverDebugLogFiles = new Map<string, string>();

  /**
   * 设置指定 MCP 服务器的 stderr 日志数组
   * 这个方法由 mcp-client.ts 在创建 transport 时调用
   */
  static setServerStderrLogs(serverName: string, logs: string[]): void {
    DiscoveredMCPTool.serverStderrLogs.set(serverName, logs);
  }

  /**
   * 获取指定 MCP 服务器的 stderr 日志数组
   */
  static getServerStderrLogs(serverName: string): string[] {
    return DiscoveredMCPTool.serverStderrLogs.get(serverName) || [];
  }

  static setServerDebugLogFile(serverName: string, filePath?: string): void {
    if (!filePath) {
      DiscoveredMCPTool.serverDebugLogFiles.delete(serverName);
      return;
    }
    DiscoveredMCPTool.serverDebugLogFiles.set(serverName, filePath);
  }

  static getServerDebugLogFile(serverName: string): string | undefined {
    return DiscoveredMCPTool.serverDebugLogFiles.get(serverName);
  }

  static clearServerDebugLogFile(serverName: string): void {
    DiscoveredMCPTool.serverDebugLogFiles.delete(serverName);
  }

  constructor(
    private readonly mcpTool: CallableTool,
    readonly serverName: string,
    readonly serverToolName: string,
    description: string,
    override readonly parameterSchema: unknown,
    readonly trust?: boolean,
    nameOverride?: string,
    private readonly cliConfig?: Config,
  ) {
    super(
      nameOverride ?? generateValidName(serverToolName),
      `${serverToolName} (${serverName} MCP Server)`,
      description,
      Kind.Other,
      parameterSchema,
      true, // isOutputMarkdown
      false, // canUpdateOutput
    );
  }

  asFullyQualifiedTool(): DiscoveredMCPTool {
    return new DiscoveredMCPTool(
      this.mcpTool,
      this.serverName,
      this.serverToolName,
      this.description,
      this.parameterSchema,
      this.trust,
      `${this.serverName}__${this.serverToolName}`,
      this.cliConfig,
    );
  }

  protected createInvocation(
    params: ToolParams,
  ): ToolInvocation<ToolParams, ToolResult> {
    return new DiscoveredMCPToolInvocation(
      this.mcpTool,
      this.serverName,
      this.serverToolName,
      this.displayName,
      this.trust,
      params,
      this.cliConfig,
    );
  }
}

function transformTextBlock(block: McpTextBlock): Part {
  return { text: block.text };
}

function transformImageAudioBlock(
  block: McpMediaBlock,
  toolName: string,
): Part[] {
  return [
    {
      text: `[Tool '${toolName}' provided the following ${
        block.type
      } data with mime-type: ${block.mimeType}]`,
    },
    {
      inlineData: {
        mimeType: block.mimeType,
        data: block.data,
      },
    },
  ];
}

function transformResourceBlock(
  block: McpResourceBlock,
  toolName: string,
): Part | Part[] | null {
  const resource = block.resource;
  if (resource?.text) {
    return { text: resource.text };
  }
  if (resource?.blob) {
    const mimeType = resource.mimeType || 'application/octet-stream';
    return [
      {
        text: `[Tool '${toolName}' provided the following embedded resource with mime-type: ${mimeType}]`,
      },
      {
        inlineData: {
          mimeType,
          data: resource.blob,
        },
      },
    ];
  }
  return null;
}

function transformResourceLinkBlock(block: McpResourceLinkBlock): Part {
  return {
    text: `Resource Link: ${block.title || block.name} at ${block.uri}`,
  };
}

/**
 * Transforms the raw MCP content blocks from the SDK response into a
 * standard GenAI Part array.
 * @param sdkResponse The raw Part[] array from `mcpTool.callTool()`.
 * @returns A clean Part[] array ready for the scheduler.
 */
function transformMcpContentToParts(sdkResponse: Part[]): Part[] {
  const funcResponse = sdkResponse?.[0]?.functionResponse;
  const mcpContent = funcResponse?.response?.['content'] as McpContentBlock[];
  const toolName = funcResponse?.name || 'unknown tool';

  if (!Array.isArray(mcpContent)) {
    return [{ text: '[Error: Could not parse tool response]' }];
  }

  const transformed = mcpContent.flatMap(
    (block: McpContentBlock): Part | Part[] | null => {
      switch (block.type) {
        case 'text':
          return transformTextBlock(block);
        case 'image':
        case 'audio':
          return transformImageAudioBlock(block, toolName);
        case 'resource':
          return transformResourceBlock(block, toolName);
        case 'resource_link':
          return transformResourceLinkBlock(block);
        default:
          return null;
      }
    },
  );

  return transformed.filter((part): part is Part => part !== null);
}

/**
 * Processes the raw response from the MCP tool to generate a clean,
 * human-readable string for display in the CLI. It summarizes non-text
 * content and presents text directly.
 *
 * @param rawResponse The raw Part[] array from the GenAI SDK.
 * @returns A formatted string representing the tool's output.
 */
function getStringifiedResultForDisplay(rawResponse: Part[]): string {
  const mcpContent = rawResponse?.[0]?.functionResponse?.response?.[
    'content'
  ] as McpContentBlock[];

  if (!Array.isArray(mcpContent)) {
    return '```json\n' + JSON.stringify(rawResponse, null, 2) + '\n```';
  }

  const displayParts = mcpContent.map((block: McpContentBlock): string => {
    switch (block.type) {
      case 'text':
        return block.text;
      case 'image':
        return `[Image: ${block.mimeType}]`;
      case 'audio':
        return `[Audio: ${block.mimeType}]`;
      case 'resource_link':
        return `[Link to ${block.title || block.name}: ${block.uri}]`;
      case 'resource':
        if (block.resource?.text) {
          return block.resource.text;
        }
        return `[Embedded Resource: ${
          block.resource?.mimeType || 'unknown type'
        }]`;
      default:
        return `[Unknown content type: ${(block as { type: string }).type}]`;
    }
  });

  return displayParts.join('\n');
}

/** Visible for testing */
export function generateValidName(name: string) {
  // Replace invalid characters (based on 400 error message from Gemini API) with underscores
  let validToolname = name.replace(/[^a-zA-Z0-9_.-]/g, '_');

  // If longer than 63 characters, replace middle with '___'
  // (Gemini API says max length 64, but actual limit seems to be 63)
  if (validToolname.length > 63) {
    validToolname =
      validToolname.slice(0, 28) + '___' + validToolname.slice(-32);
  }
  return validToolname;
}
