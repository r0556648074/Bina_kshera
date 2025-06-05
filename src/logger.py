"""
Advanced Logging System - מערכת לוגים מתקדמת

מערכת לוגים מקיפה לנגן בינה כשרה:
- רישום כל פעולות המשתמש
- מעקב ביצועים
- שמירה בקבצים עם רוטציה
- פורמט מובנה וקריא
"""

import logging
import os
import json
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, List
import threading
from logging.handlers import RotatingFileHandler

class BinaPlayerLogger:
    """מערכת לוגים מתקדמת לנגן בינה כשרה."""
    
    def __init__(self, log_dir: str = "logs"):
        """
        יוצר מערכת לוגים חדשה.
        
        Args:
            log_dir: תיקיית לוגים
        """
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # קבצי לוגים
        self.main_log_file = self.log_dir / "bina.log"
        self.events_log_file = self.log_dir / "events.log"
        self.performance_log_file = self.log_dir / "performance.log"
        self.errors_log_file = self.log_dir / "errors.log"
        
        # מונים ומעקב
        self.session_start = datetime.now()
        self.session_id = f"session_{int(time.time())}"
        self.event_counter = 0
        self.performance_metrics = {}
        self.lock = threading.Lock()
        
        self._setup_loggers()
        self._log_session_start()
        
        print(f"מערכת לוגים אותחלה: {self.log_dir}")
    
    def _setup_loggers(self):
        """מגדיר את כל הלוגרים."""
        # פורמט כללי
        formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # לוגר ראשי
        self.main_logger = logging.getLogger('bina_main')
        self.main_logger.setLevel(logging.INFO)
        
        main_handler = RotatingFileHandler(
            self.main_log_file, 
            maxBytes=5*1024*1024,  # 5MB
            backupCount=5,
            encoding='utf-8'
        )
        main_handler.setFormatter(formatter)
        self.main_logger.addHandler(main_handler)
        
        # לוגר אירועים
        self.events_logger = logging.getLogger('bina_events')
        self.events_logger.setLevel(logging.INFO)
        
        events_handler = RotatingFileHandler(
            self.events_log_file,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=10,
            encoding='utf-8'
        )
        events_handler.setFormatter(logging.Formatter(
            '[%(asctime)s] EVENT: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        self.events_logger.addHandler(events_handler)
        
        # לוגר ביצועים
        self.performance_logger = logging.getLogger('bina_performance')
        self.performance_logger.setLevel(logging.INFO)
        
        perf_handler = RotatingFileHandler(
            self.performance_log_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=5,
            encoding='utf-8'
        )
        perf_handler.setFormatter(logging.Formatter(
            '[%(asctime)s] PERF: %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        self.performance_logger.addHandler(perf_handler)
        
        # לוגר שגיאות
        self.error_logger = logging.getLogger('bina_errors')
        self.error_logger.setLevel(logging.ERROR)
        
        error_handler = RotatingFileHandler(
            self.errors_log_file,
            maxBytes=5*1024*1024,  # 5MB
            backupCount=10,
            encoding='utf-8'
        )
        error_handler.setFormatter(logging.Formatter(
            '[%(asctime)s] ERROR: %(message)s\n%(pathname)s:%(lineno)d\n%(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        self.error_logger.addHandler(error_handler)
    
    def _log_session_start(self):
        """רושם תחילת סשן."""
        self.main_logger.info(f"=== תחילת סשן חדש ===")
        self.main_logger.info(f"Session ID: {self.session_id}")
        self.main_logger.info(f"זמן התחלה: {self.session_start}")
        
        # מידע מערכת
        import platform
        import sys
        
        self.main_logger.info(f"מערכת הפעלה: {platform.system()} {platform.release()}")
        self.main_logger.info(f"Python: {sys.version}")
        self.main_logger.info(f"ארכיטקטורה: {platform.machine()}")
    
    def log_event(self, event_name: str, details: Dict[str, Any] = None):
        """
        רושם אירוע משתמש.
        
        Args:
            event_name: שם האירוע
            details: פרטים נוספים
        """
        with self.lock:
            self.event_counter += 1
            
            if details is None:
                details = {}
            
            # הוספת מידע בסיסי
            event_data = {
                "session_id": self.session_id,
                "event_id": self.event_counter,
                "event_name": event_name,
                "timestamp": datetime.now().isoformat(),
                **details
            }
            
            # פורמט מובנה לקובץ
            log_message = f"{event_name} - {json.dumps(details, ensure_ascii=False)}"
            self.events_logger.info(log_message)
            
            # לוג גם בלוגר הראשי
            self.main_logger.info(f"אירוע: {event_name}")
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] {event_name}: {details}")
    
    def log_performance(self, operation: str, duration: float, details: Dict[str, Any] = None):
        """
        רושם מדד ביצועים.
        
        Args:
            operation: שם הפעולה
            duration: משך זמן בשניות
            details: פרטים נוספים
        """
        with self.lock:
            if details is None:
                details = {}
            
            # עדכון מטריקות
            if operation not in self.performance_metrics:
                self.performance_metrics[operation] = {
                    "count": 0,
                    "total_time": 0.0,
                    "min_time": float('inf'),
                    "max_time": 0.0
                }
            
            metrics = self.performance_metrics[operation]
            metrics["count"] += 1
            metrics["total_time"] += duration
            metrics["min_time"] = min(metrics["min_time"], duration)
            metrics["max_time"] = max(metrics["max_time"], duration)
            
            # חישוב ממוצע
            avg_time = metrics["total_time"] / metrics["count"]
            
            # רישום
            perf_data = {
                "operation": operation,
                "duration": round(duration, 3),
                "avg_duration": round(avg_time, 3),
                "count": metrics["count"],
                **details
            }
            
            log_message = f"{operation} - {json.dumps(perf_data, ensure_ascii=False)}"
            self.performance_logger.info(log_message)
            
            self.main_logger.debug(f"ביצועים: {operation} - {duration:.3f}s")
    
    def log_error(self, error_type: str, error_message: str, details: Dict[str, Any] = None, exception: Exception = None):
        """
        רושם שגיאה.
        
        Args:
            error_type: סוג השגיאה
            error_message: הודעת שגיאה
            details: פרטים נוספים
            exception: חריג אם יש
        """
        with self.lock:
            if details is None:
                details = {}
            
            error_data = {
                "session_id": self.session_id,
                "error_type": error_type,
                "error_message": error_message,
                "timestamp": datetime.now().isoformat(),
                **details
            }
            
            if exception:
                import traceback
                error_data["traceback"] = traceback.format_exc()
            
            log_message = f"{error_type}: {error_message} - {json.dumps(details, ensure_ascii=False)}"
            self.error_logger.error(log_message)
            
            self.main_logger.error(f"שגיאה: {error_type} - {error_message}")
            
            print(f"[שגיאה] {error_type}: {error_message}")
    
    def get_session_summary(self) -> Dict[str, Any]:
        """מחזיר סיכום הסשן הנוכחי."""
        session_duration = datetime.now() - self.session_start
        
        return {
            "session_id": self.session_id,
            "start_time": self.session_start.isoformat(),
            "duration": str(session_duration),
            "total_events": self.event_counter,
            "performance_metrics": self.performance_metrics.copy()
        }
    
    def export_session_data(self, export_path: str = None) -> str:
        """מייצא נתוני סשן לקובץ JSON."""
        if export_path is None:
            export_path = self.log_dir / f"session_export_{self.session_id}.json"
        
        summary = self.get_session_summary()
        
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(summary, f, ensure_ascii=False, indent=2)
            
            self.main_logger.info(f"נתוני סשן יוצאו ל: {export_path}")
            return str(export_path)
            
        except Exception as e:
            self.log_error("export_error", f"שגיאה בייצוא נתוני סשן: {e}")
            return ""
    
    def cleanup_old_logs(self, days_to_keep: int = 30):
        """מנקה לוגים ישנים."""
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        cleaned_count = 0
        
        for log_file in self.log_dir.glob("*.log*"):
            try:
                file_time = datetime.fromtimestamp(log_file.stat().st_mtime)
                if file_time < cutoff_date:
                    log_file.unlink()
                    cleaned_count += 1
            except Exception as e:
                self.log_error("cleanup_error", f"שגיאה במחיקת לוג {log_file}: {e}")
        
        if cleaned_count > 0:
            self.main_logger.info(f"נוקו {cleaned_count} קבצי לוג ישנים")
        
        return cleaned_count
    
    def finalize_session(self):
        """מסיים את הסשן ושומר סיכום."""
        session_duration = datetime.now() - self.session_start
        
        self.main_logger.info(f"=== סיום סשן ===")
        self.main_logger.info(f"משך זמן: {session_duration}")
        self.main_logger.info(f"סך אירועים: {self.event_counter}")
        
        # שמירת סיכום ביצועים
        if self.performance_metrics:
            self.main_logger.info("=== סיכום ביצועים ===")
            for operation, metrics in self.performance_metrics.items():
                avg_time = metrics["total_time"] / metrics["count"]
                self.main_logger.info(
                    f"{operation}: {metrics['count']} פעמים, "
                    f"ממוצע {avg_time:.3f}s, "
                    f"טווח {metrics['min_time']:.3f}-{metrics['max_time']:.3f}s"
                )
        
        # ייצוא נתוני סשן
        self.export_session_data()

# Performance timing decorator
class PerformanceTimer:
    """Context manager למדידת ביצועים."""
    
    def __init__(self, logger: BinaPlayerLogger, operation: str, details: Dict[str, Any] = None):
        self.logger = logger
        self.operation = operation
        self.details = details or {}
        self.start_time = None
    
    def __enter__(self):
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        duration = time.time() - self.start_time
        self.logger.log_performance(self.operation, duration, self.details)

# Global logger instance
_bina_logger: Optional[BinaPlayerLogger] = None

def get_bina_logger() -> BinaPlayerLogger:
    """מחזיר instance גלובלי של הלוגר."""
    global _bina_logger
    if _bina_logger is None:
        _bina_logger = BinaPlayerLogger()
    return _bina_logger

# פונקציות עזר לתאימות לבקשה המקורית
def log_event(event_name: str, details: Dict[str, Any] = None):
    """רושם אירוע - פונקציה עזר."""
    logger = get_bina_logger()
    logger.log_event(event_name, details)

def log_performance(operation: str, duration: float, details: Dict[str, Any] = None):
    """רושם ביצועים - פונקציה עזר."""
    logger = get_bina_logger()
    logger.log_performance(operation, duration, details)

def log_error(error_type: str, error_message: str, details: Dict[str, Any] = None):
    """רושם שגיאה - פונקציה עזר."""
    logger = get_bina_logger()
    logger.log_error(error_type, error_message, details)

# Audio player specific event loggers
def log_play_pressed(file_path: str, position: float):
    """רושם לחיצה על נגן."""
    log_event("play_pressed", {
        "file": os.path.basename(file_path),
        "position": round(position, 2)
    })

def log_file_loaded(file_path: str, file_type: str, load_time: float):
    """רושם טעינת קובץ."""
    file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
    
    log_event("file_loaded", {
        "file": os.path.basename(file_path),
        "file_type": file_type,
        "file_size": file_size,
        "load_time": round(load_time, 3)
    })

def log_search_performed(query: str, results_count: int, search_time: float):
    """רושם חיפוש."""
    log_event("search_performed", {
        "query": query,
        "results_count": results_count,
        "search_time": round(search_time, 3)
    })

def log_bookmark_created(file_path: str, position: float, note: str):
    """רושם יצירת bookmark."""
    log_event("bookmark_created", {
        "file": os.path.basename(file_path),
        "position": round(position, 2),
        "has_note": bool(note.strip())
    })

def log_volume_changed(new_volume: int, old_volume: int):
    """רושם שינוי עוצמה."""
    log_event("volume_changed", {
        "new_volume": new_volume,
        "old_volume": old_volume,
        "change": new_volume - old_volume
    })

def log_seek_performed(from_position: float, to_position: float):
    """רושם קפיצה בזמן."""
    log_event("seek_performed", {
        "from_position": round(from_position, 2),
        "to_position": round(to_position, 2),
        "jump_distance": round(abs(to_position - from_position), 2)
    })

if __name__ == "__main__":
    # בדיקה בסיסית
    print("בדיקת מערכת לוגים...")
    
    # יצירת לוגר
    logger = BinaPlayerLogger("test_logs")
    
    # בדיקת אירועים
    logger.log_event("app_started", {"version": "1.0.0"})
    
    # בדיקת ביצועים
    with PerformanceTimer(logger, "test_operation", {"test": True}):
        time.sleep(0.1)
    
    # בדיקת שגיאה
    logger.log_error("test_error", "זוהי שגיאת בדיקה", {"component": "test"})
    
    # בדיקת פונקציות עזר
    log_play_pressed("test_file.mp3", 45.5)
    log_volume_changed(80, 70)
    
    # סיכום
    summary = logger.get_session_summary()
    print(f"סיכום סשן: {summary}")
    
    # סיום
    logger.finalize_session()
    print("בדיקת לוגים הושלמה")