#!/bin/bash
#
# 快速测试脚本 - 演示如何使用 run_automated_benchmark.py
#

echo "╔══════════════════════════════════════════════════════════╗"
echo "║      Gemini CLI 自动化测试 - 使用说明                   ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# 显示帮助信息
echo "📖 查看完整帮助:"
echo "   python3 run_automated_benchmark.py --help"
echo ""

# 显示使用示例
echo "💡 使用示例:"
echo ""
echo "1️⃣  测试所有类型 (DeepResearch + SWE-bench):"
echo "   python3 run_automated_benchmark.py --type all"
echo ""

echo "2️⃣  只测试 DeepResearch:"
echo "   python3 run_automated_benchmark.py --type deepresearch"
echo ""

echo "3️⃣  只测试 SWE-bench:"
echo "   python3 run_automated_benchmark.py --type swebench"
echo ""

echo "4️⃣  测试前 3 个 DeepResearch prompts:"
echo "   python3 run_automated_benchmark.py --type deepresearch --limit 3"
echo ""

echo "5️⃣  测试前 5 个 SWE-bench prompts:"
echo "   python3 run_automated_benchmark.py --type swebench --limit 5"
echo ""

echo "6️⃣  快速测试 (每种类型各测 1 个):"
echo "   python3 run_automated_benchmark.py --type deepresearch --limit 1"
echo "   python3 run_automated_benchmark.py --type swebench --limit 1"
echo ""

# 显示当前可用的 prompts
echo "📊 当前可用的 Prompts:"
echo ""

deepresearch_count=$(ls deepresearch-bench-prompts/prompt_*.txt 2>/dev/null | wc -l)
swebench_count=$(ls swe-bench-prompts/prompt_*.txt 2>/dev/null | wc -l)

echo "   DeepResearch: $deepresearch_count 个"
if [ $deepresearch_count -gt 0 ]; then
    echo "   示例:"
    ls deepresearch-bench-prompts/prompt_*.txt 2>/dev/null | head -3 | while read file; do
        echo "     - $(basename $file)"
    done
fi
echo ""

echo "   SWE-bench: $swebench_count 个"
if [ $swebench_count -gt 0 ]; then
    echo "   示例:"
    ls swe-bench-prompts/prompt_*.txt 2>/dev/null | head -3 | while read file; do
        echo "     - $(basename $file)"
    done
fi
echo ""

# 显示结果目录
echo "📁 测试结果保存位置:"
echo "   - DeepResearch: results/deep_research/"
echo "   - SWE-bench: results/code/"
echo ""

# 询问是否运行快速测试
echo "═══════════════════════════════════════════════════════════"
echo ""
read -p "是否运行快速测试? (每种类型各测 1 个) [y/N]: " response

if [[ "$response" =~ ^[Yy]$ ]]; then
    echo ""
    echo "🚀 开始快速测试..."
    echo ""
    
    # 测试 DeepResearch
    if [ $deepresearch_count -gt 0 ]; then
        echo "📝 测试 DeepResearch (1个)..."
        python3 run_automated_benchmark.py --type deepresearch --limit 1
        echo ""
    fi
    
    # 测试 SWE-bench
    if [ $swebench_count -gt 0 ]; then
        echo "📝 测试 SWE-bench (1个)..."
        python3 run_automated_benchmark.py --type swebench --limit 1
        echo ""
    fi
    
    echo "✅ 快速测试完成!"
    echo ""
    echo "查看结果:"
    echo "   ls -lh results/deep_research/"
    echo "   ls -lh results/code/"
else
    echo ""
    echo "ℹ️  跳过测试。使用上述命令手动运行测试。"
fi

echo ""
