"""
UI package for PySide6-based user interface components.

This package contains all UI widgets, windows, and interface components
for the Bina Cshera audio player application.
"""

from .main_window import MainWindow
from .waveform_widget import WaveformWidget
from .transcript_widget import TranscriptWidget
from .audio_controls import AudioControlsWidget

__all__ = ['MainWindow', 'WaveformWidget', 'TranscriptWidget', 'AudioControlsWidget']
