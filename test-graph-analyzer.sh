#!/bin/bash
# 快速测试脚本 - 分析一个日志文件并显示结果

set -e

echo "=========================================="
echo "事件-资源图分析 - 快速测试"
echo "=========================================="
echo

# 查找第一个日志文件
log_file=$(ls logs/*.log 2>/dev/null | head -1)

if [ -z "$log_file" ]; then
    echo "✗ 错误: 在logs/目录下没有找到日志文件"
    exit 1
fi

echo "测试日志文件: $log_file"
echo

# 运行分析
echo "开始分析..."
python3 analyze_event_resource_graph.py "$log_file" -o test_output

echo
echo "=========================================="
echo "✓ 测试完成!"
echo "=========================================="
echo

# 显示结果
if [ -d "test_output" ]; then
    echo "生成的文件:"
    ls -lh test_output/
    echo
    
    # 如果有DOT文件,显示统计信息
    dot_file=$(ls test_output/*.dot 2>/dev/null | head -1)
    if [ -n "$dot_file" ]; then
        echo "DOT文件内容预览:"
        echo "----------------------------------------"
        head -30 "$dot_file"
        echo "..."
        echo "----------------------------------------"
        echo
        
        # 统计节点和边
        nodes=$(grep -c '^\s*".*"\s*\[' "$dot_file" || true)
        edges=$(grep -c '^\s*".*"\s*->\s*".*"' "$dot_file" || true)
        
        echo "图统计:"
        echo "  节点数: $nodes"
        echo "  边数: $edges"
        echo
    fi
    
    # 检查PNG文件
    png_file=$(ls test_output/*.png 2>/dev/null | head -1)
    if [ -n "$png_file" ]; then
        echo "✓ PNG图像已生成: $png_file"
        
        # 尝试打开图像
        if [[ "$OSTYPE" == "darwin"* ]]; then
            echo "正在打开图像..."
            open "$png_file"
        fi
    else
        echo "⚠ 未生成PNG图像 (可能因为Graphviz未安装)"
        echo
        echo "可以手动转换DOT为PNG:"
        echo "  dot -Tpng $dot_file -o ${dot_file%.dot}.png"
    fi
fi

echo
echo "查看详细使用方法:"
echo "  cat EVENT_RESOURCE_GRAPH_README.md"
echo
