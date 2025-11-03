#!/bin/bash

# 意图-行为-目标图分析器 - 快速运行脚本

echo "🚀 意图-行为-目标图分析器"
echo "================================"
echo ""

# 检查Python
if ! command -v python3 &> /dev/null; then
    echo "❌ 错误: 未找到 python3"
    exit 1
fi

# 检查依赖
echo "📦 检查依赖..."
if ! python3 -c "import matplotlib, networkx" 2>/dev/null; then
    echo "⚠️  缺少依赖，正在安装..."
    pip3 install -q -r requirements_intent_graph.txt
    echo "✅ 依赖安装完成"
else
    echo "✅ 依赖已安装"
fi

echo ""

# 运行分析
echo "🔍 开始分析日志文件..."
echo ""
python3 analyze_intent_behavior_target_graph.py --logs-dir logs

echo ""
echo "================================"
echo "✨ 分析完成！"
echo ""
echo "查看生成的图形:"
echo "  open intent_behavior_target_graphs/"
echo ""
echo "或者查看特定图形:"
ls -1 intent_behavior_target_graphs/*.png | head -3 | while read file; do
    echo "  open \"$file\""
done
