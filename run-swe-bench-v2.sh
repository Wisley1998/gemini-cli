#!/bin/bash
# SWE-bench 精简执行脚本 v2
# 使用方法：
#   超精简: PROMPT_VERSION=ultra ./run-swe-bench-v2.sh
#   精简版: ./run-swe-bench-v2.sh  (默认)
#   完整版: PROMPT_VERSION=full ./run-swe-bench-v2.sh
#   自定义时长: TIMEOUT=300 ./run-swe-bench-v2.sh  (默认180秒)

set -e

# 取消代理
unset http_proxy https_proxy all_proxy HTTP_PROXY HTTPS_PROXY ALL_PROXY

# 配置
PROMPT_VERSION="${PROMPT_VERSION:-lite}"
WORK_DIR="./swe-bench-workspace/pytest-fix-13802"
TIMEOUT="${TIMEOUT:-180}"  # 默认 3 分钟（180秒）

echo "🚀 SWE-bench 任务：pytest #13802"
echo "版本: $PROMPT_VERSION"
echo "超时: ${TIMEOUT}秒"
echo ""

# 清理并创建工作目录
rm -rf "$WORK_DIR"
mkdir -p "$WORK_DIR"

# 执行任务
case $PROMPT_VERSION in
    "ultra")
        echo "使用超精简版（~50 tokens）"
        PROMPT_CMD='cat << '\''EOF'\'' | gemini --yolo
分析并修复 pytest issue #13802: https://github.com/pytest-dev/pytest/issues/13802
工作目录：./swe-bench-workspace/pytest-fix-13802/
EOF'
        ;;
    "lite")
        echo "使用精简版（~150 tokens）"
        PROMPT_CMD='cat << '\''EOF'\'' | gemini --yolo
任务：分析并修复 pytest issue #13802
Issue: https://github.com/pytest-dev/pytest/issues/13802
工作目录：./swe-bench-workspace/pytest-fix-13802/

步骤：
1. 用 run_shell_command 克隆 pytest 仓库
2. 访问 issue 了解问题详情
3. 定位并分析相关代码
4. 实施修复（如果是 bug）或实现功能（如果是功能请求）
5. 测试验证
6. 生成补丁文件和报告
EOF'
        ;;
    "full")
        echo "使用完整版（~300 tokens）"
        PROMPT_CMD='cat << '\''EOF'\'' | gemini --yolo
任务：处理 pytest 项目的 issue #13802

Issue 链接：https://github.com/pytest-dev/pytest/issues/13802
工作目录：./swe-bench-workspace/pytest-fix-13802/

执行步骤：
1. 使用 run_shell_command 克隆 pytest 仓库到工作目录
2. 访问 issue 链接，仔细阅读问题描述
3. 判断这是 bug 修复还是功能实现
4. 定位相关代码文件
5. 分析当前实现和问题根因
6. 提出并实施解决方案
7. 编写测试用例验证
8. 使用 run_shell_command("git diff") 生成补丁保存为 fix_13802.patch
9. 生成修复报告 fix_report_13802.md

注意：所有 git 操作使用 run_shell_command 执行
EOF'
        ;;
    *)
        echo "错误：未知版本 $PROMPT_VERSION"
        echo "可选: ultra, lite, full"
        exit 1
        ;;
esac

# 在后台运行 gemini 命令
echo "启动任务（PID 将在下方显示）..."
eval "$PROMPT_CMD" &
GEMINI_PID=$!

echo "Gemini PID: $GEMINI_PID"
echo "将在 ${TIMEOUT} 秒后自动停止..."
echo ""

# 等待指定时间
sleep "$TIMEOUT" &
SLEEP_PID=$!

# 等待 sleep 完成或 gemini 提前结束
wait $SLEEP_PID 2>/dev/null || true

# 检查 gemini 是否还在运行
if kill -0 $GEMINI_PID 2>/dev/null; then
    echo ""
    echo "⏰ 超时！正在停止任务..."
    
    # 发送第一个 SIGINT (Ctrl+C)
    kill -INT $GEMINI_PID 2>/dev/null || true
    sleep 1
    
    # 检查是否还在运行
    if kill -0 $GEMINI_PID 2>/dev/null; then
        echo "发送第二个 Ctrl+C..."
        # 发送第二个 SIGINT
        kill -INT $GEMINI_PID 2>/dev/null || true
        sleep 1
        
        # 如果还在运行，强制终止
        if kill -0 $GEMINI_PID 2>/dev/null; then
            echo "强制终止..."
            kill -9 $GEMINI_PID 2>/dev/null || true
        fi
    fi
    
    echo "✅ 任务已停止"
else
    echo ""
    echo "✅ 任务已自然完成"
fi

echo ""
echo "✅ 执行完成！"
echo "工作目录: $WORK_DIR"
