"""
High-performance audio loader with smart caching.
"""

import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any
from PySide6.QtCore import QObject, Signal, QThread
import numpy as np

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from utils.logger import detailed_logger
    from formats.bc1_format import open_bc1
    import librosa
except ImportError as e:
    detailed_logger = None

class FastAudioLoader(QThread):
    """Ultra-fast audio loader with optimization."""
    
    audio_loaded = Signal(object, int, float)  # audio_data, sample_rate, duration
    transcript_loaded = Signal(list)  # segments
    error_occurred = Signal(str)
    progress_updated = Signal(str, int)  # message, percentage
    
    def __init__(self, file_path: str, is_bc1: bool = False):
        super().__init__()
        self.file_path = file_path
        self.is_bc1 = is_bc1
        self.temp_audio_file = None
    
    def run(self):
        """Load audio with optimizations."""
        try:
            if detailed_logger:
                detailed_logger.start_operation("טעינה מהירה")
            
            start_time = time.time()
            self.progress_updated.emit("מתחיל טעינה...", 10)
            
            if self.is_bc1:
                self._load_bc1_fast()
            else:
                self._load_regular_fast()
            
            load_time = time.time() - start_time
            if detailed_logger:
                detailed_logger.end_operation("טעינה מהירה")
                detailed_logger.info(f"טעינה הושלמה ב-{load_time:.2f}s")
            
        except Exception as e:
            if detailed_logger:
                detailed_logger.exception(f"שגיאה בטעינה: {e}")
            self.error_occurred.emit(str(e))
    
    def _load_bc1_fast(self):
        """Load BC1 with speed optimizations."""
        self.progress_updated.emit("פותח BC1...", 20)
        
        with open(self.file_path, 'rb') as f:
            bc1_data = f.read()
        
        self.progress_updated.emit("מפענח BC1...", 40)
        
        from io import BytesIO
        bundle = open_bc1(BytesIO(bc1_data))
        
        self.progress_updated.emit("טוען אודיו...", 60)
        
        # Fast audio loading with downsampling for performance
        audio_data, sr = librosa.load(
            bundle.audio_file,
            sr=22050,  # Downsample for speed
            mono=True,  # Mono for performance
            dtype=np.float32
        )
        
        self.progress_updated.emit("מסיים עיבוד...", 90)
        
        duration = len(audio_data) / sr
        self.temp_audio_file = bundle.audio_file
        
        # Emit results
        self.audio_loaded.emit(audio_data, sr, duration)
        
        if bundle.segments:
            self.transcript_loaded.emit(bundle.segments)
        
        self.progress_updated.emit("הושלם!", 100)
    
    def _load_regular_fast(self):
        """Load regular audio with optimizations."""
        self.progress_updated.emit("טוען אודיו...", 40)
        
        audio_data, sr = librosa.load(
            self.file_path,
            sr=22050,
            mono=True,
            dtype=np.float32
        )
        
        self.progress_updated.emit("מעבד...", 80)
        
        duration = len(audio_data) / sr
        self.temp_audio_file = self.file_path
        
        self.audio_loaded.emit(audio_data, sr, duration)
        self.progress_updated.emit("הושלם!", 100)