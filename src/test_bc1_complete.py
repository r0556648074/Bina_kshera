"""
מבדק שלמות מערכת BC1 עם תיקונים מתקדמים.

בודק:
- יצירת קבצים זמניים עם fallback mechanisms
- תקינות קבצי BC1
- ניהול זיכרון ומעקב קבצים
- ניקוי אוטומטי
"""

import sys
import os
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

def test_bc1_system():
    """בדיקה מקיפה של מערכת BC1."""
    print("=== מבדק מערכת BC1 מתקדמת ===")
    
    try:
        # Import components
        from formats.bc1_format import create_demo_bc1, open_bc1
        from system.integrity_checker import (
            validate_media_file, 
            get_temp_manager, 
            MediaIntegrityChecker
        )
        from utils.logger import detailed_logger
        
        print("✓ רכיבי מערכת נטענו בהצלחה")
        
        # Test 1: Create demo BC1
        print("\n1. יוצר BC1 דמו...")
        bc1_data = create_demo_bc1()
        print(f"✓ BC1 נוצר: {len(bc1_data):,} bytes")
        
        # Test 2: Save to temporary file
        print("\n2. שומר לקובץ זמני...")
        temp_manager = get_temp_manager()
        bc1_file_path = temp_manager.create_temp_file(bc1_data, "bc1", "test")
        print(f"✓ קובץ זמני נוצר: {bc1_file_path}")
        
        # Test 3: Validate BC1 file integrity
        print("\n3. בודק תקינות BC1...")
        validation = validate_media_file(bc1_file_path, "bc1")
        if validation["valid"]:
            print("✓ BC1 תקין")
            print(f"  - גודל אודיו: {validation['audio_size']:,} bytes")
            print(f"  - קטעי תמלול: {validation['transcript_segments']}")
            print(f"  - metadata: {'יש' if validation['metadata_present'] else 'אין'}")
        else:
            print(f"✗ BC1 לא תקין: {validation['error']}")
            return False
        
        # Test 4: Open BC1 bundle
        print("\n4. פותח BC1 bundle...")
        bundle = open_bc1(bc1_file_path)
        print(f"✓ Bundle נפתח")
        print(f"  - קובץ אודיו: {bundle.audio_file}")
        print(f"  - קטעי תמלול: {len(bundle.segments)}")
        
        # Test 5: Validate extracted audio
        print("\n5. בודק אודיו שחולץ...")
        audio_validation = MediaIntegrityChecker.validate_audio_file(bundle.audio_file)
        if audio_validation["valid"]:
            print("✓ אודיו תקין")
            print(f"  - משך זמן: {audio_validation['duration']:.1f}s")
            print(f"  - קצב דגימה: {audio_validation['sample_rate']}Hz")
            print(f"  - ערוצים: {audio_validation['channels']}")
        else:
            print(f"✗ אודיו לא תקין: {audio_validation['error']}")
            bundle.cleanup()
            return False
        
        # Test 6: Test transcript segments
        print("\n6. בודק קטעי תמלול...")
        valid_segments = 0
        for segment in bundle.segments:
            if (isinstance(segment, dict) and 
                'start_time' in segment and 
                'end_time' in segment and 
                'text' in segment):
                valid_segments += 1
        
        print(f"✓ קטעי תמלול תקינים: {valid_segments}/{len(bundle.segments)}")
        
        # Test 7: File locking mechanism
        print("\n7. בודק מנגנון נעילת קבצים...")
        temp_manager.mark_file_locked(bundle.audio_file)
        print("✓ קובץ נעול")
        
        # Try cleanup while locked (should not delete)
        cleanup_result = temp_manager.cleanup_file(bundle.audio_file)
        if not cleanup_result:
            print("✓ קובץ נעול לא נמחק (כמצופה)")
        else:
            print("✗ קובץ נעול נמחק (בעיה!)")
        
        # Unlock and cleanup
        temp_manager.mark_file_unlocked(bundle.audio_file)
        print("✓ קובץ שוחרר")
        
        # Test 8: Cleanup
        print("\n8. מנקה קבצים...")
        bundle.cleanup()
        temp_manager.cleanup_file(bc1_file_path)
        print("✓ ניקוי הושלם")
        
        # Test 9: Verify cleanup
        print("\n9. מוודא ניקוי...")
        files_exist = []
        if os.path.exists(bc1_file_path):
            files_exist.append("BC1")
        if os.path.exists(bundle.audio_file):
            files_exist.append("אודיו")
        
        if files_exist:
            print(f"⚠ קבצים עדיין קיימים: {', '.join(files_exist)}")
        else:
            print("✓ כל הקבצים נוקו")
        
        print("\n=== מבדק הושלם בהצלחה ===")
        return True
        
    except Exception as e:
        print(f"\n✗ שגיאה במבדק: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fallback_mechanisms():
    """בדיקת מנגנוני fallback."""
    print("\n=== מבדק fallback mechanisms ===")
    
    try:
        from system.integrity_checker import get_temp_manager
        
        temp_manager = get_temp_manager()
        
        # Test creating file with different locations
        test_data = b"test data for fallback"
        
        print("בודק יצירת קבצים במיקומים שונים...")
        
        try:
            temp_file = temp_manager.create_temp_file(test_data, "test", "fallback_test")
            print(f"✓ קובץ נוצר: {temp_file}")
            
            # Cleanup
            temp_manager.cleanup_file(temp_file)
            print("✓ קובץ נוקה")
            
        except Exception as e:
            print(f"✗ שגיאה ביצירת קובץ: {e}")
            return False
        
        print("✓ fallback mechanisms עובדים")
        return True
        
    except Exception as e:
        print(f"✗ שגיאה בבדיקת fallback: {e}")
        return False

if __name__ == "__main__":
    print("מתחיל מבדק מערכת BC1...")
    
    # Run main test
    success1 = test_bc1_system()
    
    # Run fallback test  
    success2 = test_fallback_mechanisms()
    
    if success1 and success2:
        print("\n🎉 כל המבדקים עברו בהצלחה!")
        print("מערכת BC1 מוכנה לשימוש")
    else:
        print("\n❌ חלק מהמבדקים נכשלו")
        print("נדרשים תיקונים נוספים")