#!/usr/bin/env python3
"""
测试 --range 参数功能
"""

from pathlib import Path

def test_range_selection():
    """测试范围选择逻辑"""
    
    # 模拟 prompt 文件列表
    prompts_dir = Path("deepresearch-bench-prompts")
    
    if not prompts_dir.exists():
        print("❌ deepresearch-bench-prompts 目录不存在")
        return
    
    all_prompts = sorted(prompts_dir.glob("prompt_*.txt"))
    print(f"✅ 总共找到 {len(all_prompts)} 个 DeepResearch prompts\n")
    
    # 测试场景 1: 选择第 1-5 个
    print("📋 测试场景 1: --range 1-5")
    start_idx, end_idx = 1, 5
    selected = all_prompts[start_idx-1:end_idx]
    print(f"   选中: {len(selected)} 个")
    for p in selected:
        print(f"   - {p.name}")
    print()
    
    # 测试场景 2: 选择第 10-15 个
    print("📋 测试场景 2: --range 10-15")
    start_idx, end_idx = 10, 15
    selected = all_prompts[start_idx-1:end_idx]
    print(f"   选中: {len(selected)} 个")
    for p in selected:
        print(f"   - {p.name}")
    print()
    
    # 测试场景 3: 选择第 95-105 个（超出范围）
    print("📋 测试场景 3: --range 95-105 (超出范围)")
    start_idx, end_idx = 95, 105
    total_available = len(all_prompts)
    if end_idx > total_available:
        print(f"   ⚠️  结束索引 {end_idx} 超过总数 {total_available}，将使用 {total_available}")
        actual_end = total_available
    else:
        actual_end = end_idx
    selected = all_prompts[start_idx-1:actual_end]
    print(f"   选中: {len(selected)} 个")
    for p in selected:
        print(f"   - {p.name}")
    print()
    
    # 测试场景 4: 单个 prompt
    print("📋 测试场景 4: --range 50-50 (单个)")
    start_idx, end_idx = 50, 50
    selected = all_prompts[start_idx-1:end_idx]
    print(f"   选中: {len(selected)} 个")
    for p in selected:
        print(f"   - {p.name}")
    print()

if __name__ == "__main__":
    test_range_selection()
