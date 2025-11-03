#!/usr/bin/env python3
"""
单个 prompt 测试脚本 - 用于调试
"""

import time
import re
from pathlib import Path
import sys

try:
    import pexpect
except ImportError:
    print("需要安装 pexpect 库: pip install pexpect")
    sys.exit(1)

PROMPTS_DIR = Path("/Users/suiyifan/Desktop/multi-agnets/gemini-cli/deepresearch-bench-prompts")
TIMEOUT_SECONDS = 180

def extract_performance_summary(text):
    """提取性能统计部分 - 从 'Agent powering down' 或 'Interaction Summary' 开始到结束"""
    # 方法1: 查找 "Agent powering down" 开始
    match = re.search(r'Agent powering down.*?Goodbye!', text, re.DOTALL | re.IGNORECASE)
    if match:
        start_idx = match.start()
        # 从这里开始到文件末尾或下一个明显的分隔符
        remaining = text[start_idx:]
        # 查找结束的框线
        end_match = re.search(r'╰─+╯\s*$', remaining, re.MULTILINE)
        if end_match:
            return remaining[:end_match.end()].strip()
        return remaining.strip()
    
    # 方法2: 查找 "Interaction Summary"
    match = re.search(r'Interaction Summary', text, re.IGNORECASE)
    if match:
        start_idx = match.start()
        # 向前找开始的框线
        before = text[:start_idx]
        box_start = before.rfind('╭─')
        if box_start != -1:
            start_idx = box_start
        
        remaining = text[start_idx:]
        # 查找结束的框线
        end_match = re.search(r'╰─+╯', remaining)
        if end_match:
            return remaining[:end_match.end()].strip()
        return remaining.strip()
    
    # 方法3: 查找 "Performance"
    match = re.search(r'Performance\s*\n', text, re.IGNORECASE)
    if match:
        start_idx = max(0, match.start() - 500)  # 向前取500字符作为上下文
        remaining = text[start_idx:]
        # 查找结束
        end_match = re.search(r'╰─+╯', remaining)
        if end_match:
            return remaining[:end_match.end()].strip()
        return remaining[:5000].strip()  # 最多返回5000字符
    
    return None

# 用于捕获输出的类
class OutputCapture:
    def __init__(self):
        self.buffer = []
    
    def write(self, data):
        self.buffer.append(data)
        sys.stdout.write(data)  # 同时输出到屏幕
    
    def flush(self):
        sys.stdout.flush()
    
    def get_output(self):
        return ''.join(self.buffer)

def clean_ansi_codes(text):
    """清理ANSI转义码和控制字符,保留可读文本"""
    # 移除ANSI颜色和样式代码 (ESC[...m 格式)
    text = re.sub(r'\x1b\[[0-9;]*m', '', text)
    
    # 移除光标控制序列 (ESC[...A/B/C/D/G/H/J/K/S/T 等)
    text = re.sub(r'\x1b\[[0-9;]*[ABCDEFGHJKSTfhlu]', '', text)
    
    # 移除其他ESC序列
    text = re.sub(r'\x1b\[[\?]?[0-9;]*[a-zA-Z]', '', text)
    text = re.sub(r'\x1b\][0-9;]*;[^\x07]*\x07', '', text)
    text = re.sub(r'\x1b\][0-9;]*;[^\a]*\a', '', text)
    
    # 移除特殊字符序列
    text = re.sub(r'\x1b[\[\]()][0-9;]*[A-Za-z]', '', text)
    text = re.sub(r'\x1b[=>]', '', text)
    text = re.sub(r'\[\?[0-9]+[hl]', '', text)
    
    # 移除回车符但保留换行符
    text = text.replace('\r', '')
    
    # 移除连续的空行 (保留最多2个连续换行)
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text

def test_simple_prompt():
    """使用简单的问题测试"""
    print("开始测试 gemini --yolo")
    print("="*80)
    
    # 使用一个简单的测试问题
    test_prompt = "计算 123 + 456"
    
    try:
        # 使用 --prompt-interactive 参数直接传入并执行 prompt
        print("启动 gemini 并执行 prompt...")
        cmd = f'gemini --prompt-interactive "{test_prompt}" --yolo'
        child = pexpect.spawn(cmd, encoding='utf-8', timeout=180)
        
        # 创建输出捕获对象
        output_capture = OutputCapture()
        child.logfile_read = output_capture
        
        # 等待任务完成 (检测空闲)
        print("等待任务完成...")
        idle_start = time.time()
        max_idle = 15  # 15秒空闲认为完成
        
        while True:
            try:
                child.expect('.+', timeout=0.5)
                idle_start = time.time()
            except pexpect.TIMEOUT:
                idle_time = time.time() - idle_start
                if idle_time > max_idle:
                    print(f"\n检测到空闲 {idle_time:.1f}秒,认为任务完成")
                    break
            except pexpect.EOF:
                print("\n进程已结束")
                break
        
        # 发送两次 Ctrl+C 触发性能统计输出
        print("\n发送第一次 Ctrl+C...")
        child.sendintr()
        time.sleep(1)
        
        print("发送第二次 Ctrl+C...")
        child.sendintr()
        time.sleep(5)  # 等待更长时间让统计信息完全输出
        
        # 读取所有剩余输出
        print("读取所有输出...")
        try:
            for _ in range(50):  # 增加读取次数
                child.expect('.+', timeout=1)
        except pexpect.TIMEOUT:
            pass
        except pexpect.EOF:
            print("进程已结束")
        
        # 等待进程完全结束
        try:
            child.expect(pexpect.EOF, timeout=5)
        except:
            child.close(force=True)
        
        # 获取完整输出
        output = output_capture.get_output()
        
        # 清理ANSI代码
        print("\n清理ANSI转义码...")
        cleaned_output = clean_ansi_codes(output)
        
        print("\n" + "="*80)
        print("完整输出已保存")
        print("="*80)
        
        # 保存原始输出
        with open('test_output_raw.txt', 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"✓ 原始输出已保存到: test_output_raw.txt ({len(output)} 字符)")
        
        # 保存清理后的输出
        with open('test_output.txt', 'w', encoding='utf-8') as f:
            f.write(cleaned_output)
        print(f"✓ 清理后输出已保存到: test_output.txt ({len(cleaned_output)} 字符)")
        
        # 提取并保存性能摘要
        print("提取性能摘要...")
        performance_summary = extract_performance_summary(cleaned_output)
        if performance_summary:
            with open('test_output_summary.txt', 'w', encoding='utf-8') as f:
                f.write(performance_summary)
            print(f"✓ 性能摘要已保存到: test_output_summary.txt ({len(performance_summary)} 字符)")
        else:
            print(f"✗ 未能提取性能摘要")
        
        # 屏幕预览
        print("\n" + "="*80)
        print("性能摘要预览:")
        print("="*80)
        if performance_summary:
            # 只显示前1000字符
            preview = performance_summary[:1000]
            print(preview)
            if len(performance_summary) > 1000:
                print(f"\n... (还有 {len(performance_summary) - 1000} 字符)")
        else:
            print("未找到性能统计!")
            print("\n输出末尾500字符:")
            print(cleaned_output[-500:])
        
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    test_simple_prompt()
