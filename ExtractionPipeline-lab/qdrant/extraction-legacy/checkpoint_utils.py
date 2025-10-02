#!/usr/bin/env python3
"""
Utility script for managing extraction checkpoints.
Provides command-line interface for checkpoint operations.
"""

import argparse
import sys

from checkpoint_manager import CheckpointManager


def main():
    parser = argparse.ArgumentParser(description="Manage extraction checkpoints")
    parser.add_argument(
        "--storage",
        choices=["json", "db"],
        default="json",
        help="Storage type for checkpoint (default: json)",
    )
    parser.add_argument(
        "--json-file",
        type=str,
        default=None,
        help="Path to JSON checkpoint file (default: .checkpoint)",
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Show checkpoint command
    show_parser = subparsers.add_parser("show", help="Show current checkpoint")

    # Set checkpoint command
    set_parser = subparsers.add_parser("set", help="Set checkpoint to specific ID")
    set_parser.add_argument("id", type=int, help="ID to set as checkpoint")

    # Reset checkpoint command
    reset_parser = subparsers.add_parser("reset", help="Reset checkpoint (remove it)")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    # Initialize checkpoint manager
    use_json = args.storage == "json"
    checkpoint_manager = CheckpointManager(use_json=use_json, json_file_path=args.json_file)

    try:
        if args.command == "show":
            checkpoint = checkpoint_manager.get_checkpoint()
            if checkpoint:
                print(f"Current checkpoint: {checkpoint}")
            else:
                print("No checkpoint found")

        elif args.command == "set":
            checkpoint_manager.update_checkpoint(args.id)
            print(f"Checkpoint set to: {args.id}")

        elif args.command == "reset":
            checkpoint_manager.reset_checkpoint()
            print("Checkpoint reset")

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
