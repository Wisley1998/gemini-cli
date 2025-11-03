/**
 * @license
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { EventEmitter } from 'node:events';
import {
  EVENT_API_ERROR,
  EVENT_API_RESPONSE,
  EVENT_TOOL_CALL,
} from './constants.js';

import { ToolCallDecision } from './tool-call-decision.js';
import type {
  ApiErrorEvent,
  ApiResponseEvent,
  ToolCallEvent,
} from './types.js';

export type UiEvent =
  | (ApiResponseEvent & { 'event.name': typeof EVENT_API_RESPONSE })
  | (ApiErrorEvent & { 'event.name': typeof EVENT_API_ERROR })
  | (ToolCallEvent & { 'event.name': typeof EVENT_TOOL_CALL });

export interface ToolCallStats {
  count: number;
  success: number;
  fail: number;
  durationMs: number;
  decisions: {
    [ToolCallDecision.ACCEPT]: number;
    [ToolCallDecision.REJECT]: number;
    [ToolCallDecision.MODIFY]: number;
    [ToolCallDecision.AUTO_ACCEPT]: number;
  };
  // For run_shell_command, track individual shell commands
  shellCommands?: Record<string, ToolCallStats>;
  // For google_web_search, track execution phases
  webSearchPhases?: Record<string, ToolCallStats>;
}

export interface ModelMetrics {
  api: {
    totalRequests: number;
    totalErrors: number;
    totalLatencyMs: number;
  };
  tokens: {
    prompt: number;
    candidates: number;
    total: number;
    cached: number;
    thoughts: number;
    tool: number;
  };
}

export interface McpServerMetrics {
  serverName: string;
  connectionTimeMs: number;
  discoveryTimeMs: number;
  toolsDiscovered: number;
  promptsDiscovered: number;
  dockerPullTimeMs?: number;
  containerStartTimeMs?: number;
}

export interface McpToolExecutionPhases {
  serializationTimeMs: number;
  mcpCallTimeMs: number;
  processingTimeMs: number;
  totalTimeMs: number;
  // 新增：MCP Call 内部的细分阶段（可选）
  internalPhases?: Array<{
    name: string;
    timeMs: number;
  }>;
}

export interface McpToolMetrics {
  toolName: string;
  executionCount: number;
  totalSerializationTimeMs: number;
  totalMcpCallTimeMs: number;
  totalProcessingTimeMs: number;
  totalExecutionTimeMs: number;
  // 新增：累积的内部阶段时间
  internalPhases?: Array<{
    name: string;
    totalTimeMs: number; // 所有执行的累加
    count: number; // 出现次数
  }>;
}

export interface SessionMetrics {
  models: Record<string, ModelMetrics>;
  tools: {
    totalCalls: number;
    totalSuccess: number;
    totalFail: number;
    totalDurationMs: number;
    totalDecisions: {
      [ToolCallDecision.ACCEPT]: number;
      [ToolCallDecision.REJECT]: number;
      [ToolCallDecision.MODIFY]: number;
      [ToolCallDecision.AUTO_ACCEPT]: number;
    };
    byName: Record<string, ToolCallStats>;
  };
  files: {
    totalLinesAdded: number;
    totalLinesRemoved: number;
  };
  mcp?: {
    totalInitTimeMs: number;
    servers: Record<string, McpServerMetrics>;
    toolExecutions?: Record<string, Record<string, McpToolMetrics>>; // serverName -> toolName -> metrics
  };
  timing?: {
    totalUserConfirmationTimeMs: number;
    totalToolValidationTimeMs: number;
    totalToolExecutionTimeMs: number;
    totalIdleTimeMs: number;
  };
}

const createInitialModelMetrics = (): ModelMetrics => ({
  api: {
    totalRequests: 0,
    totalErrors: 0,
    totalLatencyMs: 0,
  },
  tokens: {
    prompt: 0,
    candidates: 0,
    total: 0,
    cached: 0,
    thoughts: 0,
    tool: 0,
  },
});

const createInitialMetrics = (): SessionMetrics => ({
  models: {},
  tools: {
    totalCalls: 0,
    totalSuccess: 0,
    totalFail: 0,
    totalDurationMs: 0,
    totalDecisions: {
      [ToolCallDecision.ACCEPT]: 0,
      [ToolCallDecision.REJECT]: 0,
      [ToolCallDecision.MODIFY]: 0,
      [ToolCallDecision.AUTO_ACCEPT]: 0,
    },
    byName: {},
  },
  files: {
    totalLinesAdded: 0,
    totalLinesRemoved: 0,
  },
  mcp: {
    totalInitTimeMs: 0,
    servers: {},
    toolExecutions: {},
  },
  timing: {
    totalUserConfirmationTimeMs: 0,
    totalToolValidationTimeMs: 0,
    totalToolExecutionTimeMs: 0,
    totalIdleTimeMs: 0,
  },
});

export class UiTelemetryService extends EventEmitter {
  #metrics: SessionMetrics = createInitialMetrics();
  #lastPromptTokenCount = 0;

  addEvent(event: UiEvent) {
    switch (event['event.name']) {
      case EVENT_API_RESPONSE:
        this.processApiResponse(event);
        break;
      case EVENT_API_ERROR:
        this.processApiError(event);
        break;
      case EVENT_TOOL_CALL:
        this.processToolCall(event);
        break;
      default:
        // We should not emit update for any other event metric.
        return;
    }

    this.emit('update', {
      metrics: this.#metrics,
      lastPromptTokenCount: this.#lastPromptTokenCount,
    });
  }

  getMetrics(): SessionMetrics {
    return this.#metrics;
  }

  getLastPromptTokenCount(): number {
    return this.#lastPromptTokenCount;
  }

  setLastPromptTokenCount(lastPromptTokenCount: number): void {
    this.#lastPromptTokenCount = lastPromptTokenCount;
    this.emit('update', {
      metrics: this.#metrics,
      lastPromptTokenCount: this.#lastPromptTokenCount,
    });
  }

  private getOrCreateModelMetrics(modelName: string): ModelMetrics {
    if (!this.#metrics.models[modelName]) {
      this.#metrics.models[modelName] = createInitialModelMetrics();
    }
    return this.#metrics.models[modelName];
  }

  private processApiResponse(event: ApiResponseEvent) {
    const modelMetrics = this.getOrCreateModelMetrics(event.model);

    modelMetrics.api.totalRequests++;
    modelMetrics.api.totalLatencyMs += event.duration_ms;

    modelMetrics.tokens.prompt += event.input_token_count;
    modelMetrics.tokens.candidates += event.output_token_count;
    modelMetrics.tokens.total += event.total_token_count;
    modelMetrics.tokens.cached += event.cached_content_token_count;
    modelMetrics.tokens.thoughts += event.thoughts_token_count;
    modelMetrics.tokens.tool += event.tool_token_count;
  }

  private processApiError(event: ApiErrorEvent) {
    const modelMetrics = this.getOrCreateModelMetrics(event.model);
    modelMetrics.api.totalRequests++;
    modelMetrics.api.totalErrors++;
    modelMetrics.api.totalLatencyMs += event.duration_ms;
  }

  private processToolCall(event: ToolCallEvent) {
    const { tools, files } = this.#metrics;
    tools.totalCalls++;
    tools.totalDurationMs += event.duration_ms;

    if (event.success) {
      tools.totalSuccess++;
    } else {
      tools.totalFail++;
    }

    if (!tools.byName[event.function_name]) {
      tools.byName[event.function_name] = {
        count: 0,
        success: 0,
        fail: 0,
        durationMs: 0,
        decisions: {
          [ToolCallDecision.ACCEPT]: 0,
          [ToolCallDecision.REJECT]: 0,
          [ToolCallDecision.MODIFY]: 0,
          [ToolCallDecision.AUTO_ACCEPT]: 0,
        },
      };
    }

    const toolStats = tools.byName[event.function_name];
    toolStats.count++;
    toolStats.durationMs += event.duration_ms;
    if (event.success) {
      toolStats.success++;
    } else {
      toolStats.fail++;
    }

    if (event.decision) {
      tools.totalDecisions[event.decision]++;
      toolStats.decisions[event.decision]++;
    }

    // Track individual shell commands for run_shell_command
    if (event.function_name === 'run_shell_command' && event.function_args) {
      const command = event.function_args['command'] as string | undefined;
      if (command) {
        // Extract the first word (command name) from the shell command
        const commandName = command.trim().split(/\s+/)[0];

        if (!toolStats.shellCommands) {
          toolStats.shellCommands = {};
        }

        if (!toolStats.shellCommands[commandName]) {
          toolStats.shellCommands[commandName] = {
            count: 0,
            success: 0,
            fail: 0,
            durationMs: 0,
            decisions: {
              [ToolCallDecision.ACCEPT]: 0,
              [ToolCallDecision.REJECT]: 0,
              [ToolCallDecision.MODIFY]: 0,
              [ToolCallDecision.AUTO_ACCEPT]: 0,
            },
          };
        }

        const shellCmdStats = toolStats.shellCommands[commandName];
        shellCmdStats.count++;
        shellCmdStats.durationMs += event.duration_ms;
        if (event.success) {
          shellCmdStats.success++;
        } else {
          shellCmdStats.fail++;
        }
        if (event.decision) {
          shellCmdStats.decisions[event.decision]++;
        }
      }
    }

    // Track execution phases for google_web_search
    if (event.function_name === 'google_web_search' && event.metadata) {
      const phaseKeys = [
        'api_request',
        'grounding_processing',
        'citation_insertion',
        'source_formatting',
      ];

      for (const phaseKey of phaseKeys) {
        if (event.metadata[phaseKey] !== undefined) {
          const phaseDuration = event.metadata[phaseKey] as number;

          if (!toolStats.webSearchPhases) {
            toolStats.webSearchPhases = {};
          }

          if (!toolStats.webSearchPhases[phaseKey]) {
            toolStats.webSearchPhases[phaseKey] = {
              count: 0,
              success: 0,
              fail: 0,
              durationMs: 0,
              decisions: {
                [ToolCallDecision.ACCEPT]: 0,
                [ToolCallDecision.REJECT]: 0,
                [ToolCallDecision.MODIFY]: 0,
                [ToolCallDecision.AUTO_ACCEPT]: 0,
              },
            };
          }

          const phaseStats = toolStats.webSearchPhases[phaseKey];
          phaseStats.count++;
          phaseStats.durationMs += phaseDuration;
          if (event.success) {
            phaseStats.success++;
          } else {
            phaseStats.fail++;
          }
          if (event.decision) {
            phaseStats.decisions[event.decision]++;
          }
        }
      }
    }

    // Aggregate line count data from metadata
    if (event.metadata) {
      if (event.metadata['model_added_lines'] !== undefined) {
        files.totalLinesAdded += event.metadata['model_added_lines'];
      }
      if (event.metadata['model_removed_lines'] !== undefined) {
        files.totalLinesRemoved += event.metadata['model_removed_lines'];
      }
    }
  }

  /**
   * Record MCP server initialization metrics
   */
  recordMcpServerInit(
    serverName: string,
    connectionTimeMs: number,
    discoveryTimeMs: number,
    toolsDiscovered: number,
    promptsDiscovered: number,
    dockerPullTimeMs?: number,
    containerStartTimeMs?: number,
  ): void {
    if (!this.#metrics.mcp) {
      this.#metrics.mcp = {
        totalInitTimeMs: 0,
        servers: {},
        toolExecutions: {},
      };
    }

    const totalServerTime =
      connectionTimeMs +
      discoveryTimeMs +
      (dockerPullTimeMs || 0) +
      (containerStartTimeMs || 0);

    this.#metrics.mcp.servers[serverName] = {
      serverName,
      connectionTimeMs,
      discoveryTimeMs,
      toolsDiscovered,
      promptsDiscovered,
      dockerPullTimeMs,
      containerStartTimeMs,
    };

    this.#metrics.mcp.totalInitTimeMs += totalServerTime;

    this.emit('update', {
      metrics: this.#metrics,
      lastPromptTokenCount: this.#lastPromptTokenCount,
    });
  }

  /**
   * Record MCP tool execution phases
   */
  recordMcpToolExecution(
    serverName: string,
    toolName: string,
    phases: McpToolExecutionPhases,
  ): void {
    if (!this.#metrics.mcp) {
      this.#metrics.mcp = {
        totalInitTimeMs: 0,
        servers: {},
        toolExecutions: {},
      };
    }

    if (!this.#metrics.mcp.toolExecutions) {
      this.#metrics.mcp.toolExecutions = {};
    }

    if (!this.#metrics.mcp.toolExecutions[serverName]) {
      this.#metrics.mcp.toolExecutions[serverName] = {};
    }

    if (!this.#metrics.mcp.toolExecutions[serverName][toolName]) {
      this.#metrics.mcp.toolExecutions[serverName][toolName] = {
        toolName,
        executionCount: 0,
        totalSerializationTimeMs: 0,
        totalMcpCallTimeMs: 0,
        totalProcessingTimeMs: 0,
        totalExecutionTimeMs: 0,
      };
    }

    const toolMetrics = this.#metrics.mcp.toolExecutions[serverName][toolName];
    toolMetrics.executionCount += 1;
    toolMetrics.totalSerializationTimeMs += phases.serializationTimeMs;
    toolMetrics.totalMcpCallTimeMs += phases.mcpCallTimeMs;
    toolMetrics.totalProcessingTimeMs += phases.processingTimeMs;
    toolMetrics.totalExecutionTimeMs += phases.totalTimeMs;

    // 累积内部阶段时间
    if (phases.internalPhases && phases.internalPhases.length > 0) {
      if (!toolMetrics.internalPhases) {
        toolMetrics.internalPhases = [];
      }

      for (const phase of phases.internalPhases) {
        const existing = toolMetrics.internalPhases.find(
          (p) => p.name === phase.name,
        );
        if (existing) {
          existing.totalTimeMs += phase.timeMs;
          existing.count += 1;
        } else {
          toolMetrics.internalPhases.push({
            name: phase.name,
            totalTimeMs: phase.timeMs,
            count: 1,
          });
        }
      }
    }

    this.emit('update', {
      metrics: this.#metrics,
      lastPromptTokenCount: this.#lastPromptTokenCount,
    });
  }

  /**
   * Record timing breakdown for tool calls
   */
  recordToolTiming(
    validationTimeMs: number,
    userConfirmationTimeMs: number,
    executionTimeMs: number,
  ): void {
    if (!this.#metrics.timing) {
      this.#metrics.timing = {
        totalUserConfirmationTimeMs: 0,
        totalToolValidationTimeMs: 0,
        totalToolExecutionTimeMs: 0,
        totalIdleTimeMs: 0,
      };
    }

    this.#metrics.timing.totalToolValidationTimeMs += validationTimeMs;
    this.#metrics.timing.totalUserConfirmationTimeMs += userConfirmationTimeMs;
    this.#metrics.timing.totalToolExecutionTimeMs += executionTimeMs;

    this.emit('update', {
      metrics: this.#metrics,
      lastPromptTokenCount: this.#lastPromptTokenCount,
    });
  }

  /**
   * Record idle time (time when agent is not active)
   */
  recordIdleTime(idleTimeMs: number): void {
    if (!this.#metrics.timing) {
      this.#metrics.timing = {
        totalUserConfirmationTimeMs: 0,
        totalToolValidationTimeMs: 0,
        totalToolExecutionTimeMs: 0,
        totalIdleTimeMs: 0,
      };
    }

    this.#metrics.timing.totalIdleTimeMs += idleTimeMs;

    this.emit('update', {
      metrics: this.#metrics,
      lastPromptTokenCount: this.#lastPromptTokenCount,
    });
  }
}

export const uiTelemetryService = new UiTelemetryService();
