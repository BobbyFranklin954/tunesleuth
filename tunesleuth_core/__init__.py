"""
TuneSleuth Core Library

The brain of TuneSleuth - provides pattern detection, file analysis,
and library management that powers both CLI and GUI interfaces.
"""

from tunesleuth_core.models import Album, Artist, Library, Track
from tunesleuth_core.patterns import PatternDetector, PatternMatch, PatternType
from tunesleuth_core.scanner import Scanner, ScanProgress

__version__ = "0.1.0"

__all__ = [
    # Models
    "Track",
    "Album",
    "Artist",
    "Library",
    # Scanner
    "Scanner",
    "ScanProgress",
    # Patterns
    "PatternDetector",
    "PatternMatch",
    "PatternType",
]
