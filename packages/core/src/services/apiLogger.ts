/**
 * @license
 * Copyright 2025 Google LLC
 * SPDX-License-Identifier: Apache-2.0
 */

import * as fs from 'node:fs';
import * as path from 'node:path';

/**
 * Service for logging all LLM API calls (inputs and outputs) to persistent files.
 * Each gemini-cli execution creates a new log file with timestamp-based naming (MM-DD-HH-N.log).
 * This allows for better organization and tracking of API calls across different sessions.
 */
export class ApiLogger {
  private static logFilePath: string | null = null;
  private static isEnabled = true;

  /**
   * Generate a unique log filename based on current date and time.
   * Format: MM-DD-HH-N.log where N is an incrementing number for files with the same timestamp.
   * @param logsDir - The logs directory path
   * @returns The generated filename
   */
  private static generateLogFilename(logsDir: string): string {
    const now = new Date();
    const month = String(now.getMonth() + 1).padStart(2, '0');
    const day = String(now.getDate()).padStart(2, '0');
    const hour = String(now.getHours()).padStart(2, '0');

    // Base filename without the counter
    const baseFilename = `${month}-${day}-${hour}`;

    // Find the next available number
    let counter = 1;
    let filename = `${baseFilename}-${counter}.log`;
    let filePath = path.join(logsDir, filename);

    // Increment counter until we find a filename that doesn't exist
    while (fs.existsSync(filePath)) {
      counter++;
      filename = `${baseFilename}-${counter}.log`;
      filePath = path.join(logsDir, filename);
    }

    return filename;
  }

  /**
   * Initialize the API logger with the log file path.
   * Creates the log directory if it doesn't exist.
   * Each gemini-cli execution creates a new log file with timestamp-based naming.
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

      // Generate a unique log filename for this session
      const filename = this.generateLogFilename(logsDir);
      this.logFilePath = path.join(logsDir, filename);

      // Write initialization header for this new session
      this.writeToLog(`${'='.repeat(80)}\n`);
      this.writeToLog(`Session started at: ${new Date().toISOString()}\n`);
      this.writeToLog(`Project: ${projectRoot}\n`);
      this.writeToLog(`Log file: ${filename}\n`);
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
