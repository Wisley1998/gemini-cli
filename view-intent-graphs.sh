#!/bin/bash

# 快速查看所有生成的意图-行为-目标图

echo "🎨 意图-行为-目标图 - 查看器"
echo "========================================"
echo ""

GRAPH_DIR="intent_behavior_target_graphs"

if [ ! -d "$GRAPH_DIR" ]; then
    echo "❌ 错误: 图形目录不存在"
    echo "   请先运行: ./run-intent-graph-analysis.sh"
    exit 1
fi

# 统计图形文件数量
PNG_COUNT=$(ls -1 "$GRAPH_DIR"/*.png 2>/dev/null | wc -l)

if [ "$PNG_COUNT" -eq 0 ]; then
    echo "❌ 错误: 未找到图形文件"
    echo "   请先运行: ./run-intent-graph-analysis.sh"
    exit 1
fi

echo "📊 找到 $PNG_COUNT 个图形文件"
echo ""

# 列出所有图形及其统计信息
for png in "$GRAPH_DIR"/*.png; do
    base=$(basename "$png" .png)
    json="${GRAPH_DIR}/${base//_intent_behavior_target_graph/}_stats.json"
    
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "📝 $(basename "$png")"
    
    if [ -f "$json" ]; then
        # 提取统计信息
        llm_count=$(grep -o '"total_llm_decisions": [0-9]*' "$json" | grep -o '[0-9]*')
        tool_count=$(grep -o '"total_tool_calls": [0-9]*' "$json" | grep -o '[0-9]*')
        target_count=$(grep -o '"total_target_resources": [0-9]*' "$json" | grep -o '[0-9]*')
        
        echo "   📊 统计:"
        echo "      • LLM决策: $llm_count 次"
        echo "      • 工具调用: $tool_count 次"
        echo "      • 目标资源: $target_count 个"
    fi
    
    # 文件大小
    size=$(ls -lh "$png" | awk '{print $5}')
    echo "   💾 文件大小: $size"
    echo ""
done

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "🔍 查看选项:"
echo ""
echo "1️⃣  打开所有图形 (推荐)"
echo "   open $GRAPH_DIR/*.png"
echo ""
echo "2️⃣  在文件夹中查看"
echo "   open $GRAPH_DIR"
echo ""
echo "3️⃣  查看特定图形"
for png in "$GRAPH_DIR"/*.png; do
    echo "   open \"$png\""
done
echo ""

# 询问用户
read -p "👉 选择操作 (1-3, 或按Enter跳过): " choice

case $choice in
    1)
        echo ""
        echo "🚀 打开所有图形..."
        open "$GRAPH_DIR"/*.png
        ;;
    2)
        echo ""
        echo "📁 打开文件夹..."
        open "$GRAPH_DIR"
        ;;
    3)
        echo ""
        echo "📋 请复制上面的命令手动执行"
        ;;
    *)
        echo ""
        echo "👋 退出"
        ;;
esac

echo ""
echo "✨ 完成！"
