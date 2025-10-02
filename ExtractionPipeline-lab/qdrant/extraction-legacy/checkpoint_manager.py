"""
Checkpoint manager for extraction pipeline.
Provides both database and JSON file checkpoint storage options.
"""

import json
import os
from datetime import datetime
from typing import Optional, Union
from uuid import UUID

from db import get_checkpoint as db_get_checkpoint
from db import update_checkpoint as db_update_checkpoint


class CheckpointManager:
    """
    Manages checkpoints for the extraction pipeline.
    Supports both database and JSON file storage.
    """

    def __init__(self, use_json: bool = True, json_file_path: str = None):
        """
        Initialize the checkpoint manager.

        Args:
            use_json: Whether to use JSON file storage (default: True)
            json_file_path: Path to the JSON checkpoint file (default: .checkpoint)
        """
        self.use_json = use_json
        self.json_file_path = json_file_path or os.path.join(
            os.path.dirname(__file__), ".checkpoint"
        )

    def get_checkpoint(self) -> Optional[str]:
        """
        Get the last processed ID from the checkpoint.

        Returns:
            The last processed ID as a string, or None if no checkpoint exists
        """
        if self.use_json:
            return self._get_json_checkpoint()
        else:
            return db_get_checkpoint()

    def update_checkpoint(self, last_processed_id: Union[str, UUID]) -> None:
        """
        Update the checkpoint with the last processed ID.

        Args:
            last_processed_id: The ID of the last successfully processed record
        """
        if self.use_json:
            self._update_json_checkpoint(last_processed_id)
        else:
            db_update_checkpoint(last_processed_id)

    def _get_json_checkpoint(self) -> Optional[str]:
        """
        Get the last processed ID from the JSON checkpoint file.

        Returns:
            The last processed ID as a string, or None if no checkpoint exists
        """
        try:
            if os.path.exists(self.json_file_path):
                with open(self.json_file_path, "r") as f:
                    data = json.load(f)
                    return data.get("last_processed_id")
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Could not read checkpoint file: {e}")
        return None

    def _update_json_checkpoint(self, last_processed_id: Union[str, UUID]) -> None:
        """
        Update the JSON checkpoint file with the last processed ID.

        Args:
            last_processed_id: The ID of the last successfully processed record
        """
        try:
            # Convert UUID to string if necessary
            id_str = (
                str(last_processed_id) if isinstance(last_processed_id, UUID) else last_processed_id
            )

            checkpoint_data = {
                "last_processed_id": id_str,
                "updated_at": datetime.utcnow().isoformat(),
            }

            # Ensure directory exists
            os.makedirs(os.path.dirname(self.json_file_path), exist_ok=True)

            with open(self.json_file_path, "w") as f:
                json.dump(checkpoint_data, f, indent=2)

        except IOError as e:
            print(f"Error: Could not write checkpoint file: {e}")
            raise

    def reset_checkpoint(self) -> None:
        """
        Reset the checkpoint (remove it entirely).
        """
        if self.use_json:
            try:
                if os.path.exists(self.json_file_path):
                    os.remove(self.json_file_path)
            except IOError as e:
                print(f"Warning: Could not remove checkpoint file: {e}")
        else:
            # For database, we could implement a reset function
            # For now, we'll just print a warning
            print(
                "Warning: Database checkpoint reset not implemented. "
                "Please manually delete the checkpoint record."
            )
