"""
Advanced Waveform and Spectrogram visualization.

This module provides advanced audio visualization including waveform display,
spectrogram with FFT analysis, and speaker diarization visualization.
"""

import numpy as np
import logging
from typing import Optional, List, Dict, Tuple, Any
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from PySide6.QtCore import Qt, QTimer, QRect, Signal, QThread
from PySide6.QtGui import QPainter, QColor, QPen, QBrush, QLinearGradient
import scipy.signal
import librosa

try:
    from utils.logger import get_logger
    detailed_logger = get_logger()
except ImportError:
    detailed_logger = None

logger = logging.getLogger(__name__)

class SpectrogramWorker(QThread):
    """Worker thread for computing spectrogram data."""
    
    spectrogramReady = Signal(np.ndarray, np.ndarray, np.ndarray)
    
    def __init__(self, audio_data: np.ndarray, sample_rate: int):
        super().__init__()
        self.audio_data = audio_data
        self.sample_rate = sample_rate
        
    def run(self):
        """Compute spectrogram in background thread."""
        try:
            if detailed_logger:
                detailed_logger.start_operation("חישוב ספקטרוגרמה")
            
            # Compute spectrogram using scipy
            frequencies, times, Sxx = scipy.signal.spectrogram(
                self.audio_data,
                fs=self.sample_rate,
                window='hann',
                nperseg=2048,
                noverlap=1024,
                nfft=2048
            )
            
            # Convert to dB scale
            Sxx_db = 10 * np.log10(Sxx + 1e-10)
            
            # Limit frequency range to 0-10kHz as per spec
            max_freq_idx = np.where(frequencies <= 10000)[0][-1]
            frequencies = frequencies[:max_freq_idx]
            Sxx_db = Sxx_db[:max_freq_idx, :]
            
            if detailed_logger:
                detailed_logger.end_operation("חישוב ספקטרוגרמה")
                detailed_logger.log_audio_operation("ספקטרוגרמה מוכנה", {
                    "freq_bins": len(frequencies),
                    "time_bins": len(times),
                    "max_freq": frequencies[-1],
                    "duration": times[-1]
                })
            
            self.spectrogramReady.emit(frequencies, times, Sxx_db)
            
        except Exception as e:
            if detailed_logger:
                detailed_logger.exception(f"שגיאה בחישוב ספקטרוגרמה: {e}")
            logger.exception(f"Error computing spectrogram: {e}")

class AdvancedWaveformWidget(QWidget):
    """Advanced waveform widget with spectrogram and speaker diarization."""
    
    # Signals
    seekRequested = Signal(float)
    regionSelected = Signal(float, float)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Audio data
        self.audio_data: Optional[np.ndarray] = None
        self.sample_rate: int = 44100
        self.duration: float = 0.0
        
        # Visualization data
        self.waveform_data: Optional[np.ndarray] = None
        self.spectrogram_freqs: Optional[np.ndarray] = None
        self.spectrogram_times: Optional[np.ndarray] = None
        self.spectrogram_data: Optional[np.ndarray] = None
        
        # Playback state
        self.current_position: float = 0.0
        self.zoom_level: float = 1.0
        self.scroll_position: float = 0.0
        
        # Speaker diarization
        self.speaker_segments: List[Dict[str, Any]] = []
        self.speaker_colors: Dict[str, QColor] = {}
        
        # UI state
        self.show_spectrogram: bool = True
        self.show_waveform: bool = True
        self.spectrogram_height_ratio: float = 0.6  # 60% for spectrogram, 40% for waveform
        
        # Worker thread
        self.spectrogram_worker: Optional[SpectrogramWorker] = None
        
        self._setup_ui()
        
        if detailed_logger:
            detailed_logger.info("יצירת ווידג'ט ויזואליזציה מתקדם")
    
    def _setup_ui(self):
        """Setup the user interface."""
        self.setMinimumHeight(160)
        self.setMinimumWidth(400)
        
        # Set RTL layout
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        # Setup styling
        self.setStyleSheet("""
            QWidget {
                background-color: #1E1E1E;
                border: 1px solid #3C3C3C;
                border-radius: 8px;
            }
        """)
        
        # Add control buttons
        layout = QVBoxLayout(self)
        
        controls_layout = QHBoxLayout()
        
        self.waveform_btn = QPushButton("גלים")
        self.waveform_btn.setCheckable(True)
        self.waveform_btn.setChecked(True)
        self.waveform_btn.clicked.connect(self._toggle_waveform)
        
        self.spectrogram_btn = QPushButton("ספקטרוגרמה")
        self.spectrogram_btn.setCheckable(True)
        self.spectrogram_btn.setChecked(True)
        self.spectrogram_btn.clicked.connect(self._toggle_spectrogram)
        
        self.zoom_in_btn = QPushButton("זום +")
        self.zoom_in_btn.clicked.connect(self._zoom_in)
        
        self.zoom_out_btn = QPushButton("זום -")
        self.zoom_out_btn.clicked.connect(self._zoom_out)
        
        self.reset_zoom_btn = QPushButton("איפוס זום")
        self.reset_zoom_btn.clicked.connect(self._reset_zoom)
        
        controls_layout.addWidget(self.waveform_btn)
        controls_layout.addWidget(self.spectrogram_btn)
        controls_layout.addWidget(self.zoom_in_btn)
        controls_layout.addWidget(self.zoom_out_btn)
        controls_layout.addWidget(self.reset_zoom_btn)
        controls_layout.addStretch()
        
        # Style buttons
        button_style = """
            QPushButton {
                background-color: #3C3C3C;
                border: 1px solid #5C5C5C;
                border-radius: 4px;
                padding: 4px 8px;
                color: white;
                font-size: 10px;
            }
            QPushButton:hover {
                background-color: #4C4C4C;
            }
            QPushButton:checked {
                background-color: #4CAF50;
            }
        """
        
        for btn in [self.waveform_btn, self.spectrogram_btn, self.zoom_in_btn, 
                   self.zoom_out_btn, self.reset_zoom_btn]:
            btn.setStyleSheet(button_style)
        
        layout.addLayout(controls_layout)
        layout.addStretch()
    
    def set_audio_data(self, audio_data: np.ndarray, sample_rate: int):
        """Set audio data for visualization."""
        try:
            if detailed_logger:
                detailed_logger.start_operation("הגדרת נתוני אודיו לויזואליזציה")
            
            self.audio_data = audio_data
            self.sample_rate = sample_rate
            self.duration = len(audio_data) / sample_rate
            
            # Downsample for waveform display
            self._prepare_waveform_data()
            
            # Start spectrogram computation in background
            self._compute_spectrogram()
            
            if detailed_logger:
                detailed_logger.end_operation("הגדרת נתוני אודיו לויזואליזציה")
                detailed_logger.log_audio_operation("נתוני אודיו הוגדרו", {
                    "sample_rate": sample_rate,
                    "duration": self.duration,
                    "samples": len(audio_data)
                })
            
            self.update()
            
        except Exception as e:
            if detailed_logger:
                detailed_logger.exception(f"שגיאה בהגדרת נתוני אודיו: {e}")
            logger.exception(f"Error setting audio data: {e}")
    
    def _prepare_waveform_data(self):
        """Prepare waveform data for display."""
        if self.audio_data is None:
            return
        
        # Downsample to reasonable resolution for display
        target_samples = 2000  # Target number of samples for display
        
        if len(self.audio_data) > target_samples:
            # Calculate downsampling factor
            downsample_factor = len(self.audio_data) // target_samples
            
            # Create envelope by taking max/min in each window
            waveform_data = []
            for i in range(0, len(self.audio_data), downsample_factor):
                window = self.audio_data[i:i + downsample_factor]
                if len(window) > 0:
                    waveform_data.append(np.max(np.abs(window)))
            
            self.waveform_data = np.array(waveform_data)
        else:
            self.waveform_data = np.abs(self.audio_data)
        
        if detailed_logger:
            detailed_logger.info(f"נתוני גלים הוכנו: {len(self.waveform_data)} דגימות")
    
    def _compute_spectrogram(self):
        """Compute spectrogram in background thread."""
        if self.audio_data is None:
            return
        
        # Stop any existing worker
        if self.spectrogram_worker and self.spectrogram_worker.isRunning():
            self.spectrogram_worker.terminate()
            self.spectrogram_worker.wait()
        
        # Start new worker
        self.spectrogram_worker = SpectrogramWorker(self.audio_data, self.sample_rate)
        self.spectrogram_worker.spectrogramReady.connect(self._on_spectrogram_ready)
        self.spectrogram_worker.start()
    
    def _on_spectrogram_ready(self, frequencies: np.ndarray, times: np.ndarray, spectrogram: np.ndarray):
        """Handle spectrogram computation completion."""
        self.spectrogram_freqs = frequencies
        self.spectrogram_times = times
        self.spectrogram_data = spectrogram
        
        if detailed_logger:
            detailed_logger.info("ספקטרוגרמה מוכנה להצגה")
        
        self.update()
    
    def set_position(self, position: float):
        """Set current playback position."""
        self.current_position = position
        
        # Auto-scroll to keep position visible
        visible_duration = self.duration / self.zoom_level
        if (position < self.scroll_position or 
            position > self.scroll_position + visible_duration):
            self.scroll_position = max(0, position - visible_duration / 2)
        
        self.update()
    
    def set_speaker_segments(self, segments: List[Dict[str, Any]]):
        """Set speaker diarization segments."""
        self.speaker_segments = segments
        
        # Generate colors for speakers
        colors = [
            QColor(255, 107, 107),  # Red
            QColor(78, 205, 196),   # Teal
            QColor(255, 195, 0),    # Yellow
            QColor(199, 125, 255),  # Purple
            QColor(129, 236, 236),  # Cyan
            QColor(255, 154, 162),  # Pink
        ]
        
        speakers = set(segment.get('speaker', 'unknown') for segment in segments)
        self.speaker_colors = {}
        
        for i, speaker in enumerate(speakers):
            self.speaker_colors[speaker] = colors[i % len(colors)]
        
        if detailed_logger:
            detailed_logger.log_audio_operation("הגדרת דוברים", {
                "segments_count": len(segments),
                "speakers_count": len(speakers),
                "speakers": list(speakers)
            })
        
        self.update()
    
    def paintEvent(self, event):
        """Paint the waveform and spectrogram."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        rect = self.rect()
        painter.fillRect(rect, QColor(30, 30, 30))
        
        if self.duration == 0:
            painter.setPen(QColor(150, 150, 150))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "טען קובץ אודיו לויזואליזציה")
            return
        
        # Calculate visible time range
        visible_duration = self.duration / self.zoom_level
        start_time = self.scroll_position
        end_time = min(start_time + visible_duration, self.duration)
        
        # Draw background grid
        self._draw_time_grid(painter, rect, start_time, end_time)
        
        # Split areas for spectrogram and waveform
        if self.show_spectrogram and self.show_waveform:
            spectrogram_rect = QRect(rect.x(), rect.y() + 30, rect.width(), 
                                   int(rect.height() * self.spectrogram_height_ratio))
            waveform_rect = QRect(rect.x(), spectrogram_rect.bottom(), rect.width(),
                                rect.height() - spectrogram_rect.height() - 30)
        elif self.show_spectrogram:
            spectrogram_rect = QRect(rect.x(), rect.y() + 30, rect.width(), rect.height() - 30)
            waveform_rect = QRect()
        elif self.show_waveform:
            waveform_rect = QRect(rect.x(), rect.y() + 30, rect.width(), rect.height() - 30)
            spectrogram_rect = QRect()
        else:
            return
        
        # Draw spectrogram
        if self.show_spectrogram and not spectrogram_rect.isEmpty():
            self._draw_spectrogram(painter, spectrogram_rect, start_time, end_time)
        
        # Draw speaker segments
        if self.speaker_segments:
            self._draw_speaker_segments(painter, rect, start_time, end_time)
        
        # Draw waveform
        if self.show_waveform and not waveform_rect.isEmpty():
            self._draw_waveform(painter, waveform_rect, start_time, end_time)
        
        # Draw playhead
        self._draw_playhead(painter, rect, start_time, end_time)
    
    def _draw_time_grid(self, painter: QPainter, rect: QRect, start_time: float, end_time: float):
        """Draw time grid lines."""
        painter.setPen(QPen(QColor(60, 60, 60), 1))
        
        # Calculate time step
        duration = end_time - start_time
        if duration <= 10:
            step = 1.0
        elif duration <= 60:
            step = 5.0
        elif duration <= 300:
            step = 30.0
        else:
            step = 60.0
        
        # Draw vertical grid lines
        time = int(start_time / step) * step
        while time <= end_time:
            if time >= start_time:
                x = rect.x() + int((time - start_time) / duration * rect.width())
                painter.drawLine(x, rect.y(), x, rect.bottom())
                
                # Draw time label
                painter.setPen(QColor(150, 150, 150))
                painter.drawText(x + 2, rect.y() + 15, f"{int(time//60):02d}:{int(time%60):02d}")
                painter.setPen(QColor(60, 60, 60))
            
            time += step
    
    def _draw_spectrogram(self, painter: QPainter, rect: QRect, start_time: float, end_time: float):
        """Draw spectrogram."""
        if (self.spectrogram_data is None or 
            self.spectrogram_times is None or 
            self.spectrogram_freqs is None):
            painter.setPen(QColor(100, 100, 100))
            painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, "מחשב ספקטרוגרמה...")
            return
        
        # Find visible time indices
        time_mask = ((self.spectrogram_times >= start_time) & 
                     (self.spectrogram_times <= end_time))
        
        if not np.any(time_mask):
            return
        
        visible_times = self.spectrogram_times[time_mask]
        visible_data = self.spectrogram_data[:, time_mask]
        
        # Normalize data for color mapping
        vmin, vmax = np.percentile(visible_data, [5, 95])
        normalized_data = np.clip((visible_data - vmin) / (vmax - vmin), 0, 1)
        
        # Draw spectrogram pixels
        time_step = rect.width() / len(visible_times)
        freq_step = rect.height() / len(self.spectrogram_freqs)
        
        for i, time in enumerate(visible_times):
            x = rect.x() + int(i * time_step)
            
            for j, freq in enumerate(self.spectrogram_freqs):
                y = rect.bottom() - int(j * freq_step)
                
                # Color mapping (blue to red)
                intensity = normalized_data[j, i]
                red = int(255 * intensity)
                blue = int(255 * (1 - intensity))
                green = int(128 * intensity)
                
                color = QColor(red, green, blue, 180)
                painter.fillRect(x, y - int(freq_step), max(1, int(time_step)), max(1, int(freq_step)), color)
    
    def _draw_waveform(self, painter: QPainter, rect: QRect, start_time: float, end_time: float):
        """Draw waveform."""
        if self.waveform_data is None:
            return
        
        # Calculate visible samples
        start_sample = int(start_time / self.duration * len(self.waveform_data))
        end_sample = int(end_time / self.duration * len(self.waveform_data))
        start_sample = max(0, start_sample)
        end_sample = min(len(self.waveform_data), end_sample)
        
        if start_sample >= end_sample:
            return
        
        visible_data = self.waveform_data[start_sample:end_sample]
        
        # Set up gradient
        gradient = QLinearGradient(0, rect.top(), 0, rect.bottom())
        gradient.setColorAt(0, QColor(78, 205, 196))  # Teal
        gradient.setColorAt(1, QColor(199, 125, 255))  # Purple
        
        painter.setBrush(QBrush(gradient))
        painter.setPen(QPen(QColor(78, 205, 196), 1))
        
        # Draw waveform
        center_y = rect.center().y()
        max_amplitude = rect.height() / 2 - 10
        
        for i, amplitude in enumerate(visible_data):
            x = rect.x() + int(i / len(visible_data) * rect.width())
            height = int(amplitude * max_amplitude)
            
            painter.drawLine(x, center_y - height, x, center_y + height)
    
    def _draw_speaker_segments(self, painter: QPainter, rect: QRect, start_time: float, end_time: float):
        """Draw speaker diarization segments."""
        duration = end_time - start_time
        
        # Draw speaker bar at the top
        speaker_bar_height = 20
        speaker_rect = QRect(rect.x(), rect.y() + 5, rect.width(), speaker_bar_height)
        
        for segment in self.speaker_segments:
            seg_start = segment.get('start_time', 0)
            seg_end = segment.get('end_time', 0)
            speaker = segment.get('speaker', 'unknown')
            
            # Check if segment is visible
            if seg_end < start_time or seg_start > end_time:
                continue
            
            # Calculate segment position
            visible_start = max(seg_start, start_time)
            visible_end = min(seg_end, end_time)
            
            x_start = int((visible_start - start_time) / duration * rect.width())
            x_end = int((visible_end - start_time) / duration * rect.width())
            
            # Get speaker color
            color = self.speaker_colors.get(speaker, QColor(128, 128, 128))
            
            # Draw segment
            segment_rect = QRect(rect.x() + x_start, speaker_rect.y(), 
                               x_end - x_start, speaker_rect.height())
            painter.fillRect(segment_rect, color)
            
            # Draw speaker label if segment is wide enough
            if segment_rect.width() > 30:
                painter.setPen(QColor(255, 255, 255))
                painter.drawText(segment_rect, Qt.AlignmentFlag.AlignCenter, speaker)
    
    def _draw_playhead(self, painter: QPainter, rect: QRect, start_time: float, end_time: float):
        """Draw playback position indicator."""
        if start_time <= self.current_position <= end_time:
            duration = end_time - start_time
            x = rect.x() + int((self.current_position - start_time) / duration * rect.width())
            
            # Draw playhead line
            painter.setPen(QPen(QColor(255, 255, 255), 2))
            painter.drawLine(x, rect.y(), x, rect.bottom())
            
            # Draw time indicator
            painter.setPen(QColor(255, 255, 255))
            time_text = f"{int(self.current_position//60):02d}:{int(self.current_position%60):02d}"
            painter.drawText(x + 5, rect.y() + 30, time_text)
    
    def mousePressEvent(self, event):
        """Handle mouse press for seeking."""
        if event.button() == Qt.MouseButton.LeftButton:
            rect = self.rect()
            if rect.contains(event.position().toPoint()):
                # Calculate time position
                visible_duration = self.duration / self.zoom_level
                relative_x = (event.position().x() - rect.x()) / rect.width()
                time_position = self.scroll_position + relative_x * visible_duration
                
                if 0 <= time_position <= self.duration:
                    if detailed_logger:
                        detailed_logger.log_audio_operation("לחיצה על ויזואליזציה", {
                            "time_position": time_position,
                            "relative_x": relative_x
                        })
                    
                    self.seekRequested.emit(time_position)
    
    def wheelEvent(self, event):
        """Handle mouse wheel for zooming."""
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            # Zoom
            delta = event.angleDelta().y()
            if delta > 0:
                self._zoom_in()
            else:
                self._zoom_out()
        else:
            # Scroll
            delta = event.angleDelta().y()
            scroll_amount = self.duration / self.zoom_level * 0.1
            
            if delta > 0:
                self.scroll_position = max(0, self.scroll_position - scroll_amount)
            else:
                max_scroll = max(0, self.duration - self.duration / self.zoom_level)
                self.scroll_position = min(max_scroll, self.scroll_position + scroll_amount)
            
            self.update()
    
    def _toggle_waveform(self):
        """Toggle waveform display."""
        self.show_waveform = self.waveform_btn.isChecked()
        if detailed_logger:
            detailed_logger.log_ui_operation("החלפת תצוגת גלים", "waveform_toggle", 
                                           show=self.show_waveform)
        self.update()
    
    def _toggle_spectrogram(self):
        """Toggle spectrogram display."""
        self.show_spectrogram = self.spectrogram_btn.isChecked()
        if detailed_logger:
            detailed_logger.log_ui_operation("החלפת תצוגת ספקטרוגרמה", "spectrogram_toggle", 
                                           show=self.show_spectrogram)
        self.update()
    
    def _zoom_in(self):
        """Zoom in on waveform."""
        self.zoom_level = min(10.0, self.zoom_level * 1.5)
        if detailed_logger:
            detailed_logger.log_ui_operation("זום פנימה", "zoom", level=self.zoom_level)
        self.update()
    
    def _zoom_out(self):
        """Zoom out on waveform."""
        self.zoom_level = max(0.1, self.zoom_level / 1.5)
        if detailed_logger:
            detailed_logger.log_ui_operation("זום החוצה", "zoom", level=self.zoom_level)
        self.update()
    
    def _reset_zoom(self):
        """Reset zoom to default."""
        self.zoom_level = 1.0
        self.scroll_position = 0.0
        if detailed_logger:
            detailed_logger.log_ui_operation("איפוס זום", "zoom_reset")
        self.update()