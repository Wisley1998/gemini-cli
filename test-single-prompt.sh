#!/bin/bash
#
# 快速测试单个 prompt 的执行
# 用于验证优化后的测试系统是否正常工作
#

echo "=================================="
echo "快速测试 - 单个 Prompt 执行"
echo "=================================="
echo ""

# 检查 prompt 文件
if [ ! -f "deepresearch-bench-prompts/prompt_001_1.txt" ]; then
    echo "❌ 错误: 找不到 prompt 文件"
    echo "请先运行: python3 extract-deepresearch-bench-prompts.py --limit 10"
    exit 1
fi

echo "✓ 找到 DeepResearch prompt"
echo ""

# 显示 prompt 内容的前几行
echo "Prompt 内容预览:"
echo "-----------------------------------"
head -n 30 deepresearch-bench-prompts/prompt_001_1.txt
echo "..."
echo "-----------------------------------"
echo ""

echo "📝 MCP 工具要求摘要:"
grep -A 3 "MCP 工具使用要求" deepresearch-bench-prompts/prompt_001_1.txt | head -n 4
echo ""

echo "✅ 验证完成！"
echo ""
echo "要运行完整测试，请执行:"
echo "  python3 run_automated_benchmark.py"
echo ""
echo "结果将保存到:"
echo "  - results/deep_research/ (DeepResearch)"
echo "  - results/code/ (SWE-bench)"
