#!/usr/bin/env python3
"""
Main entry point for the Bina Cshera audio player application.

This module serves as the primary entry point and handles application initialization,
dependency injection setup, and main window creation.
"""

import sys
import os
import logging
from pathlib import Path

# Add src directory to Python path for imports
src_path = Path(__file__).parent
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from app import create_application

def setup_logging():
    """Configure application logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('bina_cshera.log', mode='a')
        ]
    )

def main():
    """Main application entry point."""
    try:
        # Setup logging
        setup_logging()
        logger = logging.getLogger(__name__)
        logger.info("Starting Bina Cshera application")
        
        # Create and run the application
        app = create_application()
        
        if app is None:
            logger.error("Failed to create application")
            return 1
            
        # Start the application event loop
        exit_code = app.exec()
        logger.info(f"Application exited with code: {exit_code}")
        return exit_code
        
    except Exception as e:
        print(f"Fatal error starting application: {e}")
        logging.exception("Fatal error in main()")
        return 1

if __name__ == "__main__":
    sys.exit(main())
