"""
High-performance audio loader with smart caching.
"""

import sys
import time
from pathlib import Path
from typing import Optional, Dict, Any
from PySide6.QtCore import QObject, Signal, QThread
import numpy as np
import os  # Import the os module

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
        """Load BC1 file with revolutionary speed."""
        try:
            self.progress_updated.emit("פותח קובץ BC1 מוצפן...", 10)

            # Use the BC1 format module to open the file
            with open(self.file_path, 'rb') as f:
                bundle = open_bc1(f) # Pass the file object

            self.progress_updated.emit("מפענח אודיו מקובץ BC1...", 30)

            # Verify temporary audio file exists and is valid
            if not os.path.exists(bundle.audio_file):
                raise Exception(f"קובץ אודיו זמני לא נמצא: {bundle.audio_file}")

            if os.path.getsize(bundle.audio_file) == 0:
                raise Exception("קובץ אודיו זמני ריק")

            # Load audio data using librosa with error handling
            import librosa
            try:
                audio_data, sample_rate = librosa.load(bundle.audio_file, sr=None, mono=True)
            except Exception as librosa_error:
                # Fallback to scipy
                try:
                    from scipy.io.wavfile import read
                    sample_rate, audio_data = read(bundle.audio_file)
                    # Convert to float and normalize
                    if audio_data.dtype == np.int16:
                        audio_data = audio_data.astype(np.float32) / 32767.0
                    elif audio_data.dtype == np.int32:
                        audio_data = audio_data.astype(np.float32) / 2147483647.0
                except Exception as scipy_error:
                    raise Exception(f"Failed to load audio with librosa ({librosa_error}) and scipy ({scipy_error})")

            self.progress_updated.emit("מעבד נתוני אודיו...", 60)

            # Validate audio data
            if audio_data is None or len(audio_data) == 0:
                raise Exception("נתוני אודיו ריקים")

            # Calculate duration
            duration = len(audio_data) / sample_rate

            self.progress_updated.emit("מעבד תמלול...", 80)

            # Store the bundle and temp file for cleanup and media player access
            self.current_bundle = bundle
            self.temp_audio_file = bundle.audio_file

            # CRITICAL: Make sure the temp file path is accessible
            if not os.access(bundle.audio_file, os.R_OK):
                raise Exception(f"אין הרשאת קריאה לקובץ זמני: {bundle.audio_file}")

            self.progress_updated.emit("השלמת טעינה...", 100)

            # Emit signals
            self.audio_loaded.emit(audio_data, sample_rate, duration)

            if bundle.segments:
                self.transcript_loaded.emit(bundle.segments)

            if detailed_logger:
                detailed_logger.info(f"BC1 נטען בהצלחה: {duration:.1f}s, {len(bundle.segments)} קטעים, קובץ זמני: {bundle.audio_file}")

        except Exception as e:
            if detailed_logger:
                detailed_logger.exception(f"שגיאה בטעינת BC1: {e}")
            self.error_occurred.emit(f"שגיאה בטעינת BC1: {e}")


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