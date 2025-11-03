#!/usr/bin/env python3
"""
自动生成 DeepResearch 和 SWE-bench Prompts
一键生成所有测试数据
"""

import subprocess
import sys
from pathlib import Path

def run_command(command, description):
    """运行命令并显示输出"""
    print(f"\n{'='*60}")
    print(f"▶ {description}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            check=True,
            text=True,
            capture_output=True
        )
        print(result.stdout)
        if result.stderr:
            print("警告:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ 错误: {e}")
        print(f"输出: {e.stdout}")
        print(f"错误: {e.stderr}")
        return False

def main():
    """主函数"""
    print("""
╔══════════════════════════════════════════════════════════╗
║         Prompt 自动生成脚本                              ║
║   生成 DeepResearch 和 SWE-bench 测试 Prompts           ║
╚══════════════════════════════════════════════════════════╝
    """)
    
    # 获取参数
    import argparse
    parser = argparse.ArgumentParser(description='自动生成测试 prompts')
    parser.add_argument(
        '--deepresearch',
        type=int,
        default=10,
        help='生成 DeepResearch prompts 的数量 (默认: 10)'
    )
    parser.add_argument(
        '--swebench',
        type=int,
        default=10,
        help='生成 SWE-bench prompts 的数量 (默认: 10)'
    )
    parser.add_argument(
        '--clean',
        action='store_true',
        help='清理旧的 prompt 文件'
    )
    
    args = parser.parse_args()
    
    base_dir = Path(__file__).parent
    deepresearch_dir = base_dir / "deepresearch-bench-prompts"
    swebench_dir = base_dir / "swe-bench-prompts"
    
    print(f"📁 工作目录: {base_dir}")
    print(f"   DeepResearch: {deepresearch_dir}")
    print(f"   SWE-bench: {swebench_dir}")
    print(f"\n📊 生成配置:")
    print(f"   DeepResearch prompts: {args.deepresearch} 个")
    print(f"   SWE-bench prompts: {args.swebench} 个")
    
    # 清理旧文件
    if args.clean:
        print("\n🧹 清理旧的 prompt 文件...")
        run_command(
            f"rm -f {deepresearch_dir}/prompt_*.txt {swebench_dir}/prompt_*.txt",
            "删除旧的 prompt 文件"
        )
    
    # 生成 DeepResearch prompts
    success_deep = run_command(
        f"cd {base_dir} && python3 extract-deepresearch-bench-prompts.py --limit {args.deepresearch}",
        f"生成 {args.deepresearch} 个 DeepResearch Prompts"
    )
    
    # 生成 SWE-bench prompts
    success_swe = run_command(
        f"cd {base_dir} && python3 extract-swe-bench-prompts.py --limit {args.swebench}",
        f"生成 {args.swebench} 个 SWE-bench Prompts"
    )
    
    # 验证生成结果
    print(f"\n{'='*60}")
    print("📊 生成结果验证")
    print(f"{'='*60}")
    
    deepresearch_files = list(deepresearch_dir.glob("prompt_*.txt"))
    swebench_files = list(swebench_dir.glob("prompt_*.txt"))
    
    print(f"\n✅ DeepResearch Prompts: {len(deepresearch_files)} 个")
    if deepresearch_files:
        for f in sorted(deepresearch_files)[:3]:
            print(f"   - {f.name}")
        if len(deepresearch_files) > 3:
            print(f"   ... 以及其他 {len(deepresearch_files) - 3} 个")
    
    print(f"\n✅ SWE-bench Prompts: {len(swebench_files)} 个")
    if swebench_files:
        for f in sorted(swebench_files)[:3]:
            print(f"   - {f.name}")
        if len(swebench_files) > 3:
            print(f"   ... 以及其他 {len(swebench_files) - 3} 个")
    
    # 显示示例
    if deepresearch_files:
        print(f"\n{'='*60}")
        print("📝 DeepResearch Prompt 示例")
        print(f"{'='*60}")
        sample_file = sorted(deepresearch_files)[0]
        with open(sample_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"{content[:200]}...")
    
    if swebench_files:
        print(f"\n{'='*60}")
        print("📝 SWE-bench Prompt 示例")
        print(f"{'='*60}")
        sample_file = sorted(swebench_files)[0]
        with open(sample_file, 'r', encoding='utf-8') as f:
            content = f.read()
            print(f"{content[:200]}...")
    
    # 总结
    print(f"\n{'='*60}")
    print("🎉 生成完成！")
    print(f"{'='*60}")
    
    if success_deep and success_swe:
        print("✅ 所有 prompts 生成成功")
        print(f"\n💡 下一步操作:")
        print(f"   1. 查看生成的 prompts:")
        print(f"      ls {deepresearch_dir}/prompt_*.txt")
        print(f"      ls {swebench_dir}/prompt_*.txt")
        print(f"   2. 运行基准测试:")
        print(f"      python3 run_automated_benchmark.py")
        print(f"   3. 查看结果:")
        print(f"      ls results/deep_research/")
        print(f"      ls results/code/")
        return 0
    else:
        print("⚠️  部分任务失败，请检查错误信息")
        return 1

if __name__ == "__main__":
    sys.exit(main())
