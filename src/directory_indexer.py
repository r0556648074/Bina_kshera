"""
Directory Indexer - אינדקס תיקיות עם חיפוש חוצה קבצים

יוצר מסד נתונים SQLite מקומי עם כל התמלילים מתיקייה.
מאפשר חיפוש מהיר על פני מספר קבצי MP7/BC1.
"""

import sqlite3
import os
import logging
from pathlib import Path
from typing import List, Dict, Any, Optional
import json
from datetime import datetime

from mp7_reader import load_mp7, is_mp7_file, cleanup_mp7_data

class DirectoryIndexer:
    """מאנדקס תיקיות ומאפשר חיפוש."""
    
    def __init__(self, db_path: str = None):
        """
        יוצר אינדקסר חדש.
        
        Args:
            db_path: נתיב למסד הנתונים. אם None, ייוצר בתיקייה הנוכחית.
        """
        if db_path is None:
            db_path = "audio_transcripts.db"
        
        self.db_path = db_path
        self._init_database()
        logging.info(f"אינדקסר הופעל עם מסד נתונים: {db_path}")
    
    def _init_database(self):
        """יוצר טבלאות במסד הנתונים."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # טבלת קבצים
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS files (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT UNIQUE NOT NULL,
                    file_name TEXT NOT NULL,
                    indexed_at TEXT NOT NULL,
                    file_size INTEGER,
                    duration REAL,
                    segment_count INTEGER
                )
            ''')
            
            # טבלת תמלילים
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS transcripts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_id INTEGER NOT NULL,
                    file_name TEXT NOT NULL,
                    start_time REAL NOT NULL,
                    end_time REAL NOT NULL,
                    text TEXT NOT NULL,
                    speaker TEXT,
                    confidence REAL,
                    FOREIGN KEY (file_id) REFERENCES files (id)
                )
            ''')
            
            # אינדקס לחיפוש מהיר
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_text_search 
                ON transcripts (text)
            ''')
            
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_file_time 
                ON transcripts (file_id, start_time)
            ''')
            
            conn.commit()
            logging.info("מסד נתונים אותחל")

    def index_audio_folder(self, folder_path: str) -> Dict[str, Any]:
        """
        מאנדקס תיקייה עם קבצי אודיו.
        
        Args:
            folder_path: נתיב לתיקייה
            
        Returns:
            דוח על תהליך האינדוס
        """
        logging.info(f"מתחיל אינדוס תיקייה: {folder_path}")
        
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"תיקייה לא נמצאה: {folder_path}")
        
        results = {
            "folder_path": folder_path,
            "processed_files": 0,
            "failed_files": 0,
            "total_segments": 0,
            "errors": []
        }
        
        # חיפוש קבצי MP7/BC1
        audio_files = self._find_audio_files(folder_path)
        logging.info(f"נמצאו {len(audio_files)} קבצי אודיו")
        
        for file_path in audio_files:
            try:
                self._index_single_file(file_path)
                results["processed_files"] += 1
                
            except Exception as e:
                error_msg = f"שגיאה בעיבוד {file_path}: {e}"
                logging.error(error_msg)
                results["errors"].append(error_msg)
                results["failed_files"] += 1
        
        # עדכון סטטיסטיקות
        results["total_segments"] = self._count_total_segments()
        
        logging.info(f"אינדוס הושלם: {results['processed_files']} קבצים, {results['total_segments']} קטעים")
        return results
    
    def _find_audio_files(self, folder_path: str) -> List[str]:
        """מוצא קבצי אודיו בתיקייה."""
        audio_files = []
        
        for root, dirs, files in os.walk(folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                
                # בדיקה לפי סיומת
                if file.lower().endswith(('.mp7', '.bc1')):
                    audio_files.append(file_path)
                # בדיקה עמוקה לקבצי ZIP שעשויים להיות MP7
                elif file.lower().endswith('.zip'):
                    if is_mp7_file(file_path):
                        audio_files.append(file_path)
        
        return audio_files
    
    def _index_single_file(self, file_path: str):
        """מאנדקס קובץ בודד."""
        logging.info(f"מאנדקס קובץ: {file_path}")
        
        # טעינת הקובץ
        mp7_data = load_mp7(file_path)
        
        try:
            file_name = os.path.basename(file_path)
            file_size = os.path.getsize(file_path)
            duration = self._calculate_duration(mp7_data["transcript"])
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # בדיקה אם הקובץ כבר קיים
                cursor.execute(
                    "SELECT id FROM files WHERE file_path = ?", 
                    (file_path,)
                )
                existing = cursor.fetchone()
                
                if existing:
                    # עדכון קובץ קיים
                    file_id = existing[0]
                    cursor.execute('''
                        UPDATE files 
                        SET indexed_at = ?, file_size = ?, duration = ?, segment_count = ?
                        WHERE id = ?
                    ''', (
                        datetime.now().isoformat(),
                        file_size,
                        duration,
                        len(mp7_data["transcript"]),
                        file_id
                    ))
                    
                    # מחיקת תמלילים ישנים
                    cursor.execute("DELETE FROM transcripts WHERE file_id = ?", (file_id,))
                    
                else:
                    # הוספת קובץ חדש
                    cursor.execute('''
                        INSERT INTO files (file_path, file_name, indexed_at, file_size, duration, segment_count)
                        VALUES (?, ?, ?, ?, ?, ?)
                    ''', (
                        file_path,
                        file_name,
                        datetime.now().isoformat(),
                        file_size,
                        duration,
                        len(mp7_data["transcript"])
                    ))
                    file_id = cursor.lastrowid
                
                # הוספת קטעי תמלול
                for segment in mp7_data["transcript"]:
                    cursor.execute('''
                        INSERT INTO transcripts 
                        (file_id, file_name, start_time, end_time, text, speaker, confidence)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        file_id,
                        file_name,
                        segment["start_time"],
                        segment["end_time"],
                        segment["text"],
                        segment.get("speaker"),
                        segment.get("confidence")
                    ))
                
                conn.commit()
                logging.info(f"נוספו {len(mp7_data['transcript'])} קטעי תמלול לקובץ {file_name}")
        
        finally:
            # ניקוי קבצים זמניים
            cleanup_mp7_data(mp7_data)
    
    def _calculate_duration(self, segments: List[Dict[str, Any]]) -> float:
        """מחשב משך זמן כולל מקטעי התמלול."""
        if not segments:
            return 0.0
        
        max_end_time = max(segment["end_time"] for segment in segments)
        return max_end_time
    
    def _count_total_segments(self) -> int:
        """סופר סך הקטעים במסד הנתונים."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM transcripts")
            return cursor.fetchone()[0]

    def search_transcripts(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        מחפש במסד הנתונים.
        
        Args:
            query: מחרוזת החיפוש
            limit: מספר תוצאות מקסימלי
            
        Returns:
            רשימת תוצאות חיפוש
        """
        if not query.strip():
            return []
        
        logging.info(f"מחפש: '{query}'")
        
        # חיפוש פשוט - מכיל את המילים
        search_pattern = f"%{query}%"
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT 
                    t.file_name,
                    f.file_path,
                    t.start_time,
                    t.end_time,
                    t.text,
                    t.speaker,
                    t.confidence
                FROM transcripts t
                JOIN files f ON t.file_id = f.id
                WHERE t.text LIKE ?
                ORDER BY f.file_name, t.start_time
                LIMIT ?
            ''', (search_pattern, limit))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    "file_name": row[0],
                    "file_path": row[1],
                    "start_time": row[2],
                    "end_time": row[3],
                    "text": row[4],
                    "speaker": row[5],
                    "confidence": row[6]
                })
            
            logging.info(f"נמצאו {len(results)} תוצאות")
            return results

    def get_file_transcript(self, file_path: str) -> List[Dict[str, Any]]:
        """מחזיר את כל התמלול של קובץ ספציפי."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT start_time, end_time, text, speaker, confidence
                FROM transcripts t
                JOIN files f ON t.file_id = f.id
                WHERE f.file_path = ?
                ORDER BY start_time
            ''', (file_path,))
            
            results = []
            for row in cursor.fetchall():
                results.append({
                    "start_time": row[0],
                    "end_time": row[1],
                    "text": row[2],
                    "speaker": row[3],
                    "confidence": row[4]
                })
            
            return results

    def get_indexed_files(self) -> List[Dict[str, Any]]:
        """מחזיר רשימת קבצים מאונדקסים."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT file_path, file_name, indexed_at, file_size, duration, segment_count
                FROM files
                ORDER BY indexed_at DESC
            ''')
            
            files = []
            for row in cursor.fetchall():
                files.append({
                    "file_path": row[0],
                    "file_name": row[1],
                    "indexed_at": row[2],
                    "file_size": row[3],
                    "duration": row[4],
                    "segment_count": row[5]
                })
            
            return files

    def get_statistics(self) -> Dict[str, Any]:
        """מחזיר סטטיסטיקות על מסד הנתונים."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # ספירת קבצים
            cursor.execute("SELECT COUNT(*) FROM files")
            file_count = cursor.fetchone()[0]
            
            # ספירת קטעים
            cursor.execute("SELECT COUNT(*) FROM transcripts")
            segment_count = cursor.fetchone()[0]
            
            # סך משך זמן
            cursor.execute("SELECT SUM(duration) FROM files")
            total_duration = cursor.fetchone()[0] or 0
            
            # סך גודל קבצים
            cursor.execute("SELECT SUM(file_size) FROM files")
            total_size = cursor.fetchone()[0] or 0
            
            return {
                "file_count": file_count,
                "segment_count": segment_count,
                "total_duration": total_duration,
                "total_size": total_size,
                "avg_segments_per_file": segment_count / file_count if file_count > 0 else 0
            }

    def remove_file(self, file_path: str) -> bool:
        """מסיר קובץ מהאינדקס."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # מחיקת תמלילים
            cursor.execute('''
                DELETE FROM transcripts 
                WHERE file_id IN (SELECT id FROM files WHERE file_path = ?)
            ''', (file_path,))
            
            # מחיקת קובץ
            cursor.execute("DELETE FROM files WHERE file_path = ?", (file_path,))
            
            deleted = cursor.rowcount > 0
            conn.commit()
            
            if deleted:
                logging.info(f"קובץ הוסר מהאינדקס: {file_path}")
            
            return deleted

# פונקציות עזר
def index_audio_folder(folder_path: str, db_path: str = None) -> sqlite3.Connection:
    """פונקציה קצרה לאינדוס תיקייה - לתאימות לבקשה המקורית."""
    indexer = DirectoryIndexer(db_path)
    indexer.index_audio_folder(folder_path)
    return sqlite3.connect(indexer.db_path)

def search_transcripts(query: str, db_path: str = "audio_transcripts.db") -> List[Dict[str, Any]]:
    """פונקציה קצרה לחיפוש - לתאימות לבקשה המקורית."""
    indexer = DirectoryIndexer(db_path)
    return indexer.search_transcripts(query)

if __name__ == "__main__":
    # בדיקה בסיסית
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    test_folder = "demo"
    if os.path.exists(test_folder):
        try:
            indexer = DirectoryIndexer("test_audio.db")
            results = indexer.index_audio_folder(test_folder)
            print(f"אינדוס הושלם: {results}")
            
            # בדיקת חיפוש
            search_results = indexer.search_transcripts("test")
            print(f"תוצאות חיפוש: {len(search_results)}")
            
            # סטטיסטיקות
            stats = indexer.get_statistics()
            print(f"סטטיסטיקות: {stats}")
            
        except Exception as e:
            print(f"שגיאה בבדיקה: {e}")
    else:
        print("יוצר אינדקסר ריק לדוגמה")
        indexer = DirectoryIndexer("example.db")
        print("אינדקסר נוצר בהצלחה")