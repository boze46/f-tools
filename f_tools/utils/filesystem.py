"""Filesystem utilities for F-Tool."""

import os
import stat
import shutil
from pathlib import Path
from typing import Tuple, Optional


# Configuration constants
SINGLE_FILE_PROGRESS_THRESHOLD = 32 * 1024 * 1024  # 32MB
MULTI_FILE_PROGRESS_THRESHOLD = 5  # 5 files


class FileSystemError(Exception):
    """Base exception for filesystem operations."""
    pass


class FileNotFoundError(FileSystemError):
    """Source file not found."""
    pass


class TargetIsFileError(FileSystemError):
    """Target must be directory but is a file."""
    pass


class SameFileError(FileSystemError):
    """Source and target are the same file."""
    pass


class TargetInSourceError(FileSystemError):
    """Target directory is inside source directory."""
    pass


def validate_paths(source: str, target: str) -> Tuple[Path, Path]:
    """
    Validate source and target paths.
    
    Args:
        source: Source file or directory path
        target: Target directory path
        
    Returns:
        Tuple of (source_path, target_path)
        
    Raises:
        FileNotFoundError: If source doesn't exist
        TargetIsFileError: If target exists and is a file
        SameFileError: If source and target are the same
        TargetInSourceError: If target is inside source directory
    """
    source_path = Path(source).resolve()
    target_path = Path(target).resolve()
    
    # Check if source exists
    if not source_path.exists():
        raise FileNotFoundError(f"Source does not exist: {source}")
    
    # Check if target is a file (should be directory)
    if target_path.exists() and target_path.is_file():
        raise TargetIsFileError(f"Target must be directory: {target}")
    
    # Calculate final destination
    final_dest = target_path / source_path.name
    
    # Check if source and destination are the same
    if source_path == final_dest:
        raise SameFileError(f"Source and target are the same: {source}")
    
    # Check if target is inside source (for directory moves)
    if source_path.is_dir():
        try:
            final_dest.relative_to(source_path)
            raise TargetInSourceError(f"Target directory is inside source: {target}")
        except ValueError:
            # target is not inside source, which is good
            pass
    
    return source_path, target_path


def get_file_size(path: Path) -> int:
    """
    Get total size of file or directory.
    
    Args:
        path: File or directory path
        
    Returns:
        Size in bytes
    """
    if path.is_file():
        return path.stat().st_size
    
    total_size = 0
    try:
        for item in path.rglob('*'):
            if item.is_file():
                try:
                    total_size += item.stat().st_size
                except (OSError, PermissionError):
                    # Skip files we can't read
                    continue
    except (OSError, PermissionError):
        # If we can't read the directory, return 0
        pass
    
    return total_size


def count_items(path: Path) -> int:
    """
    Count total number of files and directories.
    
    Args:
        path: Directory path
        
    Returns:
        Number of items
    """
    if path.is_file():
        return 1
    
    count = 0
    try:
        for _ in path.rglob('*'):
            count += 1
    except (OSError, PermissionError):
        # If we can't read the directory, return 1 for the directory itself
        count = 1
    
    return count


def needs_progress_bar(path: Path, file_count: int = 1) -> bool:
    """
    Determine if operation needs a progress bar.
    
    Args:
        path: Source path
        file_count: Number of files being processed
        
    Returns:
        True if progress bar should be shown
    """
    # Show progress for multiple files
    if file_count >= MULTI_FILE_PROGRESS_THRESHOLD:
        return True
    
    # Show progress for large single files
    if file_count == 1 and get_file_size(path) >= SINGLE_FILE_PROGRESS_THRESHOLD:
        return True
    
    return False


def same_filesystem(path1: Path, path2: Path) -> bool:
    """
    Check if two paths are on the same filesystem.
    
    Args:
        path1: First path
        path2: Second path
        
    Returns:
        True if on same filesystem
    """
    try:
        stat1 = path1.stat() if path1.exists() else path1.parent.stat()
        stat2 = path2.stat() if path2.exists() else path2.parent.stat()
        return stat1.st_dev == stat2.st_dev
    except (OSError, AttributeError):
        # On Windows or if stat fails, assume different filesystems
        return False


def ensure_parent_dirs(target_path: Path) -> None:
    """
    Ensure parent directories exist.
    
    Args:
        target_path: Target path whose parent directories should be created
        
    Raises:
        PermissionError: If cannot create directories
    """
    target_path.parent.mkdir(parents=True, exist_ok=True)


def safe_move(source: Path, target: Path) -> None:
    """
    Safely move a file or directory.
    
    Args:
        source: Source path
        target: Target directory path
        
    Raises:
        PermissionError: If permission denied
        OSError: If move fails
    """
    final_dest = target / source.name
    
    # Use shutil.move for cross-platform compatibility
    shutil.move(str(source), str(final_dest))


def get_available_space(path: Path) -> int:
    """
    Get available disk space at path.
    
    Args:
        path: Path to check
        
    Returns:
        Available bytes
    """
    try:
        statvfs = shutil.disk_usage(str(path))
        return statvfs.free
    except (OSError, AttributeError):
        # If we can't determine, assume sufficient space
        return float('inf')


def has_sufficient_space(source: Path, target: Path) -> bool:
    """
    Check if target has sufficient space for source.
    
    Args:
        source: Source path
        target: Target path
        
    Returns:
        True if sufficient space
    """
    if same_filesystem(source, target):
        # Move on same filesystem doesn't require additional space
        return True
    
    source_size = get_file_size(source)
    available_space = get_available_space(target)
    
    # Add 10% buffer for filesystem overhead
    required_space = int(source_size * 1.1)
    
    return available_space >= required_space