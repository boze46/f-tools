"""Move command implementation."""

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
    count_items,
    FileSystemError,
    FileNotFoundError as FSFileNotFoundError,
    TargetIsFileError,
    SameFileError,
    TargetInSourceError
)


class MoveOperation:
    """Handles move operations with all required features."""
    
    def __init__(self, auto_mkdir: bool = False, force: bool = False, 
                 verbose: bool = False, no_clobber: bool = False):
        """
        Initialize move operation.
        
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
    
    def execute(self, source: str, target: str) -> bool:
        """
        Execute move operation.
        
        Args:
            source: Source file or directory path
            target: Target directory path
            
        Returns:
            True if operation completed successfully
        """
        try:
            # Validate paths
            source_path, target_path = validate_paths(source, target)
            
            # Check disk space
            if not has_sufficient_space(source_path, target_path):
                print_error('error_disk_full')
                return False
            
            # Ensure target directory exists
            if not self._ensure_target_directory(target_path):
                return False
            
            # Check if destination file exists
            final_dest = target_path / source_path.name
            if final_dest.exists():
                should_overwrite = confirm_file_overwrite(final_dest, self.overwrite_state)
                
                if self.overwrite_state.should_quit():
                    return False
                    
                if not should_overwrite:
                    if self.verbose:
                        print(i18n.warning(f"Skipped: {source_path.name}"))
                    return True
            
            # Perform the move operation
            return self._perform_single_move(source_path, target_path, 1, 1)
            
        except FSFileNotFoundError as e:
            print_error('error_file_not_found', path=source)
            return False
        except TargetIsFileError as e:
            print_error('error_target_is_file', path=target)
            return False
        except SameFileError as e:
            print_error('error_same_file')
            return False
        except TargetInSourceError as e:
            print_error('error_target_in_source')
            return False
        except PermissionError as e:
            print_error('error_permission_denied', path=str(e))
            return False
        except KeyboardInterrupt:
            handle_keyboard_interrupt()
            return False
        except Exception as e:
            print_error('error_file_not_found', path=str(e))
            return False
    
    def execute_multiple(self, sources: List[str], target: str) -> bool:
        """
        Execute move operation for multiple sources.
        
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
        
        # Setup multi-file progress if needed
        from ..utils.filesystem import MULTI_FILE_PROGRESS_THRESHOLD
        show_multi_progress = total_count >= MULTI_FILE_PROGRESS_THRESHOLD
        if show_multi_progress and self.verbose:
            print(i18n.info(f"Moving {total_count} items..."))
        
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
                
                # Perform the move operation
                if self._perform_single_move(source_path, target_path, i, total_count):
                    success_count += 1
                else:
                    if self.verbose:
                        print(i18n.error(f"Failed to move: {source_path.name}"))
                
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
                print(i18n.success(f"Successfully moved {success_count}/{total_count} items"))
            else:
                print(i18n.warning(f"Moved {success_count}/{total_count} items ({total_count - success_count} failed/skipped)"))
        
        return success_count > 0  # Success if at least one file moved
    
    def _perform_single_move(self, source_path: Path, target_path: Path, 
                           current_index: int, total_count: int) -> bool:
        """
        Perform move operation for a single file in multi-file context.
        
        Args:
            source_path: Source path
            target_path: Target directory path
            current_index: Current file index (1-based)
            total_count: Total number of files
            
        Returns:
            True if move succeeded
        """
        try:
            # Show operation info if verbose
            if self.verbose:
                if total_count > 1:
                    prefix = f"[{current_index}/{total_count}] "
                    print(i18n.info(f"{prefix}Moving {source_path.name} → {target_path.name}"))
                else:
                    print_operation_info(source_path, target_path, self.verbose)
            
            # Determine if we need progress display
            show_progress = needs_progress_bar(source_path) and total_count == 1
            
            # Perform move with progress tracking
            with ProgressManager(show_progress=show_progress) as progress:
                progress.move_with_progress(source_path, target_path)
            
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
    

def move_command(sources: List[str], target: str, auto_mkdir: bool = False,
                force: bool = False, verbose: bool = False, 
                no_clobber: bool = False) -> bool:
    """
    Execute move command with given options.
    
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
    operation = MoveOperation(
        auto_mkdir=auto_mkdir,
        force=force,
        verbose=verbose,
        no_clobber=no_clobber
    )
    
    return operation.execute_multiple(sources, target)