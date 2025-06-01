"""
Audio control widgets for playback control and audio management.

This module provides a comprehensive set of audio control widgets including
play/pause/stop buttons, seek slider, volume control, and time display.
"""

import logging
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QPushButton, QSlider, 
    QLabel, QSizePolicy, QSpacerItem, QFrame
)
from PySide6.QtCore import Qt, Signal, QTimer, QSize
from PySide6.QtGui import QIcon, QFont, QPalette

from controllers.playback_controller import PlaybackController, PlaybackState

logger = logging.getLogger(__name__)

class PlaybackButton(QPushButton):
    """Custom button for playback controls with consistent styling."""
    
    def __init__(self, text: str, parent=None):
        super().__init__(text, parent)
        self.setMinimumSize(QSize(80, 35))
        self.setMaximumSize(QSize(100, 35))
        self.setFont(QFont("Arial", 10))
        self._setup_style()
    
    def _setup_style(self):
        """Setup button styling."""
        self.setStyleSheet("""
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #c0c0c0;
                border-radius: 4px;
                padding: 5px 10px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border: 1px solid #a0a0a0;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
                border: 1px solid #808080;
            }
            QPushButton:disabled {
                background-color: #f8f8f8;
                border: 1px solid #e0e0e0;
                color: #a0a0a0;
            }
        """)

class SeekSlider(QSlider):
    """Custom seek slider with enhanced functionality."""
    
    # Signal emitted when user seeks (not during programmatic updates)
    user_seek = Signal(float)
    
    def __init__(self, parent=None):
        super().__init__(Qt.Orientation.Horizontal, parent)
        
        self.is_seeking = False
        self.duration = 0.0
        
        # Setup slider
        self.setMinimum(0)
        self.setMaximum(1000)  # Use 1000 steps for smooth seeking
        self.setValue(0)
        
        # Connect signals
        self.sliderPressed.connect(self._on_slider_pressed)
        self.sliderReleased.connect(self._on_slider_released)
        self.sliderMoved.connect(self._on_slider_moved)
        
        self._setup_style()
    
    def _setup_style(self):
        """Setup slider styling."""
        self.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #bbb;
                background: white;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #66e, stop: 1 #bbf);
                background: qlineargradient(x1: 0, y1: 0.2, x2: 1, y2: 1,
                    stop: 0 #bbf, stop: 1 #55f);
                border: 1px solid #777;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::add-page:horizontal {
                background: #fff;
                border: 1px solid #777;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #eee, stop:1 #ccc);
                border: 1px solid #777;
                width: 16px;
                margin-top: -4px;
                margin-bottom: -4px;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:hover {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #fff, stop:1 #ddd);
                border: 1px solid #444;
                border-radius: 8px;
            }
            QSlider::handle:horizontal:pressed {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #ddd, stop:1 #bbb);
                border: 1px solid #444;
                border-radius: 8px;
            }
        """)
    
    def set_duration(self, duration: float):
        """Set the duration for the slider."""
        self.duration = duration
    
    def set_position(self, position: float):
        """Set current position (only if not currently seeking)."""
        if not self.is_seeking and self.duration > 0:
            # Convert position to slider value
            value = int((position / self.duration) * self.maximum())
            self.setValue(value)
    
    def _on_slider_pressed(self):
        """Handle slider press start."""
        self.is_seeking = True
    
    def _on_slider_released(self):
        """Handle slider release."""
        self.is_seeking = False
        
        # Emit seek signal with time value
        if self.duration > 0:
            position = (self.value() / self.maximum()) * self.duration
            self.user_seek.emit(position)
    
    def _on_slider_moved(self, value):
        """Handle slider movement during seeking."""
        if self.is_seeking and self.duration > 0:
            position = (value / self.maximum()) * self.duration
            self.user_seek.emit(position)

class VolumeSlider(QSlider):
    """Volume control slider."""
    
    volume_changed = Signal(float)  # 0.0 to 1.0
    
    def __init__(self, parent=None):
        super().__init__(Qt.Orientation.Horizontal, parent)
        
        # Setup slider
        self.setMinimum(0)
        self.setMaximum(100)
        self.setValue(100)  # Default to 100% volume
        self.setMaximumWidth(100)
        
        # Connect signal
        self.valueChanged.connect(self._on_value_changed)
        
        self._setup_style()
    
    def _setup_style(self):
        """Setup volume slider styling."""
        self.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #bbb;
                background: white;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1: 0, y1: 0, x2: 0, y2: 1,
                    stop: 0 #6a6, stop: 1 #afa);
                border: 1px solid #777;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::add-page:horizontal {
                background: #fff;
                border: 1px solid #777;
                height: 6px;
                border-radius: 3px;
            }
            QSlider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #eee, stop:1 #ccc);
                border: 1px solid #777;
                width: 12px;
                margin-top: -3px;
                margin-bottom: -3px;
                border-radius: 6px;
            }
        """)
    
    def _on_value_changed(self, value):
        """Handle volume change."""
        volume = value / 100.0
        self.volume_changed.emit(volume)

class TimeDisplay(QLabel):
    """Time display widget showing current/total time."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.current_time = 0.0
        self.total_time = 0.0
        
        # Setup display
        self.setFont(QFont("Courier", 10))  # Monospace font for consistent width
        self.setMinimumWidth(100)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self._update_display()
    
    def set_time(self, current: float, total: float):
        """Update time display."""
        if self.current_time != current or self.total_time != total:
            self.current_time = current
            self.total_time = total
            self._update_display()
    
    def _update_display(self):
        """Update the displayed text."""
        current_str = self._format_time(self.current_time)
        total_str = self._format_time(self.total_time)
        self.setText(f"{current_str} / {total_str}")
    
    def _format_time(self, seconds: float) -> str:
        """Format seconds to MM:SS or HH:MM:SS."""
        if seconds < 0:
            seconds = 0
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"

class AudioControlsWidget(QWidget):
    """Main audio controls widget containing all playback controls."""
    
    def __init__(self, playback_controller: PlaybackController, parent=None):
        super().__init__(parent)
        
        self.playback_controller = playback_controller
        
        # Create UI
        self._setup_ui()
        
        # Connect signals
        self._connect_signals()
        
        # Initial state
        self._update_controls_state()
        
        logger.info("Audio controls widget initialized")
    
    def _setup_ui(self):
        """Setup the user interface."""
        # Main layout
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 5, 10, 5)
        main_layout.setSpacing(5)
        
        # Top row: Transport controls
        controls_layout = QHBoxLayout()
        
        # Playback buttons
        self.play_button = PlaybackButton("Play")
        self.pause_button = PlaybackButton("Pause")
        self.stop_button = PlaybackButton("Stop")
        
        controls_layout.addWidget(self.play_button)
        controls_layout.addWidget(self.pause_button)
        controls_layout.addWidget(self.stop_button)
        
        # Spacer
        controls_layout.addItem(QSpacerItem(20, 0, QSizePolicy.Policy.Fixed))
        
        # Time display
        self.time_display = TimeDisplay()
        controls_layout.addWidget(self.time_display)
        
        # Spacer
        controls_layout.addItem(QSpacerItem(40, 0, QSizePolicy.Policy.Expanding))
        
        # Volume control
        volume_label = QLabel("Volume:")
        volume_label.setFont(QFont("Arial", 10))
        controls_layout.addWidget(volume_label)
        
        self.volume_slider = VolumeSlider()
        controls_layout.addWidget(self.volume_slider)
        
        main_layout.addLayout(controls_layout)
        
        # Bottom row: Seek bar
        seek_layout = QHBoxLayout()
        
        # Position label
        self.position_label = QLabel("00:00")
        self.position_label.setFont(QFont("Courier", 9))
        self.position_label.setMinimumWidth(40)
        seek_layout.addWidget(self.position_label)
        
        # Seek slider
        self.seek_slider = SeekSlider()
        seek_layout.addWidget(self.seek_slider, 1)  # Take most space
        
        # Duration label
        self.duration_label = QLabel("00:00")
        self.duration_label.setFont(QFont("Courier", 9))
        self.duration_label.setMinimumWidth(40)
        seek_layout.addWidget(self.duration_label)
        
        main_layout.addLayout(seek_layout)
        
        # Add separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        main_layout.addWidget(separator)
    
    def _connect_signals(self):
        """Connect widget signals to controller methods."""
        # Playback buttons
        self.play_button.clicked.connect(self.playback_controller.play)
        self.pause_button.clicked.connect(self.playback_controller.pause)
        self.stop_button.clicked.connect(self.playback_controller.stop)
        
        # Seek slider
        self.seek_slider.user_seek.connect(self.playback_controller.seek)
        
        # Volume slider
        self.volume_slider.volume_changed.connect(self.playback_controller.set_volume)
        
        # Controller signals
        self.playback_controller.state_changed.connect(self._on_state_changed)
        self.playback_controller.position_changed.connect(self._on_position_changed)
        self.playback_controller.duration_changed.connect(self._on_duration_changed)
        self.playback_controller.file_loaded.connect(self._on_file_loaded)
    
    def _on_state_changed(self, state: str):
        """Handle playback state change."""
        self._update_controls_state()
        
        # Update button text based on state
        if state == PlaybackState.PLAYING:
            self.play_button.setText("Resume")  # In case it's paused later
        elif state == PlaybackState.PAUSED:
            self.play_button.setText("Resume")
        elif state == PlaybackState.STOPPED:
            self.play_button.setText("Play")
        elif state == PlaybackState.LOADING:
            self.play_button.setText("Loading...")
    
    def _on_position_changed(self, position: float):
        """Handle position change."""
        # Update seek slider
        self.seek_slider.set_position(position)
        
        # Update time displays
        duration = self.playback_controller.get_duration()
        self.time_display.set_time(position, duration)
        
        # Update position label
        self.position_label.setText(self._format_time(position))
    
    def _on_duration_changed(self, duration: float):
        """Handle duration change."""
        # Update seek slider
        self.seek_slider.set_duration(duration)
        
        # Update time displays
        position = self.playback_controller.get_current_position()
        self.time_display.set_time(position, duration)
        
        # Update duration label
        self.duration_label.setText(self._format_time(duration))
    
    def _on_file_loaded(self, file_path: str, metadata):
        """Handle file loaded."""
        self._update_controls_state()
    
    def _update_controls_state(self):
        """Update control button states based on current state."""
        can_play = self.playback_controller.can_play()
        can_pause = self.playback_controller.can_pause()
        can_stop = self.playback_controller.can_stop()
        can_seek = self.playback_controller.can_seek()
        
        # Update button states
        self.play_button.setEnabled(can_play)
        self.pause_button.setEnabled(can_pause)
        self.stop_button.setEnabled(can_stop)
        
        # Update seek slider
        self.seek_slider.setEnabled(can_seek)
        
        # Volume is always available
        self.volume_slider.setEnabled(True)
    
    def _format_time(self, seconds: float) -> str:
        """Format seconds to MM:SS format."""
        if seconds < 0:
            seconds = 0
        
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
    
    def get_volume(self) -> float:
        """Get current volume setting."""
        return self.volume_slider.value() / 100.0
    
    def set_volume(self, volume: float):
        """Set volume (0.0 to 1.0)."""
        value = int(volume * 100)
        self.volume_slider.setValue(value)
    
    def reset_position(self):
        """Reset position display to zero."""
        self.seek_slider.setValue(0)
        self.time_display.set_time(0.0, 0.0)
        self.position_label.setText("00:00")
        self.duration_label.setText("00:00")
