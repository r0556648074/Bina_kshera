"""
Utilities package for common helper functions and utilities.

This package contains various utility modules for audio processing,
file operations, and other common functionality used throughout
the application.
"""

from .audio_utils import (
    format_duration,
    parse_time_string,
    calculate_rms,
    normalize_audio,
    db_to_linear,
    linear_to_db,
    detect_silence,
    AudioFormatInfo
)

__all__ = [
    'format_duration',
    'parse_time_string', 
    'calculate_rms',
    'normalize_audio',
    'db_to_linear',
    'linear_to_db',
    'detect_silence',
    'AudioFormatInfo'
]
