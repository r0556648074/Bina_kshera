"""
MP7 Format Reader - קורא קבצי MP7 (BC1) 

מטפל בקריאה וחילוץ של:
- קבצי אודיו (MP3, AAC, WAV)
- קבצי תמלול (transcript.jsonl)
- מטא-דאטה (metadata.json)

MP7 הוא בעצם קובץ ZIP עם מבנה מוגדר.
"""

import zipfile
import json
import tempfile
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
import logging

def load_mp7(path: str) -> Dict[str, Any]:
    """
    טוען קובץ MP7 ומחזיר את התוכן המפוענח.
    
    Args:
        path: נתיב לקובץ MP7
        
    Returns:
        Dict עם:
        - audio_path: נתיב לקובץ אודיו זמני
        - transcript: רשימת קטעי תמלול
        - metadata: מטא-דאטה אם קיימת
        - temp_files: רשימת קבצים זמניים לניקוי
    """
    logging.info(f"טוען קובץ MP7: {path}")
    
    if not os.path.exists(path):
        raise FileNotFoundError(f"קובץ MP7 לא נמצא: {path}")
    
    result = {
        "audio_path": None,
        "transcript": [],
        "metadata": {},
        "temp_files": []
    }
    
    try:
        with zipfile.ZipFile(path, 'r') as zip_file:
            # רשימת קבצים בארכיון
            file_list = zip_file.namelist()
            logging.info(f"קבצים בארכיון: {file_list}")
            
            # חיפוש קובץ אודיו
            audio_file = _find_audio_file(file_list)
            if audio_file:
                result["audio_path"] = _extract_audio_file(zip_file, audio_file)
                result["temp_files"].append(result["audio_path"])
                logging.info(f"קובץ אודיו חולץ: {result['audio_path']}")
            else:
                logging.warning("לא נמצא קובץ אודיו בארכיון")
            
            # חיפוש קובץ תמלול
            transcript_file = _find_transcript_file(file_list)
            if transcript_file:
                result["transcript"] = _extract_transcript(zip_file, transcript_file)
                logging.info(f"נטען תמלול עם {len(result['transcript'])} קטעים")
            else:
                logging.warning("לא נמצא קובץ תמלול בארכיון")
            
            # חיפוש מטא-דאטה
            metadata_file = _find_metadata_file(file_list)
            if metadata_file:
                result["metadata"] = _extract_metadata(zip_file, metadata_file)
                logging.info("מטא-דאטה נטענה")
            else:
                logging.info("אין מטא-דאטה")
                
    except zipfile.BadZipFile:
        raise ValueError(f"קובץ MP7 פגום או לא תקין: {path}")
    except Exception as e:
        # ניקוי קבצים זמניים במקרה של שגיאה
        _cleanup_temp_files(result.get("temp_files", []))
        raise RuntimeError(f"שגיאה בטעינת MP7: {e}")
    
    return result

def _find_audio_file(file_list: List[str]) -> Optional[str]:
    """מוצא קובץ אודיו בארכיון."""
    audio_extensions = ['.mp3', '.aac', '.wav', '.m4a', '.ogg', '.flac']
    
    # חיפוש לפי שם מוכר
    for filename in file_list:
        if filename.startswith('audio_content.'):
            return filename
    
    # חיפוש לפי סיומת
    for filename in file_list:
        for ext in audio_extensions:
            if filename.lower().endswith(ext):
                return filename
    
    return None

def _find_transcript_file(file_list: List[str]) -> Optional[str]:
    """מוצא קובץ תמלול בארכיון."""
    for filename in file_list:
        if filename == 'transcript.jsonl' or filename.endswith('transcript.jsonl'):
            return filename
        if filename == 'transcript.json' or filename.endswith('transcript.json'):
            return filename
    return None

def _find_metadata_file(file_list: List[str]) -> Optional[str]:
    """מוצא קובץ מטא-דאטה בארכיון."""
    for filename in file_list:
        if filename == 'metadata.json' or filename.endswith('metadata.json'):
            return filename
        if filename == 'manifest.json' or filename.endswith('manifest.json'):
            return filename
    return None

def _extract_audio_file(zip_file: zipfile.ZipFile, audio_filename: str) -> str:
    """מחלץ קובץ אודיו לתיקייה זמנית."""
    # יצירת קובץ זמני עם סיומת נכונה
    file_ext = Path(audio_filename).suffix
    temp_fd, temp_path = tempfile.mkstemp(suffix=file_ext, prefix='mp7_audio_')
    
    try:
        with os.fdopen(temp_fd, 'wb') as temp_file:
            temp_file.write(zip_file.read(audio_filename))
        
        logging.info(f"קובץ אודיו חולץ לתיקייה זמנית: {temp_path}")
        return temp_path
        
    except Exception as e:
        os.close(temp_fd)
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        raise RuntimeError(f"שגיאה בחילוץ קובץ אודיו: {e}")

def _extract_transcript(zip_file: zipfile.ZipFile, transcript_filename: str) -> List[Dict[str, Any]]:
    """מחלץ ומפענח קובץ תמלול."""
    try:
        transcript_data = zip_file.read(transcript_filename).decode('utf-8')
        
        segments = []
        
        if transcript_filename.endswith('.jsonl'):
            # קובץ JSONL - כל שורה היא JSON נפרד
            for line_num, line in enumerate(transcript_data.strip().split('\n'), 1):
                if line.strip():
                    try:
                        segment = json.loads(line)
                        segments.append(_normalize_segment(segment))
                    except json.JSONDecodeError as e:
                        logging.warning(f"שגיאה בפענוח שורה {line_num} בתמלול: {e}")
        
        elif transcript_filename.endswith('.json'):
            # קובץ JSON רגיל
            data = json.loads(transcript_data)
            if isinstance(data, list):
                segments = [_normalize_segment(seg) for seg in data]
            elif isinstance(data, dict) and 'segments' in data:
                segments = [_normalize_segment(seg) for seg in data['segments']]
            else:
                logging.warning("מבנה תמלול לא מוכר")
        
        logging.info(f"נטענו {len(segments)} קטעי תמלול")
        return segments
        
    except Exception as e:
        logging.error(f"שגיאה בחילוץ תמלול: {e}")
        return []

def _extract_metadata(zip_file: zipfile.ZipFile, metadata_filename: str) -> Dict[str, Any]:
    """מחלץ ומפענח מטא-דאטה."""
    try:
        metadata_data = zip_file.read(metadata_filename).decode('utf-8')
        metadata = json.loads(metadata_data)
        return metadata
        
    except Exception as e:
        logging.error(f"שגיאה בחילוץ מטא-דאטה: {e}")
        return {}

def _normalize_segment(segment: Dict[str, Any]) -> Dict[str, Any]:
    """מנרמל קטע תמלול לפורמט אחיד."""
    normalized = {
        "start_time": 0.0,
        "end_time": 0.0,
        "text": "",
        "speaker": None,
        "confidence": None
    }
    
    # זמן התחלה
    if "start_time" in segment:
        normalized["start_time"] = float(segment["start_time"])
    elif "start" in segment:
        normalized["start_time"] = float(segment["start"])
    
    # זמן סיום
    if "end_time" in segment:
        normalized["end_time"] = float(segment["end_time"])
    elif "end" in segment:
        normalized["end_time"] = float(segment["end"])
    
    # טקסט
    if "text" in segment:
        normalized["text"] = str(segment["text"]).strip()
    elif "content" in segment:
        normalized["text"] = str(segment["content"]).strip()
    
    # רמקול (אופציונלי)
    if "speaker" in segment:
        normalized["speaker"] = segment["speaker"]
    elif "speaker_id" in segment:
        normalized["speaker"] = segment["speaker_id"]
    
    # רמת ביטחון (אופציונלי)
    if "confidence" in segment:
        normalized["confidence"] = float(segment["confidence"])
    
    return normalized

def _cleanup_temp_files(temp_files: List[str]):
    """מנקה קבצים זמניים."""
    for temp_file in temp_files:
        try:
            if os.path.exists(temp_file):
                os.unlink(temp_file)
                logging.info(f"קובץ זמני נמחק: {temp_file}")
        except Exception as e:
            logging.warning(f"לא ניתן למחוק קובץ זמני {temp_file}: {e}")

def cleanup_mp7_data(mp7_data: Dict[str, Any]):
    """מנקה נתוני MP7 כולל קבצים זמניים."""
    if "temp_files" in mp7_data:
        _cleanup_temp_files(mp7_data["temp_files"])
        mp7_data["temp_files"] = []

# פונקציות עזר לבדיקה
def is_mp7_file(path: str) -> bool:
    """בודק אם קובץ הוא MP7 תקין."""
    try:
        if not os.path.exists(path):
            return False
        
        with zipfile.ZipFile(path, 'r') as zip_file:
            file_list = zip_file.namelist()
            # בדיקה בסיסית - צריך להיות לפחות קובץ אחד
            return len(file_list) > 0 and (_find_audio_file(file_list) is not None)
    
    except (zipfile.BadZipFile, Exception):
        return False

def get_mp7_info(path: str) -> Dict[str, Any]:
    """מחזיר מידע בסיסי על קובץ MP7 בלי לחלץ אותו."""
    info = {
        "is_valid": False,
        "has_audio": False,
        "has_transcript": False,
        "has_metadata": False,
        "file_list": []
    }
    
    try:
        if not os.path.exists(path):
            return info
        
        with zipfile.ZipFile(path, 'r') as zip_file:
            file_list = zip_file.namelist()
            info["file_list"] = file_list
            info["is_valid"] = True
            
            info["has_audio"] = _find_audio_file(file_list) is not None
            info["has_transcript"] = _find_transcript_file(file_list) is not None
            info["has_metadata"] = _find_metadata_file(file_list) is not None
    
    except Exception as e:
        logging.error(f"שגיאה בקבלת מידע על MP7: {e}")
    
    return info

if __name__ == "__main__":
    # בדיקה בסיסית
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    
    test_file = "test.mp7"
    if os.path.exists(test_file):
        try:
            data = load_mp7(test_file)
            print(f"נטען MP7 עם {len(data['transcript'])} קטעי תמלול")
            print(f"קובץ אודיו: {data['audio_path']}")
            print(f"מטא-דאטה: {data['metadata']}")
            
            # ניקוי
            cleanup_mp7_data(data)
            
        except Exception as e:
            print(f"שגיאה בטעינת MP7: {e}")
    else:
        print("לא נמצא קובץ בדיקה test.mp7")