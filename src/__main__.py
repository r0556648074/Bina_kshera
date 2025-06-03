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
        
        # Try advanced player first, fallback to simple
        logger.info("מנסה לטעון נגן מתקדם עם כל התכונות")
        
        try:
            from ultra_modern_player import create_revolutionary_audio_app
            logger.start_operation("טעינת נגן מהפכני")
            
            app, window = create_revolutionary_audio_app()
            if app and window:
                logger.end_operation("טעינת נגן מהפכני")
                logger.start_operation("הרצת נגן מהפכני")
                logger.info("נגן מהפכני מוכן ופועל")
                
                exit_code = app.exec()
                logger.end_operation("הרצת נגן מהפכני")
                logger.info(f"הנגן המהפכני הסתיים עם קוד: {exit_code}")
                return exit_code
                
        except Exception as e:
            logger.warning(f"נגן מהפכני לא זמין, עובר למתקדם: {e}")
            
        # Fallback to advanced player
        try:
            from advanced_audio_app import create_advanced_audio_app
            logger.start_operation("טעינת נגן מתקדם")
            
            app, window = create_advanced_audio_app()
            if app and window:
                logger.end_operation("טעינת נגן מתקדם")
                logger.start_operation("הרצת נגן מתקדם")
                logger.info("נגן מתקדם מוכן ופועל")
                
                exit_code = app.exec()
                logger.end_operation("הרצת נגן מתקדם")
                logger.info(f"הנגן המתקדם הסתיים עם קוד: {exit_code}")
                return exit_code
                
        except Exception as e:
            logger.warning(f"שגיאה בנגן מתקדם, עובר לנגן פשוט: {e}")
        
        # Fallback to simple interface
        logger.info("מתחיל ממשק יחיד ופשוט")
        logger.start_operation("טעינת ממשק")
        
        try:
            from simple_audio_app import create_simple_audio_app
            logger.info("יוצר נגן אודיו פשוט ועובד")
            
            app, window = create_simple_audio_app()
            
            if app is None or window is None:
                logger.error("יצירת נגן פשוט נכשלה")
                return 1
            
            logger.end_operation("טעינת ממשק")
            logger.start_operation("הרצת נגן פשוט")
            logger.info("נגן אודיו פשוט מוכן ופועל")
            
            # Start the application event loop
            exit_code = app.exec()
            logger.end_operation("הרצת נגן פשוט")
            logger.info(f"הנגן הפשוט הסתיים עם קוד: {exit_code}")
            return exit_code
            
        except Exception as e:
            logger.end_operation("טעינת ממשק")
            logger.exception(f"שגיאה בהפעלת הנגן הפשוט: {e}")
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
