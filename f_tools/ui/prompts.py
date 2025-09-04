"""User interaction prompts for F-Tool."""

import sys
from enum import Enum
from pathlib import Path
from typing import Optional

from ..ui.i18n import i18n


class OverwriteAction(Enum):
    """Actions for file overwrite handling."""
    OVERWRITE = "overwrite"
    SKIP = "skip"
    OVERWRITE_ALL = "overwrite_all"
    SKIP_ALL = "skip_all"
    QUIT = "quit"


class OverwriteState:
    """Manages global overwrite behavior state."""
    
    def __init__(self):
        self.action: Optional[OverwriteAction] = None
    
    def should_prompt(self) -> bool:
        """Check if we should prompt for overwrite decision."""
        return self.action not in (OverwriteAction.OVERWRITE_ALL, 
                                  OverwriteAction.SKIP_ALL,
                                  OverwriteAction.QUIT)
    
    def should_overwrite(self) -> bool:
        """Check if we should overwrite based on current state."""
        return self.action in (OverwriteAction.OVERWRITE, 
                              OverwriteAction.OVERWRITE_ALL)
    
    def should_quit(self) -> bool:
        """Check if user wants to quit."""
        return self.action == OverwriteAction.QUIT


def confirm_directory_creation(target_dir: Path, auto_mkdir: bool = False) -> bool:
    """
    Confirm directory creation with user.
    
    Args:
        target_dir: Directory to create
        auto_mkdir: If True, auto-create without prompting
        
    Returns:
        True if should create directory
    """
    if auto_mkdir:
        print(i18n.info(i18n.t('creating_dirs', path=str(target_dir))))
        return True
    
    prompt = i18n.t('dir_not_exist', path=str(target_dir))
    while True:
        try:
            response = input(prompt).strip().lower()
            
            # Default to 'yes' if empty input
            if not response or response in ('y', 'yes', '是'):
                print(i18n.info(i18n.t('creating_dirs', path=str(target_dir))))
                return True
            elif response in ('n', 'no', '否'):
                return False
            else:
                # Invalid input, ask again
                continue
                
        except (KeyboardInterrupt, EOFError):
            print(f"\\n{i18n.warning(i18n.t('operation_cancelled'))}")
            return False


def confirm_file_overwrite(file_path: Path, state: OverwriteState) -> bool:
    """
    Confirm file overwrite with user.
    
    Args:
        file_path: File that would be overwritten
        state: Current overwrite state
        
    Returns:
        True if should overwrite the file
    """
    # Check global state first
    if not state.should_prompt():
        return state.should_overwrite()
    
    print(i18n.warning(i18n.t('file_exists', path=str(file_path))))
    
    while True:
        try:
            prompt = i18n.t('overwrite_prompt')
            response = input(prompt).strip().lower()
            
            if not response or response in ('y', 'yes', '是'):
                state.action = OverwriteAction.OVERWRITE
                return True
            elif response in ('n', 'no', '否'):
                state.action = OverwriteAction.SKIP
                return False
            elif response in ('a', 'all', '全部'):
                state.action = OverwriteAction.OVERWRITE_ALL
                return True
            elif response in ('s', 'skip', '跳过'):
                state.action = OverwriteAction.SKIP_ALL
                return False
            elif response in ('q', 'quit', '退出'):
                state.action = OverwriteAction.QUIT
                return False
            else:
                # Invalid input, show prompt again
                continue
                
        except (KeyboardInterrupt, EOFError):
            print(f"\\n{i18n.warning(i18n.t('operation_cancelled'))}")
            state.action = OverwriteAction.QUIT
            return False


def print_operation_info(source: Path, target: Path, verbose: bool = False) -> None:
    """
    Print information about the operation being performed.
    
    Args:
        source: Source path
        target: Target directory
        verbose: Whether to show verbose output
    """
    if verbose:
        print(i18n.info(i18n.t('moving', source=str(source), target=str(target))))


def print_success(message_key: str = 'move_complete') -> None:
    """
    Print success message.
    
    Args:
        message_key: I18n key for the message
    """
    print(i18n.success(i18n.t(message_key)))


def print_error(error_key: str, **kwargs) -> None:
    """
    Print error message and exit.
    
    Args:
        error_key: I18n key for error message
        **kwargs: Formatting parameters for message
    """
    print(i18n.error(i18n.t(error_key, **kwargs)), file=sys.stderr)


def handle_keyboard_interrupt() -> None:
    """Handle Ctrl+C gracefully."""
    print(f"\\n{i18n.warning(i18n.t('operation_cancelled'))}")
    sys.exit(1)