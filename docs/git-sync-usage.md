# Git 同步脚本使用说明

这是一个交互式的 Git 同步工具,支持安全的拉取和推送操作,所有操作都需要人工二次确认。

## 功能特性

✅ **拉取代码** - 从 GitHub 拉取最新版本  
✅ **推送代码** - 推送本地更改到 GitHub  
✅ **二次确认** - 所有操作都需要人工确认  
✅ **安全检查** - 自动检测未提交的更改  
✅ **彩色输出** - 清晰易读的界面

## 使用方法

### 1. 拉取最新代码

```bash
./scripts/git-sync.sh pull
```

**流程:**

1. 显示当前仓库状态
2. 检查是否有未提交的更改(如有会警告)
3. 显示将要执行的操作
4. 要求确认后执行拉取
5. 显示拉取结果

### 2. 推送代码到远程

```bash
./scripts/git-sync.sh push
```

**流程:**

1. 显示当前仓库状态
2. 检查是否有未提交的更改
3. 如有未提交更改,提示是否先提交
4. 显示将要推送的提交
5. 要求确认后执行推送
6. 显示推送结果

### 3. 查看状态

```bash
./scripts/git-sync.sh status
```

显示当前分支、远程仓库和未提交的更改。

### 4. 显示帮助

```bash
./scripts/git-sync.sh help
```

## 使用示例

### 示例 1: 拉取代码

```bash
$ ./scripts/git-sync.sh pull

ℹ 准备从远程仓库拉取最新代码...

ℹ === Git 仓库状态 ===
  当前分支: yifan
  远程仓库: https://github.com/Wisley1998/gemini-cli.git

ℹ 将执行以下操作:
  1. git fetch origin
  2. git pull origin yifan

? 确认要拉取分支 'yifan' 的最新代码吗? (y/n): y
ℹ 正在获取远程更新...
ℹ 正在拉取代码...
✓ 代码拉取成功!
```

### 示例 2: 推送代码

```bash
$ ./scripts/git-sync.sh push

ℹ 准备推送代码到远程仓库...

ℹ === Git 仓库状态 ===
  当前分支: yifan
  远程仓库: https://github.com/Wisley1998/gemini-cli.git

⚠ 发现未提交的更改:
 M scripts/git-sync.sh

✗ 你有未提交的更改,请先提交后再推送!

? 是否现在提交这些更改? (y/n): y

ℹ 更改的文件:
 M scripts/git-sync.sh

? 请输入提交信息: Add git sync script
? 确认提交这些更改吗? (y/n): y
✓ 代码已提交

ℹ 准备推送的提交:
ff94ea2e Add git sync script

ℹ 将执行以下操作:
  git push origin yifan

? 确认要推送分支 'yifan' 到远程仓库吗? (y/n): y
ℹ 正在推送代码...
✓ 代码推送成功!
```

## 安全特性

### 🔒 二次确认机制

所有关键操作都需要明确的用户确认:

- 拉取前确认
- 推送前确认
- 提交前确认

### ⚠️ 冲突预警

- 拉取前检查本地未提交更改
- 推送前强制要求先提交
- 清晰显示将要执行的操作

### 📊 状态可见

- 显示当前分支
- 显示未提交的文件
- 显示将要推送的提交

## 快捷方式(可选)

你可以在 `package.json` 中添加快捷命令:

```json
{
  "scripts": {
    "git:pull": "./scripts/git-sync.sh pull",
    "git:push": "./scripts/git-sync.sh push",
    "git:status": "./scripts/git-sync.sh status"
  }
}
```

然后可以使用:

```bash
npm run git:pull
npm run git:push
npm run git:status
```

## 注意事项

⚠️ **推送时会自动跳过 pre-commit 检查**  
如果你的代码有 ESLint 错误,推送时会使用 `--no-verify` 标志跳过检查。建议在提交前先修复这些问题。

⚠️ **确保配置了正确的远程仓库**  
使用前请确认 `git remote -v` 显示的远程仓库地址正确。

⚠️ **敏感信息检查**  
GitHub 会自动扫描 token 等敏感信息,确保代码中没有硬编码的密钥。

## 故障排除

### 问题: 推送被拒绝

如果远程仓库有新的提交,你需要先拉取:

```bash
./scripts/git-sync.sh pull
./scripts/git-sync.sh push
```

### 问题: 拉取时出现冲突

如果拉取时遇到冲突:

1. 手动解决冲突的文件
2. 使用 `git add .` 标记为已解决
3. 使用 `git commit` 完成合并
4. 再次运行 `./scripts/git-sync.sh push`

### 问题: 未提交的更改被暂存

如果你不想提交某些文件:

```bash
git restore <file>  # 撤销对文件的修改
# 或
git reset <file>    # 取消暂存
```

## 高级用法

### 强制推送(谨慎使用)

如果需要强制推送,可以手动执行:

```bash
git push origin yifan --force
```

⚠️ 这会覆盖远程仓库的历史,请谨慎使用!

### 拉取其他分支

脚本会自动使用当前分支,如果需要切换分支:

```bash
git checkout main
./scripts/git-sync.sh pull
```

## 贡献

如果你想改进这个脚本,欢迎提交 PR!
