"""
Simple and clean main window for Bina Cshera audio player.

This module provides a simplified, user-friendly interface focused on core functionality.
"""

import logging
import os
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QSlider, QFileDialog, QProgressBar, QTextEdit, QSplitter,
    QGroupBox, QGridLayout, QSpacerItem, QSizePolicy
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont, QPixmap, QPalette, QColor

from controllers.simple_playback_controller import SimplePlaybackController, PlaybackState

logger = logging.getLogger(__name__)

# Import detailed logger
try:
    from utils.logger import get_logger
    detailed_logger = get_logger()
except ImportError:
    detailed_logger = None

class ModernButton(QPushButton):
    """Modern styled button with rounded corners."""
    
    def __init__(self, text: str = "", parent=None):
        super().__init__(text, parent)
        self.setStyleSheet("""
            QPushButton {
                background-color: #E0D6F5;
                border: 2px solid #CFF0E8;
                border-radius: 12px;
                padding: 8px 16px;
                font-size: 14px;
                font-weight: bold;
                color: #2C3E50;
                min-height: 20px;
            }
            QPushButton:hover {
                background-color: #CFF0E8;
                border-color: #A8E6CF;
            }
            QPushButton:pressed {
                background-color: #A8E6CF;
            }
            QPushButton:disabled {
                background-color: #F0F0F0;
                color: #888;
                border-color: #DDD;
            }
        """)

class ModernSlider(QSlider):
    """Modern styled slider with rounded appearance."""
    
    def __init__(self, orientation=Qt.Orientation.Horizontal, parent=None):
        super().__init__(orientation, parent)
        self.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 1px solid #CFF0E8;
                height: 8px;
                background: #FAF7F0;
                border-radius: 4px;
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1: 0, y1: 0, x2: 1, y2: 0,
                    stop: 0 #E0D6F5, stop: 1 #CFF0E8);
                border: 1px solid #CFF0E8;
                height: 8px;
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: #E0D6F5;
                border: 2px solid #CFF0E8;
                width: 18px;
                height: 18px;
                border-radius: 9px;
                margin: -6px 0;
            }
            QSlider::handle:horizontal:hover {
                background: #CFF0E8;
            }
        """)

class SimpleAudioPlayer(QMainWindow):
    """Simple and clean audio player interface."""
    
    def __init__(self, playback_controller: SimplePlaybackController):
        super().__init__()
        self.playback_controller = playback_controller
        self.current_file = None
        
        self.setWindowTitle("נגן בינה כשרה - נגן אודיו פשוט ויפה")
        self.setMinimumSize(800, 600)
        
        # Apply modern styling
        self._setup_styling()
        
        # Create UI
        self._create_ui()
        
        # Connect signals
        self._connect_signals()
        
        # Status update timer
        self.status_timer = QTimer()
        self.status_timer.timeout.connect(self._update_position)
        self.status_timer.start(100)  # Update every 100ms
        
        logger.info("Simple audio player window created")
    
    def _setup_styling(self):
        """Apply modern pastel styling with RTL support."""
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)  # Hebrew RTL layout
        self.setStyleSheet("""
            QMainWindow {
                background-color: #FAF7F0;
                color: #2C3E50;
                direction: rtl;
            }
            QGroupBox {
                font-weight: bold;
                font-size: 14px;
                border: 2px solid #E0D6F5;
                border-radius: 12px;
                margin-top: 1ex;
                padding-top: 10px;
                background-color: white;
                direction: rtl;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                right: 10px;
                padding: 0 8px 0 8px;
                color: #2C3E50;
            }
            QLabel {
                color: #2C3E50;
                font-size: 12px;
                direction: rtl;
            }
            QTextEdit {
                border: 2px solid #E0D6F5;
                border-radius: 8px;
                background-color: white;
                padding: 8px;
                font-size: 12px;
                direction: rtl;
            }
            QHBoxLayout {
                direction: rtl;
            }
        """)
    
    def _create_ui(self):
        """Create the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setSpacing(16)
        main_layout.setContentsMargins(16, 16, 16, 16)
        
        # Header
        header_group = QGroupBox("נגן בינה כשרה")
        header_layout = QHBoxLayout(header_group)
        
        self.file_label = QLabel("לא נטען קובץ")
        self.file_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        
        self.open_button = ModernButton("פתח קובץ אודיו")
        self.open_button.clicked.connect(self._open_file)
        
        header_layout.addWidget(self.file_label)
        header_layout.addStretch()
        header_layout.addWidget(self.open_button)
        
        main_layout.addWidget(header_group)
        
        # Controls section
        controls_group = QGroupBox("בקרות ניגון")
        controls_layout = QVBoxLayout(controls_group)
        
        # Transport buttons
        buttons_layout = QHBoxLayout()
        
        self.play_button = ModernButton("▶️ נגן")
        self.play_button.clicked.connect(self._toggle_play)
        self.play_button.setEnabled(False)
        
        self.stop_button = ModernButton("⏹️ עצור")
        self.stop_button.clicked.connect(self._stop)
        self.stop_button.setEnabled(False)
        
        buttons_layout.addWidget(self.play_button)
        buttons_layout.addWidget(self.stop_button)
        buttons_layout.addStretch()
        
        controls_layout.addLayout(buttons_layout)
        
        # Position slider
        position_layout = QHBoxLayout()
        
        self.current_time_label = QLabel("00:00")
        self.position_slider = ModernSlider()
        self.position_slider.setEnabled(False)
        self.position_slider.sliderPressed.connect(self._on_seek_start)
        self.position_slider.sliderReleased.connect(self._on_seek_end)
        self.total_time_label = QLabel("00:00")
        
        position_layout.addWidget(self.current_time_label)
        position_layout.addWidget(self.position_slider)
        position_layout.addWidget(self.total_time_label)
        
        controls_layout.addLayout(position_layout)
        
        # Volume control
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(QLabel("עוצמה:"))
        
        self.volume_slider = ModernSlider()
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(70)
        self.volume_slider.valueChanged.connect(self._on_volume_changed)
        
        self.volume_label = QLabel("70%")
        
        volume_layout.addWidget(self.volume_slider)
        volume_layout.addWidget(self.volume_label)
        volume_layout.addStretch()
        
        controls_layout.addLayout(volume_layout)
        
        main_layout.addWidget(controls_group)
        
        # Status and transcript area
        info_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Status area
        status_group = QGroupBox("מידע ומצב")
        status_layout = QVBoxLayout(status_group)
        
        self.status_label = QLabel("מוכן")
        self.status_label.setWordWrap(True)
        
        self.file_info_label = QLabel("אין קובץ טעון")
        self.file_info_label.setWordWrap(True)
        
        status_layout.addWidget(QLabel("סטטוס:"))
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(QLabel("מידע קובץ:"))
        status_layout.addWidget(self.file_info_label)
        status_layout.addStretch()
        
        info_splitter.addWidget(status_group)
        
        # Transcript area (placeholder for future)
        transcript_group = QGroupBox("תמלול (בקרוב)")
        transcript_layout = QVBoxLayout(transcript_group)
        
        self.transcript_text = QTextEdit()
        self.transcript_text.setPlainText("תכונת התמלול תהיה זמינה בגרסה הבאה.\n\nבינתיים תוכל ליהנות מנגן האודיו המתקדם.")
        self.transcript_text.setReadOnly(True)
        
        transcript_layout.addWidget(self.transcript_text)
        
        info_splitter.addWidget(transcript_group)
        info_splitter.setSizes([300, 400])
        
        main_layout.addWidget(info_splitter)
    
    def _connect_signals(self):
        """Connect playback controller signals."""
        self.playback_controller.state_changed.connect(self._on_state_changed)
        self.playback_controller.position_changed.connect(self._on_position_changed)
        self.playback_controller.duration_changed.connect(self._on_duration_changed)
        self.playback_controller.file_loaded.connect(self._on_file_loaded)
        self.playback_controller.error_occurred.connect(self._on_error)
    
    def _open_file(self):
        """Open file dialog to select audio file."""
        try:
            if detailed_logger:
                detailed_logger.start_operation("פתיחת דיאלוג בחירת קובץ")
                detailed_logger.log_ui_operation("פתיחת דיאלוג", "QFileDialog")
            
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "בחר קובץ אודיו",
                "",
                "Audio Files (*.mp3 *.wav *.flac *.ogg *.m4a *.aac *.wma);;All Files (*)"
            )
            
            if file_path:
                if detailed_logger:
                    detailed_logger.end_operation("פתיחת דיאלוג בחירת קובץ")
                    detailed_logger.log_file_operation("נבחר קובץ", file_path, True, 
                                                     size=Path(file_path).stat().st_size if Path(file_path).exists() else 0)
                
                self.status_label.setText(f"טוען קובץ: {Path(file_path).name}")
                success = self.playback_controller.load_file(file_path)
                
                if not success:
                    self.status_label.setText("שגיאה בטעינת הקובץ")
                    if detailed_logger:
                        detailed_logger.error(f"טעינת קובץ נכשלה: {file_path}")
                else:
                    if detailed_logger:
                        detailed_logger.info(f"קובץ נטען בהצלחה: {Path(file_path).name}")
            else:
                if detailed_logger:
                    detailed_logger.end_operation("פתיחת דיאלוג בחירת קובץ")
                    detailed_logger.info("המשתמש ביטל בחירת קובץ")
                
        except Exception as e:
            if detailed_logger:
                detailed_logger.exception(f"שגיאה בפתיחת דיאלוג קובץ: {e}")
            self.status_label.setText(f"שגיאה: {e}")
    
    def _toggle_play(self):
        """Toggle play/pause."""
        try:
            current_state = self.playback_controller.get_current_state()
            
            if detailed_logger:
                detailed_logger.log_ui_operation("לחיצה על נגן/השהה", "play_button", 
                                                current_state=current_state)
            
            if current_state == PlaybackState.PLAYING:
                if detailed_logger:
                    detailed_logger.info("משתמש לחץ להשהות ניגון")
                self.playback_controller.pause()
            else:
                if detailed_logger:
                    detailed_logger.info("משתמש לחץ להתחיל ניגון")
                success = self.playback_controller.play()
                if not success:
                    self.status_label.setText("לא ניתן להתחיל ניגון")
                    if detailed_logger:
                        detailed_logger.error("ניגון לא התחיל - בדוק אם קובץ נטען")
                        
        except Exception as e:
            if detailed_logger:
                detailed_logger.exception(f"שגיאה בלחיצה על כפתור ניגון: {e}")
            self.status_label.setText(f"שגיאה: {e}")
    
    def _stop(self):
        """Stop playback."""
        self.playback_controller.stop()
    
    def _on_seek_start(self):
        """Handle seek start."""
        self.seeking = True
    
    def _on_seek_end(self):
        """Handle seek end."""
        if hasattr(self, 'seeking') and self.seeking:
            duration = self.playback_controller.get_duration()
            if duration > 0:
                position = (self.position_slider.value() / 1000.0) * duration
                self.playback_controller.seek(position)
        self.seeking = False
    
    def _on_volume_changed(self, value):
        """Handle volume change."""
        volume = value / 100.0
        self.playback_controller.set_volume(volume)
        self.volume_label.setText(f"{value}%")
    
    def _on_state_changed(self, state: str):
        """Handle playback state change."""
        if state == PlaybackState.PLAYING:
            self.play_button.setText("⏸️ השהה")
            self.status_label.setText("מנגן...")
        elif state == PlaybackState.PAUSED:
            self.play_button.setText("▶️ המשך")
            self.status_label.setText("מושהה")
        elif state == PlaybackState.STOPPED:
            self.play_button.setText("▶️ נגן")
            self.status_label.setText("עצר")
        elif state == PlaybackState.LOADING:
            self.play_button.setText("טוען...")
            self.status_label.setText("טוען קובץ...")
    
    def _on_position_changed(self, position: float):
        """Handle position change."""
        if not hasattr(self, 'seeking') or not self.seeking:
            duration = self.playback_controller.get_duration()
            if duration > 0:
                slider_value = int((position / duration) * 1000)
                self.position_slider.setValue(slider_value)
        
        self.current_time_label.setText(self._format_time(position))
    
    def _on_duration_changed(self, duration: float):
        """Handle duration change."""
        self.total_time_label.setText(self._format_time(duration))
        self.position_slider.setEnabled(duration > 0)
        self.position_slider.setMaximum(1000)
    
    def _on_file_loaded(self, file_path: str, metadata):
        """Handle file loaded."""
        filename = Path(file_path).name
        self.file_label.setText(filename)
        self.current_file = file_path
        
        # Enable controls
        self.play_button.setEnabled(True)
        self.stop_button.setEnabled(True)
        
        # Update file info
        if metadata:
            info_text = f"קובץ: {filename}\n"
            info_text += f"משך: {self._format_time(metadata.duration)}\n"
            info_text += f"תדירות דגימה: {metadata.sample_rate} Hz\n"
            info_text += f"ערוצים: {metadata.channels}\n"
            if metadata.bitrate:
                info_text += f"קצב סיביות: {metadata.bitrate} kbps"
            self.file_info_label.setText(info_text)
        else:
            self.file_info_label.setText(f"קובץ: {filename}")
        
        self.status_label.setText("קובץ נטען בהצלחה")
    
    def _on_error(self, error_message: str):
        """Handle error."""
        self.status_label.setText(f"שגיאה: {error_message}")
    
    def _update_position(self):
        """Update position display."""
        # This is called by timer - let the controller handle position updates
        pass
    
    def _format_time(self, seconds: float) -> str:
        """Format time in MM:SS format."""
        if seconds < 0:
            return "00:00"
        
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"