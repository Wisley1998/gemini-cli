# SWE-bench 任务 Prompt 文件夹

这个文件夹包含从 SWE-bench 数据集提取的任务信息,每个任务都被格式化为独立的 prompt 文件。

## 📁 文件结构

```
swe-bench-prompts/
├── README.md                    # 本说明文件
├── INDEX.md                     # 任务索引
├── prompt_001_*.txt            # 任务 #1 的 prompt
├── prompt_002_*.txt            # 任务 #2 的 prompt
├── prompt_003_*.txt            # 任务 #3 的 prompt
└── ...
```

## 📋 每个 Prompt 文件包含的内容

每个 prompt 文件都包含完整的任务信息:

1. **任务基本信息**
   - 任务 ID
   - GitHub 仓库
   - 基础提交 SHA
   - 版本号
   - 创建时间

2. **相关链接**
   - GitHub 仓库完整链接
   - Issue/PR 完整链接 (直接可点击)

3. **问题描述**
   - 详细的 bug 描述或功能需求
   - 复现步骤
   - 期望行为

4. **测试要求**
   - 需要通过的测试 (FAIL_TO_PASS)
   - 需要保持通过的测试 (PASS_TO_PASS)

5. **参考解决方案**
   - 官方的 patch (代码修改)
   - 测试代码补丁

6. **任务要求**
   - 结构化的任务执行步骤

## 🚀 使用方法

### 方式 1: 直接使用 prompt 文件

直接打开任何 `prompt_*.txt` 文件,将内容复制到你的 AI 助手中:

```bash
cat prompt_001_astropy__astropy-12907.txt
```

### 方式 2: 使用 gemini-cli

如果你正在使用 gemini-cli,可以直接传入 prompt 文件:

```bash
gemini < swe-bench-prompts/prompt_001_astropy__astropy-12907.txt
```

### 方式 3: 批量处理

你可以编写脚本批量处理所有任务:

```bash
for file in swe-bench-prompts/prompt_*.txt; do
    echo "Processing $file..."
    gemini < "$file" > "results/$(basename $file .txt)_result.txt"
done
```

## 🔧 重新生成 Prompt 文件

如果你想提取不同数量的任务或使用不同的数据集,可以使用根目录下的 `extract-swe-bench-prompts.py` 脚本:

### 提取前 5 个任务 (默认)

```bash
python extract-swe-bench-prompts.py --limit 5
```

### 提取前 20 个任务

```bash
python extract-swe-bench-prompts.py --limit 20
```

### 使用完整的 SWE-bench 数据集 (而不是 Lite 版本)

```bash
python extract-swe-bench-prompts.py --dataset princeton-nlp/SWE-bench --limit 50
```

### 指定输出目录

```bash
python extract-swe-bench-prompts.py --limit 10 --output-dir ./my-custom-prompts
```

### 查看所有选项

```bash
python extract-swe-bench-prompts.py --help
```

## 📊 数据集信息

- **当前数据集**: princeton-nlp/SWE-bench_Lite
- **数据集分割**: test
- **任务总数**: 300 个任务
- **已提取**: 5 个任务

### 可用的 SWE-bench 数据集

1. `princeton-nlp/SWE-bench_Lite` - 精简版,包含 300 个高质量任务
2. `princeton-nlp/SWE-bench` - 完整版,包含 2,294 个任务
3. `SWE-bench/SWE-bench_Verified` - 验证版
4. `SWE-bench/SWE-smith` - 52,000+ 个任务的扩展集

## 📝 示例任务

查看 `INDEX.md` 文件获取所有任务的列表和概述。

### 已提取的任务

1. **astropy\_\_astropy-12907** - 修复 separability_matrix 对嵌套 CompoundModels 的计算错误
   - Issue: https://github.com/astropy/astropy/issues/12907

2. **astropy\_\_astropy-14182** - 支持 RestructuredText 输出中的 header_rows
   - Issue: https://github.com/astropy/astropy/issues/14182

3. **astropy\_\_astropy-14365** - 修复 QDP 格式大小写敏感问题
   - Issue: https://github.com/astropy/astropy/issues/14365

4. **astropy\_\_astropy-14995**
   - Issue: https://github.com/astropy/astropy/issues/14995

5. **astropy\_\_astropy-6938** - 修复 io.fits 中 D 指数的问题
   - Issue: https://github.com/astropy/astropy/issues/6938

## 🔗 相关资源

- [SWE-bench 官方仓库](https://github.com/SWE-bench/SWE-bench)
- [SWE-bench 论文](https://arxiv.org/abs/2310.06770)
- [SWE-bench 排行榜](https://www.swebench.com/)

## ⚙️ 依赖要求

生成这些 prompt 文件需要以下 Python 库:

```bash
pip install datasets
```

## 📄 许可

这些 prompt 文件是从 SWE-bench 数据集提取的,遵循 SWE-bench 的许可条款。
