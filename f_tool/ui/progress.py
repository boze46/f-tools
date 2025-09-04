"""Progress display module using tqdm."""

import shutil
from pathlib import Path
from typing import Optional, Callable
from tqdm import tqdm

from ..ui.i18n import i18n
from ..utils.filesystem import get_file_size, same_filesystem


class ProgressManager:
    """Manages progress display for file operations."""
    
    def __init__(self, show_progress: bool = True):
        self.show_progress = show_progress
        self.current_pbar: Optional[tqdm] = None
        self.overall_pbar: Optional[tqdm] = None
    
    def move_with_progress(self, source: Path, target: Path, 
                          operation_desc: str = None) -> None:
        """
        Move file/directory with progress display.
        
        Args:
            source: Source path
            target: Target directory path
            operation_desc: Description for progress bar
        """
        if not self.show_progress:
            self._simple_move(source, target)
            return
        
        final_dest = target / source.name
        
        if source.is_file():
            self._move_file_with_progress(source, final_dest, operation_desc)
        else:
            self._move_directory_with_progress(source, final_dest, operation_desc)
    
    def copy_with_progress(self, source: Path, target: Path, 
                          operation_desc: str = None) -> None:
        """
        Copy file/directory with progress display.
        
        Args:
            source: Source path
            target: Target directory path
            operation_desc: Description for progress bar
        """
        if not self.show_progress:
            self._simple_copy(source, target)
            return
        
        final_dest = target / source.name
        
        if source.is_file():
            self._copy_file_with_progress(source, final_dest, operation_desc)
        else:
            self._copy_directory_with_progress(source, final_dest, operation_desc)
    
    def backup_with_progress(self, source: Path, backup_path: Path, 
                           operation_desc: str = None) -> None:
        """
        Backup file/directory with progress display.
        
        Args:
            source: Source path
            backup_path: Target backup path (full path including .bak suffix)
            operation_desc: Description for progress bar
        """
        if not self.show_progress:
            self._simple_backup(source, backup_path)
            return
        
        if source.is_file():
            self._backup_file_with_progress(source, backup_path, operation_desc)
        else:
            self._backup_directory_with_progress(source, backup_path, operation_desc)
    
    def _move_file_with_progress(self, source: Path, dest: Path, 
                               operation_desc: str = None) -> None:
        """Move single file with progress bar."""
        file_size = get_file_size(source)
        desc = operation_desc or i18n.t('moving', source=source.name, target=dest.parent.name)
        
        if same_filesystem(source, dest):
            # Simple rename on same filesystem - usually instant
            shutil.move(str(source), str(dest))
        else:
            # Cross-filesystem copy - show progress
            with tqdm(total=file_size, unit='B', unit_scale=True, 
                     desc=desc, leave=False) as pbar:
                self._copy_with_progress(source, dest, pbar)
                source.unlink()  # Remove source after successful copy
    
    def _move_directory_with_progress(self, source: Path, dest: Path,
                                    operation_desc: str = None) -> None:
        """Move directory with progress tracking."""
        if same_filesystem(source, dest):
            # Simple rename on same filesystem
            shutil.move(str(source), str(dest))
        else:
            # Cross-filesystem copy
            desc = operation_desc or i18n.t('moving', source=source.name, target=dest.parent.name)
            total_size = get_file_size(source)
            
            with tqdm(total=total_size, unit='B', unit_scale=True,
                     desc=desc, leave=False) as pbar:
                self._copy_tree_with_progress(source, dest, pbar)
                shutil.rmtree(str(source))  # Remove source after successful copy
    
    def _copy_with_progress(self, source: Path, dest: Path, pbar: tqdm) -> None:
        """Copy single file with progress updates."""
        with open(source, 'rb') as src, open(dest, 'wb') as dst:
            while True:
                chunk = src.read(64 * 1024)  # 64KB chunks
                if not chunk:
                    break
                dst.write(chunk)
                pbar.update(len(chunk))
    
    def _copy_tree_with_progress(self, source: Path, dest: Path, pbar: tqdm) -> None:
        """Copy directory tree with progress updates."""
        dest.mkdir(exist_ok=True)
        
        for item in source.rglob('*'):
            relative_path = item.relative_to(source)
            dest_item = dest / relative_path
            
            try:
                if item.is_dir():
                    dest_item.mkdir(exist_ok=True)
                elif item.is_file():
                    dest_item.parent.mkdir(parents=True, exist_ok=True)
                    with open(item, 'rb') as src, open(dest_item, 'wb') as dst:
                        while True:
                            chunk = src.read(64 * 1024)
                            if not chunk:
                                break
                            dst.write(chunk)
                            pbar.update(len(chunk))
                    
                    # Copy file metadata
                    shutil.copystat(str(item), str(dest_item))
            except (OSError, PermissionError) as e:
                # Skip files we can't copy, but continue with others
                pbar.write(f"Warning: Skipping {item}: {e}")
                continue
    
    def _simple_move(self, source: Path, target: Path) -> None:
        """Simple move without progress display."""
        final_dest = target / source.name
        shutil.move(str(source), str(final_dest))
    
    def _simple_copy(self, source: Path, target: Path) -> None:
        """Simple copy without progress display."""
        final_dest = target / source.name
        if source.is_file():
            shutil.copy2(str(source), str(final_dest))
        else:
            shutil.copytree(str(source), str(final_dest))
    
    def _copy_file_with_progress(self, source: Path, dest: Path, 
                               operation_desc: str = None) -> None:
        """Copy single file with progress bar."""
        file_size = get_file_size(source)
        desc = operation_desc or i18n.t('copying', source=source.name, target=dest.parent.name)
        
        # Copy operations always show progress for better user feedback
        with tqdm(total=file_size, unit='B', unit_scale=True, 
                 desc=desc, leave=False) as pbar:
            self._copy_with_progress(source, dest, pbar)
    
    def _copy_directory_with_progress(self, source: Path, dest: Path,
                                    operation_desc: str = None) -> None:
        """Copy directory with progress tracking."""
        desc = operation_desc or i18n.t('copying', source=source.name, target=dest.parent.name)
        total_size = get_file_size(source)
        
        with tqdm(total=total_size, unit='B', unit_scale=True,
                 desc=desc, leave=False) as pbar:
            self._copy_tree_with_progress(source, dest, pbar)
    
    def _simple_backup(self, source: Path, backup_path: Path) -> None:
        """Simple backup without progress display."""
        if source.is_file():
            shutil.copy2(str(source), str(backup_path))
        else:
            shutil.copytree(str(source), str(backup_path))
    
    def _backup_file_with_progress(self, source: Path, backup_path: Path, 
                                 operation_desc: str = None) -> None:
        """Backup single file with progress bar."""
        file_size = get_file_size(source)
        desc = operation_desc or i18n.t('backing_up', source=source.name, target=backup_path.name)
        
        # Backup operations always show progress for better user feedback
        with tqdm(total=file_size, unit='B', unit_scale=True, 
                 desc=desc, leave=False) as pbar:
            self._copy_with_progress(source, backup_path, pbar)
    
    def _backup_directory_with_progress(self, source: Path, backup_path: Path,
                                      operation_desc: str = None) -> None:
        """Backup directory with progress tracking."""
        desc = operation_desc or i18n.t('backing_up', source=source.name, target=backup_path.name)
        total_size = get_file_size(source)
        
        with tqdm(total=total_size, unit='B', unit_scale=True,
                 desc=desc, leave=False) as pbar:
            self._copy_tree_with_progress(source, backup_path, pbar)
    
    def setup_multi_file_progress(self, total_files: int, 
                                operation_desc: str = None) -> None:
        """Setup progress tracking for multiple files."""
        if not self.show_progress or total_files < 2:
            return
        
        desc = operation_desc or i18n.t('progress_files', current=0, total=total_files)
        self.overall_pbar = tqdm(total=total_files, desc=desc, position=0)
    
    def update_multi_file_progress(self, current_file: int, total_files: int,
                                 current_file_name: str = "") -> None:
        """Update multi-file progress."""
        if self.overall_pbar:
            desc = i18n.t('progress_files', current=current_file, total=total_files)
            if current_file_name:
                desc += f" - {current_file_name}"
            self.overall_pbar.set_description(desc)
            self.overall_pbar.update(1)
    
    def close_progress_bars(self) -> None:
        """Close all progress bars."""
        if self.current_pbar:
            self.current_pbar.close()
            self.current_pbar = None
        
        if self.overall_pbar:
            self.overall_pbar.close()
            self.overall_pbar = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_progress_bars()