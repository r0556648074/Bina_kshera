"""
מערכת בדיקת תקינות ומעקב קבצים זמניים עבור נגן בינה כשרה.

מטפלת בניהול קבצים זמניים, בדיקת תקינות מדיה וניקוי אוטומטי.
"""

import os
import sys
import time
import atexit
import tempfile
import threading
from pathlib import Path
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from utils.logger import detailed_logger
except ImportError:
    detailed_logger = None

@dataclass
class FileTracker:
    """מעקב אחר קובץ זמני."""
    path: str
    created_time: float
    size: int
    purpose: str  # "audio", "transcript", "cache"
    locked: bool = False
    attempts: int = 0

class TempFileManager:
    """מנהל קבצים זמניים מתקדם עם fallback mechanisms."""
    
    def __init__(self):
        self.tracked_files: Dict[str, FileTracker] = {}
        self.cleanup_thread: Optional[threading.Thread] = None
        self.cleanup_event = threading.Event()
        self.lock = threading.Lock()
        
        # Register cleanup on exit
        atexit.register(self.cleanup_all)
        
        if detailed_logger:
            detailed_logger.info("מנהל קבצים זמניים אותחל")
    
    def create_temp_file(self, data: bytes, extension: str = "tmp", purpose: str = "unknown") -> str:
        """יוצר קובץ זמני עם fallback למיקומים שונים."""
        if not data:
            raise ValueError("לא ניתן ליצור קובץ זמני ריק")
        
        # רשימת מיקומים לנסות בסדר יורד של עדיפות
        temp_locations = self._get_temp_locations()
        
        for location in temp_locations:
            try:
                if not os.path.exists(location):
                    continue
                
                # ניסיון יצירת קובץ זמני
                temp_file = tempfile.NamedTemporaryFile(
                    suffix=f'.{extension}',
                    delete=False,
                    dir=location
                )
                
                temp_file.write(data)
                temp_file.close()
                
                # בדיקת תקינות הכתיבה
                if not os.path.exists(temp_file.name):
                    raise RuntimeError("קובץ לא נוצר")
                
                actual_size = os.path.getsize(temp_file.name)
                if actual_size != len(data):
                    os.unlink(temp_file.name)
                    raise RuntimeError(f"כתיבה לא שלמה: {actual_size}/{len(data)}")
                
                # מעקב אחר הקובץ
                with self.lock:
                    self.tracked_files[temp_file.name] = FileTracker(
                        path=temp_file.name,
                        created_time=time.time(),
                        size=actual_size,
                        purpose=purpose
                    )
                
                if detailed_logger:
                    detailed_logger.log_file_operation(
                        f"נוצר קובץ זמני ({purpose})", 
                        temp_file.name, 
                        True, 
                        size=actual_size
                    )
                
                return temp_file.name
                
            except Exception as e:
                if detailed_logger:
                    detailed_logger.debug(f"כשל ביצירת קובץ זמני ב-{location}: {e}")
                continue
        
        raise RuntimeError("לא ניתן ליצור קובץ זמני באף מיקום")
    
    def _get_temp_locations(self) -> List[str]:
        """מחזיר רשימת מיקומים זמניים בסדר עדיפות."""
        locations = []
        
        # מיקום זמני ברירת המחדל
        try:
            default_temp = tempfile.gettempdir()
            if os.access(default_temp, os.W_OK):
                locations.append(default_temp)
        except:
            pass
        
        # תיקיית המשתמש
        try:
            user_temp = os.path.expanduser("~/tmp")
            if user_temp != "~/tmp" and os.access(os.path.dirname(user_temp), os.W_OK):
                os.makedirs(user_temp, exist_ok=True)
                locations.append(user_temp)
        except:
            pass
        
        # תיקיית הפרויקט
        try:
            project_temp = os.path.join(".", "temp")
            os.makedirs(project_temp, exist_ok=True)
            if os.access(project_temp, os.W_OK):
                locations.append(project_temp)
        except:
            pass
        
        # מיקום נוכחי כפתרון אחרון
        if os.access(".", os.W_OK):
            locations.append(".")
        
        return locations
    
    def validate_file(self, file_path: str) -> bool:
        """בודק תקינות קובץ."""
        try:
            if not os.path.exists(file_path):
                return False
            
            stat = os.stat(file_path)
            if stat.st_size == 0:
                return False
            
            # בדיקת הרשאות קריאה
            if not os.access(file_path, os.R_OK):
                return False
            
            # בדיקה שהקובץ לא נעול
            try:
                with open(file_path, 'rb') as f:
                    f.read(1)
            except (IOError, OSError):
                return False
            
            return True
            
        except Exception:
            return False
    
    def mark_file_locked(self, file_path: str):
        """מסמן קובץ כנעול (בשימוש)."""
        with self.lock:
            if file_path in self.tracked_files:
                self.tracked_files[file_path].locked = True
    
    def mark_file_unlocked(self, file_path: str):
        """מסמן קובץ כפנוי למחיקה."""
        with self.lock:
            if file_path in self.tracked_files:
                self.tracked_files[file_path].locked = False
    
    def cleanup_file(self, file_path: str) -> bool:
        """מנקה קובץ ספציפי."""
        try:
            with self.lock:
                tracker = self.tracked_files.get(file_path)
                if tracker and tracker.locked:
                    if detailed_logger:
                        detailed_logger.debug(f"קובץ נעול, דחיית ניקוי: {file_path}")
                    return False
            
            if os.path.exists(file_path):
                # השהיה קצרה לוודא שהקובץ לא בשימוש
                time.sleep(0.1)
                os.unlink(file_path)
                
                with self.lock:
                    if file_path in self.tracked_files:
                        del self.tracked_files[file_path]
                
                if detailed_logger:
                    detailed_logger.log_file_operation("נוקה קובץ זמני", file_path, True)
                
                return True
            
        except PermissionError:
            # קובץ נעול, נסה שוב מאוחר יותר
            with self.lock:
                if file_path in self.tracked_files:
                    self.tracked_files[file_path].attempts += 1
            
            if detailed_logger:
                detailed_logger.debug(f"קובץ נעול, ניקוי מתוזמן: {file_path}")
            
        except Exception as e:
            if detailed_logger:
                detailed_logger.warning(f"שגיאה בניקוי קובץ {file_path}: {e}")
        
        return False
    
    def cleanup_old_files(self, max_age_seconds: int = 3600):
        """מנקה קבצים ישנים."""
        current_time = time.time()
        files_to_cleanup = []
        
        with self.lock:
            for file_path, tracker in self.tracked_files.items():
                if (not tracker.locked and 
                    current_time - tracker.created_time > max_age_seconds):
                    files_to_cleanup.append(file_path)
        
        cleaned = 0
        for file_path in files_to_cleanup:
            if self.cleanup_file(file_path):
                cleaned += 1
        
        if cleaned > 0 and detailed_logger:
            detailed_logger.info(f"נוקו {cleaned} קבצים ישנים")
    
    def cleanup_all(self):
        """מנקה את כל הקבצים הזמניים."""
        if detailed_logger:
            detailed_logger.info("מתחיל ניקוי כללי של קבצים זמניים")
        
        # עצירת thread הניקוי
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            self.cleanup_event.set()
            self.cleanup_thread.join(timeout=5)
        
        files_to_cleanup = []
        with self.lock:
            files_to_cleanup = list(self.tracked_files.keys())
        
        cleaned = 0
        for file_path in files_to_cleanup:
            # בניקוי כללי, מתעלמים ממצב נעול
            try:
                if os.path.exists(file_path):
                    time.sleep(0.05)  # השהיה קצרה
                    os.unlink(file_path)
                    cleaned += 1
            except Exception as e:
                if detailed_logger:
                    detailed_logger.debug(f"לא ניתן לנקות {file_path}: {e}")
        
        with self.lock:
            self.tracked_files.clear()
        
        if detailed_logger:
            detailed_logger.info(f"ניקוי כללי הושלם: {cleaned} קבצים")
    
    def start_background_cleanup(self, interval_seconds: int = 300):
        """מתחיל ניקוי ברקע."""
        if self.cleanup_thread and self.cleanup_thread.is_alive():
            return
        
        def cleanup_worker():
            while not self.cleanup_event.wait(interval_seconds):
                try:
                    self.cleanup_old_files()
                except Exception as e:
                    if detailed_logger:
                        detailed_logger.warning(f"שגיאה בניקוי ברקע: {e}")
        
        self.cleanup_thread = threading.Thread(target=cleanup_worker, daemon=True)
        self.cleanup_thread.start()
        
        if detailed_logger:
            detailed_logger.info("ניקוי ברקע התחיל")

class MediaIntegrityChecker:
    """בודק תקינות קבצי מדיה."""
    
    @staticmethod
    def validate_audio_file(file_path: str) -> Dict[str, any]:
        """בדיקת תקינות קובץ אודיו."""
        result = {
            "valid": False,
            "error": None,
            "duration": 0,
            "sample_rate": 0,
            "channels": 0,
            "format": None,
            "size": 0
        }
        
        try:
            if not os.path.exists(file_path):
                result["error"] = "קובץ לא קיים"
                return result
            
            # בדיקת גודל קובץ
            result["size"] = os.path.getsize(file_path)
            if result["size"] < 1000:  # מינימום סביר
                result["error"] = "קובץ קטן מדי"
                return result
            
            # ניסיון טעינה עם librosa
            try:
                import librosa
                import soundfile as sf
                
                # בדיקת מידע בסיסי
                info = sf.info(file_path)
                result["duration"] = info.duration
                result["sample_rate"] = info.samplerate
                result["channels"] = info.channels
                result["format"] = info.format
                
                # בדיקות תקינות
                if result["duration"] <= 0:
                    result["error"] = "משך זמן לא תקין"
                    return result
                
                if result["sample_rate"] <= 0:
                    result["error"] = "קצב דגימה לא תקין"
                    return result
                
                # ניסיון טעינת דגימה קטנה
                y, sr = librosa.load(file_path, duration=1.0, sr=None)
                if len(y) == 0:
                    result["error"] = "לא ניתן לטעון נתוני אודיו"
                    return result
                
                result["valid"] = True
                
            except Exception as e:
                result["error"] = f"שגיאה בטעינת אודיו: {e}"
                return result
        
        except Exception as e:
            result["error"] = f"שגיאה כללית: {e}"
        
        return result
    
    @staticmethod
    def validate_bc1_file(file_path: str) -> Dict[str, any]:
        """בדיקת תקינות קובץ BC1."""
        result = {
            "valid": False,
            "error": None,
            "audio_size": 0,
            "transcript_segments": 0,
            "metadata_present": False,
            "total_size": 0
        }
        
        try:
            if not os.path.exists(file_path):
                result["error"] = "קובץ BC1 לא קיים"
                return result
            
            result["total_size"] = os.path.getsize(file_path)
            if result["total_size"] < 1000:
                result["error"] = "קובץ BC1 קטן מדי"
                return result
            
            # ניסיון פתיחת BC1
            try:
                from formats.bc1_format import open_bc1
                
                bundle = open_bc1(file_path)
                
                # בדיקת רכיבים
                if not bundle.audio_file:
                    result["error"] = "לא נמצא אודיו ב-BC1"
                    return result
                
                if not os.path.exists(bundle.audio_file):
                    result["error"] = "קובץ אודיו זמני לא נוצר"
                    return result
                
                result["audio_size"] = os.path.getsize(bundle.audio_file)
                result["transcript_segments"] = len(bundle.segments or [])
                result["metadata_present"] = bool(bundle.metadata)
                
                # בדיקת תקינות אודיו
                audio_check = MediaIntegrityChecker.validate_audio_file(bundle.audio_file)
                if not audio_check["valid"]:
                    result["error"] = f"אודיו לא תקין: {audio_check['error']}"
                    bundle.cleanup()  # ניקוי
                    return result
                
                result["valid"] = True
                bundle.cleanup()  # ניקוי אחרי בדיקה
                
            except Exception as e:
                result["error"] = f"שגיאה בפענוח BC1: {e}"
                return result
        
        except Exception as e:
            result["error"] = f"שגיאה כללית: {e}"
        
        return result

# מופע גלובלי של מנהל הקבצים
_temp_manager = None

def get_temp_manager() -> TempFileManager:
    """מחזיר מופע יחיד של מנהל הקבצים הזמניים."""
    global _temp_manager
    if _temp_manager is None:
        _temp_manager = TempFileManager()
        _temp_manager.start_background_cleanup()
    return _temp_manager

def create_temp_audio_file(audio_data: bytes, extension: str = "mp3") -> str:
    """יוצר קובץ אודיו זמני עם ניהול מתקדם."""
    return get_temp_manager().create_temp_file(audio_data, extension, "audio")

def validate_media_file(file_path: str, file_type: str = "auto") -> Dict[str, any]:
    """בודק תקינות קובץ מדיה."""
    if file_type == "auto":
        if file_path.lower().endswith('.bc1'):
            file_type = "bc1"
        else:
            file_type = "audio"
    
    if file_type == "bc1":
        return MediaIntegrityChecker.validate_bc1_file(file_path)
    else:
        return MediaIntegrityChecker.validate_audio_file(file_path)