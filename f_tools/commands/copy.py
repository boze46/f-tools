"""Copy command implementation."""

import sys
from pathlib import Path
from typing import List

from ..ui.i18n import i18n
from ..ui.prompts import (
    OverwriteState, 
    confirm_directory_creation,
    confirm_file_overwrite,
    print_operation_info,
    print_success,
    print_error,
    handle_keyboard_interrupt
)
from ..ui.progress import ProgressManager
from ..utils.filesystem import (
    validate_paths,
    needs_progress_bar,
    ensure_parent_dirs,
    has_sufficient_space,
    get_file_size,
    MULTI_FILE_PROGRESS_THRESHOLD,
    FileSystemError,
    FileNotFoundError as FSFileNotFoundError,
    TargetIsFileError,
    SameFileError,
    TargetInSourceError
)


class CopyOperation:
    """Handles copy operations with all required features."""
    
    def __init__(self, auto_mkdir: bool = False, force: bool = False, 
                 verbose: bool = False, no_clobber: bool = False):
        """
        Initialize copy operation.
        
        Args:
            auto_mkdir: Automatically create target directories
            force: Force overwrite existing files
            verbose: Show verbose output
            no_clobber: Never overwrite existing files
        """
        self.auto_mkdir = auto_mkdir
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
    
    def execute_multiple(self, sources: List[str], target: str) -> bool:
        """
        Execute copy operation for multiple sources.
        
        Args:
            sources: List of source file or directory paths
            target: Target directory path
            
        Returns:
            True if all operations completed successfully
        """
        if not sources:
            return True
        
        target_path = Path(target)
        success_count = 0
        total_count = len(sources)
        
        # Ensure target directory exists once for all files
        if not self._ensure_target_directory(target_path):
            return False
        
        # Check total disk space needed for all sources
        if not self._check_total_disk_space(sources, target):
            print_error('error_disk_full')
            return False
        
        # Setup multi-file progress if needed
        show_multi_progress = total_count >= MULTI_FILE_PROGRESS_THRESHOLD
        if show_multi_progress and self.verbose:
            print(i18n.info(f"Copying {total_count} items..."))
        
        # Process each source file
        for i, source in enumerate(sources, 1):
            try:
                # Validate individual source path
                source_path, _ = validate_paths(source, target)
                
                # Check if destination file exists  
                final_dest = target_path / source_path.name
                if final_dest.exists():
                    should_overwrite = confirm_file_overwrite(final_dest, self.overwrite_state)
                    
                    if self.overwrite_state.should_quit():
                        # User chose to quit, stop processing
                        break
                        
                    if not should_overwrite:
                        if self.verbose:
                            print(i18n.warning(f"Skipped: {source_path.name}"))
                        continue
                
                # Perform the copy operation
                if self._perform_single_copy(source_path, target_path, i, total_count):
                    success_count += 1
                else:
                    if self.verbose:
                        print(i18n.error(f"Failed to copy: {source_path.name}"))
                
            except FSFileNotFoundError:
                print_error('error_file_not_found', path=source)
                continue
            except TargetIsFileError:
                print_error('error_target_is_file', path=target)
                return False  # This affects all files, so stop
            except SameFileError:
                if self.verbose:
                    print(i18n.warning(f"Skipped same file: {source}"))
                continue
            except TargetInSourceError:
                print_error('error_target_in_source')
                continue
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
                print(i18n.success(f"Successfully copied {success_count}/{total_count} items"))
            else:
                print(i18n.warning(f"Copied {success_count}/{total_count} items ({total_count - success_count} failed/skipped)"))
        
        return success_count > 0  # Success if at least one file copied
    
    def _check_total_disk_space(self, sources: List[str], target: str) -> bool:
        """
        Check if there's sufficient disk space for all sources.
        
        Args:
            sources: List of source paths
            target: Target directory path
            
        Returns:
            True if sufficient space available
        """
        target_path = Path(target)
        total_size_needed = 0
        
        for source in sources:
            try:
                source_path = Path(source)
                if source_path.exists():
                    # For copy operations, we always need full space
                    # (unlike move which can use rename on same filesystem)
                    size = get_file_size(source_path)
                    total_size_needed += size
            except (OSError, PermissionError):
                # Skip files we can't read, but don't fail the whole operation
                continue
        
        # Check if target has sufficient space
        from ..utils.filesystem import get_available_space
        available_space = get_available_space(target_path.parent if target_path.exists() else target_path)
        
        # Add 10% buffer for filesystem overhead
        required_space = int(total_size_needed * 1.1)
        
        return available_space >= required_space
    
    def _perform_single_copy(self, source_path: Path, target_path: Path, 
                           current_index: int, total_count: int) -> bool:
        """
        Perform copy operation for a single file in multi-file context.
        
        Args:
            source_path: Source path
            target_path: Target directory path
            current_index: Current file index (1-based)
            total_count: Total number of files
            
        Returns:
            True if copy succeeded
        """
        try:
            # Show operation info if verbose
            if self.verbose:
                if total_count > 1:
                    prefix = f"[{current_index}/{total_count}] "
                    print(i18n.info(f"{prefix}Copying {source_path.name} → {target_path.name}"))
                else:
                    print(i18n.info(i18n.t('copying', source=str(source_path), target=str(target_path))))
            
            # Determine if we need progress display (copy operations benefit more from progress)
            show_progress = needs_progress_bar(source_path) or get_file_size(source_path) > 10*1024*1024  # 10MB+
            
            # Perform copy with progress tracking
            with ProgressManager(show_progress=show_progress) as progress:
                progress.copy_with_progress(source_path, target_path)
            
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
    
    def _ensure_target_directory(self, target_path: Path) -> bool:
        """
        Ensure target directory exists.
        
        Args:
            target_path: Target directory path
            
        Returns:
            True if directory exists or was created
        """
        if target_path.exists():
            return True
        
        # Ask user for confirmation to create directory
        if not confirm_directory_creation(target_path, self.auto_mkdir):
            return False
        
        try:
            ensure_parent_dirs(target_path)
            target_path.mkdir(exist_ok=True)
            
            if self.verbose:
                print(i18n.success(i18n.t('dir_created', path=str(target_path))))
            
            return True
            
        except PermissionError:
            print_error('error_permission_denied', path=str(target_path))
            return False
        except Exception as e:
            print_error('error_file_not_found', path=str(e))
            return False


def copy_command(sources: List[str], target: str, auto_mkdir: bool = False,
                force: bool = False, verbose: bool = False, 
                no_clobber: bool = False) -> bool:
    """
    Execute copy command with given options.
    
    Args:
        sources: List of source file or directory paths
        target: Target directory path
        auto_mkdir: Automatically create target directories (-p)
        force: Force overwrite existing files (-f)
        verbose: Show verbose output (-v)
        no_clobber: Never overwrite existing files (-n)
        
    Returns:
        True if all operations completed successfully
    """
    operation = CopyOperation(
        auto_mkdir=auto_mkdir,
        force=force,
        verbose=verbose,
        no_clobber=no_clobber
    )
    
    return operation.execute_multiple(sources, target)