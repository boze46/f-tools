"""Backup command implementation."""

import sys
from pathlib import Path
from typing import List

from ..ui.i18n import i18n
from ..ui.prompts import (
    OverwriteState, 
    confirm_file_overwrite,
    print_success,
    print_error,
    handle_keyboard_interrupt
)
from ..ui.progress import ProgressManager
from ..utils.filesystem import (
    get_file_size,
    needs_progress_bar,
    has_sufficient_space,
    MULTI_FILE_PROGRESS_THRESHOLD,
    FileSystemError,
    FileNotFoundError as FSFileNotFoundError
)


class BackupOperation:
    """Handles backup operations with intelligent naming."""
    
    def __init__(self, force: bool = False, verbose: bool = False, 
                 no_clobber: bool = False):
        """
        Initialize backup operation.
        
        Args:
            force: Force overwrite existing backup files
            verbose: Show verbose output
            no_clobber: Never overwrite existing backup files
        """
        self.force = force
        self.verbose = verbose
        self.no_clobber = no_clobber
        self.overwrite_state = OverwriteState()
        
        # Set initial overwrite state based on flags
        if force:
            from ..ui.prompts import OverwriteAction
            self.overwrite_state.action = OverwriteAction.OVERWRITE_ALL
        elif no_clobber:
            from ..ui.prompts import OverwriteAction
            self.overwrite_state.action = OverwriteAction.SKIP_ALL
    
    def execute_multiple(self, sources: List[str]) -> bool:
        """
        Execute backup operation for multiple sources.
        
        Args:
            sources: List of source file or directory paths
            
        Returns:
            True if all operations completed successfully
        """
        if not sources:
            return True
        
        success_count = 0
        total_count = len(sources)
        
        # Check total disk space needed for all sources
        if not self._check_total_disk_space(sources):
            print_error('error_disk_full')
            return False
        
        # Setup multi-file progress if needed
        show_multi_progress = total_count >= MULTI_FILE_PROGRESS_THRESHOLD
        if show_multi_progress and self.verbose:
            print(i18n.info(f"Creating {total_count} backups..."))
        
        # Process each source file
        for i, source in enumerate(sources, 1):
            try:
                source_path = Path(source)
                
                # Check if source exists
                if not source_path.exists():
                    print_error('error_file_not_found', path=source)
                    continue
                
                # Generate backup path
                backup_path = self._generate_backup_path(source_path)
                
                # Check if backup already exists
                if backup_path.exists():
                    should_overwrite = confirm_file_overwrite(backup_path, self.overwrite_state)
                    
                    if self.overwrite_state.should_quit():
                        # User chose to quit, stop processing
                        break
                        
                    if not should_overwrite:
                        if self.verbose:
                            print(i18n.warning(f"Skipped: {source_path.name}"))
                        continue
                
                # Perform the backup operation
                if self._perform_single_backup(source_path, backup_path, i, total_count):
                    success_count += 1
                else:
                    if self.verbose:
                        print(i18n.error(f"Failed to backup: {source_path.name}"))
                
            except PermissionError as e:
                print_error('error_permission_denied', path=str(e))
                continue
            except KeyboardInterrupt:
                handle_keyboard_interrupt()
                return False
            except Exception as e:
                print_error('error_file_not_found', path=str(e))
                continue
        
        # Show final summary
        if show_multi_progress and self.verbose:
            if success_count == total_count:
                print(i18n.success(f"Successfully created {success_count}/{total_count} backups"))
            else:
                print(i18n.warning(f"Created {success_count}/{total_count} backups ({total_count - success_count} failed/skipped)"))
        
        return success_count > 0  # Success if at least one backup created
    
    def _generate_backup_path(self, source_path: Path) -> Path:
        """
        Generate backup path with intelligent naming to avoid conflicts.
        
        Args:
            source_path: Source file or directory path
            
        Returns:
            Path for backup file/directory
        """
        base_backup = source_path.parent / f"{source_path.name}.bak"
        
        # If no conflict, use simple .bak suffix
        if not base_backup.exists():
            return base_backup
        
        # Find next available numbered backup
        counter = 2
        while True:
            numbered_backup = source_path.parent / f"{source_path.name}.bak{counter}"
            if not numbered_backup.exists():
                return numbered_backup
            counter += 1
            
            # Safety limit to prevent infinite loop
            if counter > 1000:
                raise RuntimeError(f"Too many backup files for {source_path}")
    
    def _check_total_disk_space(self, sources: List[str]) -> bool:
        """
        Check if there's sufficient disk space for all backups.
        
        Args:
            sources: List of source paths
            
        Returns:
            True if sufficient space available
        """
        total_size_needed = 0
        
        for source in sources:
            try:
                source_path = Path(source)
                if source_path.exists():
                    size = get_file_size(source_path)
                    total_size_needed += size
            except (OSError, PermissionError):
                # Skip files we can't read, but don't fail the whole operation
                continue
        
        # Check if we have sufficient space in the source directories
        # (backups are created in the same location as source files)
        checked_dirs = set()
        
        for source in sources:
            try:
                source_path = Path(source)
                if source_path.exists():
                    parent_dir = source_path.parent
                    if parent_dir in checked_dirs:
                        continue
                    
                    from ..utils.filesystem import get_available_space
                    available_space = get_available_space(parent_dir)
                    
                    # Add 10% buffer for filesystem overhead
                    required_space = int(total_size_needed * 1.1)
                    
                    if available_space < required_space:
                        return False
                    
                    checked_dirs.add(parent_dir)
                    
            except (OSError, PermissionError):
                continue
        
        return True
    
    def _perform_single_backup(self, source_path: Path, backup_path: Path, 
                             current_index: int, total_count: int) -> bool:
        """
        Perform backup operation for a single file.
        
        Args:
            source_path: Source path
            backup_path: Target backup path
            current_index: Current file index (1-based)
            total_count: Total number of files
            
        Returns:
            True if backup succeeded
        """
        try:
            # Show operation info if verbose
            if self.verbose:
                if total_count > 1:
                    prefix = f"[{current_index}/{total_count}] "
                    print(i18n.info(f"{prefix}Backing up {source_path.name} → {backup_path.name}"))
                else:
                    print(i18n.info(i18n.t('backing_up', source=str(source_path), target=str(backup_path))))
            
            # Determine if we need progress display
            show_progress = needs_progress_bar(source_path) or get_file_size(source_path) > 10*1024*1024  # 10MB+
            
            # Perform backup with progress tracking
            with ProgressManager(show_progress=show_progress) as progress:
                progress.backup_with_progress(source_path, backup_path)
            
            return True
            
        except PermissionError as e:
            print_error('error_permission_denied', path=str(e))
            return False
        except OSError as e:
            if "No space left on device" in str(e):
                print_error('error_disk_full')
            else:
                print_error('error_file_not_found', path=str(e))
            return False
        except Exception as e:
            print_error('error_file_not_found', path=str(e))
            return False


def backup_command(sources: List[str], force: bool = False, verbose: bool = False, 
                  no_clobber: bool = False) -> bool:
    """
    Execute backup command with given options.
    
    Args:
        sources: List of source file or directory paths to backup
        force: Force overwrite existing backup files (-f)
        verbose: Show verbose output (-v)
        no_clobber: Never overwrite existing backup files (-n)
        
    Returns:
        True if all operations completed successfully
    """
    operation = BackupOperation(
        force=force,
        verbose=verbose,
        no_clobber=no_clobber
    )
    
    return operation.execute_multiple(sources)