"""Main entry point for F-Tool."""

import argparse
import sys
from pathlib import Path

from f_tool.commands.move import move_command
from f_tool.commands.copy import copy_command
from f_tool.commands.backup import backup_command
from f_tool.ui.i18n import i18n


def create_parser() -> argparse.ArgumentParser:
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        prog='f',
        description='Unified file operation CLI tool with auto-mkdir and progress display',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Move command
    move_parser = subparsers.add_parser(
        'move', 
        aliases=['mv'],
        help='Move files or directories to target directory'
    )
    move_parser.add_argument(
        'sources',
        nargs='+',
        help='Source files or directories (one or more)'
    )
    move_parser.add_argument(
        'target', 
        help='Target directory path (must be directory, not file)'
    )
    move_parser.add_argument(
        '-p', '--mkdir', 
        action='store_true',
        help='Automatically create target directories'
    )
    move_parser.add_argument(
        '-f', '--force', 
        action='store_true',
        help='Force overwrite existing files'
    )
    move_parser.add_argument(
        '-v', '--verbose', 
        action='store_true',
        help='Show verbose operation information'
    )
    move_parser.add_argument(
        '-n', '--no-clobber', 
        action='store_true',
        help='Never overwrite existing files'
    )
    
    # Copy command
    copy_parser = subparsers.add_parser(
        'copy', 
        aliases=['cp'],
        help='Copy files or directories to target directory'
    )
    copy_parser.add_argument(
        'sources',
        nargs='+',
        help='Source files or directories (one or more)'
    )
    copy_parser.add_argument(
        'target', 
        help='Target directory path (must be directory, not file)'
    )
    copy_parser.add_argument(
        '-p', '--mkdir', 
        action='store_true',
        help='Automatically create target directories'
    )
    copy_parser.add_argument(
        '-f', '--force', 
        action='store_true',
        help='Force overwrite existing files'
    )
    copy_parser.add_argument(
        '-v', '--verbose', 
        action='store_true',
        help='Show verbose operation information'
    )
    copy_parser.add_argument(
        '-n', '--no-clobber', 
        action='store_true',
        help='Never overwrite existing files'
    )
    
    # Backup command
    backup_parser = subparsers.add_parser(
        'backup', 
        aliases=['bak'],
        help='Create backup copies of files or directories'
    )
    backup_parser.add_argument(
        'sources',
        nargs='+',
        help='Source files or directories to backup (one or more)'
    )
    backup_parser.add_argument(
        '-f', '--force', 
        action='store_true',
        help='Force overwrite existing backup files'
    )
    backup_parser.add_argument(
        '-v', '--verbose', 
        action='store_true',
        help='Show verbose operation information'
    )
    backup_parser.add_argument(
        '-n', '--no-clobber', 
        action='store_true',
        help='Never overwrite existing backup files'
    )
    
    return parser


def main() -> None:
    """Main entry point."""
    try:
        parser = create_parser()
        
        # If no arguments provided, show help
        if len(sys.argv) == 1:
            parser.print_help()
            sys.exit(1)
        
        args = parser.parse_args()
        
        # Handle commands
        if args.command in ('move', 'mv'):
            # Validate conflicting options
            if args.force and args.no_clobber:
                print(i18n.error("Error: Cannot use --force and --no-clobber together"), 
                      file=sys.stderr)
                sys.exit(1)
            
            # Execute move command
            success = move_command(
                sources=args.sources,
                target=args.target,
                auto_mkdir=args.mkdir,
                force=args.force,
                verbose=args.verbose,
                no_clobber=args.no_clobber
            )
            
            sys.exit(0 if success else 1)
        elif args.command in ('copy', 'cp'):
            # Validate conflicting options
            if args.force and args.no_clobber:
                print(i18n.error("Error: Cannot use --force and --no-clobber together"), 
                      file=sys.stderr)
                sys.exit(1)
            
            # Execute copy command
            success = copy_command(
                sources=args.sources,
                target=args.target,
                auto_mkdir=args.mkdir,
                force=args.force,
                verbose=args.verbose,
                no_clobber=args.no_clobber
            )
            
            sys.exit(0 if success else 1)
        elif args.command in ('backup', 'bak'):
            # Validate conflicting options
            if args.force and args.no_clobber:
                print(i18n.error("Error: Cannot use --force and --no-clobber together"), 
                      file=sys.stderr)
                sys.exit(1)
            
            # Execute backup command
            success = backup_command(
                sources=args.sources,
                force=args.force,
                verbose=args.verbose,
                no_clobber=args.no_clobber
            )
            
            sys.exit(0 if success else 1)
        else:
            # Unknown command
            print(i18n.error(f"Unknown command: {args.command}"), file=sys.stderr)
            parser.print_help()
            sys.exit(1)
    
    except KeyboardInterrupt:
        print(f"\\n{i18n.warning(i18n.t('operation_cancelled'))}")
        sys.exit(1)
    except Exception as e:
        print(i18n.error(f"Unexpected error: {e}"), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()