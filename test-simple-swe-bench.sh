#!/bin/bash
# 简易SWE-bench工具测试脚本

echo "🧪 测试简易SWE-bench工具配置"
echo "================================"
echo ""

# 创建测试目录
TEST_DIR="/tmp/swe-bench-test-$(date +%s)"
mkdir -p "$TEST_DIR"
cd "$TEST_DIR"

echo "📁 测试目录: $TEST_DIR"
echo ""

# 测试场景：修复一个简单的Python bug
echo "📝 创建测试任务..."

# 1. 创建一个有bug的Python文件
cat > buggy_code.py << 'EOF'
def calculate_average(numbers):
    """计算数字列表的平均值"""
    total = sum(numbers)
    # Bug: 没有处理空列表的情况
    return total / len(numbers)

def test_average():
    """测试函数"""
    assert calculate_average([1, 2, 3, 4, 5]) == 3.0
    assert calculate_average([10, 20, 30]) == 20.0
    # 这个测试会失败
    try:
        calculate_average([])
        print("❌ 空列表测试失败 - 应该抛出异常或返回0")
    except ZeroDivisionError:
        print("✅ 发现了除零错误！")

if __name__ == "__main__":
    test_average()
EOF

echo "✅ 创建了有bug的代码文件: buggy_code.py"
echo ""

# 2. 创建问题描述
cat > issue.md << 'EOF'
# Issue: calculate_average函数无法处理空列表

## 问题描述
`calculate_average` 函数在接收空列表时会抛出 `ZeroDivisionError`。

## 重现步骤
```python
result = calculate_average([])
# ZeroDivisionError: division by zero
```

## 期望行为
应该返回 0 或者抛出更友好的异常。

## 受影响代码
文件: `buggy_code.py`
函数: `calculate_average`
EOF

echo "✅ 创建了问题描述: issue.md"
echo ""

# 3. 运行测试查看bug
echo "🔍 运行测试以确认bug..."
python3 buggy_code.py
echo ""

# 4. 创建修复后的代码
cat > fixed_code.py << 'EOF'
def calculate_average(numbers):
    """计算数字列表的平均值"""
    if not numbers:
        return 0
    total = sum(numbers)
    return total / len(numbers)

def test_average():
    """测试函数"""
    assert calculate_average([1, 2, 3, 4, 5]) == 3.0
    assert calculate_average([10, 20, 30]) == 20.0
    assert calculate_average([]) == 0
    print("✅ 所有测试通过！")

if __name__ == "__main__":
    test_average()
EOF

echo "✅ 创建了修复后的代码: fixed_code.py"
echo ""

# 5. 运行修复后的测试
echo "✨ 运行修复后的测试..."
python3 fixed_code.py
echo ""

# 6. 创建使用gemini-cli的提示
cat > gemini_prompt.txt << 'EOF'
# 使用 gemini-cli 处理这个SWE-bench任务的示例提示：

gemini --yolo "
我有一个简单的SWE-bench风格的任务：

1. 阅读 issue.md 了解问题
2. 阅读 buggy_code.py 找到bug
3. 修复这个bug（处理空列表的情况）
4. 将修复后的代码写入 buggy_code.py
5. 运行测试验证修复

请帮我完成这个任务。
"
EOF

echo "📋 已创建gemini-cli提示文件: gemini_prompt.txt"
echo ""

echo "================================"
echo "✅ 测试准备完成！"
echo ""
echo "📂 测试文件位置: $TEST_DIR"
echo ""
echo "🎯 下一步："
echo "  1. cd $TEST_DIR"
echo "  2. cat gemini_prompt.txt  # 查看提示"
echo "  3. 使用gemini-cli执行任务"
echo ""
echo "🧹 清理测试: rm -rf $TEST_DIR"
