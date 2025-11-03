#!/usr/bin/env python3
"""
使用改进的 prompts 运行自动化 Gemini CLI 性能测试

该脚本使用 swe-bench-prompts-improved 目录中明确指定了工作目录的 prompts，
解决了原始 prompts 导致的 workspace 问题。
"""

import time
import re
from pathlib import Path
from datetime import datetime
import sys

try:
    import pexpect
except ImportError:
    print("需要安装 pexpect 库:")
    print("pip install pexpect")
    sys.exit(1)

# 配置 - 使用改进的 prompts 目录
BASE_DIR = Path("/Users/suiyifan/Desktop/multi-agnets/gemini-cli")
IMPROVED_PROMPTS_DIR = BASE_DIR / "swe-bench-prompts-improved"
RESULTS_DIR = BASE_DIR / "results" / "code-improved"

TIMEOUT_SECONDS = 60  # 1 分钟 (用于快速测试超时处理)
RETRY_DELAY = 120  # API 错误后重试前等待时间（秒）
MAX_RETRIES = 2  # 最大重试次数
INTER_TEST_DELAY = 15  # 测试之间的延迟（秒，避免 API 速率限制）
IDLE_THRESHOLD = 15  # 15秒无输出认为完成

def get_prompt_files():
    """获取所有改进的 prompt 文件并排序"""
    if not IMPROVED_PROMPTS_DIR.exists():
        print(f"❌ 错误: 改进的 prompts 目录不存在: {IMPROVED_PROMPTS_DIR}")
        print(f"请先运行: python3 generate_improved_prompts.py")
        return []
    
    prompt_files = sorted(IMPROVED_PROMPTS_DIR.glob("prompt_*.txt"))
    return prompt_files

def read_prompt(file_path):
    """读取 prompt 文件内容"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return content

def clean_ansi_codes(text):
    """清除ANSI转义码,保留可读文本"""
    # 移除ESC序列
    text = re.sub(r'\x1b\[[0-9;]*m', '', text)
    text = re.sub(r'\x1b\[[0-9;]*[A-HJKSTfhlu]', '', text)
    text = re.sub(r'\x1b\][^\x07\x1b]*(\x07|\x1b\\)', '', text)
    text = re.sub(r'\x1b\[\?[0-9;]*[hl]', '', text)
    text = re.sub(r'\x1b[=>]', '', text)
    text = re.sub(r'\x1b\([0-9A-B]', '', text)
    text = text.replace('\r', '')
    text = re.sub(r'\n{3,}', '\n\n', text)
    return text

def extract_performance_summary(output: str) -> str:
    """从输出中提取性能统计摘要
    
    提取策略：
    1. 优先查找标准性能统计（Agent powering down 部分）
    2. 如果没有，查找 MCP Debug 性能数据
    3. 如果有 API 错误，记录错误信息
    """
    summary_parts = []
    
    # 1. 查找 API 错误
    error_patterns = [
        r'Error when talking to Gemini API.*?\.json',
        r'got status: INTERNAL.*?INTERNAL',
        r'429.*?Too Many Requests',
        r'quota.*?exceeded',
    ]
    for pattern in error_patterns:
        matches = re.findall(pattern, output, re.DOTALL | re.IGNORECASE)
        if matches:
            if not summary_parts:
                summary_parts.append("⚠️ API 错误:")
            for error in matches:
                summary_parts.append(f"  {error.strip()}")
    
    # 2. 查找 MCP Debug 性能数据
    mcp_pattern = r'\[MCP Debug\] Parsed \d+ internal phases: \[(.*?)\]'
    mcp_matches = re.findall(mcp_pattern, output, re.DOTALL)
    if mcp_matches:
        if summary_parts:
            summary_parts.append("\n📊 MCP 性能数据:")
        else:
            summary_parts.append("📊 MCP 性能数据:")
        for match in mcp_matches:
            summary_parts.append(f"  [{match.strip()}]")
    
    # 3. 查找标准性能统计（Agent powering down 部分）
    perf_patterns = [
        r'Agent powering down.*?Goodbye!',
        r'Interaction Summary:.*?(?=\n\n|\Z)',
        r'Performance.*?(?=\n\n|\Z)',
        r'Statistics:.*?(?=\n\n|\Z)',
    ]
    
    for pattern in perf_patterns:
        match = re.search(pattern, output, re.DOTALL | re.IGNORECASE)
        if match:
            if summary_parts:
                summary_parts.append("\n✅ 标准性能统计:")
            summary_parts.append(match.group(0))
            break
    
    if summary_parts:
        return '\n'.join(summary_parts)
    
    return ""

def run_gemini_with_prompt(prompt_file, prompt_content):
    """运行 gemini CLI 并执行指定的 prompt"""
    print(f"\n{'='*80}")
    print(f"正在测试: {prompt_file.name}")
    print(f"{'='*80}\n")
    
    output_buffer = []
    
    try:
        # 使用 --prompt (headless 模式) 而不是 --prompt-interactive
        # headless 模式会在任务完成后自动退出并输出性能统计
        escaped_prompt = prompt_content.replace('"', '\\"').replace('$', '\\$').replace('`', '\\`')
        cmd = f'gemini --prompt "{escaped_prompt}" --yolo'
        
        print(f"启动命令: gemini --prompt \"...\" --yolo (headless 模式)")
        child = pexpect.spawn(cmd, encoding='utf-8', timeout=TIMEOUT_SECONDS)
        
        # 捕获输出
        class OutputCapture:
            def __init__(self, buffer_list):
                self.buffer = buffer_list
            
            def write(self, data):
                self.buffer.append(data)
                sys.stdout.write(data)
            
            def flush(self):
                sys.stdout.flush()
        
        child.logfile_read = OutputCapture(output_buffer)
        
        # 等待任务完成 (headless 模式会自动退出)
        print(f"等待处理完成 (超时: {TIMEOUT_SECONDS}秒)...")
        
        try:
            # 等待进程自然结束 (headless 模式会在任务完成后自动退出并输出性能统计)
            child.expect(pexpect.EOF, timeout=TIMEOUT_SECONDS)
            print(f"\n✓ 任务已完成，进程正常退出")
        except pexpect.TIMEOUT:
            print(f"\n⚠ 达到超时时间 ({TIMEOUT_SECONDS}秒)，强制退出并生成性能报告")
            
            try:
                # 发送 /quit 命令来触发性能统计并退出
                print("发送 /quit 命令...")
                child.sendline('/quit')
                time.sleep(2)
                
                # 读取退出后的输出（包括性能统计）
                print("读取性能统计信息...")
                try:
                    for _ in range(100):
                        child.expect('.+', timeout=0.5)
                except (pexpect.TIMEOUT, pexpect.EOF):
                    pass
                
                # 等待进程结束
                try:
                    child.expect(pexpect.EOF, timeout=5)
                except:
                    # 如果 /quit 不起作用，尝试发送两次 Ctrl+C
                    print("尝试使用 Ctrl+C...")
                    try:
                        child.sendintr()
                        time.sleep(1)
                        child.sendintr()
                        time.sleep(2)
                        
                        # 读取中断后的输出
                        for _ in range(50):
                            child.expect('.+', timeout=0.5)
                    except:
                        pass
                        
            except Exception as e:
                print(f"⚠ 触发退出失败: {e}")
                print("继续处理已捕获的输出...")
        
        # 确保进程结束
        try:
            child.expect(pexpect.EOF, timeout=5)
        except:
            pass
        
        try:
            child.close(force=True)
        except:
            pass
        
        # 合并输出并清理ANSI代码
        full_output = ''.join(output_buffer)
        cleaned_output = clean_ansi_codes(full_output)
        return cleaned_output
    
    except Exception as e:
        print(f"错误: {e}")
        import traceback
        traceback.print_exc()
        return None

def save_performance_result(prompt_file, cleaned_output):
    """只保存性能摘要（不保存完整输出）"""
    prompt_name = prompt_file.stem
    
    # 确保输出目录存在
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 提取并保存性能摘要
    performance_summary = extract_performance_summary(cleaned_output)
    summary_output_file = RESULTS_DIR / f"{prompt_name}_summary.txt"
    
    # 调试：如果没有提取到性能统计，保存最后部分用于检查
    if not performance_summary:
        print(f"  ⚠ 未能提取性能统计数据，保存输出的最后 5000 字符用于调试")
        debug_output = cleaned_output[-5000:] if len(cleaned_output) > 5000 else cleaned_output
        debug_file = RESULTS_DIR / f"{prompt_name}_debug.txt"
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(f"调试信息 - 输出总长度: {len(cleaned_output)} 字符\n")
            f.write(f"{'='*80}\n\n")
            f.write("最后 5000 字符:\n")
            f.write(debug_output)
    
    with open(summary_output_file, 'w', encoding='utf-8') as f:
        f.write(f"Prompt 文件: {prompt_file.name}\n")
        f.write(f"Prompt 类型: swebench\n")
        f.write(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"{'='*80}\n\n")
        
        if performance_summary:
            f.write(performance_summary)
        else:
            f.write("未能提取性能统计数据\n")
            f.write(f"输出总长度: {len(cleaned_output)} 字符\n")
            f.write(f"请查看 {prompt_name}_debug.txt 了解详情\n")
    
    print(f"  ✓ 性能摘要: {summary_output_file.name}")
    
    return summary_output_file

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Gemini CLI 自动化性能测试 (使用改进的 prompts)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 测试前 5 个 prompts
  python3 run_automated_benchmark_improved.py --limit 5
  
  # 测试第 10 到 20 个 prompts
  python3 run_automated_benchmark_improved.py --range 10-20
  
  # 测试单个 prompt
  python3 run_automated_benchmark_improved.py --range 5-5
        """
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        default=None,
        help='限制测试的 prompt 数量 (默认: 全部)'
    )
    
    parser.add_argument(
        '--range',
        type=str,
        default=None,
        metavar='START-END',
        help='指定执行的 prompt 范围 (例如: 10-20) [优先于 --limit]'
    )
    
    args = parser.parse_args()
    
    # 解析范围参数
    start_idx = None
    end_idx = None
    if args.range:
        try:
            range_parts = args.range.split('-')
            if len(range_parts) != 2:
                print(f"错误: --range 格式不正确，应为 'START-END' (例如: 10-20)")
                return 1
            
            start_idx = int(range_parts[0].strip())
            end_idx = int(range_parts[1].strip())
            
            if start_idx < 1 or end_idx < start_idx:
                print(f"错误: 无效的范围")
                return 1
            
            print(f"将执行第 {start_idx} 到第 {end_idx} 个 prompts")
        except ValueError:
            print(f"错误: --range 参数必须是数字")
            return 1
    
    print(f"Gemini CLI 自动化性能测试 (改进版)")
    print(f"{'='*80}")
    print(f"Prompts 目录: {IMPROVED_PROMPTS_DIR}")
    print(f"结果目录: {RESULTS_DIR}")
    print(f"超时时间: {TIMEOUT_SECONDS}秒")
    if args.range:
        print(f"执行范围: 第 {start_idx} 到第 {end_idx} 个")
    elif args.limit:
        print(f"限制数量: {args.limit}")
    print(f"{'='*80}\n")
    
    # 获取所有 prompt 文件
    all_prompt_files = get_prompt_files()
    
    if not all_prompt_files:
        return 1
    
    # 应用范围或数量限制
    if args.range and start_idx is not None and end_idx is not None:
        total_available = len(all_prompt_files)
        
        if start_idx > total_available:
            print(f"错误: 起始索引 {start_idx} 超过了可用总数 {total_available}")
            return 1
        
        actual_end = min(end_idx, total_available)
        prompt_files = all_prompt_files[start_idx-1:actual_end]
        print(f"已选择第 {start_idx} 到第 {actual_end} 个 prompts (共 {len(prompt_files)} 个)")
    elif args.limit and args.limit > 0:
        prompt_files = all_prompt_files[:args.limit]
    else:
        prompt_files = all_prompt_files
    
    print(f"找到 {len(prompt_files)} 个 prompt 文件\n")
    
    # 确保结果目录存在
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 对每个 prompt 运行测试
    success_count = 0
    failed_count = 0
    
    for i, prompt_file in enumerate(prompt_files, 1):
        print(f"\n进度: {i}/{len(prompt_files)}")
        
        # 测试之间延迟，避免 API 速率限制
        if i > 1:
            print(f"⏱️  等待 {INTER_TEST_DELAY} 秒后继续下一个测试...")
            time.sleep(INTER_TEST_DELAY)
        
        # 重试逻辑
        retry_count = 0
        success = False
        
        while retry_count <= MAX_RETRIES and not success:
            try:
                if retry_count > 0:
                    print(f"🔄 重试 {retry_count}/{MAX_RETRIES}...")
                
                # 读取 prompt
                prompt_content = read_prompt(prompt_file)
                
                # 运行 gemini
                output = run_gemini_with_prompt(prompt_file, prompt_content)
                
                if output:
                    cleaned_output = clean_ansi_codes(output)
                    
                    # 检查是否有 API 错误
                    if 'Error when talking to Gemini API' in cleaned_output or 'got status: INTERNAL' in cleaned_output:
                        print(f"\n⚠️  检测到 API 错误")
                        if retry_count < MAX_RETRIES:
                            print(f"⏱️  等待 {RETRY_DELAY} 秒后重试...")
                            time.sleep(RETRY_DELAY)
                            retry_count += 1
                            continue
                    
                    print(f"\n✓ 成功获取输出 ({len(cleaned_output)} 字符)")
                    
                    # 只保存性能摘要
                    save_performance_result(prompt_file, cleaned_output)
                    
                    success = True
                    success_count += 1
                else:
                    print(f"\n✗ 未能获取输出")
                    if retry_count < MAX_RETRIES:
                        print(f"⏱️  等待 {RETRY_DELAY} 秒后重试...")
                        time.sleep(RETRY_DELAY)
                        retry_count += 1
                    else:
                        failed_count += 1
                        break
            
            except KeyboardInterrupt:
                print("\n\n测试被用户中断")
                return 0
            except Exception as e:
                print(f"\n✗ 测试失败: {e}")
                import traceback
                traceback.print_exc()
                
                if retry_count < MAX_RETRIES:
                    print(f"⏱️  等待 {RETRY_DELAY} 秒后重试...")
                    time.sleep(RETRY_DELAY)
                    retry_count += 1
                else:
                    failed_count += 1
                    break
    
    # 打印总结
    print(f"\n{'='*80}")
    print(f"测试完成!")
    print(f"{'='*80}")
    print(f"总计: {len(prompt_files)} 个测试")
    print(f"成功: {success_count}")
    print(f"失败: {failed_count}")
    print(f"\n结果目录: {RESULTS_DIR}")
    print(f"{'='*80}\n")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n程序被中断")
        sys.exit(1)
