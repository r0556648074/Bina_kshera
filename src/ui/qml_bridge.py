"""
QML Bridge for integrating modern QML interface with Python audio engine.

This module provides the bridge between the QML interface and the Python
audio processing backend, handling signals, data conversion, and UI updates.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict, Any

from PySide6.QtCore import QObject, Signal, Slot, Property, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine, qmlRegisterType, qmlRegisterSingletonType
from PySide6.QtQuick import QQuickItem

from controllers.playback_controller import PlaybackController, PlaybackState
from engine.audio_engine import AudioEngine
from engine.file_handler import TranscriptData, TranscriptSegment

logger = logging.getLogger(__name__)

class AudioDataModel(QObject):
    """Model for exposing audio data to QML."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._audio_data: Optional[List[float]] = None
        self._sample_rate: int = 44100
        self._duration: float = 0.0
    
    audioDataChanged = Signal()
    sampleRateChanged = Signal()
    durationChanged = Signal()
    
    @Property(list, notify=audioDataChanged)
    def audioData(self):
        return self._audio_data or []
    
    @Property(int, notify=sampleRateChanged)
    def sampleRate(self):
        return self._sample_rate
    
    @Property(float, notify=durationChanged)
    def duration(self):
        return self._duration
    
    def setAudioData(self, data, sample_rate):
        """Set audio data for visualization."""
        if data is not None:
            # Convert numpy array to Python list for QML
            self._audio_data = data.tolist() if hasattr(data, 'tolist') else list(data)
            self._sample_rate = sample_rate
            self._duration = len(self._audio_data) / sample_rate
        else:
            self._audio_data = None
            self._sample_rate = 44100
            self._duration = 0.0

class TranscriptModel(QObject):
    """Model for exposing transcript data to QML."""
    
    segmentsChanged = Signal()
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._segments: List[Dict[str, Any]] = []
    
    @Property(list, notify=segmentsChanged)
    def segments(self):
        return self._segments
    
    def setTranscriptData(self, transcript_data: Optional[TranscriptData]):
        """Set transcript data from the file handler."""
        if transcript_data:
            self._segments = []
            for segment in transcript_data.segments:
                segment_dict = {
                    'startTime': segment.start_time,
                    'endTime': segment.end_time,
                    'text': segment.text,
                    'speaker': segment.speaker or '',
                    'confidence': segment.confidence or 0.0
                }
                self._segments.append(segment_dict)
        else:
            self._segments = []
        
        self.segmentsChanged.emit()

class QMLAudioController(QObject):
    """Main controller exposed to QML for audio operations."""
    
    # Signals for QML
    stateChanged = Signal(str)
    positionChanged = Signal(float)
    durationChanged = Signal(float)
    fileLoaded = Signal(str)
    errorOccurred = Signal(str)
    statusChanged = Signal(str)
    
    def __init__(self, playback_controller: PlaybackController, parent=None):
        super().__init__(parent)
        
        self.playback_controller = playback_controller
        self.audio_data_model = AudioDataModel(self)
        self.transcript_model = TranscriptModel(self)
        
        # Connect playback controller signals
        self._connect_signals()
        
        logger.info("QML Audio Controller initialized")
    
    def _connect_signals(self):
        """Connect playback controller signals to QML signals."""
        self.playback_controller.state_changed.connect(self.stateChanged)
        self.playback_controller.position_changed.connect(self.positionChanged)
        self.playback_controller.duration_changed.connect(self.durationChanged)
        self.playback_controller.file_loaded.connect(self._on_file_loaded)
        self.playback_controller.transcript_loaded.connect(self._on_transcript_loaded)
        self.playback_controller.error_occurred.connect(self.errorOccurred)
        self.playback_controller.loading_progress.connect(self.statusChanged)
        
        # Connect audio data signal
        self.playback_controller.audio_engine.audio_data_ready.connect(
            self._on_audio_data_ready
        )
    
    def _on_file_loaded(self, file_path: str, metadata):
        """Handle file loaded signal."""
        filename = Path(file_path).name
        self.fileLoaded.emit(filename)
        logger.info(f"File loaded in QML bridge: {filename}")
    
    def _on_transcript_loaded(self, transcript_data: TranscriptData):
        """Handle transcript loaded signal."""
        self.transcript_model.setTranscriptData(transcript_data)
        logger.info("Transcript loaded in QML bridge")
    
    def _on_audio_data_ready(self, audio_data, sample_rate):
        """Handle audio data ready for visualization."""
        self.audio_data_model.setAudioData(audio_data, sample_rate)
        logger.info("Audio data ready for QML visualization")
    
    # Properties exposed to QML
    @Property(QObject, constant=True)
    def audioDataModel(self):
        return self.audio_data_model
    
    @Property(QObject, constant=True)
    def transcriptModel(self):
        return self.transcript_model
    
    @Property(str, notify=stateChanged)
    def currentState(self):
        return self.playback_controller.get_current_state()
    
    @Property(float, notify=positionChanged)
    def currentPosition(self):
        return self.playback_controller.get_current_position()
    
    @Property(float, notify=durationChanged)
    def currentDuration(self):
        return self.playback_controller.get_duration()
    
    @Property(bool, notify=stateChanged)
    def canPlay(self):
        return self.playback_controller.can_play()
    
    @Property(bool, notify=stateChanged)
    def canPause(self):
        return self.playback_controller.can_pause()
    
    @Property(bool, notify=stateChanged)
    def canStop(self):
        return self.playback_controller.can_stop()
    
    # Slots for QML to call
    @Slot()
    def openFileDialog(self):
        """Open file dialog to select audio file."""
        try:
            success = self.playback_controller.open_file_dialog()
            if not success:
                self.statusChanged.emit("לא נבחר קובץ")
        except Exception as e:
            logger.error(f"Error opening file dialog: {e}")
            self.errorOccurred.emit(f"שגיאה בפתיחת תיבת הדו-שיח: {str(e)}")
    
    @Slot()
    def play(self):
        """Start or resume playback."""
        try:
            success = self.playback_controller.play()
            if not success:
                self.errorOccurred.emit("לא ניתן להתחיל ניגון")
        except Exception as e:
            logger.error(f"Error starting playback: {e}")
            self.errorOccurred.emit(f"שגיאה בניגון: {str(e)}")
    
    @Slot()
    def pause(self):
        """Pause playback."""
        try:
            self.playback_controller.pause()
        except Exception as e:
            logger.error(f"Error pausing playback: {e}")
            self.errorOccurred.emit(f"שגיאה בהשהיית ניגון: {str(e)}")
    
    @Slot()
    def stop(self):
        """Stop playback."""
        try:
            self.playback_controller.stop()
        except Exception as e:
            logger.error(f"Error stopping playback: {e}")
            self.errorOccurred.emit(f"שגיאה בעצירת ניגון: {str(e)}")
    
    @Slot(float)
    def seek(self, position: float):
        """Seek to specific position."""
        try:
            self.playback_controller.seek(position)
        except Exception as e:
            logger.error(f"Error seeking to {position}: {e}")
            self.errorOccurred.emit(f"שגיאה בדילוג: {str(e)}")
    
    @Slot(float)
    def setVolume(self, volume: float):
        """Set playback volume (0.0 to 1.0)."""
        try:
            self.playback_controller.set_volume(volume)
        except Exception as e:
            logger.error(f"Error setting volume to {volume}: {e}")
    
    @Slot(str, result=bool)
    def loadFile(self, file_path: str):
        """Load audio file from path."""
        try:
            return self.playback_controller.load_file(file_path)
        except Exception as e:
            logger.error(f"Error loading file {file_path}: {e}")
            self.errorOccurred.emit(f"שגיאה בטעינת קובץ: {str(e)}")
            return False

class QMLMainApplication:
    """Main QML application manager."""
    
    def __init__(self, playback_controller: PlaybackController):
        self.playback_controller = playback_controller
        self.app: Optional[QGuiApplication] = None
        self.engine: Optional[QQmlApplicationEngine] = None
        self.audio_controller: Optional[QMLAudioController] = None
        
    def initialize(self) -> bool:
        """Initialize the QML application."""
        try:
            # Create QGuiApplication
            self.app = QGuiApplication(sys.argv)
            self.app.setApplicationName("נגן בינה כשרה")
            self.app.setApplicationVersion("1.0.0")
            self.app.setOrganizationName("Bina Kshera Team")
            
            # Create QML engine
            self.engine = QQmlApplicationEngine()
            
            # Register QML types
            self._register_qml_types()
            
            # Create and expose audio controller
            self.audio_controller = QMLAudioController(self.playback_controller)
            self.engine.rootContext().setContextProperty("audioController", self.audio_controller)
            
            # Set QML import paths
            qml_dir = Path(__file__).parent / "qml"
            self.engine.addImportPath(str(qml_dir))
            
            # Load main QML file
            main_qml = qml_dir / "MainWindow.qml"
            if not main_qml.exists():
                logger.error(f"Main QML file not found: {main_qml}")
                return False
            
            self.engine.load(QUrl.fromLocalFile(str(main_qml)))
            
            # Check if QML loaded successfully
            if not self.engine.rootObjects():
                logger.error("Failed to load QML interface")
                return False
            
            logger.info("QML application initialized successfully")
            return True
            
        except Exception as e:
            logger.exception(f"Failed to initialize QML application: {e}")
            return False
    
    def _register_qml_types(self):
        """Register custom QML types."""
        try:
            # Note: In this implementation we'll use context properties instead of registered types
            # This is more reliable for complex data models
            logger.info("Using context properties for QML integration")
            
        except Exception as e:
            logger.error(f"Failed to register QML types: {e}")
    
    def run(self) -> int:
        """Run the QML application."""
        if not self.app:
            logger.error("Application not initialized")
            return 1
        
        try:
            return self.app.exec()
        except Exception as e:
            logger.exception(f"Error running QML application: {e}")
            return 1
    
    def cleanup(self):
        """Cleanup QML application resources."""
        try:
            if self.audio_controller:
                # Cleanup audio controller if needed
                pass
            
            if self.engine:
                self.engine.deleteLater()
                self.engine = None
            
            logger.info("QML application cleanup completed")
            
        except Exception as e:
            logger.error(f"Error during QML cleanup: {e}")

def create_qml_application(playback_controller: PlaybackController) -> Optional[QMLMainApplication]:
    """Create and initialize QML application."""
    try:
        qml_app = QMLMainApplication(playback_controller)
        
        if not qml_app.initialize():
            logger.error("Failed to initialize QML application")
            return None
        
        return qml_app
        
    except Exception as e:
        logger.exception(f"Failed to create QML application: {e}")
        return None