"""
Simple audio player engine using PySide6's built-in audio capabilities.

This module provides a working audio player without FFmpeg complications.
"""

import logging
import os
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal, QTimer, QUrl, QIODevice
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

try:
    from utils.logger import get_logger
    detailed_logger = get_logger()
except ImportError:
    detailed_logger = None

logger = logging.getLogger(__name__)

@dataclass
class SimpleAudioMetadata:
    """Simple metadata container."""
    duration: float = 0.0
    file_path: str = ""
    file_name: str = ""
    file_size: int = 0

class SimpleAudioEngine(QObject):
    """Simple audio engine using Qt's built-in media player."""
    
    # Signals
    position_changed = Signal(float)  # Position in seconds
    duration_changed = Signal(float)  # Duration in seconds  
    state_changed = Signal(str)       # playing, paused, stopped
    error_occurred = Signal(str)      # Error message
    file_loaded = Signal(str, object) # File path, metadata
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Media player components
        self.media_player = None
        self.audio_output = None
        
        # State tracking
        self.current_file = None
        self.current_metadata = None
        self.is_seeking = False
        
        # Position update timer
        self.position_timer = QTimer()
        self.position_timer.timeout.connect(self._update_position)
        
        if detailed_logger:
            detailed_logger.info("יצירת מנוע אודיו פשוט")
    
    def initialize(self) -> bool:
        """Initialize the simple audio engine."""
        try:
            if detailed_logger:
                detailed_logger.start_operation("אתחול מנוע אודיו פשוט")
                detailed_logger.info("יוצר נגן מדיה וקלט אודיו")
            
            # Create audio output
            self.audio_output = QAudioOutput()
            self.audio_output.setVolume(0.7)  # 70% volume
            
            if detailed_logger:
                detailed_logger.info(f"קלט אודיו נוצר, עוצמה ראשונית: {self.audio_output.volume()}")
            
            # Create media player
            self.media_player = QMediaPlayer()
            self.media_player.setAudioOutput(self.audio_output)
            
            if detailed_logger:
                detailed_logger.info("נגן מדיה וקלט אודיו נוצרו ונקשרו")
            
            # Connect signals
            self._connect_signals()
            
            if detailed_logger:
                detailed_logger.end_operation("אתחול מנוע אודיו פשוט")
                detailed_logger.info("מנוע האודיו הפשוט אותחל בהצלחה")
            
            logger.info("Simple audio engine initialized")
            return True
            
        except Exception as e:
            logger.exception(f"Failed to initialize simple audio engine: {e}")
            if detailed_logger:
                detailed_logger.exception(f"שגיאה באתחול מנוע אודיו פשוט: {e}")
            return False
    
    def _connect_signals(self):
        """Connect media player signals."""
        if detailed_logger:
            detailed_logger.info("מחבר אותות נגן המדיה")
        
        if self.media_player:
            self.media_player.positionChanged.connect(self._on_position_changed)
            self.media_player.durationChanged.connect(self._on_duration_changed)
            self.media_player.playbackStateChanged.connect(self._on_state_changed)
            self.media_player.errorOccurred.connect(self._on_error_occurred)
            self.media_player.mediaStatusChanged.connect(self._on_media_status_changed)
            
            if detailed_logger:
                detailed_logger.info("אותות נגן המדיה חוברו בהצלחה")
        else:
            if detailed_logger:
                detailed_logger.error("נגן מדיה לא נוצר - לא ניתן לחבר אותות")
    
    def load_file(self, file_path: str) -> bool:
        """Load an audio file."""
        try:
            if detailed_logger:
                detailed_logger.start_operation("טעינת קובץ אודיו")
                detailed_logger.log_file_operation("פתיחה", file_path, os.path.exists(file_path))
            
            if not os.path.exists(file_path):
                error_msg = f"קובץ לא נמצא: {file_path}"
                logger.error(error_msg)
                if detailed_logger:
                    detailed_logger.error(error_msg)
                self.error_occurred.emit(error_msg)
                return False
            
            # Create metadata
            file_path_obj = Path(file_path)
            metadata = SimpleAudioMetadata(
                file_path=file_path,
                file_name=file_path_obj.name,
                file_size=file_path_obj.stat().st_size
            )
            
            if detailed_logger:
                detailed_logger.info(f"מטא-דאטה של הקובץ: שם={metadata.file_name}, גודל={metadata.file_size:,} bytes")
            
            # Set media source
            media_url = QUrl.fromLocalFile(str(file_path_obj.absolute()))
            if detailed_logger:
                detailed_logger.info(f"URL של המדיה: {media_url.toString()}")
            
            self.media_player.setSource(media_url)
            
            # Store current file info
            self.current_file = file_path
            self.current_metadata = metadata
            
            if detailed_logger:
                detailed_logger.end_operation("טעינת קובץ אודיו")
                detailed_logger.info(f"קובץ אודיו נטען: {metadata.file_name}")
            
            # Emit file loaded signal
            self.file_loaded.emit(file_path, metadata)
            
            logger.info(f"File loaded: {file_path}")
            return True
            
        except Exception as e:
            error_msg = f"שגיאה בטעינת קובץ: {e}"
            logger.exception(error_msg)
            if detailed_logger:
                detailed_logger.exception(error_msg)
            self.error_occurred.emit(error_msg)
            return False
    
    def play(self) -> bool:
        """Start playback."""
        try:
            if not self.media_player or not self.current_file:
                error_msg = "אין קובץ טעון לניגון"
                logger.warning(error_msg)
                if detailed_logger:
                    detailed_logger.warning(error_msg)
                self.error_occurred.emit(error_msg)
                return False
            
            if detailed_logger:
                detailed_logger.start_operation("התחלת ניגון")
                detailed_logger.log_audio_operation("play", {
                    "file": self.current_metadata.file_name if self.current_metadata else "לא ידוע",
                    "position": self.get_position()
                })
            
            self.media_player.play()
            self.position_timer.start(100)  # Update position every 100ms
            
            if detailed_logger:
                detailed_logger.end_operation("התחלת ניגון")
                detailed_logger.info("ניגון התחיל")
            
            logger.info("Playback started")
            return True
            
        except Exception as e:
            error_msg = f"שגיאה בהתחלת ניגון: {e}"
            logger.exception(error_msg)
            if detailed_logger:
                detailed_logger.exception(error_msg)
            self.error_occurred.emit(error_msg)
            return False
    
    def pause(self):
        """Pause playback."""
        try:
            if detailed_logger:
                detailed_logger.log_audio_operation("pause", {
                    "position": self.get_position()
                })
            
            self.media_player.pause()
            self.position_timer.stop()
            
            if detailed_logger:
                detailed_logger.info("ניגון הושהה")
            
            logger.info("Playback paused")
            
        except Exception as e:
            logger.exception(f"Error pausing: {e}")
            if detailed_logger:
                detailed_logger.exception(f"שגיאה בהשהיית ניגון: {e}")
    
    def stop(self):
        """Stop playback."""
        try:
            if detailed_logger:
                detailed_logger.log_audio_operation("stop", {
                    "position": self.get_position()
                })
            
            self.media_player.stop()
            self.position_timer.stop()
            
            if detailed_logger:
                detailed_logger.info("ניגון נעצר")
            
            logger.info("Playback stopped")
            
        except Exception as e:
            logger.exception(f"Error stopping: {e}")
            if detailed_logger:
                detailed_logger.exception(f"שגיאה בעצירת ניגון: {e}")
    
    def seek(self, position: float):
        """Seek to position in seconds."""
        try:
            if not self.media_player:
                return
            
            position_ms = int(position * 1000)
            
            if detailed_logger:
                detailed_logger.log_audio_operation("seek", {
                    "from_position": self.get_position(),
                    "to_position": position,
                    "to_position_ms": position_ms
                })
            
            self.is_seeking = True
            self.media_player.setPosition(position_ms)
            self.is_seeking = False
            
            if detailed_logger:
                detailed_logger.info(f"דילג למיקום: {position:.2f} שניות")
            
            logger.info(f"Seeked to {position:.2f}s")
            
        except Exception as e:
            logger.exception(f"Error seeking: {e}")
            if detailed_logger:
                detailed_logger.exception(f"שגיאה בדילוג: {e}")
    
    def set_volume(self, volume: float):
        """Set volume (0.0 to 1.0)."""
        try:
            if self.audio_output:
                self.audio_output.setVolume(volume)
                
                if detailed_logger:
                    detailed_logger.log_audio_operation("set_volume", {
                        "volume": volume,
                        "volume_percent": f"{volume*100:.0f}%"
                    })
                
                logger.info(f"Volume set to {volume:.2f}")
                
        except Exception as e:
            logger.exception(f"Error setting volume: {e}")
            if detailed_logger:
                detailed_logger.exception(f"שגיאה בהגדרת עוצמה: {e}")
    
    def get_position(self) -> float:
        """Get current position in seconds."""
        try:
            if self.media_player:
                return self.media_player.position() / 1000.0
        except:
            pass
        return 0.0
    
    def get_duration(self) -> float:
        """Get duration in seconds."""
        try:
            if self.media_player:
                duration_ms = self.media_player.duration()
                if duration_ms > 0:
                    return duration_ms / 1000.0
        except:
            pass
        return 0.0
    
    def get_metadata(self) -> Optional[SimpleAudioMetadata]:
        """Get current metadata."""
        return self.current_metadata
    
    def _on_position_changed(self, position_ms: int):
        """Handle position change from media player."""
        if not self.is_seeking:
            position_seconds = position_ms / 1000.0
            self.position_changed.emit(position_seconds)
    
    def _on_duration_changed(self, duration_ms: int):
        """Handle duration change from media player."""
        if duration_ms > 0:
            duration_seconds = duration_ms / 1000.0
            if self.current_metadata:
                self.current_metadata.duration = duration_seconds
            
            if detailed_logger:
                detailed_logger.log_audio_operation("duration_detected", {
                    "duration_seconds": duration_seconds,
                    "duration_formatted": f"{int(duration_seconds//60):02d}:{int(duration_seconds%60):02d}"
                })
            
            self.duration_changed.emit(duration_seconds)
            logger.info(f"Duration: {duration_seconds:.2f}s")
    
    def _on_state_changed(self, state):
        """Handle playback state change."""
        state_map = {
            QMediaPlayer.PlaybackState.PlayingState: "playing",
            QMediaPlayer.PlaybackState.PausedState: "paused", 
            QMediaPlayer.PlaybackState.StoppedState: "stopped"
        }
        
        state_str = state_map.get(state, "unknown")
        
        if detailed_logger:
            detailed_logger.log_audio_operation("state_change", {
                "new_state": state_str,
                "position": self.get_position()
            })
        
        self.state_changed.emit(state_str)
        logger.info(f"State changed to: {state_str}")
    
    def _on_error_occurred(self, error, error_string):
        """Handle media player error."""
        error_msg = f"שגיאת נגן מדיה: {error_string}"
        logger.error(error_msg)
        if detailed_logger:
            detailed_logger.error(f"שגיאת נגן מדיה: קוד={error}, הודעה={error_string}")
        self.error_occurred.emit(error_msg)
    
    def _on_media_status_changed(self, status):
        """Handle media status change."""
        status_map = {
            QMediaPlayer.MediaStatus.NoMedia: "אין מדיה",
            QMediaPlayer.MediaStatus.LoadingMedia: "טוען מדיה",
            QMediaPlayer.MediaStatus.LoadedMedia: "מדיה נטענה",
            QMediaPlayer.MediaStatus.BufferingMedia: "מאגר מדיה", 
            QMediaPlayer.MediaStatus.BufferedMedia: "מדיה מאוגרת",
            QMediaPlayer.MediaStatus.EndOfMedia: "סוף מדיה",
            QMediaPlayer.MediaStatus.InvalidMedia: "מדיה לא תקינה"
        }
        
        status_str = status_map.get(status, f"מצב לא ידוע ({status})")
        
        if detailed_logger:
            detailed_logger.log_audio_operation("media_status_change", {
                "status": status_str,
                "file": self.current_metadata.file_name if self.current_metadata else "לא ידוע"
            })
        
        logger.info(f"Media status: {status_str}")
        
        # Handle specific statuses
        if status == QMediaPlayer.MediaStatus.InvalidMedia:
            self.error_occurred.emit("קובץ המדיה לא תקין או לא נתמך")
        elif status == QMediaPlayer.MediaStatus.LoadedMedia:
            if detailed_logger:
                detailed_logger.info("מדיה נטענה בהצלחה ומוכנה לניגון")
    
    def _update_position(self):
        """Update position timer callback."""
        # Position is updated via signal, this is just to keep timer active
        pass
    
    def cleanup(self):
        """Cleanup resources."""
        try:
            if detailed_logger:
                detailed_logger.info("מנקה משאבי מנוע אודיו")
            
            if self.position_timer:
                self.position_timer.stop()
            
            if self.media_player:
                self.media_player.stop()
                self.media_player = None
            
            if self.audio_output:
                self.audio_output = None
            
            if detailed_logger:
                detailed_logger.info("ניקוי משאבי מנוע אודיו הושלם")
            
            logger.info("Simple audio engine cleanup completed")
            
        except Exception as e:
            logger.exception(f"Error during cleanup: {e}")
            if detailed_logger:
                detailed_logger.exception(f"שגיאה בניקוי משאבים: {e}")