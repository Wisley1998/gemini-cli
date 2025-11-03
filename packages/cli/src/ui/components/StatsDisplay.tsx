/**
 * @license
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import type React from 'react';
import { Box, Text } from 'ink';
import Gradient from 'ink-gradient';
import { theme } from '../semantic-colors.js';
import { formatDuration } from '../utils/formatters.js';
import type { ModelMetrics } from '../contexts/SessionContext.js';
import { useSessionStats } from '../contexts/SessionContext.js';
import {
  getStatusColor,
  TOOL_SUCCESS_RATE_HIGH,
  TOOL_SUCCESS_RATE_MEDIUM,
  USER_AGREEMENT_RATE_HIGH,
  USER_AGREEMENT_RATE_MEDIUM,
} from '../utils/displayUtils.js';
import { computeSessionStats } from '../utils/computeStats.js';

// A more flexible and powerful StatRow component
interface StatRowProps {
  title: string;
  children: React.ReactNode; // Use children to allow for complex, colored values
}

const StatRow: React.FC<StatRowProps> = ({ title, children }) => (
  <Box>
    {/* Fixed width for the label creates a clean "gutter" for alignment */}
    <Box width={28}>
      <Text color={theme.text.link}>{title}</Text>
    </Box>
    {/* FIX: Wrap children in a Box that can grow to fill remaining space */}
    <Box flexGrow={1}>{children}</Box>
  </Box>
);

// A SubStatRow for indented, secondary information
interface SubStatRowProps {
  title: string;
  children: React.ReactNode;
}

const SubStatRow: React.FC<SubStatRowProps> = ({ title, children }) => (
  <Box paddingLeft={2}>
    {/* Adjust width for the "» " prefix */}
    <Box width={26}>
      <Text color={theme.text.secondary}>» {title}</Text>
    </Box>
    {/* FIX: Apply the same flexGrow fix here */}
    <Box flexGrow={1}>{children}</Box>
  </Box>
);

// A Section component to group related stats
interface SectionProps {
  title: string;
  children: React.ReactNode;
}

const Section: React.FC<SectionProps> = ({ title, children }) => (
  <Box flexDirection="column" width="100%" marginBottom={1}>
    <Text bold color={theme.text.primary}>
      {title}
    </Text>
    {children}
  </Box>
);

const ModelUsageTable: React.FC<{
  models: Record<string, ModelMetrics>;
  totalCachedTokens: number;
  cacheEfficiency: number;
}> = ({ models, totalCachedTokens, cacheEfficiency }) => {
  const nameWidth = 25;
  const requestsWidth = 8;
  const inputTokensWidth = 15;
  const outputTokensWidth = 15;

  return (
    <Box flexDirection="column" marginTop={1}>
      {/* Header */}
      <Box>
        <Box width={nameWidth}>
          <Text bold color={theme.text.primary}>
            Model Usage
          </Text>
        </Box>
        <Box width={requestsWidth} justifyContent="flex-end">
          <Text bold color={theme.text.primary}>
            Reqs
          </Text>
        </Box>
        <Box width={inputTokensWidth} justifyContent="flex-end">
          <Text bold color={theme.text.primary}>
            Input Tokens
          </Text>
        </Box>
        <Box width={outputTokensWidth} justifyContent="flex-end">
          <Text bold color={theme.text.primary}>
            Output Tokens
          </Text>
        </Box>
      </Box>
      {/* Divider */}
      <Box
        borderStyle="round"
        borderBottom={true}
        borderTop={false}
        borderLeft={false}
        borderRight={false}
        borderColor={theme.border.default}
        width={nameWidth + requestsWidth + inputTokensWidth + outputTokensWidth}
      ></Box>

      {/* Rows */}
      {Object.entries(models).map(([name, modelMetrics]) => (
        <Box key={name}>
          <Box width={nameWidth}>
            <Text color={theme.text.primary}>{name.replace('-001', '')}</Text>
          </Box>
          <Box width={requestsWidth} justifyContent="flex-end">
            <Text color={theme.text.primary}>
              {modelMetrics.api.totalRequests}
            </Text>
          </Box>
          <Box width={inputTokensWidth} justifyContent="flex-end">
            <Text color={theme.status.warning}>
              {modelMetrics.tokens.prompt.toLocaleString()}
            </Text>
          </Box>
          <Box width={outputTokensWidth} justifyContent="flex-end">
            <Text color={theme.status.warning}>
              {modelMetrics.tokens.candidates.toLocaleString()}
            </Text>
          </Box>
        </Box>
      ))}
      {cacheEfficiency > 0 && (
        <Box flexDirection="column" marginTop={1}>
          <Text color={theme.text.primary}>
            <Text color={theme.status.success}>Savings Highlight:</Text>{' '}
            {totalCachedTokens.toLocaleString()} ({cacheEfficiency.toFixed(1)}
            %) of input tokens were served from the cache, reducing costs.
          </Text>
          <Box height={1} />
          <Text color={theme.text.secondary}>
            » Tip: For a full token breakdown, run `/stats model`.
          </Text>
        </Box>
      )}
    </Box>
  );
};

interface StatsDisplayProps {
  duration: string;
  wallTimeMs?: number; // Optional wall clock time in milliseconds
  title?: string;
}

export const StatsDisplay: React.FC<StatsDisplayProps> = ({
  duration,
  wallTimeMs,
  title,
}) => {
  const { stats } = useSessionStats();
  const { metrics } = stats;
  const { models, tools, files } = metrics;
  const computed = computeSessionStats(metrics, wallTimeMs);

  const successThresholds = {
    green: TOOL_SUCCESS_RATE_HIGH,
    yellow: TOOL_SUCCESS_RATE_MEDIUM,
  };
  const agreementThresholds = {
    green: USER_AGREEMENT_RATE_HIGH,
    yellow: USER_AGREEMENT_RATE_MEDIUM,
  };
  const successColor = getStatusColor(computed.successRate, successThresholds);
  const agreementColor = getStatusColor(
    computed.agreementRate,
    agreementThresholds,
  );

  const renderTitle = () => {
    if (title) {
      return theme.ui.gradient && theme.ui.gradient.length > 0 ? (
        <Gradient colors={theme.ui.gradient}>
          <Text bold color={theme.text.primary}>
            {title}
          </Text>
        </Gradient>
      ) : (
        <Text bold color={theme.text.accent}>
          {title}
        </Text>
      );
    }
    return (
      <Text bold color={theme.text.accent}>
        Session Stats
      </Text>
    );
  };

  return (
    <Box
      borderStyle="round"
      borderColor={theme.border.default}
      flexDirection="column"
      paddingY={1}
      paddingX={2}
    >
      {renderTitle()}
      <Box height={1} />

      <Section title="Interaction Summary">
        <StatRow title="Session ID:">
          <Text color={theme.text.primary}>{stats.sessionId}</Text>
        </StatRow>
        <StatRow title="Tool Calls:">
          <Text color={theme.text.primary}>
            {tools.totalCalls} ({' '}
            <Text color={theme.status.success}>✓ {tools.totalSuccess}</Text>{' '}
            <Text color={theme.status.error}>x {tools.totalFail}</Text> )
          </Text>
        </StatRow>
        <StatRow title="Success Rate:">
          <Text color={successColor}>{computed.successRate.toFixed(1)}%</Text>
        </StatRow>
        {computed.totalDecisions > 0 && (
          <StatRow title="User Agreement:">
            <Text color={agreementColor}>
              {computed.agreementRate.toFixed(1)}%{' '}
              <Text color={theme.text.secondary}>
                ({computed.totalDecisions} reviewed)
              </Text>
            </Text>
          </StatRow>
        )}
        {files &&
          (files.totalLinesAdded > 0 || files.totalLinesRemoved > 0) && (
            <StatRow title="Code Changes:">
              <Text color={theme.text.primary}>
                <Text color={theme.status.success}>
                  +{files.totalLinesAdded}
                </Text>{' '}
                <Text color={theme.status.error}>
                  -{files.totalLinesRemoved}
                </Text>
              </Text>
            </StatRow>
          )}
      </Section>

      <Section title="Performance">
        <StatRow title="Wall Time:">
          <Text color={theme.text.primary}>{duration}</Text>
        </StatRow>
        <StatRow title="Agent Active:">
          <Text color={theme.text.primary}>
            {formatDuration(computed.agentActiveTime)}
          </Text>
        </StatRow>
        <SubStatRow title="API Time:">
          <Text color={theme.text.primary}>
            {formatDuration(computed.totalApiTime)}{' '}
            <Text color={theme.text.secondary}>
              ({computed.apiTimePercent.toFixed(1)}%)
            </Text>
          </Text>
        </SubStatRow>
        {/* Show breakdown by model if there are multiple models or if there's any API time */}
        {Object.entries(computed.apiTimeByModel).length > 0 &&
          computed.totalApiTime > 0 && (
            <Box flexDirection="column" paddingLeft={4}>
              {Object.entries(computed.apiTimeByModel)
                .sort((a, b) => b[1].timeMs - a[1].timeMs)
                .map(([modelName, modelTime]) => (
                  <Box key={modelName}>
                    <Box width={24}>
                      <Text color={theme.text.secondary}>
                        • {modelName.replace('-001', '')}:
                      </Text>
                    </Box>
                    <Box flexGrow={1}>
                      <Text color={theme.text.secondary}>
                        {formatDuration(modelTime.timeMs)}{' '}
                        <Text color={theme.text.secondary} dimColor>
                          ({modelTime.percent.toFixed(1)}%)
                        </Text>
                      </Text>
                    </Box>
                  </Box>
                ))}
            </Box>
          )}
        <SubStatRow title="Tool Time:">
          <Text color={theme.text.primary}>
            {formatDuration(computed.totalToolTime)}{' '}
            <Text color={theme.text.secondary}>
              ({computed.toolTimePercent.toFixed(1)}%)
            </Text>
          </Text>
        </SubStatRow>
        {/* Show breakdown by tool if there are tools and tool time */}
        {Object.entries(computed.toolTimeByTool).length > 0 &&
          computed.totalToolTime > 0 && (
            <Box flexDirection="column" paddingLeft={4}>
              {Object.entries(computed.toolTimeByTool)
                .sort((a, b) => b[1].timeMs - a[1].timeMs)
                .map(([toolName, toolTime]) => (
                  <Box key={toolName} flexDirection="column">
                    <Box>
                      <Box width={24}>
                        <Text color={theme.text.secondary}>
                          • {toolName}
                          {computed.toolToServerMap?.[toolName] && (
                            <Text color={theme.text.secondary} dimColor>
                              {' '}
                              ({computed.toolToServerMap[toolName]})
                            </Text>
                          )}
                          :
                        </Text>
                      </Box>
                      <Box flexGrow={1}>
                        <Text color={theme.text.secondary}>
                          {formatDuration(toolTime.timeMs)}{' '}
                          <Text color={theme.text.secondary} dimColor>
                            ({toolTime.percent.toFixed(1)}%)
                          </Text>
                        </Text>
                      </Box>
                    </Box>
                    {/* Show shell command breakdown for run_shell_command */}
                    {computed.shellCommandsByTool[toolName] &&
                      Object.keys(computed.shellCommandsByTool[toolName])
                        .length > 0 && (
                        <Box flexDirection="column" paddingLeft={2}>
                          {Object.entries(
                            computed.shellCommandsByTool[toolName],
                          )
                            .sort((a, b) => b[1].timeMs - a[1].timeMs)
                            .slice(0, 5) // Show top 5 commands
                            .map(([cmdName, cmdTime]) => (
                              <Box key={cmdName}>
                                <Box width={22}>
                                  <Text color={theme.text.secondary} dimColor>
                                    ‣ {cmdName}:
                                  </Text>
                                </Box>
                                <Box flexGrow={1}>
                                  <Text color={theme.text.secondary} dimColor>
                                    {formatDuration(cmdTime.timeMs)}{' '}
                                    <Text color={theme.text.secondary} dimColor>
                                      ({cmdTime.percent.toFixed(1)}%)
                                    </Text>
                                  </Text>
                                </Box>
                              </Box>
                            ))}
                          {Object.keys(computed.shellCommandsByTool[toolName])
                            .length > 5 && (
                            <Box paddingLeft={2}>
                              <Text color={theme.text.secondary} dimColor>
                                ... and{' '}
                                {Object.keys(
                                  computed.shellCommandsByTool[toolName],
                                ).length - 5}{' '}
                                more commands
                              </Text>
                            </Box>
                          )}
                        </Box>
                      )}
                    {/* Show execution phase breakdown for google_web_search */}
                    {computed.webSearchPhasesByTool[toolName] &&
                      Object.keys(computed.webSearchPhasesByTool[toolName])
                        .length > 0 && (
                        <Box flexDirection="column" paddingLeft={2}>
                          {Object.entries(
                            computed.webSearchPhasesByTool[toolName],
                          )
                            .sort((a, b) => b[1].timeMs - a[1].timeMs)
                            .map(([phaseName, phaseTime]) => (
                              <Box key={phaseName}>
                                <Box width={22}>
                                  <Text color={theme.text.secondary} dimColor>
                                    ‣ {phaseName}:
                                  </Text>
                                </Box>
                                <Box flexGrow={1}>
                                  <Text color={theme.text.secondary} dimColor>
                                    {formatDuration(phaseTime.timeMs)}{' '}
                                    <Text color={theme.text.secondary} dimColor>
                                      ({phaseTime.percent.toFixed(1)}%)
                                    </Text>
                                  </Text>
                                </Box>
                              </Box>
                            ))}
                        </Box>
                      )}
                    {/* Show MCP execution phase breakdown for MCP tools */}
                    {computed.mcpExecutionPhasesByTool[toolName] &&
                      Object.keys(computed.mcpExecutionPhasesByTool[toolName])
                        .length > 0 && (
                        <Box flexDirection="column" paddingLeft={2}>
                          {Object.entries(
                            computed.mcpExecutionPhasesByTool[toolName],
                          )
                            // Filter out Serialization and Processing if they are 0 or near 0
                            .filter(([phaseName, phaseTime]) => {
                              if (
                                phaseName === 'Serialization' ||
                                phaseName === 'Processing'
                              ) {
                                return phaseTime.timeMs > 0.5; // Only show if > 0.5ms
                              }
                              return true; // Always show MCP Call
                            })
                            .sort((a, b) => b[1].timeMs - a[1].timeMs)
                            .map(([phaseName, phaseTime]) => (
                              <Box key={phaseName} flexDirection="column">
                                <Box>
                                  <Box width={22}>
                                    <Text color={theme.text.secondary} dimColor>
                                      ‣ {phaseName}:
                                    </Text>
                                  </Box>
                                  <Box flexGrow={1}>
                                    <Text color={theme.text.secondary} dimColor>
                                      {formatDuration(phaseTime.timeMs)}{' '}
                                      <Text
                                        color={theme.text.secondary}
                                        dimColor
                                      >
                                        ({phaseTime.percent.toFixed(1)}%)
                                      </Text>
                                    </Text>
                                  </Box>
                                </Box>
                                {/* 显示 MCP Call 的内部子阶段 */}
                                {phaseName === 'MCP Call' &&
                                  phaseTime.subPhases &&
                                  phaseTime.subPhases.length > 0 && (
                                    <Box flexDirection="column" paddingLeft={2}>
                                      {phaseTime.subPhases
                                        .sort(
                                          (
                                            a: {
                                              name: string;
                                              timeMs: number;
                                              percent: number;
                                            },
                                            b: {
                                              name: string;
                                              timeMs: number;
                                              percent: number;
                                            },
                                          ) => b.timeMs - a.timeMs,
                                        )
                                        .map(
                                          (subPhase: {
                                            name: string;
                                            timeMs: number;
                                            percent: number;
                                          }) => (
                                            <Box key={subPhase.name}>
                                              <Box width={20}>
                                                <Text
                                                  color={theme.text.secondary}
                                                  dimColor
                                                >
                                                  - {subPhase.name}:
                                                </Text>
                                              </Box>
                                              <Box flexGrow={1}>
                                                <Text
                                                  color={theme.text.secondary}
                                                  dimColor
                                                >
                                                  {formatDuration(
                                                    subPhase.timeMs,
                                                  )}{' '}
                                                  <Text
                                                    color={theme.text.secondary}
                                                    dimColor
                                                  >
                                                    (
                                                    {subPhase.percent.toFixed(
                                                      1,
                                                    )}
                                                    %)
                                                  </Text>
                                                </Text>
                                              </Box>
                                            </Box>
                                          ),
                                        )}
                                    </Box>
                                  )}
                              </Box>
                            ))}
                        </Box>
                      )}
                  </Box>
                ))}
            </Box>
          )}
        {/* Show "Processing Overhead" with breakdown */}
        {(computed.processingOverheadPercent > 1 ||
          computed.totalProcessingOverhead > 100) && (
          <SubStatRow title="Processing Overhead:">
            <Text color={theme.text.primary}>
              {formatDuration(computed.totalProcessingOverhead)}{' '}
              <Text color={theme.text.secondary}>
                ({computed.processingOverheadPercent.toFixed(1)}%)
              </Text>
            </Text>
          </SubStatRow>
        )}
        {(computed.processingOverheadPercent > 1 ||
          computed.totalProcessingOverhead > 100) && (
          <Box flexDirection="column" paddingLeft={4}>
            {computed.processingOverheadBreakdown.mcpInit > 0 && (
              <Box>
                <Box width={24}>
                  <Text color={theme.text.secondary}>• MCP Init:</Text>
                </Box>
                <Box flexGrow={1}>
                  <Text color={theme.text.secondary}>
                    {formatDuration(
                      computed.processingOverheadBreakdown.mcpInit,
                    )}{' '}
                    <Text color={theme.text.secondary} dimColor>
                      (
                      {(
                        (computed.processingOverheadBreakdown.mcpInit /
                          computed.totalProcessingOverhead) *
                        100
                      ).toFixed(1)}
                      %)
                    </Text>
                  </Text>
                </Box>
              </Box>
            )}
            {computed.processingOverheadBreakdown.mcpCommunication > 0 && (
              <Box>
                <Box width={24}>
                  <Text color={theme.text.secondary}>• MCP Communication:</Text>
                </Box>
                <Box flexGrow={1}>
                  <Text color={theme.text.secondary}>
                    {formatDuration(
                      computed.processingOverheadBreakdown.mcpCommunication,
                    )}{' '}
                    <Text color={theme.text.secondary} dimColor>
                      (
                      {(
                        (computed.processingOverheadBreakdown.mcpCommunication /
                          computed.totalProcessingOverhead) *
                        100
                      ).toFixed(1)}
                      %)
                    </Text>
                  </Text>
                </Box>
              </Box>
            )}
            {computed.processingOverheadBreakdown.resultProcessing > 0 && (
              <Box>
                <Box width={24}>
                  <Text color={theme.text.secondary}>• Result Processing:</Text>
                </Box>
                <Box flexGrow={1}>
                  <Text color={theme.text.secondary}>
                    {formatDuration(
                      computed.processingOverheadBreakdown.resultProcessing,
                    )}{' '}
                    <Text color={theme.text.secondary} dimColor>
                      (
                      {(
                        (computed.processingOverheadBreakdown.resultProcessing /
                          computed.totalProcessingOverhead) *
                        100
                      ).toFixed(1)}
                      %)
                    </Text>
                  </Text>
                </Box>
              </Box>
            )}
            {/* Browser and Network Wait Times - these are INFORMATIONAL */}
            {(computed.processingOverheadBreakdown.browserWaitTime > 0 ||
              computed.processingOverheadBreakdown.networkWaitTime > 0) && (
              <Box marginTop={1} marginBottom={0}>
                <Text color={theme.text.secondary} dimColor>
                  ℹ MCP Tool Wait Times (included in Tool Time above):
                </Text>
              </Box>
            )}
            {computed.processingOverheadBreakdown.browserWaitTime > 0 && (
              <Box>
                <Box width={28}>
                  <Text color={theme.text.secondary} dimColor>
                    ↳ Browser Wait:
                  </Text>
                </Box>
                <Box flexGrow={1}>
                  <Text color={theme.text.secondary} dimColor>
                    {formatDuration(
                      computed.processingOverheadBreakdown.browserWaitTime,
                    )}
                  </Text>
                </Box>
              </Box>
            )}
            {computed.processingOverheadBreakdown.networkWaitTime > 0 && (
              <Box>
                <Box width={28}>
                  <Text color={theme.text.secondary} dimColor>
                    ↳ Network Wait:
                  </Text>
                </Box>
                <Box flexGrow={1}>
                  <Text color={theme.text.secondary} dimColor>
                    {formatDuration(
                      computed.processingOverheadBreakdown.networkWaitTime,
                    )}
                  </Text>
                </Box>
              </Box>
            )}
            {computed.processingOverheadBreakdown.systemOverhead > 0 && (
              <Box>
                <Box width={24}>
                  <Text color={theme.text.secondary}>
                    • True System Overhead:
                  </Text>
                </Box>
                <Box flexGrow={1}>
                  <Text color={theme.text.secondary}>
                    {formatDuration(
                      computed.processingOverheadBreakdown.systemOverhead,
                    )}{' '}
                    <Text color={theme.text.secondary} dimColor>
                      (
                      {(
                        (computed.processingOverheadBreakdown.systemOverhead /
                          computed.totalProcessingOverhead) *
                        100
                      ).toFixed(1)}
                      %)
                    </Text>
                  </Text>
                </Box>
              </Box>
            )}
          </Box>
        )}

        {/* Detailed timing breakdown */}
        {(Boolean(
          computed.toolValidationTime && computed.toolValidationTime > 0,
        ) ||
          Boolean(
            computed.userConfirmationTime && computed.userConfirmationTime > 0,
          ) ||
          Boolean(
            computed.mcpServerBreakdown &&
              Object.keys(computed.mcpServerBreakdown).length > 0,
          )) && (
          <>
            <Box height={1} />
            <Text color={theme.text.primary} bold>
              Detailed Timing Breakdown
            </Text>
            <Box height={1} />
          </>
        )}

        {/* MCP Server Details (under Processing Overhead > MCP Init) */}
        {Boolean(
          computed.mcpServerBreakdown &&
            Object.keys(computed.mcpServerBreakdown).length > 0,
        ) && (
          <>
            <SubStatRow title="MCP Servers:">
              <Text color={theme.text.secondary} dimColor>
                (detailed breakdown)
              </Text>
            </SubStatRow>
            <Box flexDirection="column" paddingLeft={4}>
              {Object.entries(computed.mcpServerBreakdown ?? {}).map(
                ([serverName, serverTiming]) => {
                  // Calculate total MCP init time for percentage calculation
                  const totalMcpInitTime = Object.values(
                    computed.mcpServerBreakdown ?? {},
                  ).reduce((sum, server) => sum + server.totalTimeMs, 0);
                  return (
                    <Box
                      key={serverName}
                      flexDirection="column"
                      marginBottom={1}
                    >
                      <Box>
                        <Box width={24}>
                          <Text color={theme.text.secondary}>
                            • {serverName}:
                          </Text>
                        </Box>
                        <Box flexGrow={1}>
                          <Text color={theme.text.secondary}>
                            {formatDuration(serverTiming.totalTimeMs)}{' '}
                            <Text color={theme.text.secondary} dimColor>
                              (
                              {totalMcpInitTime > 0
                                ? (
                                    (serverTiming.totalTimeMs /
                                      totalMcpInitTime) *
                                    100
                                  ).toFixed(1)
                                : '0.0'}
                              %)
                            </Text>
                          </Text>
                        </Box>
                      </Box>
                      <Box flexDirection="column" paddingLeft={2}>
                        <Box>
                          <Box width={22}>
                            <Text color={theme.text.secondary} dimColor>
                              ‣ Connection:
                            </Text>
                          </Box>
                          <Box flexGrow={1}>
                            <Text color={theme.text.secondary} dimColor>
                              {formatDuration(serverTiming.connectionTimeMs)}{' '}
                              <Text color={theme.text.secondary} dimColor>
                                (
                                {(
                                  (serverTiming.connectionTimeMs /
                                    serverTiming.totalTimeMs) *
                                  100
                                ).toFixed(1)}
                                %)
                              </Text>
                            </Text>
                          </Box>
                        </Box>
                        <Box>
                          <Box width={22}>
                            <Text color={theme.text.secondary} dimColor>
                              ‣ Discovery:
                            </Text>
                          </Box>
                          <Box flexGrow={1}>
                            <Text color={theme.text.secondary} dimColor>
                              {formatDuration(serverTiming.discoveryTimeMs)}{' '}
                              <Text color={theme.text.secondary} dimColor>
                                (
                                {(
                                  (serverTiming.discoveryTimeMs /
                                    serverTiming.totalTimeMs) *
                                  100
                                ).toFixed(1)}
                                %)
                              </Text>
                            </Text>
                          </Box>
                        </Box>
                        {Boolean(
                          serverTiming.dockerPullTimeMs &&
                            serverTiming.dockerPullTimeMs > 0,
                        ) && (
                          <Box>
                            <Box width={24} paddingLeft={2}>
                              <Text color={theme.text.secondary}>
                                - Docker Pull:
                              </Text>
                            </Box>
                            <Box flexGrow={1}>
                              <Text color={theme.text.secondary}>
                                {formatDuration(
                                  serverTiming.dockerPullTimeMs ?? 0,
                                )}{' '}
                                <Text color={theme.text.secondary} dimColor>
                                  (
                                  {(
                                    ((serverTiming.dockerPullTimeMs ?? 0) /
                                      serverTiming.totalTimeMs) *
                                    100
                                  ).toFixed(1)}
                                  %)
                                </Text>
                              </Text>
                            </Box>
                          </Box>
                        )}
                        {Boolean(
                          serverTiming.containerStartTimeMs &&
                            serverTiming.containerStartTimeMs > 0,
                        ) && (
                          <Box>
                            <Box width={22}>
                              <Text color={theme.text.secondary} dimColor>
                                ‣ Container Start:
                              </Text>
                            </Box>
                            <Box flexGrow={1}>
                              <Text color={theme.text.secondary} dimColor>
                                {formatDuration(
                                  serverTiming.containerStartTimeMs ?? 0,
                                )}{' '}
                                <Text color={theme.text.secondary} dimColor>
                                  (
                                  {(
                                    ((serverTiming.containerStartTimeMs ?? 0) /
                                      serverTiming.totalTimeMs) *
                                    100
                                  ).toFixed(1)}
                                  %)
                                </Text>
                              </Text>
                            </Box>
                          </Box>
                        )}
                      </Box>
                    </Box>
                  );
                },
              )}
            </Box>
          </>
        )}

        {/* Tool timing breakdown - shown in "Detailed Timing Breakdown" section */}
        {Boolean(
          computed.toolValidationTime && computed.toolValidationTime > 0,
        ) && (
          <SubStatRow title="Tool Validation:">
            <Text color={theme.text.primary}>
              {formatDuration(computed.toolValidationTime ?? 0)}
            </Text>
          </SubStatRow>
        )}
        {Boolean(
          computed.userConfirmationTime && computed.userConfirmationTime > 0,
        ) && (
          <SubStatRow title="User Confirmation:">
            <Text color={theme.text.primary}>
              {formatDuration(computed.userConfirmationTime ?? 0)}
            </Text>
          </SubStatRow>
        )}
        {Boolean(
          computed.toolExecutionTime && computed.toolExecutionTime > 0,
        ) && (
          <SubStatRow title="Tool Execution:">
            <Text color={theme.text.primary}>
              {formatDuration(computed.toolExecutionTime ?? 0)}
            </Text>
          </SubStatRow>
        )}
        {/* Idle Time is NOT shown - we don't track idle/waiting time */}
      </Section>

      {Object.keys(models).length > 0 && (
        <ModelUsageTable
          models={models}
          totalCachedTokens={computed.totalCachedTokens}
          cacheEfficiency={computed.cacheEfficiency}
        />
      )}
    </Box>
  );
};
