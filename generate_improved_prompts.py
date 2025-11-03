#!/usr/bin/env python3
"""
生成改进的 SWE-bench prompts，明确指定工作目录以避免 workspace 错误

该脚本读取原始的 swe-bench-prompts/*.txt 文件，
并生成包含完整绝对路径的改进版本到 swe-bench-prompts-improved/ 目录
"""

import re
from pathlib import Path

# 配置
BASE_DIR = Path("/Users/suiyifan/Desktop/multi-agnets/gemini-cli")
INPUT_DIR = BASE_DIR / "swe-bench-prompts"
OUTPUT_DIR = BASE_DIR / "swe-bench-prompts-improved"
TEMPLATE_FILE = BASE_DIR / "prompts" / "swe-bench-improved-template.txt"
WORKSPACE_DIR = BASE_DIR / "swe-bench-workspace"

def parse_original_prompt(content):
    """解析原始 prompt 提取关键信息"""
    info = {}
    
    # 提取任务 ID (中英文)
    match = re.search(r'(?:Task ID|任务 ID):\s*(\S+)', content, re.IGNORECASE)
    if match:
        info['task_id'] = match.group(1).rstrip('.')
    else:
        info['task_id'] = 'unknown'
    
    # 提取仓库 (从 issue URL 或直接指定)
    match = re.search(r'(?:repository|仓库)\s+(\S+/\S+)', content, re.IGNORECASE)
    if match:
        info['repo'] = match.group(1).rstrip(':').rstrip('.')
        info['repo_name'] = info['repo'].split('/')[-1]
    else:
        # 尝试从 Issue URL 提取
        match = re.search(r'github\.com/(\S+/\S+)/issues', content)
        if match:
            info['repo'] = match.group(1)
            info['repo_name'] = info['repo'].split('/')[-1]
        else:
            info['repo'] = 'unknown/unknown'
            info['repo_name'] = 'unknown'
    
    # 提取 Issue URL 和编号
    match = re.search(r'(https://github\.com/\S+/\S+/issues/(\d+))', content)
    if match:
        info['issue_url'] = match.group(1)
        info['issue_number'] = match.group(2)
    else:
        # 从任务 ID 中提取 Issue 编号
        match = re.search(r'-(\d+)(?:\.|$)', info['task_id'])
        if match:
            info['issue_number'] = match.group(1)
            if info['repo'] != 'unknown/unknown':
                info['issue_url'] = f"https://github.com/{info['repo']}/issues/{info['issue_number']}"
            else:
                info['issue_url'] = "https://github.com"
        else:
            info['issue_number'] = '0000'
            info['issue_url'] = "https://github.com"
    
    # 提取基础提交
    match = re.search(r'(?:at commit|基于提交)\s+([a-f0-9]{7,40})', content, re.IGNORECASE)
    if match:
        info['base_commit'] = match.group(1).rstrip('.')
    else:
        info['base_commit'] = 'main'
    
    # 提取测试文件
    match = re.search(r'(?:Make sure these tests pass|必须通过的测试):\s*(.+?)(?:\.\s*Task|\.\s*Start|Task|$)', content, re.IGNORECASE | re.DOTALL)
    if match:
        test_text = match.group(1).strip()
        # 清理多余的文本
        test_text = test_text.split('等共')[0]  # 移除 "等共16个" 这样的文本
        test_text = test_text.strip().rstrip('.')
        info['test_files'] = test_text
    else:
        info['test_files'] = 'tests/'
    
    return info

def generate_improved_prompt(info):
    """根据模板生成改进的 prompt"""
    
    # 读取模板
    with open(TEMPLATE_FILE, 'r', encoding='utf-8') as f:
        template = f.read()
    
    # 替换占位符
    improved = template.format(
        task_id=info['task_id'],
        repo=info['repo'],
        repo_name=info['repo_name'],
        issue_number=info['issue_number'],
        issue_url=info['issue_url'],
        base_commit=info['base_commit'],
        test_files=info['test_files']
    )
    
    # 移除所有空行，只保留单个换行符
    lines = improved.split('\n')
    non_empty_lines = [line for line in lines if line.strip()]
    improved = '\n'.join(non_empty_lines)
    
    return improved

def process_all_prompts():
    """处理所有原始 prompts"""
    
    # 确保输出目录存在
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # 获取所有原始 prompt 文件
    prompt_files = sorted(INPUT_DIR.glob("prompt_*.txt"))
    
    if not prompt_files:
        print(f"❌ 未找到 prompt 文件在 {INPUT_DIR}")
        return
    
    print(f"找到 {len(prompt_files)} 个原始 prompt 文件")
    print(f"输出目录: {OUTPUT_DIR}\n")
    
    success_count = 0
    failed_count = 0
    
    for prompt_file in prompt_files:
        try:
            # 读取原始 prompt
            with open(prompt_file, 'r', encoding='utf-8') as f:
                original_content = f.read()
            
            # 解析信息
            info = parse_original_prompt(original_content)
            
            # 生成改进版本
            improved_content = generate_improved_prompt(info)
            
            # 保存到输出目录
            output_file = OUTPUT_DIR / prompt_file.name
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(improved_content)
            
            print(f"✓ {prompt_file.name}")
            print(f"  任务: {info['task_id']}")
            print(f"  仓库: {info['repo']}")
            print(f"  Issue: #{info['issue_number']}")
            print()
            
            success_count += 1
            
        except Exception as e:
            print(f"✗ {prompt_file.name}: {e}\n")
            failed_count += 1
    
    print(f"\n{'='*60}")
    print(f"处理完成!")
    print(f"{'='*60}")
    print(f"成功: {success_count}")
    print(f"失败: {failed_count}")
    print(f"输出目录: {OUTPUT_DIR}")
    print(f"{'='*60}\n")

def main():
    """主函数"""
    print("=" * 60)
    print("SWE-bench Improved Prompt Generator")
    print("=" * 60)
    print(f"输入目录: {INPUT_DIR}")
    print(f"输出目录: {OUTPUT_DIR}")
    print(f"模板文件: {TEMPLATE_FILE}")
    print(f"工作空间: {WORKSPACE_DIR}")
    print("=" * 60)
    print()
    
    if not TEMPLATE_FILE.exists():
        print(f"❌ 模板文件不存在: {TEMPLATE_FILE}")
        return 1
    
    if not INPUT_DIR.exists():
        print(f"❌ 输入目录不存在: {INPUT_DIR}")
        return 1
    
    process_all_prompts()
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
