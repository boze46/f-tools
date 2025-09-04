"""Internationalization module for F-Tool."""

import os
import locale
from typing import Dict, Any


class I18n:
    """Internationalization support for F-Tool."""
    
    # ANSI color codes for terminal output
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    END = '\033[0m'
    
    def __init__(self):
        self.lang = self._detect_language()
        
    def _detect_language(self) -> str:
        """Detect system language from environment variables."""
        lang = os.environ.get('LANG', 'en_US.UTF-8')
        if lang.startswith('zh'):
            return 'zh'
        return 'en'
    
    def t(self, key: str, **kwargs) -> str:
        """Translate message key with optional formatting parameters."""
        messages = self._get_messages()
        message = messages.get(self.lang, {}).get(key, messages['en'].get(key, key))
        
        if kwargs:
            try:
                return message.format(**kwargs)
            except (KeyError, ValueError):
                return message
        return message
    
    def error(self, message: str) -> str:
        """Format error message with color."""
        return f"{self.RED}{message}{self.END}"
    
    def success(self, message: str) -> str:
        """Format success message with color."""
        return f"{self.GREEN}{message}{self.END}"
    
    def warning(self, message: str) -> str:
        """Format warning message with color."""
        return f"{self.YELLOW}{message}{self.END}"
    
    def info(self, message: str) -> str:
        """Format info message with color."""
        return f"{self.CYAN}{message}{self.END}"
    
    def _get_messages(self) -> Dict[str, Dict[str, str]]:
        """Get all translated messages."""
        return {
            'en': {
                # File operations
                'moving': 'Moving {source} → {target}',
                'copying': 'Copying {source} → {target}',
                'backing_up': 'Backing up {source} → {target}',
                'move_complete': 'Move completed successfully',
                'copy_complete': 'Copy completed successfully',
                'backup_complete': 'Backup completed successfully',
                
                # Directory creation
                'dir_not_exist': 'Target directory does not exist, create: {path} ? [Y/n]',
                'creating_dirs': 'Creating directories: {path}',
                'dir_created': 'Directory created: {path}',
                
                # File conflicts
                'file_exists': 'File exists: {path}',
                'overwrite_prompt': '[Y]Yes(default) [n]No [a]All [s]Skip all [q]Quit: ',
                
                # Errors
                'error_file_not_found': 'Error: File not found: {path}',
                'error_target_is_file': 'Error: Target must be directory: {path}',
                'error_permission_denied': 'Error: Permission denied: {path}',
                'error_disk_full': 'Error: Insufficient disk space',
                'error_same_file': 'Error: Source and target are the same file',
                'error_target_in_source': 'Error: Target directory is inside source directory',
                
                # Progress
                'progress_files': 'Moving {current}/{total} files',
                'operation_cancelled': 'Operation cancelled',
            },
            'zh': {
                # File operations  
                'moving': '移动 {source} → {target}',
                'copying': '复制 {source} → {target}',
                'backing_up': '备份 {source} → {target}',
                'move_complete': '移动完成',
                'copy_complete': '复制完成',
                'backup_complete': '备份完成',
                
                # Directory creation
                'dir_not_exist': '目标目录不存在，是否创建: {path} ? [Y/n]',
                'creating_dirs': '创建目录: {path}',
                'dir_created': '目录已创建: {path}',
                
                # File conflicts
                'file_exists': '文件已存在: {path}',
                'overwrite_prompt': '[Y]是(默认) [n]否 [a]全部 [s]跳过全部 [q]退出: ',
                
                # Errors
                'error_file_not_found': '错误：文件不存在：{path}',
                'error_target_is_file': '错误：目标必须是目录：{path}',
                'error_permission_denied': '错误：权限不足：{path}',
                'error_disk_full': '错误：磁盘空间不足',
                'error_same_file': '错误：源文件和目标文件相同',
                'error_target_in_source': '错误：目标目录在源目录内部',
                
                # Progress
                'progress_files': '移动 {current}/{total} 个文件',
                'operation_cancelled': '操作已取消',
            }
        }


# Global instance
i18n = I18n()