/**
 * @license
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type {
  SessionMetrics,
  ComputedSessionStats,
  ModelMetrics,
} from '../contexts/SessionContext.js';

export function calculateErrorRate(metrics: ModelMetrics): number {
  if (metrics.api.totalRequests === 0) {
    return 0;
  }
  return (metrics.api.totalErrors / metrics.api.totalRequests) * 100;
}

export function calculateAverageLatency(metrics: ModelMetrics): number {
  if (metrics.api.totalRequests === 0) {
    return 0;
  }
  return metrics.api.totalLatencyMs / metrics.api.totalRequests;
}

export function calculateCacheHitRate(metrics: ModelMetrics): number {
  if (metrics.tokens.prompt === 0) {
    return 0;
  }
  return (metrics.tokens.cached / metrics.tokens.prompt) * 100;
}

export const computeSessionStats = (
  metrics: SessionMetrics,
  wallTimeMs?: number,
): ComputedSessionStats => {
  const { models, tools, files } = metrics;
  const totalApiTime = Object.values(models).reduce(
    (acc, model) => acc + model.api.totalLatencyMs,
    0,
  );

  // Extract MCP and timing metrics from session metrics
  const mcpMetrics = metrics.mcp;
  const timingMetrics = metrics.timing;

  // Calculate MCP initialization time from server breakdown (sum of all servers)
  let mcpInitTime = 0;
  if (mcpMetrics?.servers) {
    for (const serverMetrics of Object.values(mcpMetrics.servers)) {
      mcpInitTime +=
        serverMetrics.connectionTimeMs +
        serverMetrics.discoveryTimeMs +
        (serverMetrics.dockerPullTimeMs ?? 0) +
        (serverMetrics.containerStartTimeMs ?? 0);
    }
  }

  // Calculate MCP communication overhead (from tool executions)
  let mcpCommunicationOverhead = 0;
  let resultProcessingTime = 0;

  if (mcpMetrics?.toolExecutions) {
    for (const toolsMap of Object.values(mcpMetrics.toolExecutions)) {
      for (const toolMetrics of Object.values(toolsMap)) {
        // MCP Call time is the actual network/communication overhead
        mcpCommunicationOverhead += toolMetrics.totalMcpCallTimeMs;
        // Serialization + Processing is result processing overhead
        resultProcessingTime +=
          toolMetrics.totalSerializationTimeMs +
          toolMetrics.totalProcessingTimeMs;
      }
    }
  }

  // Total tool time now includes: tool execution + MCP init + MCP communication + result processing
  const totalToolTime =
    tools.totalDurationMs +
    mcpInitTime +
    mcpCommunicationOverhead +
    resultProcessingTime;

  // Calculate agent active time
  // If wallTimeMs is provided, use it as the total time; otherwise fall back to sum
  const agentActiveTime = wallTimeMs ?? totalApiTime + totalToolTime;

  const apiTimePercent =
    agentActiveTime > 0 ? (totalApiTime / agentActiveTime) * 100 : 0;
  const toolTimePercent =
    agentActiveTime > 0 ? (totalToolTime / agentActiveTime) * 100 : 0;

  // Compute API time breakdown by model
  const apiTimeByModel: Record<string, { timeMs: number; percent: number }> =
    {};
  for (const [modelName, modelMetrics] of Object.entries(models)) {
    const timeMs = modelMetrics.api.totalLatencyMs;
    apiTimeByModel[modelName] = {
      timeMs,
      percent: totalApiTime > 0 ? (timeMs / totalApiTime) * 100 : 0,
    };
  }

  // Compute tool time breakdown by tool name
  const toolTimeByTool: Record<string, { timeMs: number; percent: number }> =
    {};
  for (const [toolName, toolStats] of Object.entries(tools.byName)) {
    const timeMs = toolStats.durationMs;
    toolTimeByTool[toolName] = {
      timeMs,
      percent: totalToolTime > 0 ? (timeMs / totalToolTime) * 100 : 0,
    };
  }

  // Add MCP Init as a separate entry in tool time breakdown
  if (mcpInitTime > 0) {
    toolTimeByTool['MCP Init'] = {
      timeMs: mcpInitTime,
      percent: totalToolTime > 0 ? (mcpInitTime / totalToolTime) * 100 : 0,
    };
  }

  // Note: MCP Communication and Result Processing times are NOT added here
  // because they are already included in each individual tool's execution time.
  // Adding them separately would cause double-counting.
  // These metrics are still available in mcpCommunicationOverhead and
  // resultProcessingTime variables for internal use if needed.

  // Compute shell command breakdown for run_shell_command
  const shellCommandsByTool: Record<
    string,
    Record<string, { timeMs: number; percent: number }>
  > = {};
  for (const [toolName, toolStats] of Object.entries(tools.byName)) {
    if (toolStats.shellCommands) {
      const toolTotalTime = toolStats.durationMs;
      shellCommandsByTool[toolName] = {};
      for (const [cmdName, cmdStats] of Object.entries(
        toolStats.shellCommands,
      )) {
        shellCommandsByTool[toolName][cmdName] = {
          timeMs: cmdStats.durationMs,
          percent:
            toolTotalTime > 0 ? (cmdStats.durationMs / toolTotalTime) * 100 : 0,
        };
      }
    }
  }

  // Compute web search phase breakdown for google_web_search
  const webSearchPhasesByTool: Record<
    string,
    Record<string, { timeMs: number; percent: number }>
  > = {};
  for (const [toolName, toolStats] of Object.entries(tools.byName)) {
    if (toolStats.webSearchPhases) {
      const toolTotalTime = toolStats.durationMs;
      webSearchPhasesByTool[toolName] = {};
      for (const [phaseName, phaseStats] of Object.entries(
        toolStats.webSearchPhases,
      )) {
        webSearchPhasesByTool[toolName][phaseName] = {
          timeMs: phaseStats.durationMs,
          percent:
            toolTotalTime > 0
              ? (phaseStats.durationMs / toolTotalTime) * 100
              : 0,
        };
      }
    }
  }

  const totalCachedTokens = Object.values(models).reduce(
    (acc, model) => acc + model.tokens.cached,
    0,
  );
  const totalPromptTokens = Object.values(models).reduce(
    (acc, model) => acc + model.tokens.prompt,
    0,
  );
  const cacheEfficiency =
    totalPromptTokens > 0 ? (totalCachedTokens / totalPromptTokens) * 100 : 0;

  const totalDecisions =
    tools.totalDecisions.accept +
    tools.totalDecisions.reject +
    tools.totalDecisions.modify;
  const successRate =
    tools.totalCalls > 0 ? (tools.totalSuccess / tools.totalCalls) * 100 : 0;
  const agreementRate =
    totalDecisions > 0
      ? (tools.totalDecisions.accept / totalDecisions) * 100
      : 0;

  // Build MCP server breakdown
  const mcpServerBreakdown: Record<
    string,
    {
      connectionTimeMs: number;
      discoveryTimeMs: number;
      dockerPullTimeMs?: number;
      containerStartTimeMs?: number;
      totalTimeMs: number;
    }
  > = {};

  if (mcpMetrics?.servers) {
    for (const [serverName, serverMetrics] of Object.entries(
      mcpMetrics.servers,
    )) {
      mcpServerBreakdown[serverName] = {
        connectionTimeMs: serverMetrics.connectionTimeMs,
        discoveryTimeMs: serverMetrics.discoveryTimeMs,
        dockerPullTimeMs: serverMetrics.dockerPullTimeMs,
        containerStartTimeMs: serverMetrics.containerStartTimeMs,
        totalTimeMs:
          serverMetrics.connectionTimeMs +
          serverMetrics.discoveryTimeMs +
          (serverMetrics.dockerPullTimeMs ?? 0) +
          (serverMetrics.containerStartTimeMs ?? 0),
      };
    }
  }

  // Build MCP tool execution breakdown - organize by tool name for display in tool breakdown
  const mcpExecutionPhasesByTool: Record<
    string,
    Record<
      string,
      {
        timeMs: number;
        percent: number;
        // 新增：MCP Call 阶段可以有子阶段
        subPhases?: Array<{ name: string; timeMs: number; percent: number }>;
      }
    >
  > = {};

  // Build tool to server name mapping
  const toolToServerMap: Record<string, string> = {};

  if (mcpMetrics?.toolExecutions) {
    for (const [serverName, toolsMap] of Object.entries(
      mcpMetrics.toolExecutions,
    )) {
      for (const [toolName, toolMetrics] of Object.entries(toolsMap)) {
        // Find the matching tool in toolTimeByTool to get the right display name
        // MCP tools might be prefixed with server name or renamed
        const matchingToolName = Object.keys(toolTimeByTool).find(
          (name) => name.includes(toolName) || toolName.includes(name),
        );

        if (matchingToolName) {
          // Store the server name for this tool
          toolToServerMap[matchingToolName] = serverName;
        }

        if (matchingToolName && toolMetrics.totalExecutionTimeMs > 0) {
          // 获取工具的实际总时间（包括框架开销）
          // 这是从工具调用开始到结束的墙钟时间
          const actualToolTotalTime =
            toolTimeByTool[matchingToolName]?.timeMs ||
            toolMetrics.totalExecutionTimeMs;

          // 构建内部阶段数据
          let subPhases:
            | Array<{ name: string; timeMs: number; percent: number }>
            | undefined;
          if (
            toolMetrics.internalPhases &&
            toolMetrics.internalPhases.length > 0
          ) {
            subPhases = toolMetrics.internalPhases.map((phase) => ({
              name: phase.name,
              timeMs: phase.totalTimeMs,
              percent:
                toolMetrics.totalMcpCallTimeMs > 0
                  ? (phase.totalTimeMs / toolMetrics.totalMcpCallTimeMs) * 100
                  : 0,
            }));
          }

          // 百分比现在相对于工具的实际总时间（包括框架开销）
          mcpExecutionPhasesByTool[matchingToolName] = {
            Serialization: {
              timeMs: toolMetrics.totalSerializationTimeMs,
              percent:
                (toolMetrics.totalSerializationTimeMs / actualToolTotalTime) *
                100,
            },
            'MCP Call': {
              timeMs: toolMetrics.totalMcpCallTimeMs,
              percent:
                (toolMetrics.totalMcpCallTimeMs / actualToolTotalTime) * 100,
              subPhases, // 添加子阶段
            },
            Processing: {
              timeMs: toolMetrics.totalProcessingTimeMs,
              percent:
                (toolMetrics.totalProcessingTimeMs / actualToolTotalTime) * 100,
            },
          };
        }
      }
    }
  }

  // Extract timing breakdown (validation, confirmation, execution, idle)
  const toolValidationTime = timingMetrics?.totalToolValidationTimeMs ?? 0;
  const userConfirmationTime = timingMetrics?.totalUserConfirmationTimeMs ?? 0;
  const idleTime = timingMetrics?.totalIdleTimeMs ?? 0;

  // Calculate Browser and Network Wait Times from MCP tool execution
  // Note: These times are ALREADY INCLUDED in totalToolTime via mcpCommunicationOverhead
  // We extract them here for informational display purposes only
  let browserWaitTime = 0;
  let networkWaitTime = 0;

  if (mcpMetrics?.toolExecutions) {
    for (const [serverName, toolsMap] of Object.entries(
      mcpMetrics.toolExecutions,
    )) {
      for (const [toolName, toolMetrics] of Object.entries(toolsMap)) {
        const mcpCallTime = toolMetrics.totalMcpCallTimeMs;

        // Heuristic: Playwright tools spend most MCP call time waiting for browser
        if (
          serverName.toLowerCase().includes('playwright') ||
          toolName.toLowerCase().includes('browser') ||
          toolName.toLowerCase().includes('navigate') ||
          toolName.toLowerCase().includes('screenshot')
        ) {
          browserWaitTime += mcpCallTime;
        }
        // Heuristic: Fetcher tools spend most MCP call time waiting for network
        else if (
          serverName.toLowerCase().includes('fetch') ||
          toolName.toLowerCase().includes('fetch') ||
          toolName.toLowerCase().includes('http') ||
          toolName.toLowerCase().includes('url')
        ) {
          networkWaitTime += mcpCallTime;
        }
      }
    }
  }

  // Calculate total "processing overhead"
  // Processing overhead = Agent Active Time - (API Time + Tool Time + Tool Validation + User Confirmation + Idle)
  // This represents unexplained/unmeasured time (GC, event loop, system overhead, etc.)
  const totalProcessingOverhead = Math.max(
    0,
    agentActiveTime -
      totalApiTime -
      totalToolTime -
      toolValidationTime -
      userConfirmationTime -
      idleTime,
  );

  const processingOverheadPercent =
    agentActiveTime > 0 ? (totalProcessingOverhead / agentActiveTime) * 100 : 0;

  // Build processing overhead breakdown
  // NOTE: browserWaitTime and networkWaitTime are informational only - they're already in Tool Time
  // systemOverhead is the TRUE processing overhead (the unexplained time)
  const processingOverheadBreakdown = {
    mcpInit: 0, // Now tracked in Tool Time
    mcpCommunication: 0, // Now tracked in Tool Time
    resultProcessing: 0, // Now tracked in Tool Time
    browserWaitTime, // INFORMATIONAL: Browser time (already in Tool Time)
    networkWaitTime, // INFORMATIONAL: Network time (already in Tool Time)
    systemOverhead: totalProcessingOverhead, // TRUE system overhead (unmeasured time)
  };

  return {
    totalApiTime,
    totalToolTime,
    agentActiveTime,
    totalProcessingOverhead,
    processingOverheadBreakdown,
    apiTimePercent,
    toolTimePercent,
    processingOverheadPercent,
    apiTimeByModel,
    toolTimeByTool,
    shellCommandsByTool,
    webSearchPhasesByTool,
    mcpExecutionPhasesByTool,
    toolToServerMap, // Add the tool-to-server mapping
    cacheEfficiency,
    totalDecisions,
    successRate,
    agreementRate,
    totalCachedTokens,
    totalPromptTokens,
    totalLinesAdded: files.totalLinesAdded,
    totalLinesRemoved: files.totalLinesRemoved,
    mcpInitTime: mcpInitTime > 0 ? mcpInitTime : undefined,
    mcpServerBreakdown:
      Object.keys(mcpServerBreakdown).length > 0
        ? mcpServerBreakdown
        : undefined,
    toolValidationTime,
    userConfirmationTime,
    toolExecutionTime: timingMetrics?.totalToolExecutionTimeMs,
    idleTime,
  };
};
