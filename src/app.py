"""
Application initialization and dependency injection setup.

This module handles the creation and configuration of the main application,
setting up all necessary services and controllers.
"""

import sys
import os
import logging
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import QStandardPaths
from PySide6.QtGui import QIcon

from engine.simple_audio_player import SimpleAudioEngine
from controllers.simple_playback_controller import SimplePlaybackController
from ui.simple_window import SimpleAudioPlayer

logger = logging.getLogger(__name__)

# Import detailed logger
try:
    from utils.logger import get_logger
    detailed_logger = get_logger()
except ImportError:
    detailed_logger = None

class BinaKsheraApp:
    """Main application class that manages the lifecycle and dependencies."""
    
    def __init__(self):
        self.qt_app: Optional[QApplication] = None
        self.audio_engine: Optional[SimpleAudioEngine] = None
        self.playback_controller: Optional[SimplePlaybackController] = None
        self.main_window: Optional[SimpleAudioPlayer] = None
        
    def initialize(self) -> bool:
        """Initialize all application components."""
        try:
            # Create Qt application
            self.qt_app = QApplication(sys.argv)
            self.qt_app.setApplicationName("Bina Cshera")
            self.qt_app.setApplicationVersion("1.0.0")
            self.qt_app.setOrganizationName("Bina Cshera Team")
            
            # Set application icon if available
            icon_path = self._get_resource_path("icon.ico")
            if icon_path and icon_path.exists():
                self.qt_app.setWindowIcon(QIcon(str(icon_path)))
            
            # Initialize audio engine
            self.audio_engine = SimpleAudioEngine()
            if not self.audio_engine.initialize():
                logger.error("Failed to initialize audio engine")
                return False
            
            # Initialize playback controller
            self.playback_controller = SimplePlaybackController(self.audio_engine)
            
            # Create main window
            self.main_window = SimpleAudioPlayer(self.playback_controller)
            
            logger.info("Application initialized successfully")
            return True
            
        except Exception as e:
            logger.exception(f"Failed to initialize application: {e}")
            return False
    
    def _get_resource_path(self, filename: str) -> Optional[Path]:
        """Get path to a resource file."""
        # Try relative to executable (for PyInstaller)
        if getattr(sys, 'frozen', False):
            base_path = Path(sys.executable).parent
        else:
            base_path = Path(__file__).parent
            
        resource_path = base_path / "resources" / filename
        return resource_path if resource_path.exists() else None
    
    def show(self):
        """Show the main window."""
        if self.main_window:
            self.main_window.show()
            self.main_window.raise_()
            self.main_window.activateWindow()
    
    def exec(self) -> int:
        """Start the application event loop."""
        if self.qt_app:
            return self.qt_app.exec()
        return 1
    
    def cleanup(self):
        """Cleanup application resources."""
        try:
            if self.audio_engine:
                self.audio_engine.cleanup()
            logger.info("Application cleanup completed")
        except Exception as e:
            logger.exception(f"Error during cleanup: {e}")

def create_application() -> Optional[BinaKsheraApp]:
    """Create and initialize the application."""
    try:
        app = BinaKsheraApp()
        
        if not app.initialize():
            logger.error("Failed to initialize application")
            return None
        
        # Show main window
        app.show()
        
        return app
        
    except Exception as e:
        logger.exception(f"Failed to create application: {e}")
        return None
