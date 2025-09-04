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

### 方式一：从 Release 安装（推荐）

下载预构建的包并安装：

```bash
# 下载 wheel 文件
wget https://github.com/boze46/f-tools/releases/latest/download/f_tools-0.1.0-py3-none-any.whl

# 安装（推荐使用 pipx 进行全局安装）
pipx install f_tools-0.1.0-py3-none-any.whl

# 或使用 pip 安装
pip install f_tools-0.1.0-py3-none-any.whl

# 使用命令
f-tools --help

# 创建别名（可选）
echo 'alias f="f-tools"' >> ~/.bashrc
source ~/.bashrc
```

### 方式二：从源码安装

```bash
# 克隆项目
git clone https://github.com/boze46/f-tools.git
cd f-tools

# 构建并安装
uv build
pip install dist/f_tools-0.1.0-py3-none-any.whl

# 使用命令
f-tools --help
```

### 方式三：开发模式（使用 uv）

```bash
# 克隆项目
git clone https://github.com/boze46/f-tools.git
cd f-tools

# 使用 uv 安装依赖并运行
uv sync
uv run f-tools --help
```

### 方式四：使用 Python

```bash
# 克隆项目
git clone https://github.com/boze46/f-tools.git
cd f-tools

# 安装依赖
pip install tqdm send2trash

# 运行
python -m f_tools.main --help
```

### 创建快捷方式（可选）

```bash
# 如果通过方式一安装，推荐创建别名
echo 'alias f="f-tools"' >> ~/.bashrc
source ~/.bashrc

# 如果使用开发模式，可以创建以下别名
# 使用 uv 的别名
echo 'alias f="uv --directory /path/to/f-tools run f-tools"' >> ~/.bashrc

# 或使用 Python 的别名
echo 'alias f="cd /path/to/f-tools && python -m f_tools.main"' >> ~/.bashrc
source ~/.bashrc
```

## 命令使用指南

### 1. 移动文件（move/mv）

```bash
# 基本移动
f-tools move file.txt target/

# 多文件移动
f-tools move file1.txt file2.txt file3.txt target/
f-tools move *.txt target/

# 自动创建目标目录
f-tools move file.txt /new/path/ -p

# 强制覆盖 / 跳过覆盖
f-tools move file.txt target/ -f        # 强制覆盖
f-tools move file.txt target/ -n        # 从不覆盖

# 详细输出
f-tools move file.txt target/ -v
```

**解决的痛点：**
```bash
# 传统方式
mv file.txt /new/path/           # 报错：目录不存在
mkdir -p /new/path               # 手动创建
mv file.txt /new/path/           # 再次执行

# F-Tool 方式
f-tools move file.txt /new/path/ -p    # 一步完成
```

### 2. 复制文件（copy/cp）

```bash
# 基本复制（源文件保留）
f-tools copy file.txt target/

# 目录复制（默认递归）
f-tools copy project/ backup_location/

# 多文件复制
f-tools copy *.txt documents/

# 自动创建目录
f-tools copy file.txt /backup/today/ -p
```

**特点：**
- 目录复制默认递归，无需 `-r` 参数
- 支持与 move 相同的所有选项
- 更严格的磁盘空间检查

### 3. 备份文件（backup/bak）

```bash
# 单文件备份
f-tools backup important.txt           # → important.txt.bak

# 目录备份
f-tools backup project/                # → project.bak

# 多文件备份
f-tools backup *.py config.json

# 智能避免冲突
f-tools backup file.txt                # → file.txt.bak
f-tools backup file.txt                # → file.txt.bak2
f-tools backup file.txt                # → file.txt.bak3
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
f-tools move   ≡ f-tools mv      # 移动文件
f-tools copy   ≡ f-tools cp      # 复制文件  
f-tools backup ≡ f-tools bak     # 备份文件
```

## 智能交互

### 目录创建确认

```bash
$ f-tools move file.txt /new/path/
目标目录不存在，是否创建: /new/path ? [Y/n] y
创建目录: /new/path
移动 file.txt → /new/path
```

### 文件覆盖选择

```bash
$ f-tools copy file.txt existing/
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