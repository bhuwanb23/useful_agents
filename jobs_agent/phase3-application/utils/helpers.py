"""
Helper utility functions
"""

from datetime import datetime, timedelta
from typing import Any, Dict, List
import hashlib
import json
from pathlib import Path


def generate_id(prefix: str = "") -> str:
    """Generate unique ID"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_%f")
    return f"{prefix}_{timestamp}" if prefix else timestamp


def hash_text(text: str) -> str:
    """Generate hash of text"""
    return hashlib.md5(text.encode()).hexdigest()


def normalize_text(text: str) -> str:
    """Normalize text for comparison"""
    return text.lower().strip()


def calculate_similarity(text1: str, text2: str) -> float:
    """
    Calculate similarity between two texts (simple word overlap)
    Returns 0-1
    """
    words1 = set(normalize_text(text1).split())
    words2 = set(normalize_text(text2).split())
    
    if not words2:
        return 0.0
    
    overlap = len(words1 & words2)
    return overlap / len(words2)


def format_duration(seconds: float) -> str:
    """Format seconds as human-readable duration"""
    if seconds < 60:
        return f"{seconds:.0f}s"
    elif seconds < 3600:
        minutes = seconds / 60
        return f"{minutes:.1f}m"
    else:
        hours = seconds / 3600
        return f"{hours:.1f}h"


def format_date(dt: datetime, format: str = "short") -> str:
    """Format datetime in various ways"""
    if format == "short":
        return dt.strftime("%Y-%m-%d")
    elif format == "long":
        return dt.strftime("%B %d, %Y at %I:%M %p")
    elif format == "time_ago":
        delta = datetime.now() - dt
        if delta.days > 365:
            return f"{delta.days // 365} years ago"
        elif delta.days > 30:
            return f"{delta.days // 30} months ago"
        elif delta.days > 0:
            return f"{delta.days} days ago"
        elif delta.seconds > 3600:
            return f"{delta.seconds // 3600} hours ago"
        elif delta.seconds > 60:
            return f"{delta.seconds // 60} minutes ago"
        else:
            return "just now"
    else:
        return dt.isoformat()


def safe_filename(text: str) -> str:
    """Convert text to safe filename"""
    # Remove invalid characters
    safe = "".join(c for c in text if c.isalnum() or c in (' ', '-', '_'))
    # Replace spaces with underscores
    safe = safe.replace(' ', '_')
    # Limit length
    return safe[:100]


def load_json(file_path: str) -> Dict:
    """Load JSON file safely"""
    path = Path(file_path)
    if not path.exists():
        return {}
    
    try:
        with open(path, 'r') as f:
            return json.load(f)
    except json.JSONDecodeError:
        print(f"Error reading {file_path}")
        return {}


def save_json(data: Any, file_path: str, indent: int = 2):
    """Save data to JSON file"""
    path = Path(file_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(path, 'w') as f:
        json.dump(data, f, indent=indent, default=str)


def chunk_list(items: List, chunk_size: int) -> List[List]:
    """Split list into chunks"""
    return [items[i:i + chunk_size] for i in range(0, len(items), chunk_size)]


def merge_dicts(*dicts) -> Dict:
    """Merge multiple dictionaries"""
    result = {}
    for d in dicts:
        result.update(d)
    return result


class Timer:
    """Simple timer context manager"""
    
    def __init__(self, name: str = "Operation"):
        self.name = name
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        return self
    
    def __exit__(self, *args):
        elapsed = (datetime.now() - self.start_time).total_seconds()
        print(f"{self.name} took {format_duration(elapsed)}")
    
    @property
    def elapsed(self) -> float:
        """Get elapsed time in seconds"""
        if self.start_time:
            return (datetime.now() - self.start_time).total_seconds()
        return 0.0


# Example usage
if __name__ == "__main__":
    # Test timer
    with Timer("Test operation"):
        import time
        time.sleep(2)
    
    # Test similarity
    text1 = "Python Developer with 5 years experience"
    text2 = "Senior Python Engineer with experience"
    sim = calculate_similarity(text1, text2)
    print(f"Similarity: {sim:.2f}")
    
    # Test date formatting
    now = datetime.now()
    yesterday = now - timedelta(days=1)
    print(f"Time ago: {format_date(yesterday, 'time_ago')}")