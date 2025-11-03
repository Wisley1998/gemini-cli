/**
 * @license
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import { describe, it, expect } from 'vitest';
import {
  calculateAverageLatency,
  calculateCacheHitRate,
  calculateErrorRate,
  computeSessionStats,
} from './computeStats.js';
import type {
  ModelMetrics,
  SessionMetrics,
} from '../contexts/SessionContext.js';

describe('calculateErrorRate', () => {
  it('should return 0 if totalRequests is 0', () => {
    const metrics: ModelMetrics = {
      api: { totalRequests: 0, totalErrors: 0, totalLatencyMs: 0 },
      tokens: {
        prompt: 0,
        candidates: 0,
        total: 0,
        cached: 0,
        thoughts: 0,
        tool: 0,
      },
    };
    expect(calculateErrorRate(metrics)).toBe(0);
  });

  it('should calculate the error rate correctly', () => {
    const metrics: ModelMetrics = {
      api: { totalRequests: 10, totalErrors: 2, totalLatencyMs: 0 },
      tokens: {
        prompt: 0,
        candidates: 0,
        total: 0,
        cached: 0,
        thoughts: 0,
        tool: 0,
      },
    };
    expect(calculateErrorRate(metrics)).toBe(20);
  });
});

describe('calculateAverageLatency', () => {
  it('should return 0 if totalRequests is 0', () => {
    const metrics: ModelMetrics = {
      api: { totalRequests: 0, totalErrors: 0, totalLatencyMs: 1000 },
      tokens: {
        prompt: 0,
        candidates: 0,
        total: 0,
        cached: 0,
        thoughts: 0,
        tool: 0,
      },
    };
    expect(calculateAverageLatency(metrics)).toBe(0);
  });

  it('should calculate the average latency correctly', () => {
    const metrics: ModelMetrics = {
      api: { totalRequests: 10, totalErrors: 0, totalLatencyMs: 1500 },
      tokens: {
        prompt: 0,
        candidates: 0,
        total: 0,
        cached: 0,
        thoughts: 0,
        tool: 0,
      },
    };
    expect(calculateAverageLatency(metrics)).toBe(150);
  });
});

describe('calculateCacheHitRate', () => {
  it('should return 0 if prompt tokens is 0', () => {
    const metrics: ModelMetrics = {
      api: { totalRequests: 0, totalErrors: 0, totalLatencyMs: 0 },
      tokens: {
        prompt: 0,
        candidates: 0,
        total: 0,
        cached: 100,
        thoughts: 0,
        tool: 0,
      },
    };
    expect(calculateCacheHitRate(metrics)).toBe(0);
  });

  it('should calculate the cache hit rate correctly', () => {
    const metrics: ModelMetrics = {
      api: { totalRequests: 0, totalErrors: 0, totalLatencyMs: 0 },
      tokens: {
        prompt: 200,
        candidates: 0,
        total: 0,
        cached: 50,
        thoughts: 0,
        tool: 0,
      },
    };
    expect(calculateCacheHitRate(metrics)).toBe(25);
  });
});

describe('computeSessionStats', () => {
  it('should return all zeros for initial empty metrics', () => {
    const metrics: SessionMetrics = {
      models: {},
      tools: {
        totalCalls: 0,
        totalSuccess: 0,
        totalFail: 0,
        totalDurationMs: 0,
        totalDecisions: { accept: 0, reject: 0, modify: 0, auto_accept: 0 },
        byName: {},
      },
      files: {
        totalLinesAdded: 0,
        totalLinesRemoved: 0,
      },
    };

    const result = computeSessionStats(metrics);

    expect(result).toEqual({
      totalApiTime: 0,
      totalToolTime: 0,
      agentActiveTime: 0,
      totalProcessingOverhead: 0,
      processingOverheadBreakdown: {
        mcpInit: 0,
        mcpCommunication: 0,
        resultProcessing: 0,
        browserWaitTime: 0,
        networkWaitTime: 0,
        systemOverhead: 0,
      },
      apiTimePercent: 0,
      toolTimePercent: 0,
      processingOverheadPercent: 0,
      apiTimeByModel: {},
      toolTimeByTool: {},
      shellCommandsByTool: {},
      webSearchPhasesByTool: {},
      mcpExecutionPhasesByTool: {},
      cacheEfficiency: 0,
      totalDecisions: 0,
      successRate: 0,
      agreementRate: 0,
      totalPromptTokens: 0,
      totalCachedTokens: 0,
      totalLinesAdded: 0,
      totalLinesRemoved: 0,
      mcpInitTime: undefined,
      mcpServerBreakdown: undefined,
      toolValidationTime: 0,
      userConfirmationTime: 0,
      toolExecutionTime: undefined,
      idleTime: 0,
    });
  });

  it('should correctly calculate API and tool time percentages', () => {
    const metrics: SessionMetrics = {
      models: {
        'gemini-pro': {
          api: { totalRequests: 1, totalErrors: 0, totalLatencyMs: 750 },
          tokens: {
            prompt: 10,
            candidates: 10,
            total: 20,
            cached: 0,
            thoughts: 0,
            tool: 0,
          },
        },
      },
      tools: {
        totalCalls: 1,
        totalSuccess: 1,
        totalFail: 0,
        totalDurationMs: 250,
        totalDecisions: { accept: 0, reject: 0, modify: 0, auto_accept: 0 },
        byName: {},
      },
      files: {
        totalLinesAdded: 0,
        totalLinesRemoved: 0,
      },
    };

    const result = computeSessionStats(metrics);

    expect(result.totalApiTime).toBe(750);
    expect(result.totalToolTime).toBe(250);
    expect(result.agentActiveTime).toBe(1000);
    expect(result.totalProcessingOverhead).toBe(0);
    expect(result.apiTimePercent).toBe(75);
    expect(result.toolTimePercent).toBe(25);
    expect(result.processingOverheadPercent).toBe(0);
  });

  it('should correctly calculate other time when wall time is provided', () => {
    const metrics: SessionMetrics = {
      models: {
        'gemini-pro': {
          api: { totalRequests: 1, totalErrors: 0, totalLatencyMs: 750 },
          tokens: {
            prompt: 10,
            candidates: 10,
            total: 20,
            cached: 0,
            thoughts: 0,
            tool: 0,
          },
        },
      },
      tools: {
        totalCalls: 1,
        totalSuccess: 1,
        totalFail: 0,
        totalDurationMs: 250,
        totalDecisions: { accept: 0, reject: 0, modify: 0, auto_accept: 0 },
        byName: {},
      },
      files: {
        totalLinesAdded: 0,
        totalLinesRemoved: 0,
      },
    };

    const wallTimeMs = 2000; // 2 seconds total
    const result = computeSessionStats(metrics, wallTimeMs);

    expect(result.totalApiTime).toBe(750);
    expect(result.totalToolTime).toBe(250);
    expect(result.agentActiveTime).toBe(2000); // Uses wall time
    expect(result.totalProcessingOverhead).toBe(1000); // 2000 - 750 - 250 = 1000ms
    expect(result.apiTimePercent).toBe(37.5); // 750/2000
    expect(result.toolTimePercent).toBe(12.5); // 250/2000
    expect(result.processingOverheadPercent).toBe(50); // 1000/2000
  });

  it('should correctly calculate cache efficiency', () => {
    const metrics: SessionMetrics = {
      models: {
        'gemini-pro': {
          api: { totalRequests: 2, totalErrors: 0, totalLatencyMs: 1000 },
          tokens: {
            prompt: 150,
            candidates: 10,
            total: 160,
            cached: 50,
            thoughts: 0,
            tool: 0,
          },
        },
      },
      tools: {
        totalCalls: 0,
        totalSuccess: 0,
        totalFail: 0,
        totalDurationMs: 0,
        totalDecisions: { accept: 0, reject: 0, modify: 0, auto_accept: 0 },
        byName: {},
      },
      files: {
        totalLinesAdded: 0,
        totalLinesRemoved: 0,
      },
    };

    const result = computeSessionStats(metrics);

    expect(result.cacheEfficiency).toBeCloseTo(33.33); // 50 / 150
  });

  it('should correctly calculate success and agreement rates', () => {
    const metrics: SessionMetrics = {
      models: {},
      tools: {
        totalCalls: 10,
        totalSuccess: 8,
        totalFail: 2,
        totalDurationMs: 1000,
        totalDecisions: { accept: 6, reject: 2, modify: 2, auto_accept: 0 },
        byName: {},
      },
      files: {
        totalLinesAdded: 0,
        totalLinesRemoved: 0,
      },
    };

    const result = computeSessionStats(metrics);

    expect(result.successRate).toBe(80); // 8 / 10
    expect(result.agreementRate).toBe(60); // 6 / 10
  });

  it('should handle division by zero gracefully', () => {
    const metrics: SessionMetrics = {
      models: {},
      tools: {
        totalCalls: 0,
        totalSuccess: 0,
        totalFail: 0,
        totalDurationMs: 0,
        totalDecisions: { accept: 0, reject: 0, modify: 0, auto_accept: 0 },
        byName: {},
      },
      files: {
        totalLinesAdded: 0,
        totalLinesRemoved: 0,
      },
    };

    const result = computeSessionStats(metrics);

    expect(result.apiTimePercent).toBe(0);
    expect(result.toolTimePercent).toBe(0);
    expect(result.cacheEfficiency).toBe(0);
    expect(result.successRate).toBe(0);
    expect(result.agreementRate).toBe(0);
  });

  it('should correctly include line counts', () => {
    const metrics: SessionMetrics = {
      models: {},
      tools: {
        totalCalls: 0,
        totalSuccess: 0,
        totalFail: 0,
        totalDurationMs: 0,
        totalDecisions: { accept: 0, reject: 0, modify: 0, auto_accept: 0 },
        byName: {},
      },
      files: {
        totalLinesAdded: 42,
        totalLinesRemoved: 18,
      },
    };

    const result = computeSessionStats(metrics);

    expect(result.totalLinesAdded).toBe(42);
    expect(result.totalLinesRemoved).toBe(18);
  });

  it('should correctly identify browser and network wait times from MCP tools', () => {
    const metrics: SessionMetrics = {
      models: {
        'gemini-pro': {
          api: { totalRequests: 1, totalErrors: 0, totalLatencyMs: 1000 },
          tokens: {
            prompt: 100,
            candidates: 100,
            total: 200,
            cached: 0,
            thoughts: 0,
            tool: 0,
          },
        },
      },
      tools: {
        totalCalls: 2,
        totalSuccess: 2,
        totalFail: 0,
        totalDurationMs: 500,
        totalDecisions: { accept: 2, reject: 0, modify: 0, auto_accept: 0 },
        byName: {},
      },
      files: {
        totalLinesAdded: 0,
        totalLinesRemoved: 0,
      },
      mcp: {
        totalInitTimeMs: 100,
        servers: {},
        toolExecutions: {
          playwright: {
            browser_navigate: {
              toolName: 'browser_navigate',
              executionCount: 1,
              totalSerializationTimeMs: 10,
              totalMcpCallTimeMs: 30000, // 30 seconds in browser
              totalProcessingTimeMs: 5,
              totalExecutionTimeMs: 30015,
            },
          },
          fetcher: {
            fetch_url: {
              toolName: 'fetch_url',
              executionCount: 1,
              totalSerializationTimeMs: 8,
              totalMcpCallTimeMs: 20000, // 20 seconds network
              totalProcessingTimeMs: 3,
              totalExecutionTimeMs: 20011,
            },
          },
        },
      } as SessionMetrics['mcp'],
    };

    const wallTimeMs = 60000; // 60 seconds total
    const result = computeSessionStats(metrics, wallTimeMs);

    // Browser wait time should be identified from playwright tools
    expect(result.processingOverheadBreakdown.browserWaitTime).toBe(30000);

    // Network wait time should be identified from fetcher tools
    expect(result.processingOverheadBreakdown.networkWaitTime).toBe(20000);

    // True system overhead should be what's left
    // 60000 (wall) - 1000 (api) - 500 (tool) - 30000 (browser) - 20000 (network) = 8500
    expect(result.processingOverheadBreakdown.systemOverhead).toBe(8500);
  });
});
