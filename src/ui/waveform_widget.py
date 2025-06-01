"""
Waveform visualization widget for audio data display.

This widget provides real-time waveform visualization with playhead tracking,
seeking functionality, and interactive audio timeline display.
"""

import logging
from typing import Optional, List, Tuple
import math

import numpy as np
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from PySide6.QtCore import Qt, Signal, QTimer, QRect, QPoint
from PySide6.QtGui import QPainter, QPen, QBrush, QColor, QFont, QFontMetrics

logger = logging.getLogger(__name__)

class WaveformWidget(QWidget):
    """Widget for displaying audio waveform with playhead and seeking."""
    
    # Signals
    seek_requested = Signal(float)  # Emitted when user clicks to seek
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Audio data
        self.audio_data: Optional[np.ndarray] = None
        self.sample_rate: int = 44100
        self.duration: float = 0.0
        self.current_position: float = 0.0
        
        # Display settings
        self.zoom_level: float = 1.0
        self.scroll_position: float = 0.0
        self.waveform_color = QColor(70, 130, 180)  # Steel blue
        self.playhead_color = QColor(255, 100, 100)  # Red
        self.background_color = QColor(240, 240, 240)  # Light gray
        self.grid_color = QColor(200, 200, 200)  # Gray
        
        # UI state
        self.is_seeking = False
        self.mouse_position: Optional[QPoint] = None
        
        # Setup widget
        self.setMinimumHeight(100)
        self.setMouseTracking(True)
        self.setFocusPolicy(Qt.FocusPolicy.ClickFocus)
        
        # Create layout with info label
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        
        # Info label at top
        self.info_label = QLabel("No audio loaded")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.info_label)
        
        # Main waveform area takes remaining space
        layout.addStretch(1)
        
        logger.info("Waveform widget initialized")
    
    def set_audio_data(self, audio_data: np.ndarray, sample_rate: int):
        """Set audio data for waveform display."""
        try:
            self.audio_data = audio_data
            self.sample_rate = sample_rate
            self.duration = len(audio_data) / sample_rate
            
            # Update info label
            self.info_label.setText(
                f"Duration: {self.duration:.1f}s, "
                f"Sample Rate: {sample_rate}Hz, "
                f"Samples: {len(audio_data):,}"
            )
            
            # Reset view
            self.zoom_level = 1.0
            self.scroll_position = 0.0
            
            self.update()
            logger.info(f"Waveform data updated: {self.duration:.1f}s")
            
        except Exception as e:
            logger.error(f"Error setting audio data: {e}")
    
    def set_position(self, position: float):
        """Set current playback position."""
        if self.current_position != position:
            self.current_position = position
            self.update()
    
    def set_duration(self, duration: float):
        """Set audio duration."""
        if self.duration != duration:
            self.duration = duration
            self.update()
    
    def clear(self):
        """Clear the waveform display."""
        self.audio_data = None
        self.duration = 0.0
        self.current_position = 0.0
        self.info_label.setText("No audio loaded")
        self.update()
    
    def paintEvent(self, event):
        """Paint the waveform."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        
        # Get dimensions
        rect = self.rect()
        info_height = self.info_label.height() + 10  # Account for layout margins
        waveform_rect = QRect(rect.x(), rect.y() + info_height, 
                            rect.width(), rect.height() - info_height)
        
        # Fill background
        painter.fillRect(waveform_rect, self.background_color)
        
        if self.audio_data is None or len(self.audio_data) == 0:
            self._draw_no_data_message(painter, waveform_rect)
            return
        
        try:
            # Draw time grid
            self._draw_time_grid(painter, waveform_rect)
            
            # Draw waveform
            self._draw_waveform(painter, waveform_rect)
            
            # Draw playhead
            self._draw_playhead(painter, waveform_rect)
            
            # Draw mouse position indicator
            if self.mouse_position:
                self._draw_mouse_indicator(painter, waveform_rect)
                
        except Exception as e:
            logger.error(f"Error painting waveform: {e}")
    
    def _draw_no_data_message(self, painter: QPainter, rect: QRect):
        """Draw message when no audio data is available."""
        painter.setPen(QPen(QColor(150, 150, 150)))
        painter.setFont(QFont("Arial", 12))
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, 
                        "Click 'Open Audio File' to load audio")
    
    def _draw_time_grid(self, painter: QPainter, rect: QRect):
        """Draw time grid lines and labels."""
        if self.duration <= 0:
            return
        
        painter.setPen(QPen(self.grid_color, 1))
        painter.setFont(QFont("Arial", 9))
        
        # Calculate time intervals
        width = rect.width()
        pixels_per_second = width / (self.duration / self.zoom_level)
        
        # Determine appropriate time interval
        if pixels_per_second > 100:
            interval = 1.0  # 1 second
        elif pixels_per_second > 50:
            interval = 2.0  # 2 seconds
        elif pixels_per_second > 20:
            interval = 5.0  # 5 seconds
        elif pixels_per_second > 10:
            interval = 10.0  # 10 seconds
        else:
            interval = 30.0  # 30 seconds
        
        # Draw grid lines
        start_time = self.scroll_position
        end_time = start_time + (self.duration / self.zoom_level)
        
        current_time = math.ceil(start_time / interval) * interval
        
        while current_time <= end_time:
            x = self._time_to_x(current_time, rect.width())
            if 0 <= x <= rect.width():
                # Draw vertical line
                painter.drawLine(x, rect.top(), x, rect.bottom())
                
                # Draw time label
                time_text = self._format_time(current_time)
                text_rect = QRect(x - 30, rect.bottom() - 20, 60, 15)
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, time_text)
            
            current_time += interval
    
    def _draw_waveform(self, painter: QPainter, rect: QRect):
        """Draw the audio waveform."""
        width = rect.width()
        height = rect.height() - 25  # Leave space for time labels
        center_y = rect.top() + height // 2
        
        # Calculate visible data range
        visible_duration = self.duration / self.zoom_level
        start_time = self.scroll_position
        end_time = min(start_time + visible_duration, self.duration)
        
        start_sample = int(start_time * self.sample_rate)
        end_sample = int(end_time * self.sample_rate)
        
        if start_sample >= len(self.audio_data):
            return
        
        end_sample = min(end_sample, len(self.audio_data))
        visible_data = self.audio_data[start_sample:end_sample]
        
        if len(visible_data) == 0:
            return
        
        # Downsample for display if needed
        samples_per_pixel = len(visible_data) / width
        
        painter.setPen(QPen(self.waveform_color, 1))
        
        if samples_per_pixel > 1:
            # Multiple samples per pixel - show min/max envelope
            self._draw_envelope_waveform(painter, visible_data, width, height, 
                                       center_y, samples_per_pixel)
        else:
            # Sample-accurate drawing
            self._draw_detailed_waveform(painter, visible_data, width, height, center_y)
    
    def _draw_envelope_waveform(self, painter: QPainter, data: np.ndarray, 
                              width: int, height: int, center_y: int, samples_per_pixel: float):
        """Draw waveform using min/max envelope for performance."""
        pixels = []
        
        for x in range(width):
            start_idx = int(x * samples_per_pixel)
            end_idx = int((x + 1) * samples_per_pixel)
            end_idx = min(end_idx, len(data))
            
            if start_idx < len(data):
                chunk = data[start_idx:end_idx]
                if len(chunk) > 0:
                    min_val = np.min(chunk)
                    max_val = np.max(chunk)
                    
                    # Convert to pixel coordinates
                    min_y = center_y + int(min_val * height * 0.4)
                    max_y = center_y + int(max_val * height * 0.4)
                    
                    pixels.append((x, min_y, max_y))
        
        # Draw the envelope
        for x, min_y, max_y in pixels:
            painter.drawLine(x, min_y, x, max_y)
    
    def _draw_detailed_waveform(self, painter: QPainter, data: np.ndarray, 
                              width: int, height: int, center_y: int):
        """Draw detailed waveform for zoomed-in view."""
        if len(data) < 2:
            return
        
        # Create path for smooth waveform
        prev_x = 0
        prev_y = center_y + int(data[0] * height * 0.4)
        
        for i in range(1, min(len(data), width)):
            x = int(i * width / len(data))
            y = center_y + int(data[i] * height * 0.4)
            
            painter.drawLine(prev_x, prev_y, x, y)
            prev_x, prev_y = x, y
    
    def _draw_playhead(self, painter: QPainter, rect: QRect):
        """Draw the current playback position indicator."""
        if self.duration <= 0:
            return
        
        x = self._time_to_x(self.current_position, rect.width())
        
        if 0 <= x <= rect.width():
            painter.setPen(QPen(self.playhead_color, 2))
            painter.drawLine(x, rect.top(), x, rect.bottom() - 25)
            
            # Draw playhead time
            painter.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            time_text = self._format_time(self.current_position)
            text_rect = QRect(x - 30, rect.top(), 60, 15)
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, time_text)
    
    def _draw_mouse_indicator(self, painter: QPainter, rect: QRect):
        """Draw mouse position indicator."""
        if not self.mouse_position:
            return
        
        x = self.mouse_position.x()
        if 0 <= x <= rect.width():
            # Draw vertical line
            painter.setPen(QPen(QColor(100, 100, 100), 1, Qt.PenStyle.DashLine))
            painter.drawLine(x, rect.top(), x, rect.bottom() - 25)
            
            # Draw time at mouse position
            time_at_mouse = self._x_to_time(x, rect.width())
            if 0 <= time_at_mouse <= self.duration:
                painter.setFont(QFont("Arial", 9))
                time_text = self._format_time(time_at_mouse)
                text_rect = QRect(x - 30, rect.bottom() - 40, 60, 15)
                painter.fillRect(text_rect, QColor(255, 255, 255, 200))
                painter.setPen(QPen(QColor(0, 0, 0)))
                painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, time_text)
    
    def _time_to_x(self, time: float, width: int) -> int:
        """Convert time to x coordinate."""
        if self.duration <= 0:
            return 0
        
        visible_duration = self.duration / self.zoom_level
        relative_time = time - self.scroll_position
        return int((relative_time / visible_duration) * width)
    
    def _x_to_time(self, x: int, width: int) -> float:
        """Convert x coordinate to time."""
        if width <= 0:
            return 0.0
        
        visible_duration = self.duration / self.zoom_level
        relative_time = (x / width) * visible_duration
        return self.scroll_position + relative_time
    
    def _format_time(self, seconds: float) -> str:
        """Format time for display."""
        if seconds < 0:
            seconds = 0
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
    
    def mousePressEvent(self, event):
        """Handle mouse press for seeking."""
        if event.button() == Qt.MouseButton.LeftButton and self.duration > 0:
            # Calculate time at click position
            rect = self.rect()
            info_height = self.info_label.height() + 10
            waveform_rect = QRect(rect.x(), rect.y() + info_height, 
                                rect.width(), rect.height() - info_height)
            
            x = event.position().x()
            time_at_click = self._x_to_time(x, waveform_rect.width())
            
            if 0 <= time_at_click <= self.duration:
                self.seek_requested.emit(time_at_click)
                self.is_seeking = True
        
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        """Handle mouse move for position indicator."""
        self.mouse_position = event.position().toPoint()
        
        if self.is_seeking and self.duration > 0:
            # Continue seeking while dragging
            rect = self.rect()
            info_height = self.info_label.height() + 10
            waveform_rect = QRect(rect.x(), rect.y() + info_height, 
                                rect.width(), rect.height() - info_height)
            
            x = event.position().x()
            time_at_drag = self._x_to_time(x, waveform_rect.width())
            
            if 0 <= time_at_drag <= self.duration:
                self.seek_requested.emit(time_at_drag)
        
        self.update()
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_seeking = False
        
        super().mouseReleaseEvent(event)
    
    def leaveEvent(self, event):
        """Handle mouse leave."""
        self.mouse_position = None
        self.update()
        super().leaveEvent(event)
    
    def wheelEvent(self, event):
        """Handle mouse wheel for zooming."""
        if self.duration > 0:
            # Zoom in/out
            delta = event.angleDelta().y()
            zoom_factor = 1.1 if delta > 0 else 1.0 / 1.1
            
            old_zoom = self.zoom_level
            self.zoom_level = max(0.1, min(10.0, self.zoom_level * zoom_factor))
            
            # Adjust scroll position to keep mouse position stable
            if self.mouse_position:
                mouse_time = self._x_to_time(self.mouse_position.x(), self.width())
                
                # Calculate new scroll position
                visible_duration = self.duration / self.zoom_level
                mouse_ratio = self.mouse_position.x() / self.width()
                
                self.scroll_position = mouse_time - (visible_duration * mouse_ratio)
                self.scroll_position = max(0, min(self.scroll_position, 
                                                self.duration - visible_duration))
            
            self.update()
        
        super().wheelEvent(event)
