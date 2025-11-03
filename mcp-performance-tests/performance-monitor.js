/**
 * PerformanceMonitor - 使用 Node.js perf_hooks 测量 MCP 内部阶段的时间
 */

import { performance, PerformanceObserver } from 'perf_hooks';

export class PerformanceMonitor {
  constructor() {
    this.measurements = new Map();
  }

  /**
   * 开始一个新的性能测量
   * @param {string} id - 唯一标识符
   */
  start(id) {
    this.measurements.set(id, {
      startTime: performance.now(),
      marks: new Map(),
    });
  }

  /**
   * 添加一个性能标记点
   * @param {string} id - 测量标识符
   * @param {string} markName - 标记名称
   */
  mark(id, markName) {
    const measurement = this.measurements.get(id);
    if (!measurement) {
      console.warn(`⚠️  未找到测量 ID: ${id}`);
      return;
    }
    measurement.marks.set(markName, performance.now());
  }

  /**
   * 结束测量并返回详细的时间分解
   * @param {string} id - 测量标识符
   * @returns {Object} 时间分解数据
   */
  end(id) {
    const measurement = this.measurements.get(id);
    if (!measurement) {
      console.warn(`⚠️  未找到测量 ID: ${id}`);
      return null;
    }

    const endTime = performance.now();
    const { startTime, marks } = measurement;

    // 计算各个阶段的时间
    const breakdown = {
      total: endTime - startTime,
      phases: {},
    };

    // 将 marks 转换为时间段
    const markEntries = Array.from(marks.entries());

    if (markEntries.length > 0) {
      // 计算每个阶段的持续时间
      for (let i = 0; i < markEntries.length; i++) {
        const [currentMark, currentTime] = markEntries[i];
        const prevTime = i === 0 ? startTime : markEntries[i - 1][1];

        // 阶段名称映射
        const phaseNames = {
          'request-ready': 'requestPreparation',
          'call-started': 'transportSend',
          'response-received': 'serverExecution',
          'response-parsed': 'transportReceive',
        };

        const phaseName = phaseNames[currentMark] || currentMark;
        breakdown.phases[phaseName] = currentTime - prevTime;
      }

      // 计算最后一个阶段 (response parsing)
      const lastMarkTime = markEntries[markEntries.length - 1][1];
      breakdown.phases.responseParsing = endTime - lastMarkTime;
    }

    // 清理
    this.measurements.delete(id);

    return breakdown;
  }

  /**
   * 获取所有测量结果
   */
  getAll() {
    return Array.from(this.measurements.entries());
  }

  /**
   * 清除所有测量数据
   */
  clear() {
    this.measurements.clear();
  }
}

/**
 * 格式化时间分解数据为可读的字符串
 * @param {Object} breakdown - 时间分解数据
 * @returns {string} 格式化的字符串
 */
export function formatBreakdown(breakdown) {
  if (!breakdown) return '无数据';

  const { total, phases } = breakdown;

  let output = '\n⏱️  性能详情:\n';

  // 定义阶段的显示顺序和名称
  const phaseOrder = [
    { key: 'requestPreparation', label: '请求准备' },
    { key: 'transportSend', label: '传输发送' },
    { key: 'serverExecution', label: '服务器执行' },
    { key: 'transportReceive', label: '传输接收' },
    { key: 'responseParsing', label: '响应解析' },
  ];

  phaseOrder.forEach((phase, index) => {
    const time = phases[phase.key] || 0;
    const percentage = total > 0 ? ((time / total) * 100).toFixed(1) : '0.0';
    const isLast = index === phaseOrder.length - 1;
    const prefix = isLast ? '└─' : '├─';

    // 高亮最耗时的阶段
    const highlight = time > total * 0.5 ? ' ← 主要耗时' : '';

    output += `${prefix} ${phase.label}: ${time.toFixed(1)}ms (${percentage}%)${highlight}\n`;
  });

  output += `总耗时: ${total.toFixed(1)}ms`;

  return output;
}
