#!/bin/bash
# 自动修复 run_automated_benchmark.py 并测试

set -e

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🔧 自动修复 Workspace 问题"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查文件是否存在
if [ ! -f "run_automated_benchmark.py" ]; then
    echo -e "${RED}✗ 未找到 run_automated_benchmark.py${NC}"
    echo "请确保在 gemini-cli 目录中运行此脚本"
    exit 1
fi

echo "📋 当前目录: $(pwd)"
echo ""

# 步骤 1: 检查是否已修复
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📝 步骤 1: 检查脚本状态"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if grep -q "GEMINI_CLI_IDE_INTEGRATION=disabled" run_automated_benchmark.py; then
    echo -e "${GREEN}✓ 脚本已包含环境变量修复${NC}"
    NEEDS_FIX=false
else
    echo -e "${YELLOW}⚠️  脚本需要添加环境变量修复${NC}"
    NEEDS_FIX=true
fi
echo ""

# 步骤 2: 应用修复（如果需要）
if [ "$NEEDS_FIX" = true ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔨 步骤 2: 应用修复"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    # 备份原文件
    if [ ! -f "run_automated_benchmark.py.bak" ]; then
        echo "📁 创建备份: run_automated_benchmark.py.bak"
        cp run_automated_benchmark.py run_automated_benchmark.py.bak
    fi
    
    # 应用修复
    echo "🔧 应用环境变量修复..."
    
    # 使用 Python 进行精确替换
    python3 << 'PYEOF'
import re

with open('run_automated_benchmark.py', 'r') as f:
    content = f.read()

# 修复 1: 添加 bash -c 和正确的转义
old_pattern_1 = r'escaped_prompt = prompt_content\.replace\(\'"\'.*?\n.*?cmd = f\'gemini --prompt-interactive.*?\n.*?print\(f"启动命令:.*?\n.*?child = pexpect\.spawn\(cmd,'
new_code_1 = '''escaped_prompt = prompt_content.replace('"', '\\\\"').replace('$', '\\\\$')
        
        # 禁用 IDE 集成以避免 workspace 检查错误
        # 使用 bash -c 来设置环境变量
        cmd = f'bash -c "GEMINI_CLI_IDE_INTEGRATION=disabled gemini --prompt-interactive \\\\"{escaped_prompt}\\\\" --yolo"'
        
        print(f"启动命令: bash -c \\"GEMINI_CLI_IDE_INTEGRATION=disabled gemini --prompt-interactive ...\\" --yolo")
        child = pexpect.spawn(cmd,'''

if re.search(r"bash -c.*GEMINI_CLI_IDE_INTEGRATION", content):
    print("✓ 修复已存在（bash -c 版本）")
elif re.search(old_pattern_1, content, re.DOTALL):
    content = re.sub(old_pattern_1, new_code_1, content, flags=re.DOTALL)
    with open('run_automated_benchmark.py', 'w') as f:
        f.write(content)
    print("✓ 修复已应用（bash -c 版本）")
else:
    # 尝试简单替换
    if "cmd = f'gemini --prompt-interactive" in content:
        content = content.replace(
            "cmd = f'gemini --prompt-interactive",
            "cmd = f'bash -c \"GEMINI_CLI_IDE_INTEGRATION=disabled gemini --prompt-interactive"
        )
        with open('run_automated_benchmark.py', 'w') as f:
            f.write(content)
        print("✓ 修复已应用（简单版本）")
    else:
        print("⚠️  未找到需要修复的代码行")
PYEOF
    
    echo -e "${GREEN}✓ 修复完成${NC}"
    echo ""
else
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "🔨 步骤 2: 跳过修复（已修复）"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
fi

# 步骤 3: 显示修复后的代码
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "📄 步骤 3: 验证修复"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "修复后的命令行（第 145-150 行附近）："
echo "────────────────────────────────────────────────────────────────"
grep -A 2 -B 2 "GEMINI_CLI_IDE_INTEGRATION" run_automated_benchmark.py | head -10
echo "────────────────────────────────────────────────────────────────"
echo ""

# 步骤 4: 询问是否运行测试
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "🧪 步骤 4: 运行测试"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

read -p "是否运行测试？(y/N): " -n 1 -r
echo ""

if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo ""
    echo "运行测试（限制 1 个 prompt）..."
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    # 检查 pexpect
    if ! python3 -c "import pexpect" 2>/dev/null; then
        echo -e "${YELLOW}⚠️  安装 pexpect...${NC}"
        pip3 install pexpect
    fi
    
    # 运行测试
    python3 run_automated_benchmark.py --type swebench --limit 1
    
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${GREEN}✓ 测试完成${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    # 步骤 5: 显示结果
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📊 步骤 5: 查看结果"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    
    echo "🗂️  结果文件:"
    ls -lth results/code/ 2>/dev/null | head -5 || echo "  (未找到结果)"
    
    echo ""
    if [ -f "results/code/prompt_001_astropy__astropy-12907_summary.txt" ]; then
        echo "📄 性能统计（前 30 行）:"
        echo "────────────────────────────────────────────────────────────────"
        head -30 results/code/prompt_001_astropy__astropy-12907_summary.txt
        echo "────────────────────────────────────────────────────────────────"
    fi
    
    echo ""
    echo "查看完整结果:"
    echo "  cat results/code/prompt_001_astropy__astropy-12907_summary.txt"
else
    echo ""
    echo "跳过测试。手动运行测试命令:"
    echo "  python3 run_automated_benchmark.py --type swebench --limit 1"
fi

echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo -e "${GREEN}✨ 完成！${NC}"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "📖 相关文档:"
echo "  • WORKSPACE_PATH_ISSUE_FIX.md - 完整修复指南"
echo "  • WORKSPACE_FIX_SUMMARY.md - 技术总结"
echo ""
echo "💡 批量运行:"
echo "  python3 run_automated_benchmark.py --type swebench --range 1-5"
echo ""
