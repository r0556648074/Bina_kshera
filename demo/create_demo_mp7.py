"""
יוצר קובץ MP7 דמו לבדיקת המערכת.

מאזר קובץ MP3 ותמלול JSON לתוך קובץ MP7 (ZIP).
"""

import zipfile
import json
import os
from pathlib import Path

def create_demo_mp7():
    """יוצר קובץ MP7 דמו."""
    demo_dir = Path(__file__).parent
    
    # בדיקת קובץ אודיו
    audio_file = demo_dir / "sample.mp3"
    if not audio_file.exists():
        print(f"לא נמצא קובץ אודיו: {audio_file}")
        print("הנח קובץ MP3 בשם 'sample.mp3' בתיקיית demo")
        return False
    
    # יצירת תמלול דמו
    transcript_data = [
        {
            "start_time": 0.0,
            "end_time": 5.5,
            "text": "ברוכים הבאים לנגן בינה כשרה",
            "speaker": "מקריין",
            "confidence": 0.95
        },
        {
            "start_time": 5.5,
            "end_time": 12.0,
            "text": "זהו נגן אודיו מתקדם לקבצי BC1 ו-MP7",
            "speaker": "מקריין",
            "confidence": 0.92
        },
        {
            "start_time": 12.0,
            "end_time": 18.5,
            "text": "הנגן כולל תמיכה בחיפוש, bookmarks ותצוגת waveform",
            "speaker": "מקריין",
            "confidence": 0.94
        },
        {
            "start_time": 18.5,
            "end_time": 25.0,
            "text": "כל הקוד נכתב בעברית עם תמיכה מלאה ב-RTL",
            "speaker": "מקריין",
            "confidence": 0.96
        },
        {
            "start_time": 25.0,
            "end_time": 30.0,
            "text": "תיהנו מהשימוש!",
            "speaker": "מקריין",
            "confidence": 0.98
        }
    ]
    
    # מטא-דאטה
    metadata = {
        "title": "דמו נגן בינה כשרה",
        "duration": 30.0,
        "language": "he",
        "encoding": "utf-8",
        "created_by": "Bina Player Demo Creator",
        "created_at": "2025-06-05",
        "format_version": "1.0",
        "audio_format": "mp3",
        "sample_rate": 44100,
        "channels": 2
    }
    
    # יצירת קובץ MP7
    mp7_file = demo_dir / "sample_demo.mp7"
    
    try:
        with zipfile.ZipFile(mp7_file, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # הוספת קובץ אודיו
            zip_file.write(audio_file, "audio_content.mp3")
            print(f"נוסף קובץ אודיו: {audio_file.name}")
            
            # הוספת תמלול כ-JSONL
            transcript_jsonl = ""
            for segment in transcript_data:
                transcript_jsonl += json.dumps(segment, ensure_ascii=False) + "\n"
            
            zip_file.writestr("transcript.jsonl", transcript_jsonl.encode('utf-8'))
            print(f"נוסף תמלול עם {len(transcript_data)} קטעים")
            
            # הוספת מטא-דאטה
            metadata_json = json.dumps(metadata, ensure_ascii=False, indent=2)
            zip_file.writestr("metadata.json", metadata_json.encode('utf-8'))
            print("נוספה מטא-דאטה")
        
        print(f"✅ נוצר קובץ MP7 דמו: {mp7_file}")
        print(f"גודל: {mp7_file.stat().st_size:,} bytes")
        
        return True
        
    except Exception as e:
        print(f"❌ שגיאה ביצירת MP7: {e}")
        return False

def verify_demo_mp7():
    """בודק את קובץ ה-MP7 שנוצר."""
    demo_dir = Path(__file__).parent
    mp7_file = demo_dir / "sample_demo.mp7"
    
    if not mp7_file.exists():
        print("קובץ MP7 לא קיים")
        return False
    
    try:
        with zipfile.ZipFile(mp7_file, 'r') as zip_file:
            files = zip_file.namelist()
            print(f"קבצים בארכיון: {files}")
            
            # בדיקת תוכן
            if "audio_content.mp3" in files:
                audio_size = zip_file.getinfo("audio_content.mp3").file_size
                print(f"✅ קובץ אודיו: {audio_size:,} bytes")
            
            if "transcript.jsonl" in files:
                transcript_content = zip_file.read("transcript.jsonl").decode('utf-8')
                lines = [line for line in transcript_content.split('\n') if line.strip()]
                print(f"✅ תמלול: {len(lines)} קטעים")
            
            if "metadata.json" in files:
                metadata_content = zip_file.read("metadata.json").decode('utf-8')
                metadata = json.loads(metadata_content)
                print(f"✅ מטא-דאטה: {metadata.get('title', 'ללא כותרת')}")
        
        return True
        
    except Exception as e:
        print(f"❌ שגיאה בבדיקת MP7: {e}")
        return False

if __name__ == "__main__":
    print("יוצר קובץ MP7 דמו...")
    
    if create_demo_mp7():
        print("\nבודק קובץ שנוצר...")
        verify_demo_mp7()
        print("\n🎉 יצירת דמו הושלמה בהצלחה!")
        print("\nהשתמש בקובץ sample_demo.mp7 לבדיקת הנגן")
    else:
        print("\n❌ יצירת הדמו נכשלה")
        print("ודא שקובץ sample.mp3 קיים בתיקיית demo")