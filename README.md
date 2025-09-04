# F-Tool

统一的文件操作命令行工具，解决 `mv`/`cp`/`rm` 等命令的使用痛点，特别是目标文件夹不存在的问题。

## 核心特性

- **自动创建目录** - 目标目录不存在时自动创建，无需手动 `mkdir`
- **大文件进度显示** - 大文件和批量操作显示实时进度条
- **安全删除** - 使用垃圾箱而非直接删除，支持恢复
- **智能文件覆盖处理** - 文件冲突时提供多种选择
- **中英文界面支持** - 根据系统语言自动切换
- **多文件操作** - 支持通配符和批量文件处理

基于 Python 3.12+ 开发，使用 `tqdm` 和 `send2trash` 库。

## 安装和运行

### 方式一：使用 uv（推荐）

```bash
# 克隆项目
git clone <repository-url>
cd f

# 使用 uv 安装依赖并运行
uv sync
uv run python -m f_tool.main --help
```

### 方式二：使用 Python

```bash
# 克隆项目
git clone <repository-url>
cd f

# 安装依赖
pip install tqdm send2trash

# 运行
python -m f_tool.main --help
```

### 创建快捷方式（可选）

在 `~/.bashrc` 或 `~/.zshrc` 中添加别名：

```bash
# 使用 uv 的别名
alias f='cd /path/to/f && uv run python -m f_tool.main'

# 或使用 Python 的别名
alias f='cd /path/to/f && python -m f_tool.main'
```

## 命令使用指南

### 1. 移动文件（move/mv）

```bash
# 基本移动
f move file.txt target/

# 多文件移动
f move file1.txt file2.txt file3.txt target/
f move *.txt target/

# 自动创建目标目录
f move file.txt /new/path/ -p

# 强制覆盖 / 跳过覆盖
f move file.txt target/ -f        # 强制覆盖
f move file.txt target/ -n        # 从不覆盖

# 详细输出
f move file.txt target/ -v
```

**解决的痛点：**
```bash
# 传统方式
mv file.txt /new/path/           # 报错：目录不存在
mkdir -p /new/path               # 手动创建
mv file.txt /new/path/           # 再次执行

# F-Tool 方式
f move file.txt /new/path/ -p    # 一步完成
```

### 2. 复制文件（copy/cp）

```bash
# 基本复制（源文件保留）
f copy file.txt target/

# 目录复制（默认递归）
f copy project/ backup_location/

# 多文件复制
f copy *.txt documents/

# 自动创建目录
f copy file.txt /backup/today/ -p
```

**特点：**
- 目录复制默认递归，无需 `-r` 参数
- 支持与 move 相同的所有选项
- 更严格的磁盘空间检查

### 3. 备份文件（backup/bak）

```bash
# 单文件备份
f backup important.txt           # → important.txt.bak

# 目录备份
f backup project/                # → project.bak

# 多文件备份
f backup *.py config.json

# 智能避免冲突
f backup file.txt                # → file.txt.bak
f backup file.txt                # → file.txt.bak2
f backup file.txt                # → file.txt.bak3
```

**特点：**
- 就地备份，无需指定目标目录
- 智能命名避免覆盖已有备份
- 支持批量备份操作

## 命令选项说明

### 通用选项

- `-p, --mkdir` - 自动创建不存在的目标目录
- `-f, --force` - 强制覆盖已存在的文件
- `-v, --verbose` - 显示详细操作信息
- `-n, --no-clobber` - 从不覆盖已存在的文件
- `-h, --help` - 显示帮助信息

### 别名命令

```bash
f move   ≡ f mv      # 移动文件
f copy   ≡ f cp      # 复制文件  
f backup ≡ f bak     # 备份文件
```

## 智能交互

### 目录创建确认

```bash
$ f move file.txt /new/path/
目标目录不存在，是否创建: /new/path ? [Y/n] y
创建目录: /new/path
移动 file.txt → /new/path
```

### 文件覆盖选择

```bash
$ f copy file.txt existing/
文件已存在: existing/file.txt
[Y]是(默认) [n]否 [a]全部 [s]跳过全部 [q]退出: a
```

- **Y** - 覆盖当前文件
- **n** - 跳过当前文件
- **a** - 覆盖所有后续文件
- **s** - 跳过所有后续文件
- **q** - 退出操作

### 进度显示

**单个大文件（>32MB）：**
```
Moving large_file.iso → /backup/
████████████████████████████████ 100% (4.2GB/4.2GB) 85.3MB/s
```

**多个文件（≥5个）：**
```
Moving 8 items...
[1/8] Moving file1.txt → target
[2/8] Moving file2.txt → target
...
Successfully moved 8/8 items
```

## 开发状态

🚧 **开发中** - 当前实现的功能：
- ✅ **move** - 完整实现，支持多文件和所有选项
- ✅ **copy** - 完整实现，默认递归复制
- ✅ **backup** - 完整实现，智能命名避免冲突
- 🔄 **rename** - 规划中
- 🔄 **remove** - 规划中

## 贡献

项目使用 Python 3.12+ 开发，欢迎提交 Issue 和 Pull Request。

## 许可证

[添加许可证信息]