"""
Simple working audio player application.

A clean, working audio player with Hebrew RTL support and detailed logging.
"""

import sys
import os
import logging
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QLabel, QSlider, QFileDialog, QGroupBox, QTextEdit
)
from PySide6.QtCore import Qt, QTimer, QUrl
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtGui import QFont

try:
    from utils.logger import get_logger
    detailed_logger = get_logger()
except ImportError:
    detailed_logger = None

logger = logging.getLogger(__name__)

class WorkingAudioPlayer(QMainWindow):
    """Simple working audio player with Hebrew support."""
    
    def __init__(self):
        super().__init__()
        
        # Audio components
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        
        # State tracking
        self.current_file = None
        self.is_seeking = False
        
        # UI setup
        self.setWindowTitle("נגן בינה כשרה - נגן פשוט ועובד")
        self.setMinimumSize(800, 600)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        self._setup_ui()
        self._connect_signals()
        
        # Position update timer - faster for smooth tracking
        self.position_timer = QTimer()
        self.position_timer.timeout.connect(self._update_position)
        self.position_timer.start(50)  # 20 FPS for smooth position tracking
        
        if detailed_logger:
            detailed_logger.info("נגן אודיו פשוט נוצר ומוכן לעבודה")
    
    def _setup_ui(self):
        """Setup the user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Apply Hebrew styling
        self.setStyleSheet("""
            QMainWindow {
                background-color: #FAF7F0;
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
            QLabel {
                color: #2C3E50;
                font-size: 12px;
                direction: rtl;
            }
        """)
        
        layout = QVBoxLayout(central_widget)
        layout.setSpacing(16)
        layout.setContentsMargins(16, 16, 16, 16)
        
        # Header
        header_group = QGroupBox("נגן בינה כשרה")
        header_layout = QHBoxLayout(header_group)
        
        self.file_label = QLabel("לא נטען קובץ")
        self.file_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        
        self.open_button = QPushButton("פתח קובץ אודיו")
        self.open_button.clicked.connect(self._open_file)
        
        header_layout.addWidget(self.file_label)
        header_layout.addStretch()
        header_layout.addWidget(self.open_button)
        
        layout.addWidget(header_group)
        
        # Controls
        controls_group = QGroupBox("בקרות ניגון")
        controls_layout = QVBoxLayout(controls_group)
        
        # Transport buttons
        buttons_layout = QHBoxLayout()
        
        self.play_button = QPushButton("▶️ נגן")
        self.play_button.clicked.connect(self._toggle_play)
        self.play_button.setEnabled(False)
        
        self.stop_button = QPushButton("⏹️ עצור")
        self.stop_button.clicked.connect(self._stop)
        self.stop_button.setEnabled(False)
        
        buttons_layout.addWidget(self.play_button)
        buttons_layout.addWidget(self.stop_button)
        buttons_layout.addStretch()
        
        controls_layout.addLayout(buttons_layout)
        
        # Position slider
        position_layout = QHBoxLayout()
        
        self.current_time_label = QLabel("00:00")
        self.position_slider = QSlider(Qt.Orientation.Horizontal)
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
        
        self.volume_slider = QSlider(Qt.Orientation.Horizontal)
        self.volume_slider.setMaximum(100)
        self.volume_slider.setValue(70)
        self.volume_slider.valueChanged.connect(self._on_volume_changed)
        
        self.volume_label = QLabel("70%")
        
        volume_layout.addWidget(self.volume_slider)
        volume_layout.addWidget(self.volume_label)
        volume_layout.addStretch()
        
        controls_layout.addLayout(volume_layout)
        
        layout.addWidget(controls_group)
        
        # Status
        status_group = QGroupBox("מידע ומצב")
        status_layout = QVBoxLayout(status_group)
        
        self.status_label = QLabel("מוכן - בחר קובץ אודיו כדי להתחיל")
        self.status_label.setWordWrap(True)
        
        self.file_info_label = QLabel("אין קובץ טעון")
        self.file_info_label.setWordWrap(True)
        
        status_layout.addWidget(QLabel("סטטוס:"))
        status_layout.addWidget(self.status_label)
        status_layout.addWidget(QLabel("מידע קובץ:"))
        status_layout.addWidget(self.file_info_label)
        
        layout.addWidget(status_group)
    
    def _connect_signals(self):
        """Connect media player signals."""
        if detailed_logger:
            detailed_logger.info("מחבר אותות נגן מדיה")
        
        self.media_player.positionChanged.connect(self._on_position_changed)
        self.media_player.durationChanged.connect(self._on_duration_changed)
        self.media_player.playbackStateChanged.connect(self._on_state_changed)
        self.media_player.errorOccurred.connect(self._on_error_occurred)
        self.media_player.mediaStatusChanged.connect(self._on_media_status_changed)
        
        if detailed_logger:
            detailed_logger.info("אותות נגן מדיה חוברו")
    
    def _open_file(self):
        """Open file dialog."""
        try:
            if detailed_logger:
                detailed_logger.start_operation("בחירת קובץ אודיו")
            
            file_path, _ = QFileDialog.getOpenFileName(
                self,
                "בחר קובץ אודיו",
                "",
                "Audio Files (*.mp3 *.wav *.flac *.ogg *.m4a *.aac *.wma);;All Files (*)"
            )
            
            if file_path:
                if detailed_logger:
                    detailed_logger.log_file_operation("נבחר קובץ", file_path, True)
                    detailed_logger.end_operation("בחירת קובץ אודיו")
                
                self._load_file(file_path)
            else:
                if detailed_logger:
                    detailed_logger.end_operation("בחירת קובץ אודיו")
                    detailed_logger.info("המשתמש ביטל בחירת קובץ")
                
        except Exception as e:
            if detailed_logger:
                detailed_logger.exception(f"שגיאה בבחירת קובץ: {e}")
            self.status_label.setText(f"שגיאה: {e}")
    
    def _load_file(self, file_path: str):
        """Load audio file."""
        try:
            if detailed_logger:
                detailed_logger.start_operation("טעינת קובץ אודיו")
                detailed_logger.info(f"טוען קובץ: {Path(file_path).name}")
            
            self.current_file = file_path
            filename = Path(file_path).name
            file_size = Path(file_path).stat().st_size
            
            # Update UI
            self.file_label.setText(filename)
            self.status_label.setText(f"טוען: {filename}")
            
            # Load in media player
            media_url = QUrl.fromLocalFile(str(Path(file_path).absolute()))
            
            if detailed_logger:
                detailed_logger.info(f"URL מדיה: {media_url.toString()}")
            
            self.media_player.setSource(media_url)
            
            # Update file info
            self.file_info_label.setText(f"קובץ: {filename}\nגודל: {file_size:,} bytes")
            
            # Enable controls
            self.play_button.setEnabled(True)
            self.stop_button.setEnabled(True)
            
            if detailed_logger:
                detailed_logger.end_operation("טעינת קובץ אודיו")
                detailed_logger.info(f"קובץ נטען בהצלחה: {filename}")
            
            self.status_label.setText("קובץ נטען - לחץ נגן להתחלה")
            
        except Exception as e:
            if detailed_logger:
                detailed_logger.exception(f"שגיאה בטעינת קובץ: {e}")
            self.status_label.setText(f"שגיאה בטעינה: {e}")
    
    def _toggle_play(self):
        """Toggle play/pause."""
        try:
            state = self.media_player.playbackState()
            
            if detailed_logger:
                detailed_logger.log_audio_operation("לחיצת נגן", {
                    "current_state": state,
                    "file": Path(self.current_file).name if self.current_file else "ללא קובץ"
                })
            
            if state == QMediaPlayer.PlaybackState.PlayingState:
                if detailed_logger:
                    detailed_logger.info("משהה ניגון")
                self.media_player.pause()
            else:
                if detailed_logger:
                    detailed_logger.info("מתחיל ניגון")
                self.media_player.play()
                
        except Exception as e:
            if detailed_logger:
                detailed_logger.exception(f"שגיאה בניגון: {e}")
            self.status_label.setText(f"שגיאה: {e}")
    
    def _stop(self):
        """Stop playback."""
        try:
            if detailed_logger:
                detailed_logger.info("עוצר ניגון")
            self.media_player.stop()
        except Exception as e:
            if detailed_logger:
                detailed_logger.exception(f"שגיאה בעצירה: {e}")
    
    def _on_seek_start(self):
        """Handle seek start."""
        self.is_seeking = True
        if detailed_logger:
            detailed_logger.info("התחלת דילוג")
    
    def _on_seek_end(self):
        """Handle seek end."""
        if self.is_seeking:
            duration = self.media_player.duration()
            if duration > 0:
                position = (self.position_slider.value() / 1000.0) * duration
                if detailed_logger:
                    detailed_logger.log_audio_operation("דילוג", {
                        "to_position_ms": position,
                        "to_position_seconds": position / 1000.0
                    })
                self.media_player.setPosition(int(position))
        self.is_seeking = False
    
    def _on_volume_changed(self, value):
        """Handle volume change."""
        volume = value / 100.0
        self.audio_output.setVolume(volume)
        self.volume_label.setText(f"{value}%")
        
        if detailed_logger:
            detailed_logger.log_audio_operation("שינוי עוצמה", {
                "volume_percent": value,
                "volume_float": volume
            })
    
    def _on_position_changed(self, position_ms: int):
        """Handle position change."""
        if not self.is_seeking:
            duration = self.media_player.duration()
            if duration > 0:
                slider_value = int((position_ms / duration) * 1000)
                self.position_slider.setValue(slider_value)
        
        self.current_time_label.setText(self._format_time(position_ms / 1000.0))
    
    def _on_duration_changed(self, duration_ms: int):
        """Handle duration change."""
        duration_seconds = duration_ms / 1000.0
        self.total_time_label.setText(self._format_time(duration_seconds))
        self.position_slider.setEnabled(duration_ms > 0)
        self.position_slider.setMaximum(1000)
        
        if detailed_logger:
            detailed_logger.log_audio_operation("זוהה משך", {
                "duration_ms": duration_ms,
                "duration_seconds": duration_seconds,
                "duration_formatted": self._format_time(duration_seconds)
            })
        
        # Update file info with duration
        if self.current_file:
            filename = Path(self.current_file).name
            file_size = Path(self.current_file).stat().st_size
            self.file_info_label.setText(
                f"קובץ: {filename}\n"
                f"גודל: {file_size:,} bytes\n"
                f"משך: {self._format_time(duration_seconds)}"
            )
    
    def _on_state_changed(self, state):
        """Handle playback state change."""
        state_names = {
            QMediaPlayer.PlaybackState.PlayingState: "מנגן",
            QMediaPlayer.PlaybackState.PausedState: "מושהה",
            QMediaPlayer.PlaybackState.StoppedState: "עצר"
        }
        
        state_name = state_names.get(state, "לא ידוע")
        
        if detailed_logger:
            detailed_logger.log_audio_operation("שינוי מצב ניגון", {
                "state": state_name,
                "state_code": state
            })
        
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_button.setText("⏸️ השהה")
            self.status_label.setText("מנגן...")
        elif state == QMediaPlayer.PlaybackState.PausedState:
            self.play_button.setText("▶️ המשך")
            self.status_label.setText("מושהה")
        elif state == QMediaPlayer.PlaybackState.StoppedState:
            self.play_button.setText("▶️ נגן")
            self.status_label.setText("עצר")
    
    def _on_error_occurred(self, error, error_string):
        """Handle media player error."""
        error_msg = f"שגיאת נגן: {error_string}"
        
        if detailed_logger:
            detailed_logger.error(f"שגיאת נגן מדיה: קוד={error}, הודעה={error_string}")
        
        self.status_label.setText(error_msg)
        logger.error(error_msg)
    
    def _on_media_status_changed(self, status):
        """Handle media status change."""
        status_names = {
            QMediaPlayer.MediaStatus.NoMedia: "אין מדיה",
            QMediaPlayer.MediaStatus.LoadingMedia: "טוען מדיה",
            QMediaPlayer.MediaStatus.LoadedMedia: "מדיה נטענה",
            QMediaPlayer.MediaStatus.BufferingMedia: "מאגר מדיה",
            QMediaPlayer.MediaStatus.BufferedMedia: "מדיה מאוגרת",
            QMediaPlayer.MediaStatus.EndOfMedia: "סוף מדיה",
            QMediaPlayer.MediaStatus.InvalidMedia: "מדיה לא תקינה"
        }
        
        status_name = status_names.get(status, f"מצב לא ידוע ({status})")
        
        if detailed_logger:
            detailed_logger.log_audio_operation("שינוי מצב מדיה", {
                "status": status_name,
                "status_code": status
            })
        
        if status == QMediaPlayer.MediaStatus.InvalidMedia:
            self.status_label.setText("קובץ לא תקין או לא נתמך")
        elif status == QMediaPlayer.MediaStatus.LoadedMedia:
            self.status_label.setText("קובץ נטען בהצלחה - מוכן לניגון")
        elif status == QMediaPlayer.MediaStatus.EndOfMedia:
            self.status_label.setText("הניגון הסתיים")
    
    def _update_position(self):
        """Timer callback for position updates."""
        if self.media_player.playbackState() == QMediaPlayer.PlaybackState.PlayingState:
            # Force position update for real-time tracking
            position_ms = self.media_player.position()
            self._on_position_changed(position_ms)
    
    def _format_time(self, seconds: float) -> str:
        """Format time as MM:SS."""
        if seconds < 0:
            return "00:00"
        
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"

def create_simple_audio_app():
    """Create the simple audio application."""
    try:
        if detailed_logger:
            detailed_logger.start_operation("יצירת אפליקציה פשוטה")
        
        app = QApplication(sys.argv)
        app.setApplicationName("נגן בינה כשרה")
        app.setApplicationVersion("1.0")
        
        # Set RTL layout for the entire application
        app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        window = WorkingAudioPlayer()
        window.show()
        
        if detailed_logger:
            detailed_logger.end_operation("יצירת אפליקציה פשוטה")
            detailed_logger.info("אפליקציה פשוטה נוצרה ומוצגת")
        
        return app, window
        
    except Exception as e:
        if detailed_logger:
            detailed_logger.exception(f"שגיאה ביצירת אפליקציה פשוטה: {e}")
        logger.exception(f"Failed to create simple app: {e}")
        return None, None