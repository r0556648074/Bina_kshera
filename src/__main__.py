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
    from utils.logger import setup_logging as setup_detailed_logging
    return setup_detailed_logging()

def main():
    """Main application entry point."""
    logger = None
    try:
        # Setup detailed logging
        logger = setup_logging()
        logger.info("התחלת נגן בינה כשרה")
        logger.log_system_info()
        logger.log_dependencies()
        
        # Check for interface mode
        use_modern = "--modern" in sys.argv or "--qml" in sys.argv
        logger.info(f"מצב ממשק נבחר: {'מודרני' if use_modern else 'קלאסי'}")
        
        if use_modern:
            logger.start_operation("טעינת ממשק מודרני")
            try:
                from app_modern import create_modern_application
                logger.info("יצירת אפליקציה מודרנית")
                app = create_modern_application()
                if app is None:
                    logger.warning("יצירת ממשק מודרני נכשלה, עובר לממשק קלאסי")
                    use_modern = False
                else:
                    logger.end_operation("טעינת ממשק מודרני")
                    logger.start_operation("הרצת אפליקציה מודרנית")
                    exit_code = app.exec()
                    logger.end_operation("הרצת אפליקציה מודרנית")
                    app.cleanup()
                    logger.info(f"אפליקציה מודרנית הסתיימה עם קוד: {exit_code}")
                    return exit_code
            except ImportError as e:
                logger.end_operation("טעינת ממשק מודרני")
                logger.warning(f"ממשק מודרני לא זמין: {e}, עובר לממשק קלאסי")
                use_modern = False
            except Exception as e:
                logger.end_operation("טעינת ממשק מודרני")
                logger.exception(f"שגיאה בממשק מודרני: {e}")
                use_modern = False
        
        if not use_modern:
            logger.start_operation("טעינת ממשק קלאסי")
            try:
                from app import create_application
                logger.info("יצירת אפליקציה קלאסית")
                app = create_application()
                
                if app is None:
                    logger.error("יצירת אפליקציה נכשלה")
                    return 1
                
                logger.end_operation("טעינת ממשק קלאסי")
                logger.start_operation("הרצת אפליקציה קלאסית")
                
                # Start the application event loop
                exit_code = app.exec()
                logger.end_operation("הרצת אפליקציה קלאסית")
                app.cleanup()
                logger.info(f"אפליקציה קלאסית הסתיימה עם קוד: {exit_code}")
                return exit_code
                
            except Exception as e:
                logger.end_operation("טעינת ממשק קלאסי")
                logger.exception(f"שגיאה קריטית באפליקציה קלאסית: {e}")
                return 1
        
    except Exception as e:
        error_msg = f"שגיאה קריטית בהפעלת התוכנה: {e}"
        print(error_msg)
        if logger:
            logger.exception(error_msg)
        else:
            logging.exception("Fatal error in main()")
        return 1
    finally:
        if logger:
            logger.finalize()

if __name__ == "__main__":
    sys.exit(main())
