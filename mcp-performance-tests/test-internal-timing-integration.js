#!/usr/bin/env node

/**
 * 测试 MCP 内部时间统计功能
 *
 * 这个脚本测试 gemini-cli 中集成的 MCP 内部时间测量功能。
 * 它会调用一个 Playwright MCP 工具，然后检查 /stats 输出是否包含内部阶段。
 */

import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);
const projectRoot = join(__dirname, '..');

console.log('='.repeat(80));
console.log('🧪 测试 MCP 内部时间统计功能');
console.log('='.repeat(80) + '\n');

console.log('📝 测试场景：');
console.log('1. 启动 gemini-cli');
console.log('2. 调用 Playwright MCP 工具导航到网页');
console.log(
  '3. 查看 /stats 输出是否包含内部阶段（Browser Launch, Navigation 等）\n',
);

console.log('⚠️  注意：');
console.log('- 需要已经配置 Playwright MCP 服务器');
console.log('- 需要有效的 Gemini API 密钥');
console.log('- 需要已经 npm run build\n');

console.log('🚀 启动测试...\n');

// 构建 gemini-cli 的命令
const geminiCli = join(projectRoot, 'bundle', 'gemini.js');

// 测试命令序列
const commands = [
  'Navigate to https://example.com using Playwright',
  '/stats',
  '/exit',
];

console.log('📋 将执行以下命令：');
commands.forEach((cmd, i) => {
  console.log(`${i + 1}. ${cmd}`);
});
console.log('');

// 启动 gemini-cli
const gemini = spawn('node', [geminiCli], {
  cwd: projectRoot,
  env: {
    ...process.env,
    // 确保 DEBUG 日志被捕获
    DEBUG: 'pw:api,pw:browser',
  },
  stdio: ['pipe', 'pipe', 'pipe'],
});

let output = '';
let commandIndex = 0;

gemini.stdout.on('data', (data) => {
  const text = data.toString();
  output += text;
  process.stdout.write(text);

  // 等待提示符后发送下一个命令
  if (text.includes('>') && commandIndex < commands.length) {
    setTimeout(() => {
      const cmd = commands[commandIndex];
      console.log(`\n📤 发送命令: ${cmd}\n`);
      gemini.stdin.write(cmd + '\n');
      commandIndex++;
    }, 1000);
  }
});

gemini.stderr.on('data', (data) => {
  const text = data.toString();
  // DEBUG 日志会输出到 stderr
  if (text.includes('pw:')) {
    process.stderr.write(`[DEBUG] ${text}`);
  } else {
    process.stderr.write(text);
  }
});

gemini.on('close', (code) => {
  console.log('\n' + '='.repeat(80));
  console.log('📊 测试结果分析');
  console.log('='.repeat(80) + '\n');

  // 检查输出中是否包含内部阶段
  const hasInternalPhases =
    output.includes('Browser Launch') ||
    output.includes('Navigation') ||
    output.includes('DOMContentLoaded') ||
    output.includes('Page Load');

  if (hasInternalPhases) {
    console.log('✅ 成功：在 /stats 输出中发现了 MCP 内部阶段！');
    console.log('');

    // 提取并显示 MCP 相关的统计
    const lines = output.split('\n');
    const mcpLines = lines.filter(
      (line) =>
        line.includes('MCP Call') ||
        line.includes('Browser Launch') ||
        line.includes('Navigation') ||
        line.includes('DOMContentLoaded') ||
        line.includes('Page Load'),
    );

    if (mcpLines.length > 0) {
      console.log('📈 MCP 时间统计：');
      mcpLines.forEach((line) => console.log('  ' + line.trim()));
    }
  } else {
    console.log('❌ 失败：未在 /stats 输出中发现 MCP 内部阶段');
    console.log('');
    console.log('💡 可能的原因：');
    console.log('1. Playwright MCP 服务器未配置或未启动');
    console.log('2. DEBUG 日志未被正确捕获');
    console.log('3. 日志解析器未识别到关键事件');
  }

  console.log('');
  console.log('🏁 测试完成');
  process.exit(code);
});

// 处理错误
gemini.on('error', (err) => {
  console.error('❌ 启动 gemini-cli 失败:', err);
  process.exit(1);
});

// 超时保护（5 分钟）
setTimeout(
  () => {
    console.log('\n⏱️  测试超时，强制退出');
    gemini.kill();
    process.exit(1);
  },
  5 * 60 * 1000,
);
