"""
Audio utility functions for processing and analysis.

This module provides common audio processing utilities including
format conversion, time formatting, RMS calculation, normalization,
and silence detection.
"""

import math
import logging
from typing import Tuple, Optional, List
from dataclasses import dataclass

import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class AudioFormatInfo:
    """Information about audio format characteristics."""
    sample_rate: int
    channels: int
    bit_depth: int
    format_name: str
    is_compressed: bool
    estimated_bitrate: Optional[int] = None

def format_duration(seconds: float, include_hours: bool = None) -> str:
    """
    Format duration in seconds to human-readable string.
    
    Args:
        seconds: Duration in seconds
        include_hours: Whether to include hours. If None, auto-detect based on duration
        
    Returns:
        Formatted time string (e.g., "02:34" or "1:23:45")
    """
    if seconds < 0:
        seconds = 0
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    # Auto-detect hours inclusion if not specified
    if include_hours is None:
        include_hours = hours > 0
    
    if include_hours:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"

def format_duration_precise(seconds: float, precision: int = 1) -> str:
    """
    Format duration with decimal precision.
    
    Args:
        seconds: Duration in seconds
        precision: Number of decimal places
        
    Returns:
        Formatted time string with decimal seconds
    """
    if seconds < 0:
        seconds = 0
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:0{3+precision}.{precision}f}"
    else:
        return f"{minutes:02d}:{secs:0{3+precision}.{precision}f}"

def parse_time_string(time_str: str) -> float:
    """
    Parse time string to seconds.
    
    Args:
        time_str: Time string in format "MM:SS" or "HH:MM:SS" or "SS.sss"
        
    Returns:
        Time in seconds
        
    Raises:
        ValueError: If time string format is invalid
    """
    try:
        time_str = time_str.strip()
        
        # Handle decimal seconds only
        if ':' not in time_str:
            return float(time_str)
        
        parts = time_str.split(':')
        
        if len(parts) == 2:
            # MM:SS format
            minutes, seconds = parts
            return int(minutes) * 60 + float(seconds)
        elif len(parts) == 3:
            # HH:MM:SS format
            hours, minutes, seconds = parts
            return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
        else:
            raise ValueError(f"Invalid time format: {time_str}")
            
    except (ValueError, IndexError) as e:
        raise ValueError(f"Cannot parse time string '{time_str}': {e}")

def calculate_rms(audio_data: np.ndarray, window_size: Optional[int] = None) -> float:
    """
    Calculate RMS (Root Mean Square) value of audio data.
    
    Args:
        audio_data: Audio samples as numpy array
        window_size: Window size for chunked calculation (None for entire array)
        
    Returns:
        RMS value
    """
    try:
        if len(audio_data) == 0:
            return 0.0
        
        if window_size is None:
            # Calculate RMS for entire array
            return np.sqrt(np.mean(audio_data ** 2))
        else:
            # Calculate windowed RMS
            rms_values = []
            for i in range(0, len(audio_data), window_size):
                chunk = audio_data[i:i + window_size]
                if len(chunk) > 0:
                    rms_values.append(np.sqrt(np.mean(chunk ** 2)))
            
            return np.mean(rms_values) if rms_values else 0.0
            
    except Exception as e:
        logger.error(f"Error calculating RMS: {e}")
        return 0.0

def calculate_rms_windowed(audio_data: np.ndarray, window_size: int, hop_size: Optional[int] = None) -> np.ndarray:
    """
    Calculate RMS values for overlapping windows.
    
    Args:
        audio_data: Audio samples as numpy array
        window_size: Size of each window in samples
        hop_size: Step size between windows (defaults to window_size // 4)
        
    Returns:
        Array of RMS values for each window
    """
    try:
        if hop_size is None:
            hop_size = window_size // 4
        
        rms_values = []
        
        for start in range(0, len(audio_data) - window_size + 1, hop_size):
            window = audio_data[start:start + window_size]
            rms = np.sqrt(np.mean(window ** 2))
            rms_values.append(rms)
        
        return np.array(rms_values)
        
    except Exception as e:
        logger.error(f"Error calculating windowed RMS: {e}")
        return np.array([])

def normalize_audio(audio_data: np.ndarray, target_rms: float = 0.1, max_gain: float = 10.0) -> np.ndarray:
    """
    Normalize audio to target RMS level.
    
    Args:
        audio_data: Audio samples as numpy array
        target_rms: Target RMS level (0.0 to 1.0)
        max_gain: Maximum gain factor to prevent excessive amplification
        
    Returns:
        Normalized audio data
    """
    try:
        if len(audio_data) == 0:
            return audio_data
        
        current_rms = calculate_rms(audio_data)
        
        if current_rms == 0:
            return audio_data
        
        # Calculate gain factor
        gain = target_rms / current_rms
        gain = min(gain, max_gain)  # Limit maximum gain
        
        normalized = audio_data * gain
        
        # Prevent clipping
        max_val = np.max(np.abs(normalized))
        if max_val > 1.0:
            normalized = normalized / max_val
        
        return normalized
        
    except Exception as e:
        logger.error(f"Error normalizing audio: {e}")
        return audio_data

def db_to_linear(db: float) -> float:
    """
    Convert decibels to linear scale.
    
    Args:
        db: Value in decibels
        
    Returns:
        Linear value
    """
    return 10 ** (db / 20.0)

def linear_to_db(linear: float, min_db: float = -60.0) -> float:
    """
    Convert linear scale to decibels.
    
    Args:
        linear: Linear value
        min_db: Minimum dB value for zero/very small inputs
        
    Returns:
        Value in decibels
    """
    if linear <= 0:
        return min_db
    
    try:
        db = 20 * math.log10(abs(linear))
        return max(db, min_db)
    except ValueError:
        return min_db

def detect_silence(audio_data: np.ndarray, 
                  threshold_db: float = -40.0,
                  min_duration: float = 0.1,
                  sample_rate: int = 44100) -> List[Tuple[float, float]]:
    """
    Detect silent regions in audio data.
    
    Args:
        audio_data: Audio samples as numpy array
        threshold_db: Silence threshold in dB
        min_duration: Minimum silence duration in seconds
        sample_rate: Audio sample rate
        
    Returns:
        List of (start_time, end_time) tuples for silent regions
    """
    try:
        if len(audio_data) == 0:
            return []
        
        # Convert threshold to linear scale
        threshold_linear = db_to_linear(threshold_db)
        
        # Calculate RMS in small windows
        window_size = int(0.01 * sample_rate)  # 10ms windows
        hop_size = window_size // 2
        
        rms_values = calculate_rms_windowed(audio_data, window_size, hop_size)
        
        # Find silent windows
        silent_windows = rms_values < threshold_linear
        
        # Convert to time segments
        min_samples = int(min_duration * sample_rate)
        min_windows = max(1, min_samples // hop_size)
        
        silent_regions = []
        in_silence = False
        silence_start = 0
        
        for i, is_silent in enumerate(silent_windows):
            if is_silent and not in_silence:
                # Start of silence
                in_silence = True
                silence_start = i
            elif not is_silent and in_silence:
                # End of silence
                in_silence = False
                silence_length = i - silence_start
                
                if silence_length >= min_windows:
                    start_time = silence_start * hop_size / sample_rate
                    end_time = i * hop_size / sample_rate
                    silent_regions.append((start_time, end_time))
        
        # Handle silence extending to end of audio
        if in_silence:
            silence_length = len(silent_windows) - silence_start
            if silence_length >= min_windows:
                start_time = silence_start * hop_size / sample_rate
                end_time = len(audio_data) / sample_rate
                silent_regions.append((start_time, end_time))
        
        return silent_regions
        
    except Exception as e:
        logger.error(f"Error detecting silence: {e}")
        return []

def downsample_for_visualization(audio_data: np.ndarray, 
                               target_points: int,
                               method: str = 'peak') -> np.ndarray:
    """
    Downsample audio data for visualization.
    
    Args:
        audio_data: Audio samples as numpy array
        target_points: Target number of points for visualization
        method: Downsampling method ('peak', 'rms', 'mean')
        
    Returns:
        Downsampled audio data
    """
    try:
        if len(audio_data) <= target_points:
            return audio_data
        
        window_size = len(audio_data) // target_points
        result = []
        
        for i in range(0, len(audio_data), window_size):
            window = audio_data[i:i + window_size]
            
            if len(window) == 0:
                continue
            
            if method == 'peak':
                # Use max absolute value
                value = window[np.argmax(np.abs(window))]
            elif method == 'rms':
                # Use RMS value with sign of max
                rms = np.sqrt(np.mean(window ** 2))
                sign = np.sign(window[np.argmax(np.abs(window))])
                value = rms * sign
            elif method == 'mean':
                # Use mean value
                value = np.mean(window)
            else:
                raise ValueError(f"Unknown downsampling method: {method}")
            
            result.append(value)
        
        return np.array(result)
        
    except Exception as e:
        logger.error(f"Error downsampling audio: {e}")
        return audio_data

def estimate_audio_format_info(file_extension: str, file_size: int, duration: float) -> AudioFormatInfo:
    """
    Estimate audio format information based on file characteristics.
    
    Args:
        file_extension: File extension (e.g., '.mp3', '.wav')
        file_size: File size in bytes
        duration: Duration in seconds
        
    Returns:
        AudioFormatInfo object with estimated characteristics
    """
    ext = file_extension.lower()
    
    # Default values
    sample_rate = 44100
    channels = 2
    bit_depth = 16
    is_compressed = True
    estimated_bitrate = None
    
    if ext == '.wav':
        is_compressed = False
        format_name = "WAV"
        # Estimate bit depth from file size
        if duration > 0:
            bytes_per_second = file_size / duration
            # bytes_per_second = sample_rate * channels * (bit_depth / 8)
            estimated_bit_depth = (bytes_per_second / (sample_rate * channels)) * 8
            if estimated_bit_depth > 20:
                bit_depth = 24
            elif estimated_bit_depth > 12:
                bit_depth = 16
            else:
                bit_depth = 8
    elif ext == '.flac':
        is_compressed = False  # Lossless compression
        format_name = "FLAC"
        bit_depth = 16  # Common default
    elif ext == '.mp3':
        format_name = "MP3"
        if duration > 0:
            estimated_bitrate = int((file_size * 8) / (duration * 1000))  # kbps
    elif ext == '.ogg':
        format_name = "OGG Vorbis"
        if duration > 0:
            estimated_bitrate = int((file_size * 8) / (duration * 1000))  # kbps
    elif ext == '.m4a':
        format_name = "AAC"
        if duration > 0:
            estimated_bitrate = int((file_size * 8) / (duration * 1000))  # kbps
    else:
        format_name = f"Unknown ({ext})"
    
    return AudioFormatInfo(
        sample_rate=sample_rate,
        channels=channels,
        bit_depth=bit_depth,
        format_name=format_name,
        is_compressed=is_compressed,
        estimated_bitrate=estimated_bitrate
    )

def validate_audio_data(audio_data: np.ndarray) -> Tuple[bool, str]:
    """
    Validate audio data for common issues.
    
    Args:
        audio_data: Audio samples as numpy array
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        if audio_data is None:
            return False, "Audio data is None"
        
        if len(audio_data) == 0:
            return False, "Audio data is empty"
        
        if not isinstance(audio_data, np.ndarray):
            return False, "Audio data is not a numpy array"
        
        if audio_data.dtype not in [np.float32, np.float64, np.int16, np.int32]:
            return False, f"Unsupported audio data type: {audio_data.dtype}"
        
        # Check for NaN or infinity values
        if np.any(np.isnan(audio_data)):
            return False, "Audio data contains NaN values"
        
        if np.any(np.isinf(audio_data)):
            return False, "Audio data contains infinite values"
        
        # Check for reasonable value range
        max_val = np.max(np.abs(audio_data))
        if max_val == 0:
            return False, "Audio data contains only silence"
        
        if audio_data.dtype in [np.float32, np.float64]:
            if max_val > 10.0:  # Unusually high for normalized float audio
                return False, f"Audio values unusually high: max = {max_val}"
        
        return True, "Audio data is valid"
        
    except Exception as e:
        return False, f"Error validating audio data: {e}"
