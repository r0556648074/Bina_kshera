"""
User State Management - ניהול מצב משתמש ו-bookmarks

מנהל:
- Bookmarks לקבצי אודיו עם זמנים וטקסט
- העדפות משתמש
- היסטוריית ניגון
- אחסון בקובץ JSON מקומי
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging

class UserStateManager:
    """מנהל מצב משתמש מקומי."""
    
    def __init__(self, data_dir: str = None):
        """
        יוצר מנהל מצב חדש.
        
        Args:
            data_dir: תיקיית נתונים. אם None, ישתמש בתיקייה ברירת מחדל.
        """
        if data_dir is None:
            # תיקייה בבית המשתמש
            home_dir = Path.home()
            data_dir = home_dir / ".bina_player_data"
        
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(exist_ok=True)
        
        # קבצי נתונים
        self.bookmarks_file = self.data_dir / "bookmarks.json"
        self.preferences_file = self.data_dir / "preferences.json"
        self.history_file = self.data_dir / "playback_history.json"
        
        # נתונים בזיכרון
        self.bookmarks = self._load_bookmarks()
        self.preferences = self._load_preferences()
        self.history = self._load_history()
        
        logging.info(f"UserStateManager אותחל בתיקייה: {self.data_dir}")
    
    def _load_bookmarks(self) -> Dict[str, List[Dict[str, Any]]]:
        """טוען bookmarks מקובץ."""
        try:
            if self.bookmarks_file.exists():
                with open(self.bookmarks_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logging.warning(f"שגיאה בטעינת bookmarks: {e}")
        
        return {}
    
    def _load_preferences(self) -> Dict[str, Any]:
        """טוען העדפות משתמש."""
        default_preferences = {
            "volume": 70,
            "playback_speed": 1.0,
            "auto_scroll_transcript": True,
            "show_waveform": True,
            "theme": "light",
            "language": "he",
            "recent_files_limit": 10
        }
        
        try:
            if self.preferences_file.exists():
                with open(self.preferences_file, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    # מיזוג עם ברירות מחדל
                    default_preferences.update(loaded)
        except Exception as e:
            logging.warning(f"שגיאה בטעינת העדפות: {e}")
        
        return default_preferences
    
    def _load_history(self) -> List[Dict[str, Any]]:
        """טוען היסטוריית ניגון."""
        try:
            if self.history_file.exists():
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            logging.warning(f"שגיאה בטעינת היסטוריה: {e}")
        
        return []
    
    def _save_bookmarks(self):
        """שומר bookmarks לקובץ."""
        try:
            with open(self.bookmarks_file, 'w', encoding='utf-8') as f:
                json.dump(self.bookmarks, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"שגיאה בשמירת bookmarks: {e}")
    
    def _save_preferences(self):
        """שומר העדפות לקובץ."""
        try:
            with open(self.preferences_file, 'w', encoding='utf-8') as f:
                json.dump(self.preferences, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"שגיאה בשמירת העדפות: {e}")
    
    def _save_history(self):
        """שומר היסטוריה לקובץ."""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(self.history, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logging.error(f"שגיאה בשמירת היסטוריה: {e}")
    
    # Bookmark Management
    def save_bookmark(self, file_path: str, time: float, note: str = "") -> str:
        """
        שומר bookmark חדש.
        
        Args:
            file_path: נתיב לקובץ
            time: זמן בשניות
            note: הערה אופציונלית
            
        Returns:
            מזהה הbookmark
        """
        bookmark_id = f"{int(datetime.now().timestamp())}_{len(self.bookmarks.get(file_path, []))}"
        
        bookmark = {
            "id": bookmark_id,
            "time": time,
            "note": note,
            "created_at": datetime.now().isoformat(),
            "file_name": os.path.basename(file_path)
        }
        
        if file_path not in self.bookmarks:
            self.bookmarks[file_path] = []
        
        self.bookmarks[file_path].append(bookmark)
        
        # מיון לפי זמן
        self.bookmarks[file_path].sort(key=lambda x: x["time"])
        
        self._save_bookmarks()
        logging.info(f"נשמר bookmark: {file_path} @ {time:.1f}s")
        
        return bookmark_id
    
    def get_bookmarks(self, file_path: str) -> List[Dict[str, Any]]:
        """מחזיר bookmarks לקובץ ספציפי."""
        return self.bookmarks.get(file_path, [])
    
    def get_all_bookmarks(self) -> Dict[str, List[Dict[str, Any]]]:
        """מחזיר את כל הbookmarks."""
        return self.bookmarks.copy()
    
    def delete_bookmark(self, file_path: str, bookmark_id: str) -> bool:
        """מוחק bookmark."""
        if file_path in self.bookmarks:
            original_count = len(self.bookmarks[file_path])
            self.bookmarks[file_path] = [
                b for b in self.bookmarks[file_path] 
                if b["id"] != bookmark_id
            ]
            
            if len(self.bookmarks[file_path]) < original_count:
                self._save_bookmarks()
                logging.info(f"נמחק bookmark: {bookmark_id}")
                return True
        
        return False
    
    def update_bookmark(self, file_path: str, bookmark_id: str, note: str = None, time: float = None) -> bool:
        """מעדכן bookmark קיים."""
        if file_path in self.bookmarks:
            for bookmark in self.bookmarks[file_path]:
                if bookmark["id"] == bookmark_id:
                    if note is not None:
                        bookmark["note"] = note
                    if time is not None:
                        bookmark["time"] = time
                    
                    bookmark["updated_at"] = datetime.now().isoformat()
                    
                    # מיון מחדש אם השתנה הזמן
                    if time is not None:
                        self.bookmarks[file_path].sort(key=lambda x: x["time"])
                    
                    self._save_bookmarks()
                    logging.info(f"עודכן bookmark: {bookmark_id}")
                    return True
        
        return False
    
    # Preferences Management
    def get_preference(self, key: str, default=None):
        """מחזיר העדפה ספציפית."""
        return self.preferences.get(key, default)
    
    def set_preference(self, key: str, value: Any):
        """מגדיר העדפה."""
        self.preferences[key] = value
        self._save_preferences()
        logging.info(f"הועדפה עודכנה: {key} = {value}")
    
    def get_all_preferences(self) -> Dict[str, Any]:
        """מחזיר את כל ההעדפות."""
        return self.preferences.copy()
    
    def reset_preferences(self):
        """מאפס העדפות לברירת מחדל."""
        self.preferences = self._load_preferences()
        self._save_preferences()
        logging.info("העדפות אופסו")
    
    # Playback History
    def add_to_history(self, file_path: str, position: float = 0.0, duration: float = None):
        """מוסיף קובץ להיסטוריה."""
        # הסרת רשומות קודמות של אותו קובץ
        self.history = [h for h in self.history if h["file_path"] != file_path]
        
        # הוספת רשומה חדשה
        history_entry = {
            "file_path": file_path,
            "file_name": os.path.basename(file_path),
            "last_position": position,
            "duration": duration,
            "last_played": datetime.now().isoformat()
        }
        
        self.history.insert(0, history_entry)
        
        # שמירת מגבלה על גודל היסטוריה
        limit = self.get_preference("recent_files_limit", 10)
        self.history = self.history[:limit]
        
        self._save_history()
        logging.info(f"נוסף להיסטוריה: {file_path}")
    
    def get_recent_files(self, limit: int = None) -> List[Dict[str, Any]]:
        """מחזיר קבצים אחרונים."""
        if limit is None:
            limit = self.get_preference("recent_files_limit", 10)
        
        return self.history[:limit]
    
    def get_last_position(self, file_path: str) -> float:
        """מחזיר מיקום אחרון בקובץ."""
        for entry in self.history:
            if entry["file_path"] == file_path:
                return entry.get("last_position", 0.0)
        return 0.0
    
    def clear_history(self):
        """מנקה היסטוריה."""
        self.history = []
        self._save_history()
        logging.info("היסטוריה נוקתה")
    
    # Utility Methods
    def export_data(self, export_path: str):
        """מייצא את כל הנתונים לקובץ."""
        export_data = {
            "bookmarks": self.bookmarks,
            "preferences": self.preferences,
            "history": self.history,
            "exported_at": datetime.now().isoformat()
        }
        
        try:
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            
            logging.info(f"נתונים יוצאו ל: {export_path}")
            return True
            
        except Exception as e:
            logging.error(f"שגיאה בייצוא נתונים: {e}")
            return False
    
    def import_data(self, import_path: str, merge: bool = True):
        """מייבא נתונים מקובץ."""
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                imported_data = json.load(f)
            
            if merge:
                # מיזוג עם נתונים קיימים
                if "bookmarks" in imported_data:
                    for file_path, bookmarks in imported_data["bookmarks"].items():
                        if file_path not in self.bookmarks:
                            self.bookmarks[file_path] = []
                        self.bookmarks[file_path].extend(bookmarks)
                
                if "preferences" in imported_data:
                    self.preferences.update(imported_data["preferences"])
                
                if "history" in imported_data:
                    # מיזוג היסטוריה ללא כפילויות
                    existing_paths = {h["file_path"] for h in self.history}
                    for entry in imported_data["history"]:
                        if entry["file_path"] not in existing_paths:
                            self.history.append(entry)
            else:
                # החלפה מלאה
                self.bookmarks = imported_data.get("bookmarks", {})
                self.preferences = imported_data.get("preferences", {})
                self.history = imported_data.get("history", [])
            
            # שמירה
            self._save_bookmarks()
            self._save_preferences()
            self._save_history()
            
            logging.info(f"נתונים יובאו מ: {import_path}")
            return True
            
        except Exception as e:
            logging.error(f"שגיאה בייבוא נתונים: {e}")
            return False
    
    def get_statistics(self) -> Dict[str, Any]:
        """מחזיר סטטיסטיקות שימוש."""
        total_bookmarks = sum(len(bookmarks) for bookmarks in self.bookmarks.values())
        files_with_bookmarks = len(self.bookmarks)
        recent_files = len(self.history)
        
        # חישוב זמן ניגון כולל
        total_listening_time = 0.0
        for entry in self.history:
            if entry.get("duration"):
                total_listening_time += entry["duration"]
        
        return {
            "total_bookmarks": total_bookmarks,
            "files_with_bookmarks": files_with_bookmarks,
            "recent_files": recent_files,
            "total_listening_time": total_listening_time,
            "data_directory": str(self.data_dir)
        }

# Global instance
_user_state_manager: Optional[UserStateManager] = None

def get_user_state_manager() -> UserStateManager:
    """מחזיר instance גלובלי של מנהל המצב."""
    global _user_state_manager
    if _user_state_manager is None:
        _user_state_manager = UserStateManager()
    return _user_state_manager

# פונקציות עזר לתאימות לבקשה המקורית
def save_bookmark(file_path: str, time: float, note: str = "") -> str:
    """שומר bookmark - פונקציה עזר."""
    manager = get_user_state_manager()
    return manager.save_bookmark(file_path, time, note)

def get_bookmarks(file_path: str) -> List[Dict[str, Any]]:
    """מחזיר bookmarks - פונקציה עזר."""
    manager = get_user_state_manager()
    return manager.get_bookmarks(file_path)

if __name__ == "__main__":
    # בדיקה בסיסית
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    # יצירת מנהל מצב
    manager = UserStateManager("test_user_data")
    
    # בדיקת bookmarks
    test_file = "test_audio.mp3"
    bookmark_id = manager.save_bookmark(test_file, 45.5, "רגע מעניין")
    print(f"נוצר bookmark: {bookmark_id}")
    
    bookmarks = manager.get_bookmarks(test_file)
    print(f"Bookmarks לקובץ: {bookmarks}")
    
    # בדיקת העדפות
    manager.set_preference("volume", 80)
    volume = manager.get_preference("volume")
    print(f"עוצמת קול: {volume}")
    
    # בדיקת היסטוריה
    manager.add_to_history(test_file, 30.0, 120.0)
    recent = manager.get_recent_files()
    print(f"קבצים אחרונים: {recent}")
    
    # סטטיסטיקות
    stats = manager.get_statistics()
    print(f"סטטיסטיקות: {stats}")