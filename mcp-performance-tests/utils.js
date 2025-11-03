/**
 * MCP Performance Test Utilities
 * 独立的工具函数，用于测量MCP服务器性能
 */

/**
 * 格式化时间戳
 */
export function formatTimestamp() {
  return new Date().toISOString().replace('T', ' ').substring(0, 23);
}

/**
 * 打印带时间戳的日志
 */
export function logWithTimestamp(emoji, message) {
  console.log(`[${formatTimestamp()}] ${emoji} ${message}`);
}

/**
 * 测量函数执行时间
 */
export async function measureTime(fn, label) {
  const startTime = Date.now();
  const result = await fn();
  const duration = Date.now() - startTime;
  logWithTimestamp('⏱️ ', `${label}: ${duration}ms`);
  return { result, duration };
}

/**
 * 打印分隔线
 */
export function printSeparator(title = '') {
  console.log('\n' + '='.repeat(60));
  if (title) {
    console.log(title);
    console.log('='.repeat(60));
  }
}

/**
 * 打印性能统计摘要
 */
export function printPerformanceSummary(stats) {
  printSeparator('Performance Summary / 性能统计摘要');

  console.log(`\n📊 总体统计:`);
  console.log(`   启动+握手:     ${stats.startup}ms`);
  console.log(`   工具列表:      ${stats.listTools}ms`);
  console.log(`   首次执行:      ${stats.firstExecution}ms`);

  if (stats.secondExecution !== undefined) {
    console.log(`   二次执行:      ${stats.secondExecution}ms`);
    console.log(
      `   性能提升:      ${((1 - stats.secondExecution / stats.firstExecution) * 100).toFixed(1)}%`,
    );
  }

  console.log(`   关闭耗时:      ${stats.shutdown}ms`);
  console.log(`   ${'─'.repeat(40)}`);
  console.log(`   总耗时:        ${stats.total}ms`);

  if (stats.toolCount !== undefined) {
    console.log(`\n🔧 工具信息:`);
    console.log(`   可用工具数:    ${stats.toolCount}个`);
  }

  printSeparator();
}

/**
 * 格式化工具列表
 */
export function formatToolsList(tools) {
  if (!tools || tools.length === 0) {
    return '无工具';
  }

  return tools
    .map((tool, index) => {
      const desc = tool.description
        ? ` - ${tool.description.substring(0, 50)}${tool.description.length > 50 ? '...' : ''}`
        : '';
      return `   ${index + 1}. ${tool.name}${desc}`;
    })
    .join('\n');
}

/**
 * 安全地等待进程退出
 */
export async function safeWaitForExit(process, timeoutMs = 5000) {
  return new Promise((resolve) => {
    const timeout = setTimeout(() => {
      logWithTimestamp('⚠️ ', '进程退出超时，强制终止');
      process.kill('SIGKILL');
      resolve();
    }, timeoutMs);

    process.on('exit', () => {
      clearTimeout(timeout);
      resolve();
    });
  });
}

/**
 * 处理错误并打印
 */
export function handleError(error, context) {
  console.error(`\n❌ ${context} 失败:`);
  console.error(`   错误类型: ${error.name}`);
  console.error(`   错误信息: ${error.message}`);

  if (error.stack) {
    console.error(`\n   堆栈跟踪:`);
    error.stack
      .split('\n')
      .slice(1, 4)
      .forEach((line) => {
        console.error(`   ${line.trim()}`);
      });
  }

  printSeparator();
}

/**
 * 等待指定时间
 */
export function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * 验证环境变量
 */
export function validateEnvVars(requiredVars) {
  const missing = [];

  for (const varName of requiredVars) {
    if (!process.env[varName]) {
      missing.push(varName);
    }
  }

  if (missing.length > 0) {
    console.error(`\n❌ 缺少必需的环境变量:`);
    missing.forEach((varName) => {
      console.error(`   - ${varName}`);
    });
    console.error(`\n请在 .env 文件中配置或通过环境变量传递。`);
    console.error(`参考 .env.example 文件。\n`);
    return false;
  }

  return true;
}

/**
 * 格式化字节大小
 */
export function formatBytes(bytes) {
  if (bytes === 0) return '0 Bytes';

  const k = 1024;
  const sizes = ['Bytes', 'KB', 'MB', 'GB'];
  const i = Math.floor(Math.log(bytes) / Math.log(k));

  return Math.round((bytes / Math.pow(k, i)) * 100) / 100 + ' ' + sizes[i];
}

/**
 * 获取进程内存使用情况
 */
export function getMemoryUsage() {
  const usage = process.memoryUsage();
  return {
    rss: formatBytes(usage.rss),
    heapTotal: formatBytes(usage.heapTotal),
    heapUsed: formatBytes(usage.heapUsed),
    external: formatBytes(usage.external),
  };
}
