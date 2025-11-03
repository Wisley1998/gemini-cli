#!/usr/bin/env python3
"""
验证生成的 prompts 格式
"""

from pathlib import Path

def check_prompts():
    """检查 prompts 格式"""
    base_dir = Path(__file__).parent
    
    print("="*60)
    print("Prompt 格式验证")
    print("="*60)
    
    # 检查 DeepResearch prompts
    dr_dir = base_dir / "deepresearch-bench-prompts"
    dr_files = list(dr_dir.glob("prompt_*.txt"))
    
    print(f"\n📊 DeepResearch Prompts: {len(dr_files)} 个")
    
    for f in sorted(dr_files)[:3]:
        with open(f, 'r', encoding='utf-8') as file:
            content = file.read()
            
            # 检查换行数
            line_count = content.count('\n')
            # 检查引号
            double_quotes = content.count('"')
            single_quotes = content.count("'")
            
            print(f"\n  {f.name}:")
            print(f"    换行数: {line_count}")
            print(f"    双引号: {double_quotes}")
            print(f"    单引号: {single_quotes}")
            print(f"    长度: {len(content)} 字符")
            print(f"    预览: {content[:150]}...")
    
    # 检查 SWE-bench prompts
    swe_dir = base_dir / "swe-bench-prompts"
    swe_files = list(swe_dir.glob("prompt_*.txt"))
    
    print(f"\n📊 SWE-bench Prompts: {len(swe_files)} 个")
    
    for f in sorted(swe_files)[:3]:
        with open(f, 'r', encoding='utf-8') as file:
            content = file.read()
            
            # 检查换行数
            line_count = content.count('\n')
            # 检查引号
            double_quotes = content.count('"')
            single_quotes = content.count("'")
            # 检查是否包含问题描述关键词
            has_problem = 'Consider the following' in content or 'The problem' in content
            
            print(f"\n  {f.name}:")
            print(f"    换行数: {line_count}")
            print(f"    双引号: {double_quotes}")
            print(f"    单引号: {single_quotes}")
            print(f"    长度: {len(content)} 字符")
            print(f"    包含问题描述: {'❌ 是' if has_problem else '✅ 否'}")
            print(f"    预览: {content[:150]}...")
    
    print("\n" + "="*60)
    print("✅ 验证完成")
    print("="*60)

if __name__ == "__main__":
    check_prompts()
