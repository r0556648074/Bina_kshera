"""
Main application window for the Bina Cshera audio player.

This module contains the primary UI window that coordinates all UI components
and provides the main interface for the application.
"""

import logging
from typing import Optional

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QSplitter,
    QMenuBar, QMenu, QStatusBar, QLabel, QProgressBar, QMessageBox,
    QFileDialog, QApplication
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QAction, QKeySequence, QIcon

from controllers.playback_controller import PlaybackController, PlaybackState
from .waveform_widget import WaveformWidget
from .transcript_widget import TranscriptWidget
from .audio_controls import AudioControlsWidget

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow):
    """Main application window."""
    
    def __init__(self, playback_controller: PlaybackController, parent=None):
        super().__init__(parent)
        
        self.playback_controller = playback_controller
        self.current_file: Optional[str] = None
        
        # Setup UI
        self.setWindowTitle("Bina Cshera - Audio Player")
        self.setMinimumSize(800, 600)
        self.resize(1200, 800)
        
        # Create UI components
        self._create_menu_bar()
        self._create_status_bar()
        self._create_central_widget()
        
        # Connect signals
        self._connect_signals()
        
        # Update UI state
        self._update_ui_state()
        
        logger.info("Main window initialized")
    
    def _create_menu_bar(self):
        """Create the application menu bar."""
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        open_action = QAction("&Open Audio File...", self)
        open_action.setShortcut(QKeySequence.StandardKey.Open)
        open_action.setStatusTip("Open an audio file")
        open_action.triggered.connect(self._on_open_file)
        file_menu.addAction(open_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("E&xit", self)
        exit_action.setShortcut(QKeySequence.StandardKey.Quit)
        exit_action.setStatusTip("Exit the application")
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # Playback menu
        playback_menu = menubar.addMenu("&Playback")
        
        self.play_pause_action = QAction("&Play", self)
        self.play_pause_action.setShortcut(Qt.Key.Key_Space)
        self.play_pause_action.setStatusTip("Play or pause playback")
        self.play_pause_action.triggered.connect(self._on_play_pause)
        playback_menu.addAction(self.play_pause_action)
        
        self.stop_action = QAction("&Stop", self)
        self.stop_action.setShortcut(Qt.Key.Key_S)
        self.stop_action.setStatusTip("Stop playback")
        self.stop_action.triggered.connect(self._on_stop)
        playback_menu.addAction(self.stop_action)
        
        # View menu
        view_menu = menubar.addMenu("&View")
        
        self.show_transcript_action = QAction("Show &Transcript", self)
        self.show_transcript_action.setCheckable(True)
        self.show_transcript_action.setChecked(True)
        self.show_transcript_action.setStatusTip("Show or hide transcript panel")
        self.show_transcript_action.triggered.connect(self._on_toggle_transcript)
        view_menu.addAction(self.show_transcript_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        
        about_action = QAction("&About", self)
        about_action.setStatusTip("About Bina Cshera")
        about_action.triggered.connect(self._on_about)
        help_menu.addAction(about_action)
    
    def _create_status_bar(self):
        """Create the status bar."""
        self.status_bar = self.statusBar()
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)
        
        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        # Position/duration label
        self.time_label = QLabel("00:00 / 00:00")
        self.status_bar.addPermanentWidget(self.time_label)
    
    def _create_central_widget(self):
        """Create the central widget layout."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(5, 5, 5, 5)
        main_layout.setSpacing(5)
        
        # Audio controls at the top
        self.audio_controls = AudioControlsWidget(self.playback_controller)
        main_layout.addWidget(self.audio_controls)
        
        # Content splitter (waveform and transcript)
        self.content_splitter = QSplitter(Qt.Orientation.Horizontal)
        main_layout.addWidget(self.content_splitter, 1)  # Take remaining space
        
        # Waveform widget (left side)
        self.waveform_widget = WaveformWidget()
        self.content_splitter.addWidget(self.waveform_widget)
        
        # Transcript widget (right side)
        self.transcript_widget = TranscriptWidget()
        self.content_splitter.addWidget(self.transcript_widget)
        
        # Set splitter proportions (70% waveform, 30% transcript)
        self.content_splitter.setSizes([700, 300])
        
        # Connect waveform seeking to playback controller
        self.waveform_widget.seek_requested.connect(
            self.playback_controller.seek
        )
    
    def _connect_signals(self):
        """Connect signals from playback controller."""
        self.playback_controller.state_changed.connect(self._on_state_changed)
        self.playback_controller.position_changed.connect(self._on_position_changed)
        self.playback_controller.duration_changed.connect(self._on_duration_changed)
        self.playback_controller.file_loaded.connect(self._on_file_loaded)
        self.playback_controller.transcript_loaded.connect(self._on_transcript_loaded)
        self.playback_controller.error_occurred.connect(self._on_error)
        self.playback_controller.loading_progress.connect(self._on_loading_progress)
        
        # Connect audio data to waveform
        self.playback_controller.audio_engine.audio_data_ready.connect(
            self.waveform_widget.set_audio_data
        )
    
    def _on_open_file(self):
        """Handle open file action."""
        self.playback_controller.open_file_dialog(self)
    
    def _on_play_pause(self):
        """Handle play/pause action."""
        self.playback_controller.toggle_playback()
    
    def _on_stop(self):
        """Handle stop action."""
        self.playback_controller.stop()
    
    def _on_toggle_transcript(self, checked: bool):
        """Handle transcript panel toggle."""
        self.transcript_widget.setVisible(checked)
    
    def _on_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About Bina Cshera",
            "Bina Cshera Audio Player\n\n"
            "A sophisticated audio player with synchronized transcript display "
            "and waveform visualization.\n\n"
            "Version 1.0.0"
        )
    
    def _on_state_changed(self, state: str):
        """Handle playback state change."""
        if state == PlaybackState.PLAYING:
            self.play_pause_action.setText("&Pause")
            self.play_pause_action.setStatusTip("Pause playback")
            self.status_label.setText("Playing")
        elif state == PlaybackState.PAUSED:
            self.play_pause_action.setText("&Play")
            self.play_pause_action.setStatusTip("Resume playback")
            self.status_label.setText("Paused")
        elif state == PlaybackState.STOPPED:
            self.play_pause_action.setText("&Play")
            self.play_pause_action.setStatusTip("Start playback")
            self.status_label.setText("Stopped")
        elif state == PlaybackState.LOADING:
            self.status_label.setText("Loading...")
            self.progress_bar.setVisible(True)
        elif state == PlaybackState.ERROR:
            self.status_label.setText("Error")
            self.progress_bar.setVisible(False)
        
        self._update_ui_state()
    
    def _on_position_changed(self, position: float):
        """Handle position change."""
        duration = self.playback_controller.get_duration()
        self._update_time_display(position, duration)
        
        # Update waveform position
        self.waveform_widget.set_position(position)
        
        # Update transcript position
        self.transcript_widget.set_position(position)
    
    def _on_duration_changed(self, duration: float):
        """Handle duration change."""
        position = self.playback_controller.get_current_position()
        self._update_time_display(position, duration)
        
        # Update waveform duration
        self.waveform_widget.set_duration(duration)
    
    def _on_file_loaded(self, file_path: str, metadata):
        """Handle file loaded."""
        self.current_file = file_path
        filename = file_path.split('/')[-1].split('\\')[-1]  # Cross-platform basename
        self.setWindowTitle(f"Bina Cshera - {filename}")
        self.status_label.setText(f"Loaded: {filename}")
        self.progress_bar.setVisible(False)
        
        # Clear transcript if no new one will be loaded
        if not self.playback_controller.file_metadata or not self.playback_controller.file_metadata.has_transcript:
            self.transcript_widget.clear_transcript()
    
    def _on_transcript_loaded(self, transcript_data):
        """Handle transcript loaded."""
        self.transcript_widget.set_transcript(transcript_data)
        logger.info("Transcript loaded in UI")
    
    def _on_error(self, error_message: str):
        """Handle error message."""
        self.status_label.setText("Error")
        self.progress_bar.setVisible(False)
        
        QMessageBox.critical(
            self,
            "Error",
            f"An error occurred:\n\n{error_message}"
        )
    
    def _on_loading_progress(self, message: str):
        """Handle loading progress update."""
        self.status_label.setText(message)
    
    def _update_time_display(self, position: float, duration: float):
        """Update the time display in status bar."""
        pos_str = self._format_time(position)
        dur_str = self._format_time(duration)
        self.time_label.setText(f"{pos_str} / {dur_str}")
    
    def _format_time(self, seconds: float) -> str:
        """Format seconds to MM:SS or HH:MM:SS format."""
        if seconds < 0:
            seconds = 0
        
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        else:
            return f"{minutes:02d}:{secs:02d}"
    
    def _update_ui_state(self):
        """Update UI component states based on playback controller state."""
        can_play = self.playback_controller.can_play()
        can_pause = self.playback_controller.can_pause()
        can_stop = self.playback_controller.can_stop()
        
        # Update menu actions
        self.play_pause_action.setEnabled(can_play or can_pause)
        self.stop_action.setEnabled(can_stop)
    
    def keyPressEvent(self, event):
        """Handle key press events."""
        key = event.key()
        
        if key == Qt.Key.Key_Space:
            self.playback_controller.toggle_playback()
            event.accept()
        elif key == Qt.Key.Key_S and event.modifiers() == Qt.KeyboardModifier.NoModifier:
            self.playback_controller.stop()
            event.accept()
        elif key == Qt.Key.Key_O and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self._on_open_file()
            event.accept()
        else:
            super().keyPressEvent(event)
    
    def closeEvent(self, event):
        """Handle window close event."""
        try:
            # Cleanup playback controller
            self.playback_controller.cleanup()
            event.accept()
        except Exception as e:
            logger.error(f"Error during window close: {e}")
            event.accept()  # Close anyway
