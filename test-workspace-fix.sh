#!/bin/bash
# 测试 workspace 问题修复

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 测试 Gemini CLI Workspace 修复"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查 pexpect 是否安装
echo "📦 检查依赖..."
if ! python3 -c "import pexpect" 2>/dev/null; then
    echo -e "${YELLOW}⚠️  pexpect 未安装，正在安装...${NC}"
    pip3 install pexpect
fi
echo -e "${GREEN}✓ 依赖检查完成${NC}"
echo ""

# 检查是否有 prompt 文件
echo "📝 检查 prompt 文件..."
PROMPT_COUNT=$(ls -1 swe-bench-prompts/prompt_*.txt 2>/dev/null | wc -l | xargs)
if [ "$PROMPT_COUNT" -eq 0 ]; then
    echo -e "${RED}✗ 未找到 SWE-bench prompt 文件${NC}"
    echo "请先运行: python3 extract-swe-bench-prompts.py"
    exit 1
fi
echo -e "${GREEN}✓ 找到 $PROMPT_COUNT 个 prompt 文件${NC}"
echo ""

# 测试选项
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "选择测试方式："
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "1) 测试方案 1 - 原脚本 + 环境变量（快速）"
echo "2) 测试方案 2 - 新脚本 v2（推荐）"
echo "3) 测试环境变量是否生效"
echo "4) 查看最新测试结果"
echo "q) 退出"
echo ""
read -p "请选择 (1-4/q): " choice

case $choice in
    1)
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "🧪 测试方案 1：原脚本 + 环境变量"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        
        # 备份原文件
        if [ ! -f "run_automated_benchmark.backup.py" ]; then
            echo "📁 备份原文件..."
            cp run_automated_benchmark.py run_automated_benchmark.backup.py
            echo -e "${GREEN}✓ 已备份到 run_automated_benchmark.backup.py${NC}"
        fi
        
        echo ""
        echo "运行测试（限制 1 个 prompt）..."
        python3 run_automated_benchmark.py --type swebench --limit 1
        
        echo ""
        echo -e "${GREEN}✓ 测试完成！${NC}"
        echo "查看结果: ls -lth results/code/ | head -5"
        ;;
        
    2)
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "🧪 测试方案 2：新脚本 v2"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        
        if [ ! -f "run_automated_benchmark_v2.py" ]; then
            echo -e "${RED}✗ 未找到 run_automated_benchmark_v2.py${NC}"
            echo "请确保文件已创建"
            exit 1
        fi
        
        echo "运行测试（限制 1 个 prompt）..."
        python3 run_automated_benchmark_v2.py --type swebench --limit 1
        
        echo ""
        echo -e "${GREEN}✓ 测试完成！${NC}"
        echo "工作目录: ls -la swe-bench-workspace/"
        echo "结果文件: ls -lth results/code/ | head -5"
        ;;
        
    3)
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "🧪 测试环境变量"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        
        echo "测试 1: 正常启动（可能失败）"
        timeout 5s gemini --version 2>&1 | head -3 || true
        
        echo ""
        echo "测试 2: 使用环境变量（应该成功）"
        GEMINI_CLI_IDE_INTEGRATION=disabled timeout 5s gemini --version 2>&1 | head -3
        
        echo ""
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ 环境变量生效！${NC}"
        else
            echo -e "${RED}✗ 环境变量未生效${NC}"
        fi
        ;;
        
    4)
        echo ""
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo "📊 最新测试结果"
        echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        echo ""
        
        echo "🗂️  Code Results (results/code/):"
        ls -lth results/code/ 2>/dev/null | head -10 || echo "  (空)"
        
        echo ""
        echo "🗂️  Deep Research Results (results/deep_research/):"
        ls -lth results/deep_research/ 2>/dev/null | head -10 || echo "  (空)"
        
        echo ""
        echo "🗂️  Workspace (swe-bench-workspace/):"
        ls -la swe-bench-workspace/ 2>/dev/null | head -10 || echo "  (空)"
        
        echo ""
        if [ -f "results/code/prompt_001_astropy__astropy-12907_summary.txt" ]; then
            echo "📄 查看最新结果："
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
            head -30 results/code/prompt_001_astropy__astropy-12907_summary.txt
            echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
        fi
        ;;
        
    q|Q)
        echo "退出"
        exit 0
        ;;
        
    *)
        echo -e "${RED}无效选择${NC}"
        exit 1
        ;;
esac

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✨ 完成！${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📖 查看完整文档: cat FIX_WORKSPACE_ISSUE.md"
echo ""
