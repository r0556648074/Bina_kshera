"""
Simple playback controller using the working audio engine.

This controller manages playback with detailed logging and proper state management.
"""

import logging
from typing import Optional
from pathlib import Path

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QFileDialog

from engine.simple_audio_player import SimpleAudioEngine, SimpleAudioMetadata

try:
    from utils.logger import get_logger
    detailed_logger = get_logger()
except ImportError:
    detailed_logger = None

logger = logging.getLogger(__name__)

class PlaybackState:
    """Playback state constants."""
    STOPPED = "stopped"
    PLAYING = "playing" 
    PAUSED = "paused"
    LOADING = "loading"
    ERROR = "error"

class SimplePlaybackController(QObject):
    """Simple playback controller with working audio."""
    
    # Signals
    state_changed = Signal(str)
    position_changed = Signal(float)
    duration_changed = Signal(float)
    file_loaded = Signal(str, object)
    error_occurred = Signal(str)
    loading_progress = Signal(str)
    
    def __init__(self, audio_engine: SimpleAudioEngine, parent=None):
        super().__init__(parent)
        
        self.audio_engine = audio_engine
        self.current_state = PlaybackState.STOPPED
        
        # Connect audio engine signals
        self._connect_signals()
        
        if detailed_logger:
            detailed_logger.info("בקר ניגון פשוט נוצר")
    
    def _connect_signals(self):
        """Connect audio engine signals."""
        if detailed_logger:
            detailed_logger.info("מחבר אותות בקר ניגון")
        
        self.audio_engine.position_changed.connect(self.position_changed)
        self.audio_engine.duration_changed.connect(self.duration_changed)
        self.audio_engine.state_changed.connect(self._on_state_changed)
        self.audio_engine.error_occurred.connect(self.error_occurred)
        self.audio_engine.file_loaded.connect(self.file_loaded)
        
        if detailed_logger:
            detailed_logger.info("אותות בקר ניגון חוברו")
    
    def _on_state_changed(self, state: str):
        """Handle audio engine state change."""
        old_state = self.current_state
        self.current_state = state
        
        if detailed_logger:
            detailed_logger.log_audio_operation("controller_state_change", {
                "from_state": old_state,
                "to_state": state
            })
        
        self.state_changed.emit(state)
    
    def open_file_dialog(self, parent_widget=None) -> bool:
        """Open file dialog to select audio file."""
        try:
            if detailed_logger:
                detailed_logger.start_operation("פתיחת דיאלוג קובץ")
            
            file_path, _ = QFileDialog.getOpenFileName(
                parent_widget,
                "בחר קובץ אודיו",
                "",
                "Audio Files (*.mp3 *.wav *.flac *.ogg *.m4a *.aac);;All Files (*)"
            )
            
            if file_path:
                if detailed_logger:
                    detailed_logger.end_operation("פתיחת דיאלוג קובץ")
                    detailed_logger.log_file_operation("נבחר בדיאלוג", file_path, True)
                
                return self.load_file(file_path)
            else:
                if detailed_logger:
                    detailed_logger.end_operation("פתיחת דיאלוג קובץ")
                    detailed_logger.info("משתמש ביטל בחירת קובץ")
                
                return False
                
        except Exception as e:
            logger.exception(f"Error in file dialog: {e}")
            if detailed_logger:
                detailed_logger.exception(f"שגיאה בדיאלוג קובץ: {e}")
            return False
    
    def load_file(self, file_path: str) -> bool:
        """Load audio file."""
        try:
            if detailed_logger:
                detailed_logger.start_operation("טעינת קובץ בבקר")
                detailed_logger.info(f"מתחיל טעינת קובץ: {Path(file_path).name}")
            
            self.loading_progress.emit("טוען קובץ...")
            self._set_state(PlaybackState.LOADING)
            
            success = self.audio_engine.load_file(file_path)
            
            if success:
                if detailed_logger:
                    detailed_logger.end_operation("טעינת קובץ בבקר")
                    detailed_logger.info("קובץ נטען בהצלחה בבקר")
                
                self.loading_progress.emit("קובץ נטען בהצלחה")
                self._set_state(PlaybackState.STOPPED)
            else:
                if detailed_logger:
                    detailed_logger.end_operation("טעינת קובץ בבקר")
                    detailed_logger.error("כשל בטעינת קובץ בבקר")
                
                self.loading_progress.emit("שגיאה בטעינת קובץ")
                self._set_state(PlaybackState.ERROR)
            
            return success
            
        except Exception as e:
            logger.exception(f"Error loading file: {e}")
            if detailed_logger:
                detailed_logger.exception(f"שגיאה בטעינת קובץ בבקר: {e}")
            
            self._set_state(PlaybackState.ERROR)
            return False
    
    def play(self) -> bool:
        """Start or resume playback."""
        try:
            if detailed_logger:
                detailed_logger.start_operation("התחלת ניגון בבקר")
                detailed_logger.log_audio_operation("play_command", {
                    "current_state": self.current_state,
                    "can_play": self.can_play()
                })
            
            if not self.can_play():
                error_msg = "לא ניתן להתחיל ניגון - אין קובץ טעון או שגיאה במצב"
                if detailed_logger:
                    detailed_logger.warning(error_msg)
                self.error_occurred.emit(error_msg)
                return False
            
            success = self.audio_engine.play()
            
            if success:
                if detailed_logger:
                    detailed_logger.end_operation("התחלת ניגון בבקר")
                    detailed_logger.info("ניגון התחיל בהצלחה בבקר")
            else:
                if detailed_logger:
                    detailed_logger.end_operation("התחלת ניגון בבקר")
                    detailed_logger.error("כשל בהתחלת ניגון בבקר")
            
            return success
            
        except Exception as e:
            logger.exception(f"Error starting playback: {e}")
            if detailed_logger:
                detailed_logger.exception(f"שגיאה בהתחלת ניגון בבקר: {e}")
            return False
    
    def pause(self):
        """Pause playback."""
        try:
            if detailed_logger:
                detailed_logger.log_audio_operation("pause_command", {
                    "current_state": self.current_state,
                    "can_pause": self.can_pause()
                })
            
            if self.can_pause():
                self.audio_engine.pause()
                if detailed_logger:
                    detailed_logger.info("ניגון הושהה בבקר")
            else:
                if detailed_logger:
                    detailed_logger.warning("לא ניתן להשהות - מצב לא מתאים")
                
        except Exception as e:
            logger.exception(f"Error pausing: {e}")
            if detailed_logger:
                detailed_logger.exception(f"שגיאה בהשהיית ניגון בבקר: {e}")
    
    def stop(self):
        """Stop playback."""
        try:
            if detailed_logger:
                detailed_logger.log_audio_operation("stop_command", {
                    "current_state": self.current_state,
                    "can_stop": self.can_stop()
                })
            
            if self.can_stop():
                self.audio_engine.stop()
                if detailed_logger:
                    detailed_logger.info("ניגון נעצר בבקר")
            else:
                if detailed_logger:
                    detailed_logger.warning("לא ניתן לעצור - מצב לא מתאים")
                
        except Exception as e:
            logger.exception(f"Error stopping: {e}")
            if detailed_logger:
                detailed_logger.exception(f"שגיאה בעצירת ניגון בבקר: {e}")
    
    def seek(self, position: float):
        """Seek to position."""
        try:
            if detailed_logger:
                detailed_logger.log_audio_operation("seek_command", {
                    "target_position": position,
                    "current_position": self.get_current_position(),
                    "can_seek": self.can_seek()
                })
            
            if self.can_seek():
                self.audio_engine.seek(position)
                if detailed_logger:
                    detailed_logger.info(f"דילג למיקום {position:.2f} בבקר")
            else:
                if detailed_logger:
                    detailed_logger.warning("לא ניתן לדלג - אין קובץ טעון")
                
        except Exception as e:
            logger.exception(f"Error seeking: {e}")
            if detailed_logger:
                detailed_logger.exception(f"שגיאה בדילוג בבקר: {e}")
    
    def toggle_playback(self):
        """Toggle between play and pause."""
        if self.current_state == PlaybackState.PLAYING:
            self.pause()
        else:
            self.play()
    
    def set_volume(self, volume: float):
        """Set volume (0.0 to 1.0)."""
        try:
            if detailed_logger:
                detailed_logger.log_audio_operation("volume_command", {
                    "volume": volume,
                    "volume_percent": f"{volume*100:.0f}%"
                })
            
            self.audio_engine.set_volume(volume)
            
        except Exception as e:
            logger.exception(f"Error setting volume: {e}")
            if detailed_logger:
                detailed_logger.exception(f"שגיאה בהגדרת עוצמה בבקר: {e}")
    
    def get_current_position(self) -> float:
        """Get current position."""
        return self.audio_engine.get_position()
    
    def get_duration(self) -> float:
        """Get duration."""
        return self.audio_engine.get_duration()
    
    def get_current_file(self) -> Optional[str]:
        """Get current file path."""
        metadata = self.audio_engine.get_metadata()
        return metadata.file_path if metadata else None
    
    def get_current_metadata(self) -> Optional[SimpleAudioMetadata]:
        """Get current metadata."""
        return self.audio_engine.get_metadata()
    
    def get_current_state(self) -> str:
        """Get current state."""
        return self.current_state
    
    def is_file_loaded(self) -> bool:
        """Check if file is loaded."""
        return self.audio_engine.get_metadata() is not None
    
    def can_play(self) -> bool:
        """Check if can play."""
        return (self.is_file_loaded() and 
                self.current_state in [PlaybackState.STOPPED, PlaybackState.PAUSED])
    
    def can_pause(self) -> bool:
        """Check if can pause."""
        return self.current_state == PlaybackState.PLAYING
    
    def can_stop(self) -> bool:
        """Check if can stop."""
        return self.current_state in [PlaybackState.PLAYING, PlaybackState.PAUSED]
    
    def can_seek(self) -> bool:
        """Check if can seek."""
        return self.is_file_loaded() and self.get_duration() > 0
    
    def _set_state(self, new_state: str):
        """Set state and emit signal."""
        if self.current_state != new_state:
            old_state = self.current_state
            self.current_state = new_state
            
            if detailed_logger:
                detailed_logger.log_audio_operation("controller_set_state", {
                    "from_state": old_state,
                    "to_state": new_state
                })
            
            self.state_changed.emit(new_state)
    
    def cleanup(self):
        """Cleanup controller."""
        try:
            if detailed_logger:
                detailed_logger.info("מנקה בקר ניגון")
            
            if self.audio_engine:
                self.audio_engine.cleanup()
            
            if detailed_logger:
                detailed_logger.info("ניקוי בקר ניגון הושלם")
                
        except Exception as e:
            logger.exception(f"Error cleaning up controller: {e}")
            if detailed_logger:
                detailed_logger.exception(f"שגיאה בניקוי בקר: {e}")