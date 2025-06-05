# תיקיית Demo - קבצי בדיקה

תיקייה זו מכילה קבצי בדיקה לנגן בינה כשרה.

## קבצים

### create_demo_mp7.py
יוצר קובץ MP7 דמו לבדיקת המערכת.

**שימוש:**
1. הנח קובץ MP3 בשם `sample.mp3` בתיקייה זו
2. הרץ: `python create_demo_mp7.py`
3. יווצר קובץ `sample_demo.mp7` לבדיקה

**תוכן הדמו:**
- קובץ אודיו MP3
- תמלול בעברית עם 5 קטעים
- מטא-דאטה מלאה

## הוראות הכנה

1. **הנחת קובץ אודיו:**
   ```
   cp your_audio.mp3 demo/sample.mp3
   ```

2. **יצירת MP7 דמו:**
   ```
   cd demo
   python create_demo_mp7.py
   ```

3. **בדיקת הנגן:**
   ```
   cd ..
   python src/__main__.py
   ```

## מבנה קובץ MP7

```
sample_demo.mp7 (ZIP)
├── audio_content.mp3     # קובץ האודיו
├── transcript.jsonl      # תמלול בפורמט JSONL
└── metadata.json         # מטא-דאטה
```

## פורמט התמלול

כל שורה ב-transcript.jsonl היא JSON עם:
```json
{
  "start_time": 0.0,
  "end_time": 5.5,
  "text": "טקסט בעברית",
  "speaker": "שם הדובר",
  "confidence": 0.95
}
```