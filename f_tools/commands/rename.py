"""Rename command implementation."""

import os
import sys
from pathlib import Path
from typing import Optional

from ..ui.i18n import i18n
from ..ui.prompts import (
    OverwriteState,
    confirm_file_overwrite,
    print_success,
    print_error,
    handle_keyboard_interrupt
)
from ..utils.filesystem import (
    FileSystemError,
    FileNotFoundError as FSFileNotFoundError,
    SameFileError
)


class RenameOperation:
    """Handles rename operations within the same directory."""
    
    def __init__(self, force: bool = False, verbose: bool = False, 
                 no_clobber: bool = False):
        """
        Initialize rename operation.
        
        Args:
            force: Force overwrite existing files
            verbose: Show verbose output
            no_clobber: Never overwrite existing files
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
    
    def execute(self, old_path: str, new_name: str) -> bool:
        """
        Execute rename operation.
        
        Args:
            old_path: Path to the file or directory to rename
            new_name: New name (filename only, no path separators)
            
        Returns:
            True if operation completed successfully
        """
        try:
            # Validate inputs
            source_path, target_path = self._validate_rename_paths(old_path, new_name)
            
            # Check if target already exists
            if target_path.exists():
                if not self._handle_existing_target(source_path, target_path):
                    return False
            
            # Perform the rename operation
            self._perform_rename(source_path, target_path)
            
            # Show success message
            if self.verbose:
                print_success('rename_success', source_path.name, new_name)
            else:
                print(i18n.success(f"重命名：{source_path.name} → {new_name}"))
            
            return True
            
        except KeyboardInterrupt:
            handle_keyboard_interrupt()
            return False
        except FileSystemError as e:
            print(i18n.error(str(e)), file=sys.stderr)
            return False
        except ValueError as e:
            print(i18n.error(str(e)), file=sys.stderr)
            return False
        except Exception as e:
            print(i18n.error(f"Unexpected error: {e}"), file=sys.stderr)
            return False
    
    def _validate_rename_paths(self, old_path: str, new_name: str) -> tuple[Path, Path]:
        """
        Validate rename operation paths.
        
        Args:
            old_path: Original file path
            new_name: New filename
            
        Returns:
            Tuple of (source_path, target_path)
            
        Raises:
            FileNotFoundError: If source doesn't exist
            ValueError: If new_name contains path separators
            SameFileError: If source and target are the same
        """
        # Validate new_name doesn't contain path separators
        if '/' in new_name or '\\' in new_name:
            raise ValueError(f"New name cannot contain path separators: {new_name}")
        
        # Validate new_name is not empty
        if not new_name.strip():
            raise ValueError("New name cannot be empty")
        
        # Resolve source path
        source_path = Path(old_path).resolve()
        
        # Check if source exists
        if not source_path.exists():
            raise FSFileNotFoundError(f"Source does not exist: {old_path}")
        
        # Create target path in the same directory
        target_path = source_path.parent / new_name
        
        # Check if source and target are the same
        if source_path == target_path:
            raise SameFileError(f"Source and target are the same: {old_path}")
        
        return source_path, target_path
    
    def _handle_existing_target(self, source_path: Path, target_path: Path) -> bool:
        """
        Handle case where target file already exists.
        
        Args:
            source_path: Source file path
            target_path: Target file path
            
        Returns:
            True if should proceed with rename, False if should skip
        """
        # Check overwrite state
        should_overwrite = confirm_file_overwrite(
            target_path, 
            self.overwrite_state,
            self.force,
            self.no_clobber
        )
        
        return should_overwrite
    
    def _perform_rename(self, source_path: Path, target_path: Path) -> None:
        """
        Perform the actual rename operation.
        
        Args:
            source_path: Source file path
            target_path: Target file path
            
        Raises:
            PermissionError: If permission denied
            OSError: If rename operation fails
        """
        try:
            # Use os.rename for atomic operation
            os.rename(str(source_path), str(target_path))
        except PermissionError as e:
            raise FileSystemError(f"Permission denied: {e}")
        except OSError as e:
            raise FileSystemError(f"Rename failed: {e}")


def rename_command(old_path: str, new_name: str, force: bool = False, 
                  verbose: bool = False, no_clobber: bool = False) -> bool:
    """
    Execute rename command.
    
    Args:
        old_path: Path to the file or directory to rename
        new_name: New name (filename only)
        force: Force overwrite existing files
        verbose: Show verbose output
        no_clobber: Never overwrite existing files
        
    Returns:
        True if operation completed successfully
    """
    operation = RenameOperation(force=force, verbose=verbose, no_clobber=no_clobber)
    return operation.execute(old_path, new_name)