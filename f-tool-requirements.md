# F-Tool 文件操作工具 - 开发需求文档

## 项目概述

F-Tool 是一个统一的文件操作命令行工具，旨在解决 mv/cp/rm 等命令的使用痛点，特别是目标文件夹不存在的问题。

### 核心问题
用户在使用 `mv /tmp/A /parentfolder/testfolder/A` 时，经常遇到 `testfolder` 不存在的情况，需要先手动创建文件夹再移动文件。

### 设计目标
- 统一的文件操作接口
- 自动创建目标文件夹
- 美观的用户界面和进度提示
- 完善的错误处理和用户交互
- 国际化支持（中英文）

## 技术方案

### 推荐架构
**Python + Fish wrapper**
- **核心实现**：Python 脚本 (`~/.local/bin/f-tool`)
- **Shell 集成**：Fish 函数作为便捷入口
- **快捷键支持**：Fish 绑定 Alt+P 添加 `-p` 选项

### 技术选择理由
- **Python 优势**：丰富的文件操作库、进度条库（tqdm, rich）、跨平台支持
- **Fish 优势**：与用户环境完美集成、快捷键绑定、别名命令

## 功能规格

### 1. move 命令

#### 基本语法
```bash
f move <source> <target_directory> [options]
```

#### 参数说明
- `source`：源文件或文件夹路径
- `target_directory`：目标目录路径（**必须是目录，不能是文件**）

#### 核心逻辑
- `f move /tmp/A /home/user/documents/` → 将 A 移动到 documents 目录内
- 最终结果：`/home/user/documents/A`

#### 选项
- `-p, --mkdir`：自动创建不存在的目标目录
- `-f, --force`：强制覆盖已存在文件
- `-v, --verbose`：显示详细操作信息
- `-n, --no-clobber`：不覆盖已存在文件
- `-h, --help`：显示帮助信息

#### 行为规则

**目录创建逻辑**：
- **无 `-p`**：提示用户 "目标目录不存在，是否创建：{目录名} [Y/n]"
- **有 `-p`**：自动创建所有中间目录，并提示创建操作

**覆盖处理**：
```
文件已存在: /path/to/file.txt
[Y]是(默认) [n]否 [a]全部 [s]跳过全部 [q]退出: 
```
- Y/回车：覆盖当前文件
- n：跳过当前文件
- a：覆盖所有后续文件
- s：跳过所有后续文件
- q：退出操作

**进度显示**：
- 文件 >50MB：显示进度条
- 多个文件 >10个：显示总体进度
- 进度条格式：`████████████████████████████████ 100% (1.2GB/1.2GB) 45.3MB/s`

**错误处理**：
- 源文件不存在 → 错误提示
- 目标是文件而非目录 → 错误提示  
- 权限不足 → 错误提示

### 2. copy 命令

#### 基本语法
```bash
f copy <source> <target_directory> [options]
```

#### 行为
- 复制文件/文件夹到指定目录
- 支持与 move 相同的选项和交互逻辑

### 3. rename 命令

#### 基本语法
```bash
f rename <old_path> <new_name> [options]
```

#### 行为
- 在当前目录内重命名文件/文件夹
- `old_path` 可以是文件或文件夹
- `new_name` 只是新名称，不包含路径

### 4. remove 命令

#### 基本语法
```bash
f remove <path> [options]
```

#### 行为
- 使用 `trash-cli` 安全删除文件/文件夹
- 支持恢复功能（通过 trash 命令）

### 5. backup 命令

#### 基本语法
```bash
f backup <path> [options]
```

#### 行为
- 创建文件的备份版本
- `file.txt` → `file.txt.bak`
- `folder` → `folder.bak`

## 用户界面设计

### 国际化支持

#### 语言检测
- 基于 `$LANG` 环境变量自动检测
- 支持：`zh_CN.UTF-8`, `en_US.UTF-8`, `en_GB.UTF-8`

#### 消息示例
```bash
# 中文
目标目录不存在，是否创建: /path/to/dir ? [Y/n]
创建目录: /path/to/dir
移动 /tmp/file.txt → /home/user/documents/
文件已存在: /path/to/file.txt

# 英文  
Target directory does not exist, create: /path/to/dir ? [Y/n]
Creating directories: /path/to/dir
Moving /tmp/file.txt → /home/user/documents/
File exists: /path/to/file.txt
```

### 进度条设计

#### 小文件（<50MB）
```bash
Moving /tmp/file.txt → /home/user/documents/
```

#### 大文件（>50MB）
```bash
Moving /tmp/large_file.iso → /home/user/documents/
████████████████████████████████ 100% (4.2GB/4.2GB) 85.3MB/s
```

#### 多文件操作
```bash
Moving 25 files → /home/user/documents/
Overall: ████████████████████████████████ 100% (15/25 files) 
Current: ████████████████████████████████ 100% (1.2GB/1.2GB) 45.3MB/s
```

## 命令别名系统

### 主命令
```bash
f move   # 或 f mv
f copy   # 或 f cp  
f rename # 或 f ren
f remove # 或 f rm
f backup # 或 f bak
```

### 独立别名命令
```bash
fm    # = f move
fc    # = f copy
frn   # = f rename  
frm   # = f remove
fbak  # = f backup
```

### Fish 集成
- 主函数：`f` 作为 Fish 函数调用 Python 工具
- 别名函数：`fm`, `fc`, `frn`, `frm`, `fbak` 直接调用对应子命令
- 快捷键：`Alt+P` 在当前命令行添加 `-p` 选项

## 快捷键设计

### Alt+P 行为
参考 Fish 的 `Alt+S` (sudo) 设计：

1. **有当前命令**：在命令末尾添加 ` -p`
   ```bash
   f move /tmp/A /home/docs    # 按 Alt+P
   f move /tmp/A /home/docs -p
   ```

2. **无当前命令且上一条是 f 命令**：复制上一条命令并添加 `-p`
   ```bash
   $ f move /tmp/A /home/docs   # 执行失败
   $ _                          # 按 Alt+P  
   $ f move /tmp/A /home/docs -p
   ```

## 实现细节

### 文件移动策略

#### 小文件（<50MB）
```python
shutil.move(source, target)
```

#### 大文件（>50MB）
```python
# 使用 tqdm 显示进度
with tqdm(total=file_size, unit='B', unit_scale=True) as pbar:
    shutil.move(source, target)
```

#### 跨文件系统移动
```python
# 自动检测并使用 copy + remove
if not same_filesystem(source, target):
    shutil.copy2(source, target)
    os.remove(source)
```

### 状态管理

#### 覆盖处理状态
```python
class OverwriteState:
    PROMPT = 0      # 每次询问
    ALL = 1         # 覆盖全部  
    SKIP_ALL = 2    # 跳过全部
    QUIT = 3        # 退出操作
```

### 错误处理

#### 常见错误
- `FileNotFoundError`：源文件不存在
- `IsADirectoryError`：目标是文件但期望目录
- `PermissionError`：权限不足
- `OSError`：磁盘空间不足等系统错误

#### 错误消息格式
```python
def format_error(error_type: str, path: str, lang: str = "en") -> str:
    messages = {
        "en": {
            "file_not_found": f"Error: File not found: {path}",
            "target_is_file": f"Error: Target must be directory: {path}",
            "permission_denied": f"Error: Permission denied: {path}"
        },
        "zh": {
            "file_not_found": f"错误：文件不存在：{path}",  
            "target_is_file": f"错误：目标必须是目录：{path}",
            "permission_denied": f"错误：权限不足：{path}"
        }
    }
    return messages[lang][error_type]
```

## 项目结构

```
f-tool/
├── f-tool.py              # Python 主程序
├── f_tool/                # Python 模块
│   ├── __init__.py
│   ├── commands/          # 命令实现
│   │   ├── __init__.py
│   │   ├── move.py
│   │   ├── copy.py
│   │   ├── rename.py
│   │   ├── remove.py
│   │   └── backup.py
│   ├── ui/                # 用户界面
│   │   ├── __init__.py
│   │   ├── progress.py    # 进度条
│   │   ├── prompts.py     # 交互提示
│   │   └── i18n.py        # 国际化
│   └── utils/             # 工具函数
│       ├── __init__.py
│       ├── filesystem.py  # 文件系统操作
│       └── validation.py  # 参数验证
└── fish/                  # Fish Shell 集成
    ├── f.fish             # 主函数
    └── aliases.fish       # 别名命令
```

## 安装部署

### Python 工具
```bash
# 安装到用户 bin 目录
cp f-tool.py ~/.local/bin/f-tool
chmod +x ~/.local/bin/f-tool
```

### Fish 集成
```bash
# 复制到 Fish 配置目录  
cp fish/*.fish ~/.config/fish/conf.d/
```

### 依赖要求
```python
# Python 标准库
import shutil
import pathlib  
import argparse
import os
import sys

# 第三方库
import tqdm      # 进度条
import rich      # 终端美化 (可选)
```

## 测试用例

### move 命令测试

#### 基本功能
```bash
# 测试 1: 基本移动
f move /tmp/test.txt /home/user/documents/

# 测试 2: 目录不存在 (无 -p)
f move /tmp/test.txt /home/user/new_folder/

# 测试 3: 自动创建目录 (有 -p)  
f move /tmp/test.txt /home/user/new_folder/ -p

# 测试 4: 文件覆盖处理
f move /tmp/test.txt /home/user/documents/  # documents 中已有 test.txt

# 测试 5: 大文件进度显示
f move /tmp/large_file.iso /home/user/downloads/
```

#### 错误情况
```bash
# 测试 6: 源文件不存在
f move /tmp/nonexistent.txt /home/user/documents/

# 测试 7: 目标是文件
f move /tmp/test.txt /home/user/.bashrc

# 测试 8: 权限不足  
f move /tmp/test.txt /root/
```

## 扩展计划

### 未来功能
- **日志记录**：`f history` 查看操作历史
- **撤销功能**：`f undo` 撤销上一次操作
- **配置文件**：用户自定义设置
- **插件系统**：支持自定义操作
- **云存储集成**：支持云盘操作

### 性能优化
- **并行处理**：多文件操作支持并行
- **增量同步**：智能跳过相同文件
- **压缩传输**：跨网络移动时使用压缩

---

## 开发优先级

1. **P0 (必须)**：move 命令基本功能
2. **P1 (重要)**：进度条、国际化、错误处理
3. **P2 (有用)**：copy, rename, remove, backup 命令
4. **P3 (扩展)**：快捷键绑定、别名命令
5. **P4 (未来)**：日志、撤销、配置等高级功能

此文档为 f-tool 的完整需求规格，可供 AI 和开发者理解项目需求并实施开发。