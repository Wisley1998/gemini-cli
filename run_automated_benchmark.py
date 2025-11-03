#!/usr/bin/env python3
"""
自动化 Gemini CLI 性能测试脚本

该脚本会:
1. 从 deepresearch-bench-prompts 和 swe-bench-prompts 目录读取所有 prompt 文件
2. 对每个 prompt 启动 gemini --yolo
3. 自动输入 prompt 并等待完成(超时4分钟)
4. 使用 Ctrl+C 两次触发性能统计并退出
5. 提取 Performance 部分并保存到对应的结果目录:
   - DeepResearch prompts -> results/deep_research/
   - SWE-bench prompts -> results/code/
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

# 配置
BASE_DIR = Path("/Users/suiyifan/Desktop/multi-agnets/gemini-cli")
DEEPRESEARCH_PROMPTS_DIR = BASE_DIR / "deepresearch-bench-prompts"
SWE_BENCH_PROMPTS_DIR = BASE_DIR / "swe-bench-prompts"
RESULTS_BASE_DIR = BASE_DIR / "results"
DEEP_RESEARCH_RESULTS_DIR = RESULTS_BASE_DIR / "deep_research"
CODE_RESULTS_DIR = RESULTS_BASE_DIR / "code"

TIMEOUT_SECONDS = 300  # 8 分钟
IDLE_THRESHOLD = 15  # 15秒无输出认为完成

def get_prompt_files():
    """获取所有 prompt 文件并排序，返回 (文件路径, 类型) 列表"""
    prompt_files = []
    
    # DeepResearch prompts
    if DEEPRESEARCH_PROMPTS_DIR.exists():
        for f in sorted(DEEPRESEARCH_PROMPTS_DIR.glob("prompt_*.txt")):
            prompt_files.append((f, "deepresearch"))
    
    # SWE-bench prompts
    if SWE_BENCH_PROMPTS_DIR.exists():
        for f in sorted(SWE_BENCH_PROMPTS_DIR.glob("prompt_*.txt")):
            prompt_files.append((f, "swebench"))
    
    return prompt_files

def read_prompt(file_path):
    """读取 prompt 文件内容"""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    return content

def clean_ansi_codes(text):
    """清除ANSI转义码,保留可读文本"""
    import re
    
    # 最简单有效的方式: 只移除ESC开头的序列
    # ESC [ ... m (颜色/样式)
    text = re.sub(r'\x1b\[[0-9;]*m', '', text)
    
    # ESC [ ... 字母 (光标移动等)
    text = re.sub(r'\x1b\[[0-9;]*[A-HJKSTfhlu]', '', text)
    
    # ESC ] ... BEL/ESC\ (标题等)  
    text = re.sub(r'\x1b\][^\x07\x1b]*(\x07|\x1b\\)', '', text)
    
    # ESC [ ? ... h/l (模式设置)
    text = re.sub(r'\x1b\[\?[0-9;]*[hl]', '', text)
    
    # 其他ESC序列
    text = re.sub(r'\x1b[=>]', '', text)
    text = re.sub(r'\x1b\([0-9A-B]', '', text)
    
    # 回车符
    text = text.replace('\r', '')
    
    # 移除连续空行
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    return text

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

def run_gemini_with_prompt(prompt_file, prompt_content):
    """运行 gemini CLI 并执行指定的 prompt"""
    print(f"\n{'='*80}")
    print(f"正在测试: {prompt_file.name}")
    print(f"{'='*80}\n")
    
    output_buffer = []
    
    try:
        # 使用 --prompt-interactive 参数直接传入并执行 prompt
        # 转义双引号和美元符号以避免命令行问题
        escaped_prompt = prompt_content.replace('"', '\\"').replace('$', '\\$')
        
        # 禁用 IDE 集成以避免 workspace 检查错误
        # 使用 bash -c 来设置环境变量
        cmd = f'bash -c "gemini --prompt-interactive \\"{escaped_prompt}\\" --yolo"'
        
        print(f"启动命令: bash -c \"GEMINI_CLI_IDE_INTEGRATION=disabled gemini --prompt-interactive ...\" --yolo")
        child = pexpect.spawn(cmd, encoding='utf-8', timeout=TIMEOUT_SECONDS)
        
        # 捕获输出到 buffer
        class OutputCapture:
            def __init__(self, buffer_list):
                self.buffer = buffer_list
            
            def write(self, data):
                self.buffer.append(data)
                sys.stdout.write(data)
            
            def flush(self):
                sys.stdout.flush()
        
        child.logfile_read = OutputCapture(output_buffer)
        
        # 等待任务完成
        print(f"等待处理完成 (超时: {TIMEOUT_SECONDS}秒)...")
        start_time = time.time()
        idle_start = time.time()
        
        while True:
            try:
                child.expect('.+', timeout=0.5)
                idle_start = time.time()
                
                elapsed = time.time() - start_time
                if elapsed > TIMEOUT_SECONDS:
                    print(f"\n达到超时时间 ({TIMEOUT_SECONDS}秒)")
                    break
                    
            except pexpect.TIMEOUT:
                idle_time = time.time() - idle_start
                if idle_time > IDLE_THRESHOLD:
                    print(f"\n检测到空闲 {idle_time:.1f}秒,认为任务完成")
                    break
                    
            except pexpect.EOF:
                print(f"\n进程已结束")
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
            pass
        
        # 等待进程结束
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

def save_performance_result(prompt_file, prompt_type, cleaned_output):
    """只保存性能摘要到对应的结果目录"""
    # 获取prompt文件名(不含扩展名)
    prompt_name = prompt_file.stem  # 例如: prompt_001_1
    
    # 根据类型确定输出目录
    if prompt_type == "deepresearch":
        output_dir = DEEP_RESEARCH_RESULTS_DIR
    else:  # swebench
        output_dir = CODE_RESULTS_DIR
    
    # 确保输出目录存在
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 提取并保存性能摘要
    performance_summary = extract_performance_summary(cleaned_output)
    summary_output_file = output_dir / f"{prompt_name}_summary.txt"
    
    with open(summary_output_file, 'w', encoding='utf-8') as f:
        f.write(f"Prompt 文件: {prompt_file.name}\n")
        f.write(f"Prompt 类型: {prompt_type}\n")
        f.write(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"{'='*80}\n\n")
        
        if performance_summary:
            f.write(performance_summary)
        else:
            f.write("未能提取性能统计数据\n")
    
    print(f"  ✓ 性能摘要: {summary_output_file.name}")
    
    return summary_output_file

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description='Gemini CLI 自动化性能测试',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 测试所有类型
  python3 run_automated_benchmark.py --type all
  
  # 只测试 DeepResearch
  python3 run_automated_benchmark.py --type deepresearch
  
  # 只测试 SWE-bench
  python3 run_automated_benchmark.py --type swebench
  
  # 测试前 5 个 DeepResearch prompts
  python3 run_automated_benchmark.py --type deepresearch --limit 5
  
  # 测试第 10 到 20 个 prompts
  python3 run_automated_benchmark.py --type deepresearch --range 10-20
  
  # 测试第 15 到 25 个 prompts
  python3 run_automated_benchmark.py --range 15-25
        """
    )
    
    parser.add_argument(
        '--type',
        type=str,
        default='all',
        choices=['all', 'deepresearch', 'swebench'],
        help='测试类型: all(全部), deepresearch(深度研究), swebench(代码修复) [默认: all]'
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
        help='指定执行的 prompt 范围 (例如: 10-20 表示执行第10到第20个) [优先于 --limit]'
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
            
            if start_idx < 1:
                print(f"错误: 起始索引必须 >= 1")
                return 1
            
            if end_idx < start_idx:
                print(f"错误: 结束索引必须 >= 起始索引")
                return 1
            
            print(f"将执行第 {start_idx} 到第 {end_idx} 个 prompts")
        except ValueError:
            print(f"错误: --range 参数必须是数字 (例如: 10-20)")
            return 1
    
    print(f"Gemini CLI 自动化性能测试")
    print(f"{'='*80}")
    print(f"测试类型: {args.type}")
    print(f"DeepResearch Prompts: {DEEPRESEARCH_PROMPTS_DIR}")
    print(f"SWE-bench Prompts: {SWE_BENCH_PROMPTS_DIR}")
    print(f"结果目录: {RESULTS_BASE_DIR}")
    print(f"  - DeepResearch: {DEEP_RESEARCH_RESULTS_DIR}")
    print(f"  - Code (SWE-bench): {CODE_RESULTS_DIR}")
    print(f"超时时间: {TIMEOUT_SECONDS}秒")
    if args.range:
        print(f"执行范围: 第 {start_idx} 到第 {end_idx} 个")
    elif args.limit:
        print(f"限制数量: {args.limit}")
    print(f"{'='*80}\n")
    
    # 获取所有 prompt 文件
    all_prompt_files = get_prompt_files()
    
    # 根据类型过滤
    if args.type == 'deepresearch':
        prompt_files = [(f, t) for f, t in all_prompt_files if t == 'deepresearch']
    elif args.type == 'swebench':
        prompt_files = [(f, t) for f, t in all_prompt_files if t == 'swebench']
    else:  # all
        prompt_files = all_prompt_files
    
    # 应用范围或数量限制
    if args.range and start_idx is not None and end_idx is not None:
        # 使用范围参数 (优先级更高)
        # 注意: 索引从1开始，所以需要转换为0-based
        total_available = len(prompt_files)
        
        if start_idx > total_available:
            print(f"错误: 起始索引 {start_idx} 超过了可用总数 {total_available}")
            return 1
        
        if end_idx > total_available:
            print(f"警告: 结束索引 {end_idx} 超过了总数 {total_available}，将使用 {total_available}")
            actual_end = total_available
        else:
            actual_end = end_idx
        
        prompt_files = prompt_files[start_idx-1:actual_end]
        print(f"已选择第 {start_idx} 到第 {actual_end} 个 prompts (共 {len(prompt_files)} 个)")
    elif args.limit and args.limit > 0:
        # 使用数量限制
        prompt_files = prompt_files[:args.limit]
    
    if not prompt_files:
        print(f"错误: 未找到任何 prompt 文件")
        return 1
    
    print(f"找到 {len(prompt_files)} 个 prompt 文件")
    deepresearch_count = sum(1 for _, t in prompt_files if t == "deepresearch")
    swebench_count = sum(1 for _, t in prompt_files if t == "swebench")
    print(f"  - DeepResearch: {deepresearch_count}")
    print(f"  - SWE-bench: {swebench_count}\n")
    
    # 确保结果目录存在
    DEEP_RESEARCH_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    CODE_RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    
    # 对每个 prompt 运行测试
    success_count = 0
    failed_count = 0
    
    for i, (prompt_file, prompt_type) in enumerate(prompt_files, 1):
        print(f"\n进度: {i}/{len(prompt_files)}")
        print(f"类型: {prompt_type}")
        
        try:
            # 读取 prompt
            prompt_content = read_prompt(prompt_file)
            
            # 运行 gemini
            output = run_gemini_with_prompt(prompt_file, prompt_content)
            
            if output:
                # 清理ANSI码
                cleaned_output = clean_ansi_codes(output)
                
                print(f"\n✓ 成功获取输出")
                print(f"  清理后: {len(cleaned_output)} 字符")
                
                # 保存到对应目录
                summary_file = save_performance_result(prompt_file, prompt_type, cleaned_output)
                
                success_count += 1
            else:
                print(f"\n✗ 未能获取输出")
                failed_count += 1
        
        except KeyboardInterrupt:
            print("\n\n测试被用户中断")
            break
        except Exception as e:
            print(f"\n✗ 测试失败: {e}")
            import traceback
            traceback.print_exc()
            failed_count += 1
    
    # 打印总结
    print(f"\n{'='*80}")
    print(f"测试完成!")
    print(f"{'='*80}")
    print(f"总计: {len(prompt_files)} 个测试")
    print(f"成功: {success_count}")
    print(f"失败: {failed_count}")
    print(f"\n结果目录: {RESULTS_BASE_DIR}")
    print(f"  - DeepResearch: {DEEP_RESEARCH_RESULTS_DIR}")
    print(f"  - Code (SWE-bench): {CODE_RESULTS_DIR}")
    print(f"{'='*80}\n")
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n程序被中断")
        sys.exit(1)
