# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

F-Tools is a unified file operation CLI tool that solves common pain points with standard `mv`/`cp`/`rm` commands, particularly the issue of target directories not existing. It's built with Python 3.12+ using `tqdm` for progress bars and `send2trash` for safe deletion.

## Development Commands

### Running the Application
```bash
# Development mode with uv (recommended)
uv run f-tools --help
uv run python -m f_tools.main move file.txt target/

# Alternative: Direct Python execution
python -m f_tools.main --help
```

### Building and Distribution
```bash
# Build wheel package
uv build

# Install from source
uv sync
pip install dist/f_tools-0.1.0-py3-none-any.whl
```

### Testing Commands
```bash
# Manual testing examples
echo "test" > /tmp/test.txt
uv run f-tools move /tmp/test.txt /tmp/target/ -p
uv run f-tools rename /tmp/file.txt new_name.txt
uv run f-tools backup /tmp/important.txt
```

## Architecture Overview

### Core Module Structure
```
f_tools/
├── main.py              # CLI entry point with argparse subcommands
├── commands/            # Command implementations
│   ├── move.py         # Move files with auto-mkdir
│   ├── copy.py         # Copy with progress display
│   ├── backup.py       # In-place backup with smart naming
│   └── rename.py       # Same-directory renaming
├── ui/                 # User interface components
│   ├── i18n.py         # Internationalization (zh/en auto-detect)
│   ├── progress.py     # Progress bars for large/multiple files
│   └── prompts.py      # Interactive confirmations
└── utils/              # Core utilities
    └── filesystem.py   # Path validation, disk space checks
```

### Command Architecture Pattern
Each command follows a consistent pattern:
1. **Operation Class**: Handles state management and business logic
2. **Public Function**: Entry point called from main.py
3. **Shared Components**: All commands use common UI/filesystem utilities

### Progress Display Logic
- Single files >32MB: Show progress bar with tqdm
- Multiple files ≥5: Show item-by-item progress
- Cross-filesystem moves: Automatic copy+delete with space validation

### Internationalization System
- Auto-detects language from `$LANG` environment variable
- Supports Chinese (zh) and English (en) with fallback
- Color-coded terminal output using ANSI codes

### Error Handling Strategy
- Custom exceptions in `filesystem.py` for different error types
- Consistent user-facing error messages through i18n system
- Graceful handling of permission errors, disk space, path conflicts

## Key Design Principles

### User Experience Focus
- Auto-creates target directories when missing (with confirmation)
- Interactive file overwrite handling (Y/n/a/s/q options)
- Clear operation feedback ("重命名：old.txt → new.txt")

### File Operation Safety
- Path validation prevents dangerous operations (e.g., moving parent into child)
- Disk space validation before large operations
- Atomic operations where possible (especially rename)

### Command Line Interface
- Consistent options across commands: `-f` (force), `-v` (verbose), `-n` (no-clobber), `-p` (mkdir)
- Command aliases: `mv`/`move`, `cp`/`copy`, `bak`/`backup`, `ren`/`rename`
- Argument validation with helpful error messages

## Implementation Notes

### Adding New Commands
1. Create command module in `f_tools/commands/`
2. Follow the Operation class pattern (see `rename.py` as reference)
3. Add argument parser in `main.py` create_parser()
4. Add command handling in `main()` function
5. Update `commands/__init__.py` exports

### Progress Thresholds
- Large file threshold: 32MB (`SINGLE_FILE_PROGRESS_THRESHOLD`)
- Multi-file threshold: 5 files (`MULTI_FILE_PROGRESS_THRESHOLD`)

### Path Handling
- Uses `pathlib.Path` throughout for cross-platform compatibility
- Resolves all paths to absolute before operations
- Validates source exists and target constraints before execution