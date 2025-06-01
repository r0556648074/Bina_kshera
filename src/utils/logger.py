"""
Advanced logging system for Bina Cshera audio player.

This module provides detailed logging capabilities with real-time file updates
and performance monitoring.
"""

import logging
import sys
import os
import time
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
import threading
import traceback

class RealTimeFileHandler(logging.FileHandler):
    """Custom file handler that flushes immediately for real-time updates."""
    
    def emit(self, record):
        """Emit a record with immediate flush."""
        super().emit(record)
        self.flush()

class PerformanceLogger:
    """Logger for tracking performance metrics and detailed operations."""
    
    def __init__(self, log_dir: str = "."):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Create separate log files
        self.main_log = self.log_dir / "bina_cshera_detailed.log"
        self.performance_log = self.log_dir / "bina_cshera_performance.log"
        self.error_log = self.log_dir / "bina_cshera_errors.log"
        
        # Setup loggers
        self._setup_loggers()
        
        # Performance tracking
        self.operation_times = {}
        self.start_times = {}
        
        self.info("=== נגן בינה כשרה התחיל ===")
        self.info(f"זמן התחלה: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        self.info(f"גרסת Python: {sys.version}")
        self.info(f"מערכת הפעלה: {os.name}")
    
    def _setup_loggers(self):
        """Setup multiple loggers for different purposes."""
        
        # Main detailed logger
        self.logger = logging.getLogger('bina_cshera_main')
        self.logger.setLevel(logging.DEBUG)
        
        # Performance logger
        self.perf_logger = logging.getLogger('bina_cshera_performance')
        self.perf_logger.setLevel(logging.INFO)
        
        # Error logger
        self.error_logger = logging.getLogger('bina_cshera_errors')
        self.error_logger.setLevel(logging.ERROR)
        
        # Clear existing handlers
        for logger in [self.logger, self.perf_logger, self.error_logger]:
            logger.handlers.clear()
        
        # Create formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s | %(funcName)s:%(lineno)d | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter(
            '%(asctime)s | %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # Main log file handler
        main_handler = RealTimeFileHandler(str(self.main_log), mode='w', encoding='utf-8')
        main_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(main_handler)
        
        # Console handler for main logger
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(simple_formatter)
        self.logger.addHandler(console_handler)
        
        # Performance log handler
        perf_handler = RealTimeFileHandler(str(self.performance_log), mode='w', encoding='utf-8')
        perf_handler.setFormatter(simple_formatter)
        self.perf_logger.addHandler(perf_handler)
        
        # Error log handler
        error_handler = RealTimeFileHandler(str(self.error_log), mode='w', encoding='utf-8')
        error_handler.setFormatter(detailed_formatter)
        self.error_logger.addHandler(error_handler)
    
    def debug(self, message: str, **kwargs):
        """Log debug message with optional context."""
        context = self._format_context(kwargs)
        self.logger.debug(f"{message}{context}")
    
    def info(self, message: str, **kwargs):
        """Log info message with optional context."""
        context = self._format_context(kwargs)
        self.logger.info(f"{message}{context}")
    
    def warning(self, message: str, **kwargs):
        """Log warning message with optional context."""
        context = self._format_context(kwargs)
        self.logger.warning(f"{message}{context}")
    
    def error(self, message: str, **kwargs):
        """Log error message with optional context."""
        context = self._format_context(kwargs)
        self.logger.error(f"{message}{context}")
        self.error_logger.error(f"{message}{context}")
    
    def critical(self, message: str, **kwargs):
        """Log critical message with optional context."""
        context = self._format_context(kwargs)
        self.logger.critical(f"{message}{context}")
        self.error_logger.critical(f"{message}{context}")
    
    def exception(self, message: str, **kwargs):
        """Log exception with full traceback."""
        context = self._format_context(kwargs)
        exc_info = traceback.format_exc()
        full_message = f"{message}{context}\nTraceback:\n{exc_info}"
        self.logger.error(full_message)
        self.error_logger.error(full_message)
    
    def performance(self, message: str, duration: Optional[float] = None, **kwargs):
        """Log performance metric."""
        context = self._format_context(kwargs)
        if duration is not None:
            message = f"{message} (זמן: {duration:.3f}s)"
        self.perf_logger.info(f"{message}{context}")
    
    def start_operation(self, operation_name: str, **kwargs):
        """Start timing an operation."""
        self.start_times[operation_name] = time.time()
        context = self._format_context(kwargs)
        self.info(f"התחלת פעולה: {operation_name}{context}")
    
    def end_operation(self, operation_name: str, **kwargs):
        """End timing an operation and log the duration."""
        if operation_name in self.start_times:
            duration = time.time() - self.start_times[operation_name]
            self.operation_times[operation_name] = duration
            del self.start_times[operation_name]
            
            context = self._format_context(kwargs)
            self.info(f"סיום פעולה: {operation_name} (זמן: {duration:.3f}s){context}")
            self.performance(f"פעולה הושלמה: {operation_name}", duration, **kwargs)
        else:
            self.warning(f"ניסיון לסיים פעולה שלא התחילה: {operation_name}")
    
    def log_file_operation(self, operation: str, file_path: str, success: bool = True, **kwargs):
        """Log file operations with details."""
        status = "הצליח" if success else "נכשל"
        file_info = ""
        
        if success and os.path.exists(file_path):
            try:
                size = os.path.getsize(file_path)
                file_info = f" (גודל: {size:,} bytes)"
            except:
                pass
        
        context = self._format_context(kwargs)
        message = f"פעולת קובץ: {operation} | {file_path} | סטטוס: {status}{file_info}{context}"
        
        if success:
            self.info(message)
        else:
            self.error(message)
    
    def log_audio_operation(self, operation: str, details: Dict[str, Any]):
        """Log audio-related operations with technical details."""
        formatted_details = []
        for key, value in details.items():
            if isinstance(value, float):
                formatted_details.append(f"{key}: {value:.3f}")
            else:
                formatted_details.append(f"{key}: {value}")
        
        details_str = " | ".join(formatted_details)
        self.info(f"פעולת אודיו: {operation} | {details_str}")
    
    def log_ui_operation(self, operation: str, component: str, **kwargs):
        """Log UI operations and user interactions."""
        context = self._format_context(kwargs)
        self.debug(f"פעולת ממשק: {operation} | רכיב: {component}{context}")
    
    def log_system_info(self):
        """Log detailed system information."""
        self.info("=== מידע מערכת ===")
        
        try:
            import platform
            self.info(f"מערכת הפעלה: {platform.system()} {platform.release()}")
            self.info(f"ארכיטקטורה: {platform.machine()}")
            self.info(f"מעבד: {platform.processor()}")
        except:
            self.info("לא ניתן לקבל מידע מערכת מפורט")
        
        # Memory info (if available)
        try:
            import psutil
            memory = psutil.virtual_memory()
            self.info(f"זיכרון כולל: {memory.total // 1024 // 1024:,} MB")
            self.info(f"זיכרון פנוי: {memory.available // 1024 // 1024:,} MB")
        except ImportError:
            self.info("מידע זיכרון לא זמין (psutil לא מותקן)")
        except:
            self.info("לא ניתן לקבל מידע זיכרון")
    
    def log_dependencies(self):
        """Log information about key dependencies."""
        self.info("=== בדיקת תלויות ===")
        
        dependencies = [
            'PySide6', 'numpy', 'scipy', 'librosa', 'soundfile', 
            'audioread', 'numba', 'scikit-learn'
        ]
        
        for dep in dependencies:
            try:
                module = __import__(dep)
                version = getattr(module, '__version__', 'גרסה לא ידועה')
                self.info(f"✓ {dep}: {version}")
            except ImportError:
                self.warning(f"✗ {dep}: לא מותקן")
            except Exception as e:
                self.warning(f"? {dep}: שגיאה בבדיקה - {e}")
    
    def _format_context(self, kwargs: Dict[str, Any]) -> str:
        """Format context information for logging."""
        if not kwargs:
            return ""
        
        formatted = []
        for key, value in kwargs.items():
            if isinstance(value, float):
                formatted.append(f"{key}={value:.3f}")
            elif isinstance(value, str) and len(value) > 50:
                formatted.append(f"{key}={value[:47]}...")
            else:
                formatted.append(f"{key}={value}")
        
        return f" | {' | '.join(formatted)}"
    
    def get_performance_summary(self) -> str:
        """Get a summary of all timed operations."""
        if not self.operation_times:
            return "אין נתוני ביצועים זמינים"
        
        summary = ["=== סיכום ביצועים ==="]
        total_time = sum(self.operation_times.values())
        
        for operation, duration in sorted(self.operation_times.items(), key=lambda x: x[1], reverse=True):
            percentage = (duration / total_time) * 100 if total_time > 0 else 0
            summary.append(f"{operation}: {duration:.3f}s ({percentage:.1f}%)")
        
        summary.append(f"זמן כולל: {total_time:.3f}s")
        return "\n".join(summary)
    
    def finalize(self):
        """Finalize logging and write performance summary."""
        self.info("=== סיום תוכנה ===")
        
        # Write performance summary
        perf_summary = self.get_performance_summary()
        self.performance(perf_summary)
        
        # Close all handlers
        for logger in [self.logger, self.perf_logger, self.error_logger]:
            for handler in logger.handlers:
                handler.close()

# Global logger instance
_logger_instance: Optional[PerformanceLogger] = None

def get_logger() -> PerformanceLogger:
    """Get the global logger instance."""
    global _logger_instance
    if _logger_instance is None:
        _logger_instance = PerformanceLogger()
    return _logger_instance

def setup_logging(log_dir: str = ".") -> PerformanceLogger:
    """Setup and return the global logger."""
    global _logger_instance
    _logger_instance = PerformanceLogger(log_dir)
    return _logger_instance