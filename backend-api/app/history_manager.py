"""
Compression history manager for 8mb.local
Tracks compression jobs (metadata only, not files)
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional


HISTORY_FILE = Path("/app/history.json")


def _read_history() -> List[Dict]:
    """Read history from JSON file"""
    if not HISTORY_FILE.exists():
        return []
    
    try:
        with open(HISTORY_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


def _write_history(history: List[Dict]):
    """Write history to JSON file"""
    try:
        with open(HISTORY_FILE, 'w') as f:
            json.dump(history, f, indent=2)
        os.chmod(HISTORY_FILE, 0o600)
    except IOError:
        pass  # Silently fail if can't write


def add_history_entry(
    filename: str,
    original_size_mb: float,
    compressed_size_mb: float,
    video_codec: str,
    audio_codec: str,
    target_mb: float,
    preset: str,
    duration: float,
    task_id: str
) -> Dict:
    """Add a compression history entry"""
    entry = {
        'timestamp': datetime.utcnow().isoformat() + 'Z',
        'filename': filename,
        'original_size_mb': round(original_size_mb, 2),
        'compressed_size_mb': round(compressed_size_mb, 2),
        'reduction_percent': round((1 - compressed_size_mb / original_size_mb) * 100, 1) if original_size_mb > 0 else 0,
        'video_codec': video_codec,
        'audio_codec': audio_codec,
        'target_mb': target_mb,
        'preset': preset,
        'duration_seconds': round(duration, 1),
        'task_id': task_id
    }
    
    history = _read_history()
    history.insert(0, entry)  # Add to beginning (newest first)
    
    # Keep only last 100 entries
    if len(history) > 100:
        history = history[:100]
    
    _write_history(history)
    return entry


def get_history(limit: Optional[int] = None) -> List[Dict]:
    """Get compression history"""
    history = _read_history()
    
    if limit and limit > 0:
        return history[:limit]
    
    return history


def clear_history():
    """Clear all history"""
    _write_history([])


def delete_history_entry(task_id: str) -> bool:
    """Delete a specific history entry by task_id"""
    history = _read_history()
    original_len = len(history)
    
    history = [entry for entry in history if entry.get('task_id') != task_id]
    
    if len(history) < original_len:
        _write_history(history)
        return True
    
    return False
