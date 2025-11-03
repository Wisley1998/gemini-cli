#!/bin/bash
# 安装依赖和测试脚本

set -e

echo "=========================================="
echo "事件-资源图分析工具 - 安装脚本"
echo "=========================================="
echo

# 检查Python版本
echo "检查Python版本..."
python_version=$(python3 --version 2>&1 | grep -oE '[0-9]+\.[0-9]+')
echo "✓ Python版本: $python_version"
echo

# 安装Python依赖
echo "安装Python依赖..."
pip3 install networkx pydot
echo

# 检查Graphviz
echo "检查Graphviz..."
if command -v dot &> /dev/null; then
    graphviz_version=$(dot -V 2>&1 | grep -oE '[0-9]+\.[0-9]+\.[0-9]+' | head -1)
    echo "✓ Graphviz已安装: $graphviz_version"
else
    echo "⚠ Graphviz未安装,将无法生成PNG图像"
    echo
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        echo "在macOS上安装Graphviz:"
        echo "  brew install graphviz"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        echo "在Linux上安装Graphviz:"
        echo "  sudo apt-get install graphviz  # Ubuntu/Debian"
        echo "  sudo yum install graphviz      # CentOS/RHEL"
    fi
    echo
fi

# 创建输出目录
echo "创建输出目录..."
mkdir -p output
echo "✓ 输出目录: output/"
echo

echo "=========================================="
echo "✓ 安装完成!"
echo "=========================================="
echo
echo "快速开始:"
echo "  python3 analyze_event_resource_graph.py"
echo
echo "查看帮助:"
echo "  python3 analyze_event_resource_graph.py --help"
echo
echo "查看文档:"
echo "  cat EVENT_RESOURCE_GRAPH_README.md"
echo
