# 图形显示优化说明

## 🔧 已修复的问题

### 1. ✅ 中文显示问题

**问题**: 图形中的中文字符显示为方块或乱码  
**解决方案**:

```python
# 配置matplotlib使用支持中文的字体
plt.rcParams['font.sans-serif'] = ['Arial Unicode MS', 'SimHei', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False
```

**字体优先级**:

1. `Arial Unicode MS` - macOS系统自带，完美支持中文
2. `SimHei` - 黑体，备选方案
3. `DejaVu Sans` - 默认字体

### 2. ✅ 字符重叠问题

**问题**: 节点标签文字相互重叠，难以阅读  
**解决方案**:

#### A. 增大画布尺寸

```python
# 之前: 16x12
# 现在: 20x16
plt.figure(figsize=(20, 16), dpi=100)
```

#### B. 增大节点尺寸

```python
# LLM Decision: 3000 → 5000
# Tool Call: 2500 → 4000
# Target Resource: 2000 → 3000
```

#### C. 增加节点间距

```python
# 水平间距: 2 → 3.5
# Tool层间距: 0.5 → 0.8
# Target层间距: 0.3 → 0.6
```

#### D. 优化标签显示

```python
# 字体大小: 8 → 9
# 字体粗细: bold → normal
# 对齐方式: center + center
```

#### E. 增加边距和间隔

```python
plt.tight_layout(pad=2.0)  # 增加内边距
plt.savefig(..., pad_inches=0.5)  # 增加外边距
```

## 📊 优化效果对比

### 优化前

- ❌ 中文显示为方块
- ❌ 节点标签重叠
- ❌ 图形拥挤难读
- ❌ 分辨率: 300 DPI

### 优化后

- ✅ 中文正常显示
- ✅ 标签清晰可读
- ✅ 布局疏朗舒适
- ✅ 分辨率: 200 DPI (更好的显示效果)

## 🎨 视觉改进

### 1. 标题改进

```python
# 之前: 'Intent-Behavior-Target Graph: xxx'
# 现在: '意图-行为-目标图: xxx'
```

### 2. 图例优化

```python
# 字体大小: 10 → 12
# 添加半透明背景 (framealpha=0.9)
```

### 3. 整体布局

```python
# 标题间距: pad=20 → pad=30
# 布局间距: tight_layout() → tight_layout(pad=2.0)
```

## 📈 性能优化

### DPI调整

- **之前**: 300 DPI (文件较大，加载慢)
- **现在**: 200 DPI (清晰度足够，文件更小)

### 文件大小变化

```
10-22-18-1: 678KB → 557KB (减少18%)
10-22-18-4: 686KB → 565KB (减少18%)
10-22-19-2: 258KB → 208KB (减少19%)
10-22-19-3: 349KB → 285KB (减少18%)
10-22-19-4: 343KB → 281KB (减少18%)
```

## 🔍 技术细节

### 间距计算逻辑

#### 第一层 (LLM Decisions)

```python
# 每个节点的水平间距
x_position = node_index * 3.5
```

#### 第二层 (Tool Calls)

```python
# 基于父LLM节点位置，加上偏移
x_position = parent_llm_x + offset * 0.8
```

#### 第三层 (Target Resources)

```python
# 基于所有访问它的Tool节点的平均位置
x_position = average_of_predecessor_tools + index * 0.6
```

## 🎯 使用建议

### 查看图形的最佳方式

1. **在图片查看器中打开** (推荐)

   ```bash
   open intent_behavior_target_graphs/xxx.png
   ```

2. **在浏览器中查看**
   - 可以使用浏览器的缩放功能
   - 适合查看细节

3. **在图形编辑器中打开**
   - Preview (macOS)
   - GIMP, Photoshop 等

### 如果仍然看不清

如果你的显示器分辨率很高，可以进一步调整:

```python
# 在 analyze_intent_behavior_target_graph.py 中修改:

# 1. 增大画布尺寸
plt.figure(figsize=(24, 20), dpi=100)

# 2. 增大字体
nx.draw_networkx_labels(..., font_size=11, ...)

# 3. 增大节点
node_size=6000  # for LLM
node_size=5000  # for Tool
node_size=4000  # for Target
```

## 📝 注意事项

### 字体回退机制

脚本会按顺序尝试字体:

1. 首先尝试 `Arial Unicode MS` (macOS推荐)
2. 如果不可用，尝试 `SimHei` (Windows)
3. 最后回退到 `DejaVu Sans`

### macOS vs Windows vs Linux

**macOS**:

- ✅ `Arial Unicode MS` 完美支持
- 无需额外配置

**Windows**:

- 需要系统安装 `SimHei` 字体
- 或使用其他中文字体如 `Microsoft YaHei`

**Linux**:

- 需要安装中文字体包
- 推荐: `WenQuanYi Micro Hei`

### 如何添加自定义字体

如果系统没有合适的中文字体:

```python
# 在脚本开头添加
import matplotlib.font_manager as fm

# 添加自定义字体路径
font_path = '/path/to/your/font.ttf'
fm.fontManager.addfont(font_path)
plt.rcParams['font.sans-serif'] = ['YourFontName']
```

## ✨ 总结

现在生成的图形应该:

- ✅ 完美显示中文
- ✅ 没有字符重叠
- ✅ 布局清晰易读
- ✅ 文件大小合理
- ✅ 加载速度快

如果还有任何显示问题，请检查:

1. 系统是否有支持中文的字体
2. 图形查看器是否支持PNG格式
3. 是否需要进一步增大画布尺寸
