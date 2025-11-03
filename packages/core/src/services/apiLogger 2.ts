/**
 * @license
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import * as fs from 'node:fs';
import * as path from 'node:path';

/**
 * Service for logging all LLM API calls (inputs and outputs) to a persistent file.
 * All API calls across all sessions are logged to the same file for easy tracking.
 */
export class ApiLogger {
  private static logFilePath: string | null = null;
  private static isEnabled = true;

  /**
   * Initialize the API logger with the log file path.
   * Creates the log directory if it doesn't exist.
   * @param projectRoot - The root directory of the current project
   */
  static initialize(projectRoot: string): void {
    try {
      // Save logs in the project's logs directory
      const logsDir = path.join(projectRoot, 'logs');

      // Ensure logs directory exists
      if (!fs.existsSync(logsDir)) {
        fs.mkdirSync(logsDir, { recursive: true });
      }

      // Create log file path
      this.logFilePath = path.join(logsDir, 'api_calls.log');

      // Write initialization header if this is a new session
      this.writeToLog(`\n${'='.repeat(80)}\n`);
      this.writeToLog(`Session started at: ${new Date().toISOString()}\n`);
      this.writeToLog(`Project: ${projectRoot}\n`);
      this.writeToLog(`${'='.repeat(80)}\n\n`);
    } catch (error) {
      console.error('Failed to initialize API logger:', error);
      this.isEnabled = false;
    }
  }

  /**
   * Log an API request (input to LLM).
   */
  static logRequest(
    model: string,
    promptId: string,
    requestData: unknown,
  ): void {
    if (!this.isEnabled || !this.logFilePath) {
      return;
    }

    try {
      const timestamp = new Date().toISOString();
      const header = `\n${'-'.repeat(80)}\n`;
      const logEntry = [
        header,
        `[REQUEST] ${timestamp}`,
        `Model: ${model}`,
        `Prompt ID: ${promptId}`,
        `\nRequest Data:`,
        JSON.stringify(requestData, null, 2),
        header,
      ].join('\n');

      this.writeToLog(logEntry + '\n');
    } catch (error) {
      console.error('Failed to log API request:', error);
    }
  }

  /**
   * Log an API response (output from LLM).
   */
  static logResponse(
    model: string,
    promptId: string,
    responseData: unknown,
    durationMs?: number,
  ): void {
    if (!this.isEnabled || !this.logFilePath) {
      return;
    }

    try {
      const timestamp = new Date().toISOString();
      const header = `\n${'-'.repeat(80)}\n`;
      const durationInfo =
        durationMs !== undefined ? `Duration: ${durationMs}ms` : '';

      const logEntry = [
        header,
        `[RESPONSE] ${timestamp}`,
        `Model: ${model}`,
        `Prompt ID: ${promptId}`,
        durationInfo,
        `\nResponse Data:`,
        JSON.stringify(responseData, null, 2),
        header,
      ].join('\n');

      this.writeToLog(logEntry + '\n');
    } catch (error) {
      console.error('Failed to log API response:', error);
    }
  }

  /**
   * Log an API error.
   */
  static logError(
    model: string,
    promptId: string,
    error: unknown,
    durationMs?: number,
  ): void {
    if (!this.isEnabled || !this.logFilePath) {
      return;
    }

    try {
      const timestamp = new Date().toISOString();
      const header = `\n${'-'.repeat(80)}\n`;
      const durationInfo =
        durationMs !== undefined ? `Duration: ${durationMs}ms` : '';
      const errorMessage =
        error instanceof Error ? error.message : String(error);
      const errorStack = error instanceof Error ? error.stack : '';

      const logEntry = [
        header,
        `[ERROR] ${timestamp}`,
        `Model: ${model}`,
        `Prompt ID: ${promptId}`,
        durationInfo,
        `\nError Message: ${errorMessage}`,
        errorStack ? `\nStack Trace:\n${errorStack}` : '',
        header,
      ].join('\n');

      this.writeToLog(logEntry + '\n');
    } catch (error) {
      console.error('Failed to log API error:', error);
    }
  }

  /**
   * Get the path to the current log file.
   */
  static getLogFilePath(): string | null {
    return this.logFilePath;
  }

  /**
   * Write content to the log file.
   */
  private static writeToLog(content: string): void {
    if (!this.logFilePath) {
      return;
    }

    try {
      fs.appendFileSync(this.logFilePath, content, 'utf-8');
    } catch (error) {
      console.error('Failed to write to API log file:', error);
      this.isEnabled = false;
    }
  }

  /**
   * Disable API logging.
   */
  static disable(): void {
    this.isEnabled = false;
  }

  /**
   * Enable API logging.
   */
  static enable(): void {
    this.isEnabled = true;
  }

  /**
   * Check if API logging is enabled.
   */
  static isLoggingEnabled(): boolean {
    return this.isEnabled && this.logFilePath !== null;
  }
}
