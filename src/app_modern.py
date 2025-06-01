"""
Modern QML-based application initialization.

This module handles the creation and configuration of the modern QML interface
version of the Bina Cshera audio player.
"""

import sys
import os
import logging
from pathlib import Path
from typing import Optional

from engine.audio_engine import AudioEngine
from controllers.playback_controller import PlaybackController
from ui.qml_bridge import create_qml_application, QMLMainApplication

logger = logging.getLogger(__name__)

class ModernBinaKsheraApp:
    """Modern QML-based application class."""
    
    def __init__(self):
        self.audio_engine: Optional[AudioEngine] = None
        self.playback_controller: Optional[PlaybackController] = None
        self.qml_app: Optional[QMLMainApplication] = None
        
    def initialize(self) -> bool:
        """Initialize all application components."""
        try:
            # Initialize audio engine
            self.audio_engine = AudioEngine()
            if not self.audio_engine.initialize():
                logger.error("Failed to initialize audio engine")
                return False
            
            # Initialize playback controller
            self.playback_controller = PlaybackController(self.audio_engine)
            
            # Create QML application
            self.qml_app = create_qml_application(self.playback_controller)
            if not self.qml_app:
                logger.error("Failed to create QML application")
                return False
            
            logger.info("Modern application initialized successfully")
            return True
            
        except Exception as e:
            logger.exception(f"Failed to initialize modern application: {e}")
            return False
    
    def exec(self) -> int:
        """Start the application event loop."""
        if self.qml_app:
            return self.qml_app.run()
        return 1
    
    def cleanup(self):
        """Cleanup application resources."""
        try:
            if self.qml_app:
                self.qml_app.cleanup()
            
            if self.audio_engine:
                self.audio_engine.cleanup()
                
            logger.info("Modern application cleanup completed")
            
        except Exception as e:
            logger.exception(f"Error during modern app cleanup: {e}")

def create_modern_application() -> Optional[ModernBinaKsheraApp]:
    """Create and initialize the modern QML application."""
    try:
        app = ModernBinaKsheraApp()
        
        if not app.initialize():
            logger.error("Failed to initialize modern application")
            return None
        
        return app
        
    except Exception as e:
        logger.exception(f"Failed to create modern application: {e}")
        return None