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
        
        # Check for interface mode
        use_modern = "--modern" in sys.argv or "--qml" in sys.argv
        
        if use_modern:
            logger.info("Starting modern QML interface")
            try:
                from app_modern import create_modern_application
                app = create_modern_application()
                if app is None:
                    logger.warning("Failed to create modern interface, falling back to classic")
                    use_modern = False
                else:
                    exit_code = app.exec()
                    app.cleanup()
                    logger.info(f"Modern application exited with code: {exit_code}")
                    return exit_code
            except ImportError as e:
                logger.warning(f"Modern interface not available: {e}, using classic interface")
                use_modern = False
        
        if not use_modern:
            logger.info("Starting classic PySide6 interface")
            from app import create_application
            app = create_application()
            
            if app is None:
                logger.error("Failed to create application")
                return 1
                
            # Start the application event loop
            exit_code = app.exec()
            app.cleanup()
            logger.info(f"Classic application exited with code: {exit_code}")
            return exit_code
        
    except Exception as e:
        print(f"Fatal error starting application: {e}")
        logging.exception("Fatal error in main()")
        return 1

if __name__ == "__main__":
    sys.exit(main())
