#!/usr/bin/env node

/**
 * Run All MCP Performance Tests
 * 运行所有MCP服务器的性能测试
 */

import { spawn } from 'child_process';
import { fileURLToPath } from 'url';
import { dirname, join } from 'path';

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

function runTest(scriptName) {
  return new Promise((resolve, reject) => {
    console.log(`\n${'='.repeat(70)}`);
    console.log(`开始运行: ${scriptName}`);
    console.log('='.repeat(70));

    const testProcess = spawn('node', [join(__dirname, scriptName)], {
      stdio: 'inherit',
      env: process.env,
    });

    testProcess.on('exit', (code) => {
      if (code === 0) {
        console.log(`\n✅ ${scriptName} 完成`);
        resolve();
      } else {
        console.log(`\n❌ ${scriptName} 失败 (退出码: ${code})`);
        reject(new Error(`${scriptName} failed with code ${code}`));
      }
    });

    testProcess.on('error', (error) => {
      console.error(`\n❌ ${scriptName} 启动失败:`, error);
      reject(error);
    });
  });
}

async function runAllTests() {
  console.log('\n');
  console.log(
    '╔═══════════════════════════════════════════════════════════════════╗',
  );
  console.log(
    '║                                                                   ║',
  );
  console.log(
    '║           MCP Server Performance Test Suite                       ║',
  );
  console.log(
    '║           MCP 服务器性能测试套件                                  ║',
  );
  console.log(
    '║                                                                   ║',
  );
  console.log(
    '╚═══════════════════════════════════════════════════════════════════╝',
  );
  console.log();

  const tests = [
    { name: 'test-github.js', description: 'GitHub MCP Server' },
    { name: 'test-playwright.js', description: 'Playwright MCP Server' },
    { name: 'test-huggingface.js', description: 'Huggingface MCP Server' },
    { name: 'test-pydantic.js', description: 'Pydantic MCP Run Python' },
    { name: 'test-fetcher.js', description: 'Fetcher MCP Server' },
    { name: 'test-docker.js', description: 'Docker MCP Server' },
  ];

  const results = [];
  const startTime = Date.now();

  for (let i = 0; i < tests.length; i++) {
    const test = tests[i];
    console.log(`\n[${i + 1}/${tests.length}] 测试 ${test.description}...`);

    try {
      await runTest(test.name);
      results.push({ name: test.description, success: true });
    } catch (error) {
      results.push({ name: test.description, success: false, error });
      console.error(`⚠️  跳过后续测试，因为 ${test.description} 失败`);
      // 继续执行其他测试
    }

    // 在测试之间添加短暂延迟
    if (i < tests.length - 1) {
      await new Promise((resolve) => setTimeout(resolve, 2000));
    }
  }

  const totalTime = Date.now() - startTime;

  // 打印最终摘要
  console.log('\n\n');
  console.log(
    '╔═══════════════════════════════════════════════════════════════════╗',
  );
  console.log(
    '║                                                                   ║',
  );
  console.log(
    '║                      测试完成摘要                                 ║',
  );
  console.log(
    '║                                                                   ║',
  );
  console.log(
    '╚═══════════════════════════════════════════════════════════════════╝',
  );
  console.log();

  results.forEach((result, index) => {
    const status = result.success ? '✅ 通过' : '❌ 失败';
    console.log(`${index + 1}. ${result.name.padEnd(30)} ${status}`);
  });

  console.log();
  console.log('─'.repeat(70));

  const passed = results.filter((r) => r.success).length;
  const failed = results.filter((r) => !r.success).length;

  console.log(`总测试数: ${results.length}`);
  console.log(`通过: ${passed}`);
  console.log(`失败: ${failed}`);
  console.log(`总耗时: ${(totalTime / 1000).toFixed(2)}秒`);
  console.log('─'.repeat(70));
  console.log();

  if (failed > 0) {
    console.log('❌ 部分测试失败\n');
    process.exit(1);
  } else {
    console.log('✅ 所有测试通过!\n');
    process.exit(0);
  }
}

// 捕获未处理的异常
process.on('unhandledRejection', (error) => {
  console.error('\n❌ 未处理的Promise拒绝:', error);
  process.exit(1);
});

process.on('uncaughtException', (error) => {
  console.error('\n❌ 未捕获的异常:', error);
  process.exit(1);
});

// 运行所有测试
runAllTests().catch((error) => {
  console.error('\n❌ 测试套件执行失败:', error);
  process.exit(1);
});
