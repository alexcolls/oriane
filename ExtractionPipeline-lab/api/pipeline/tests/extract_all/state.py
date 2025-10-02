#!/usr/bin/env python3
"""
State management for tracking processed files and job persistence.

• Maintain JSON files: processed.json, pending.json inside working dir.
• Provide helpers: load_state(), save_state(), mark_processed(code).
• On startup merge remote list with local to avoid duplicates even across runs.
"""
import asyncio
import json
import logging
from typing import Dict, Any, List, Optional, Set
from datetime import datetime, timedelta
from pathlib import Path
import aiofiles
import fcntl


class StateManager:
    """Manages state persistence for processed files and job tracking."""
    
    def __init__(self, config):
        """Initialize state manager with configuration."""
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # In-memory state
        self.processed_codes = set()  # Set of processed codes
        self.pending_codes = set()    # Set of pending codes
        self.processed_files = {}     # s3_key -> {job_id, timestamp, status, result}
        self.failed_files = {}        # s3_key -> {job_id, timestamp, error, retry_count}
        self.job_history = {}         # job_id -> {s3_key, timestamp, status, result}
        
        # State file paths - use specific JSON files as required
        self.processed_file = self.config.processed_file
        self.pending_file = self.config.pending_file
        self.state_file = self.config.state_file  # Legacy compatibility
        self.backup_file = self.state_file.with_suffix('.backup')
        
        # File locking for concurrent access
        self._lock = asyncio.Lock()
        
    async def load_state(self) -> bool:
        """
        Load state from persistent storage (processed.json and pending.json).
        
        Returns:
            True if state was loaded successfully, False otherwise
        """
        async with self._lock:
            try:
                # Load processed codes
                if self.processed_file.exists():
                    self.logger.info(f"Loading processed codes from: {self.processed_file}")
                    async with aiofiles.open(self.processed_file, 'r') as f:
                        processed_data = json.loads(await f.read())
                    
                    # Handle both list and dict formats
                    if isinstance(processed_data, list):
                        self.processed_codes = set(processed_data)
                        self.processed_files = {code: {'timestamp': datetime.utcnow().isoformat(), 'status': 'completed'} for code in processed_data}
                    else:
                        self.processed_files = processed_data
                        self.processed_codes = set(processed_data.keys())
                    
                    self.logger.info(f"Loaded {len(self.processed_codes)} processed codes")
                else:
                    self.logger.info("No processed.json found, starting fresh")
                    self.processed_codes = set()
                    self.processed_files = {}
                
                # Load pending codes
                if self.pending_file.exists():
                    self.logger.info(f"Loading pending codes from: {self.pending_file}")
                    async with aiofiles.open(self.pending_file, 'r') as f:
                        pending_data = json.loads(await f.read())
                    
                    # Handle both list and dict formats
                    if isinstance(pending_data, list):
                        self.pending_codes = set(pending_data)
                    else:
                        self.pending_codes = set(pending_data.keys())
                    
                    self.logger.info(f"Loaded {len(self.pending_codes)} pending codes")
                else:
                    self.logger.info("No pending.json found, starting fresh")
                    self.pending_codes = set()
                
                # Load legacy state file if exists for backward compatibility
                if self.state_file.exists():
                    self.logger.info(f"Loading legacy state from: {self.state_file}")
                    async with aiofiles.open(self.state_file, 'r') as f:
                        state_data = json.loads(await f.read())
                    
                    # Load additional state components
                    self.failed_files = state_data.get('failed_files', {})
                    self.job_history = state_data.get('job_history', {})
                    
                    self.logger.info(f"Loaded legacy state: {len(self.failed_files)} failed files, "
                                   f"{len(self.job_history)} job records")
                
                return True
                    
            except Exception as e:
                self.logger.error(f"Error loading state: {e}")
                return False
    
    async def save_state(self) -> bool:
        """
        Save current state to persistent storage (processed.json, pending.json, and legacy state.json).
        
        Returns:
            True if state was saved successfully, False otherwise
        """
        async with self._lock:
            try:
                # Save processed codes to processed.json
                processed_temp = self.processed_file.with_suffix('.tmp')
                async with aiofiles.open(processed_temp, 'w') as f:
                    await f.write(json.dumps(self.processed_files, indent=2, default=str))
                    await f.flush()
                processed_temp.rename(self.processed_file)
                
                # Save pending codes to pending.json
                pending_temp = self.pending_file.with_suffix('.tmp')
                async with aiofiles.open(pending_temp, 'w') as f:
                    await f.write(json.dumps(list(self.pending_codes), indent=2, default=str))
                    await f.flush()
                pending_temp.rename(self.pending_file)
                
                # Save legacy state file for backward compatibility
                if self.state_file.exists():
                    await self._create_backup()
                
                state_data = {
                    'processed_files': self.processed_files,
                    'failed_files': self.failed_files,
                    'job_history': self.job_history,
                    'last_updated': datetime.utcnow().isoformat(),
                    'version': '1.0'
                }
                
                state_temp = self.state_file.with_suffix('.tmp')
                async with aiofiles.open(state_temp, 'w') as f:
                    await f.write(json.dumps(state_data, indent=2, default=str))
                    await f.flush()
                state_temp.rename(self.state_file)
                
                self.logger.debug("State saved successfully to all files")
                return True
                
            except Exception as e:
                self.logger.error(f"Error saving state: {e}")
                return False
    
    async def reset_state(self) -> bool:
        """
        Reset state (clear all processed files and job history).
        
        Returns:
            True if reset was successful, False otherwise
        """
        async with self._lock:
            try:
                self.logger.info("Resetting state")
                
                # Create backup before reset
                if self.state_file.exists():
                    backup_name = f"{self.state_file.stem}_reset_backup_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
                    backup_path = self.state_file.parent / backup_name
                    
                    async with aiofiles.open(self.state_file, 'r') as src:
                        async with aiofiles.open(backup_path, 'w') as dst:
                            await dst.write(await src.read())
                    
                    self.logger.info(f"State backup created: {backup_path}")
                
                # Clear in-memory state
                self.processed_files.clear()
                self.failed_files.clear()
                self.job_history.clear()
                
                # Save empty state
                await self.save_state()
                
                self.logger.info("State reset complete")
                return True
                
            except Exception as e:
                self.logger.error(f"Error resetting state: {e}")
                return False
    
    async def mark_processed(self, code: str, job_id: str = None, result: Optional[Dict[str, Any]] = None) -> bool:
        """
        Mark a file as successfully processed.
        
        Args:
            code: File code/key to mark as processed
            job_id: Job ID that processed the file (optional)
            result: Optional result data
        
        Returns:
            True if marked successfully, False otherwise
        """
        try:
            timestamp = datetime.utcnow().isoformat()
            
            # Add to processed codes set
            self.processed_codes.add(code)
            
            # Add to processed files with details
            self.processed_files[code] = {
                'job_id': job_id,
                'timestamp': timestamp,
                'status': 'completed',
                'result': result
            }
            
            # Add to job history if job_id provided
            if job_id:
                self.job_history[job_id] = {
                    's3_key': code,
                    'timestamp': timestamp,
                    'status': 'completed',
                    'result': result
                }
            
            # Remove from failed files if it was there
            if code in self.failed_files:
                del self.failed_files[code]
            
            # Remove from pending if it was there
            if code in self.pending_codes:
                self.pending_codes.remove(code)
            
            self.logger.info(f"Marked as processed: {code} (job: {job_id})")
            return True
            
        except Exception as e:
            self.logger.error(f"Error marking file as processed: {e}")
            return False
        finally:
            # Always attempt to save state
            try:
                await self.save_state()
            except Exception as e:
                self.logger.error(f"Error saving state after marking processed: {e}")
    
    async def mark_failed(self, s3_key: str, job_id: str, error: str, retry_count: int = 0) -> bool:
        """
        Mark a file as failed to process.
        
        Args:
            s3_key: S3 object key
            job_id: Job ID that failed
            error: Error message
            retry_count: Number of retry attempts
        
        Returns:
            True if marked successfully, False otherwise
        """
        try:
            timestamp = datetime.utcnow().isoformat()
            
            # Add to failed files
            self.failed_files[s3_key] = {
                'job_id': job_id,
                'timestamp': timestamp,
                'error': error,
                'retry_count': retry_count
            }
            
            # Add to job history
            self.job_history[job_id] = {
                's3_key': s3_key,
                'timestamp': timestamp,
                'status': 'failed',
                'error': error
            }
            
            self.logger.info(f"Marked as failed: {s3_key} (job: {job_id})")
            return True
            
        except Exception as e:
            self.logger.error(f"Error marking file as failed: {e}")
            return False
        finally:
            # Always attempt to save state
            try:
                await self.save_state()
            except Exception as e:
                self.logger.error(f"Error saving state after marking failed: {e}")
    
    async def get_processed_files(self) -> Set[str]:
        """
        Get set of processed file keys.
        
        Returns:
            Set of S3 keys that have been processed
        """
        return set(self.processed_files.keys())
    
    async def get_failed_files(self) -> Set[str]:
        """
        Get set of failed file keys.
        
        Returns:
            Set of S3 keys that failed processing
        """
        return set(self.failed_files.keys())
    
    async def get_file_status(self, s3_key: str) -> Optional[Dict[str, Any]]:
        """
        Get status information for a specific file.
        
        Args:
            s3_key: S3 object key
        
        Returns:
            Dictionary with file status or None if not found
        """
        if s3_key in self.processed_files:
            return {
                'status': 'processed',
                **self.processed_files[s3_key]
            }
        elif s3_key in self.failed_files:
            return {
                'status': 'failed',
                **self.failed_files[s3_key]
            }
        else:
            return None
    
    async def get_job_info(self, job_id: str) -> Optional[Dict[str, Any]]:
        """
        Get information about a specific job.
        
        Args:
            job_id: Job ID
        
        Returns:
            Dictionary with job information or None if not found
        """
        return self.job_history.get(job_id)
    
    async def get_statistics(self) -> Dict[str, Any]:
        """
        Get processing statistics.
        
        Returns:
            Dictionary with processing statistics
        """
        total_processed = len(self.processed_files)
        total_failed = len(self.failed_files)
        total_jobs = len(self.job_history)
        
        # Calculate success rate
        success_rate = (total_processed / max(total_processed + total_failed, 1)) * 100
        
        # Get recent activity (last 24 hours)
        recent_cutoff = datetime.utcnow() - timedelta(hours=24)
        recent_processed = 0
        recent_failed = 0
        
        for file_info in self.processed_files.values():
            if datetime.fromisoformat(file_info['timestamp']) > recent_cutoff:
                recent_processed += 1
        
        for file_info in self.failed_files.values():
            if datetime.fromisoformat(file_info['timestamp']) > recent_cutoff:
                recent_failed += 1
        
        return {
            'total_processed': total_processed,
            'total_failed': total_failed,
            'total_jobs': total_jobs,
            'success_rate': success_rate,
            'recent_processed_24h': recent_processed,
            'recent_failed_24h': recent_failed,
            'state_file': str(self.state_file),
            'last_updated': datetime.utcnow().isoformat()
        }
    
    async def _create_backup(self) -> bool:
        """
        Create a backup of the current state file.
        
        Returns:
            True if backup created successfully, False otherwise
        """
        try:
            if self.state_file.exists():
                async with aiofiles.open(self.state_file, 'r') as src:
                    async with aiofiles.open(self.backup_file, 'w') as dst:
                        await dst.write(await src.read())
                return True
            return False
        except Exception as e:
            self.logger.error(f"Error creating backup: {e}")
            return False
    
    async def _cleanup_old_entries(self, max_age_days: int = 7) -> None:
        """
        Clean up old entries from state to prevent unbounded growth.
        
        Args:
            max_age_days: Maximum age in days for keeping entries
        """
        cutoff_time = datetime.utcnow() - timedelta(days=max_age_days)
        
        # Clean up old job history
        old_jobs = []
        for job_id, job_info in self.job_history.items():
            if datetime.fromisoformat(job_info['timestamp']) < cutoff_time:
                old_jobs.append(job_id)
        
        for job_id in old_jobs:
            del self.job_history[job_id]
        
        if old_jobs:
            self.logger.info(f"Cleaned up {len(old_jobs)} old job records")
    
    async def merge_remote_list(self, remote_list: List[str]) -> List[str]:
        """
        Merge remote list with local state to avoid duplicates.
        
        Args:
            remote_list: List of remote file codes/keys
        
        Returns:
            List of codes that need to be processed (not in local state)
        """
        try:
            remote_set = set(remote_list)
            
            # Get already processed codes
            processed_set = self.processed_codes
            
            # Get currently pending codes
            pending_set = self.pending_codes
            
            # Calculate what needs to be processed
            needs_processing = remote_set - processed_set - pending_set
            
            # Update pending codes with new items
            self.pending_codes.update(needs_processing)
            
            # Save updated state
            await self.save_state()
            
            self.logger.info(f"Remote list merge complete: {len(remote_list)} remote, "
                           f"{len(processed_set)} already processed, "
                           f"{len(pending_set)} already pending, "
                           f"{len(needs_processing)} new to process")
            
            return list(needs_processing)
            
        except Exception as e:
            self.logger.error(f"Error merging remote list: {e}")
            return []
    
    async def add_pending(self, code: str) -> bool:
        """
        Add a code to the pending list.
        
        Args:
            code: File code/key to add to pending
        
        Returns:
            True if added successfully, False otherwise
        """
        try:
            self.pending_codes.add(code)
            await self.save_state()
            self.logger.debug(f"Added to pending: {code}")
            return True
        except Exception as e:
            self.logger.error(f"Error adding to pending: {e}")
            return False
    
    async def remove_pending(self, code: str) -> bool:
        """
        Remove a code from the pending list.
        
        Args:
            code: File code/key to remove from pending
        
        Returns:
            True if removed successfully, False otherwise
        """
        try:
            if code in self.pending_codes:
                self.pending_codes.remove(code)
                await self.save_state()
                self.logger.debug(f"Removed from pending: {code}")
            return True
        except Exception as e:
            self.logger.error(f"Error removing from pending: {e}")
            return False
    
    async def get_pending_codes(self) -> Set[str]:
        """
        Get set of pending codes.
        
        Returns:
            Set of codes that are pending processing
        """
        return self.pending_codes.copy()
    
    async def get_processed_codes(self) -> Set[str]:
        """
        Get set of processed codes.
        
        Returns:
            Set of codes that have been processed
        """
        return self.processed_codes.copy()
    
    async def is_processed(self, code: str) -> bool:
        """
        Check if a code has been processed.
        
        Args:
            code: File code/key to check
        
        Returns:
            True if code has been processed, False otherwise
        """
        return code in self.processed_codes
    
    async def is_pending(self, code: str) -> bool:
        """
        Check if a code is pending processing.
        
        Args:
            code: File code/key to check
        
        Returns:
            True if code is pending, False otherwise
        """
        return code in self.pending_codes
    
    async def export_state(self, export_path: Path) -> bool:
        """
        Export current state to a file.
        
        Args:
            export_path: Path to export file
        
        Returns:
            True if export successful, False otherwise
        """
        try:
            export_data = {
                'processed_files': self.processed_files,
                'failed_files': self.failed_files,
                'job_history': self.job_history,
                'processed_codes': list(self.processed_codes),
                'pending_codes': list(self.pending_codes),
                'statistics': await self.get_statistics(),
                'export_timestamp': datetime.utcnow().isoformat()
            }
            
            async with aiofiles.open(export_path, 'w') as f:
                await f.write(json.dumps(export_data, indent=2, default=str))
            
            self.logger.info(f"State exported to: {export_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting state: {e}")
            return False
