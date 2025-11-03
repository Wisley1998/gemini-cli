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

  // Add MCP Overhead (communication + result processing) as a separate entry
  const mcpOverhead = mcpCommunicationOverhead + resultProcessingTime;
  if (mcpOverhead > 0) {
    toolTimeByTool['MCP Overhead'] = {
      timeMs: mcpOverhead,
      percent: totalToolTime > 0 ? (mcpOverhead / totalToolTime) * 100 : 0,
    };
  }

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
    Record<string, { timeMs: number; percent: number }>
  > = {};

  if (mcpMetrics?.toolExecutions) {
    for (const toolsMap of Object.values(mcpMetrics.toolExecutions)) {
      for (const [toolName, toolMetrics] of Object.entries(toolsMap)) {
        // Find the matching tool in toolTimeByTool to get the right display name
        // MCP tools might be prefixed with server name or renamed
        const matchingToolName = Object.keys(toolTimeByTool).find(
          (name) => name.includes(toolName) || toolName.includes(name),
        );

        if (matchingToolName && toolMetrics.totalExecutionTimeMs > 0) {
          mcpExecutionPhasesByTool[matchingToolName] = {
            Serialization: {
              timeMs: toolMetrics.totalSerializationTimeMs,
              percent:
                (toolMetrics.totalSerializationTimeMs /
                  toolMetrics.totalExecutionTimeMs) *
                100,
            },
            'MCP Call': {
              timeMs: toolMetrics.totalMcpCallTimeMs,
              percent:
                (toolMetrics.totalMcpCallTimeMs /
                  toolMetrics.totalExecutionTimeMs) *
                100,
            },
            Processing: {
              timeMs: toolMetrics.totalProcessingTimeMs,
              percent:
                (toolMetrics.totalProcessingTimeMs /
                  toolMetrics.totalExecutionTimeMs) *
                100,
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
  // These are the "hidden" wait times that appear as system overhead
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

  // Calculate total "processing overhead" - now excludes all MCP-related time (which is in Tool Time)
  // Processing overhead = Agent Active Time - (API Time + Tool Time + Tool Validation + User Confirmation + Idle)
  //
  // Then break it down into: Browser Wait, Network Wait, and True System Overhead
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

  // Calculate true system overhead (what's left after accounting for browser/network waits)
  const trueSystemOverhead = Math.max(
    0,
    totalProcessingOverhead - browserWaitTime - networkWaitTime,
  );

  // Build processing overhead breakdown with detailed categorization
  const processingOverheadBreakdown = {
    mcpInit: 0, // Now tracked in Tool Time
    mcpCommunication: 0, // Now tracked in Tool Time
    resultProcessing: 0, // Now tracked in Tool Time
    browserWaitTime, // Browser page loading and interaction wait time
    networkWaitTime, // Network request/response wait time
    systemOverhead: trueSystemOverhead, // True system overhead (GC, event loop, etc.)
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
