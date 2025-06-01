"""
Playback controller for managing audio playback state and coordination.

This controller acts as the central coordinator between the UI and the audio engine,
managing playback state, file loading, and user interactions.
"""

import logging
from typing import Optional, Dict, Any
from pathlib import Path

from PySide6.QtCore import QObject, Signal, QTimer
from PySide6.QtWidgets import QFileDialog, QMessageBox

from engine.audio_engine import AudioEngine, AudioMetadata
from engine.file_handler import FileHandler, TranscriptData, FileMetadata

logger = logging.getLogger(__name__)

class PlaybackState:
    """Enumeration of playback states."""
    STOPPED = "stopped"
    PLAYING = "playing"
    PAUSED = "paused"
    LOADING = "loading"
    ERROR = "error"

class PlaybackController(QObject):
    """Central controller for audio playback management."""
    
    # Signals for UI updates
    state_changed = Signal(str)                    # PlaybackState
    position_changed = Signal(float)               # Current position in seconds
    duration_changed = Signal(float)               # Total duration in seconds
    file_loaded = Signal(str, object)              # File path, metadata
    transcript_loaded = Signal(object)             # TranscriptData
    error_occurred = Signal(str)                   # Error message
    loading_progress = Signal(str)                 # Loading status message
    
    def __init__(self, audio_engine: AudioEngine, parent=None):
        super().__init__(parent)
        
        self.audio_engine = audio_engine
        self.file_handler = FileHandler()
        
        # State
        self.current_state = PlaybackState.STOPPED
        self.current_file: Optional[str] = None
        self.current_metadata: Optional[AudioMetadata] = None
        self.current_transcript: Optional[TranscriptData] = None
        self.file_metadata: Optional[FileMetadata] = None
        
        # Settings
        self.volume = 1.0
        self.auto_load_transcript = True
        
        # Connect audio engine signals
        self._connect_audio_engine_signals()
        
        logger.info("Playback controller initialized")
    
    def _connect_audio_engine_signals(self):
        """Connect audio engine signals to controller methods."""
        self.audio_engine.position_changed.connect(self._on_position_changed)
        self.audio_engine.duration_changed.connect(self._on_duration_changed)
        self.audio_engine.state_changed.connect(self._on_audio_state_changed)
        self.audio_engine.error_occurred.connect(self._on_audio_error)
        self.audio_engine.audio_data_ready.connect(self._on_audio_data_ready)
    
    def _on_position_changed(self, position: float):
        """Handle position change from audio engine."""
        self.position_changed.emit(position)
    
    def _on_duration_changed(self, duration: float):
        """Handle duration change from audio engine."""
        self.duration_changed.emit(duration)
    
    def _on_audio_state_changed(self, state: str):
        """Handle state change from audio engine."""
        if state == 'playing':
            self._set_state(PlaybackState.PLAYING)
        elif state == 'paused':
            self._set_state(PlaybackState.PAUSED)
        elif state == 'stopped':
            self._set_state(PlaybackState.STOPPED)
    
    def _on_audio_error(self, error_message: str):
        """Handle error from audio engine."""
        self._set_state(PlaybackState.ERROR)
        self.error_occurred.emit(error_message)
    
    def _on_audio_data_ready(self, audio_data, sample_rate):
        """Handle audio data ready for visualization."""
        # This will be connected to the waveform widget
        pass
    
    def _set_state(self, new_state: str):
        """Set the current playback state and emit signal."""
        if self.current_state != new_state:
            self.current_state = new_state
            self.state_changed.emit(new_state)
            logger.debug(f"Playback state changed to: {new_state}")
    
    def open_file_dialog(self, parent_widget=None) -> bool:
        """Open file dialog to select an audio file."""
        try:
            file_filter = self.file_handler.get_audio_filter_string()
            
            file_path, _ = QFileDialog.getOpenFileName(
                parent_widget,
                "Open Audio File",
                "",
                file_filter
            )
            
            if file_path:
                return self.load_file(file_path)
            
            return False
            
        except Exception as e:
            logger.exception(f"Error in file dialog: {e}")
            self.error_occurred.emit(f"Failed to open file dialog: {str(e)}")
            return False
    
    def load_file(self, file_path: str) -> bool:
        """Load an audio file for playback."""
        try:
            self._set_state(PlaybackState.LOADING)
            self.loading_progress.emit("Loading file...")
            
            # Validate file
            if not self.file_handler.is_supported_audio_file(file_path):
                error_msg = f"Unsupported file format: {Path(file_path).suffix}"
                self.error_occurred.emit(error_msg)
                self._set_state(PlaybackState.ERROR)
                return False
            
            # Get file metadata
            self.loading_progress.emit("Reading file metadata...")
            self.file_metadata = self.file_handler.get_file_metadata(file_path)
            if not self.file_metadata:
                self.error_occurred.emit("Failed to read file metadata")
                self._set_state(PlaybackState.ERROR)
                return False
            
            # Load audio file
            self.loading_progress.emit("Loading audio...")
            if not self.audio_engine.load_file(file_path):
                self.error_occurred.emit("Failed to load audio file")
                self._set_state(PlaybackState.ERROR)
                return False
            
            # Update controller state
            self.current_file = file_path
            self.current_metadata = self.audio_engine.get_metadata()
            
            # Load transcript if available and auto-load is enabled
            if self.auto_load_transcript and self.file_metadata.has_transcript:
                self.loading_progress.emit("Loading transcript...")
                self.load_transcript(self.file_metadata.transcript_path)
            
            # Emit signals
            self.file_loaded.emit(file_path, self.current_metadata)
            self._set_state(PlaybackState.STOPPED)
            
            logger.info(f"Successfully loaded file: {file_path}")
            return True
            
        except Exception as e:
            logger.exception(f"Error loading file {file_path}: {e}")
            self.error_occurred.emit(f"Failed to load file: {str(e)}")
            self._set_state(PlaybackState.ERROR)
            return False
    
    def load_transcript(self, transcript_path: str) -> bool:
        """Load a transcript file."""
        try:
            if not transcript_path:
                logger.warning("No transcript path provided")
                return False
            
            transcript_data = self.file_handler.load_transcript(transcript_path)
            if not transcript_data:
                logger.error(f"Failed to load transcript: {transcript_path}")
                return False
            
            self.current_transcript = transcript_data
            self.transcript_loaded.emit(transcript_data)
            
            logger.info(f"Loaded transcript with {len(transcript_data.segments)} segments")
            return True
            
        except Exception as e:
            logger.exception(f"Error loading transcript {transcript_path}: {e}")
            self.error_occurred.emit(f"Failed to load transcript: {str(e)}")
            return False
    
    def play(self) -> bool:
        """Start or resume playback."""
        try:
            if not self.current_file:
                self.error_occurred.emit("No file loaded")
                return False
            
            if self.current_state == PlaybackState.PAUSED:
                # Resume
                success = self.audio_engine.play()
            else:
                # Start from beginning or current position
                success = self.audio_engine.play()
            
            if not success:
                self.error_occurred.emit("Failed to start playback")
                return False
            
            logger.info("Playback started")
            return True
            
        except Exception as e:
            logger.exception(f"Error starting playback: {e}")
            self.error_occurred.emit(f"Playback failed: {str(e)}")
            return False
    
    def pause(self):
        """Pause playback."""
        try:
            self.audio_engine.pause()
            logger.info("Playback paused")
        except Exception as e:
            logger.exception(f"Error pausing playback: {e}")
            self.error_occurred.emit(f"Failed to pause: {str(e)}")
    
    def stop(self):
        """Stop playback."""
        try:
            self.audio_engine.stop()
            logger.info("Playback stopped")
        except Exception as e:
            logger.exception(f"Error stopping playback: {e}")
            self.error_occurred.emit(f"Failed to stop: {str(e)}")
    
    def seek(self, position: float):
        """Seek to a specific position in seconds."""
        try:
            if not self.current_file:
                return
            
            self.audio_engine.seek(position)
            logger.debug(f"Seeked to position: {position:.2f}s")
            
        except Exception as e:
            logger.exception(f"Error seeking to {position}: {e}")
            self.error_occurred.emit(f"Seek failed: {str(e)}")
    
    def toggle_playback(self):
        """Toggle between play and pause."""
        if self.current_state == PlaybackState.PLAYING:
            self.pause()
        elif self.current_state in [PlaybackState.PAUSED, PlaybackState.STOPPED]:
            self.play()
    
    def set_volume(self, volume: float):
        """Set playback volume (0.0 to 1.0)."""
        try:
            self.volume = max(0.0, min(1.0, volume))
            # Note: Volume control would be implemented in audio engine
            logger.debug(f"Volume set to: {self.volume}")
        except Exception as e:
            logger.error(f"Error setting volume: {e}")
    
    def get_current_position(self) -> float:
        """Get current playback position in seconds."""
        return self.audio_engine.get_position()
    
    def get_duration(self) -> float:
        """Get total duration in seconds."""
        return self.audio_engine.get_duration()
    
    def get_current_file(self) -> Optional[str]:
        """Get currently loaded file path."""
        return self.current_file
    
    def get_current_metadata(self) -> Optional[AudioMetadata]:
        """Get current audio metadata."""
        return self.current_metadata
    
    def get_current_transcript(self) -> Optional[TranscriptData]:
        """Get current transcript data."""
        return self.current_transcript
    
    def get_current_state(self) -> str:
        """Get current playback state."""
        return self.current_state
    
    def is_file_loaded(self) -> bool:
        """Check if a file is currently loaded."""
        return self.current_file is not None
    
    def can_play(self) -> bool:
        """Check if playback can be started."""
        return (self.current_file is not None and 
                self.current_state in [PlaybackState.STOPPED, PlaybackState.PAUSED])
    
    def can_pause(self) -> bool:
        """Check if playback can be paused."""
        return self.current_state == PlaybackState.PLAYING
    
    def can_stop(self) -> bool:
        """Check if playback can be stopped."""
        return self.current_state in [PlaybackState.PLAYING, PlaybackState.PAUSED]
    
    def can_seek(self) -> bool:
        """Check if seeking is possible."""
        return self.current_file is not None
    
    def cleanup(self):
        """Cleanup controller resources."""
        try:
            self.stop()
            logger.info("Playback controller cleanup completed")
        except Exception as e:
            logger.error(f"Error during controller cleanup: {e}")
