"""
בדיקה מקיפה של כל הרכיבים החדשים.

בודק:
- MP7 Reader
- Directory Indexer  
- User State Manager
- Logger System
- אינטגרציה ביניהם
"""

import sys
import os
import tempfile
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

def test_mp7_reader():
    """בדיקת MP7 Reader."""
    print("=== בדיקת MP7 Reader ===")
    
    try:
        from mp7_reader import load_mp7, is_mp7_file, get_mp7_info, cleanup_mp7_data
        
        # Create test MP7 file
        import zipfile
        import json
        
        test_mp7 = "test_file.mp7"
        
        # Create simple MP7 for testing
        with zipfile.ZipFile(test_mp7, 'w') as zip_file:
            # Add audio placeholder
            zip_file.writestr("audio_content.mp3", b"fake audio data")
            
            # Add transcript
            transcript = [
                {"start_time": 0.0, "end_time": 5.0, "text": "בדיקה ראשונה"},
                {"start_time": 5.0, "end_time": 10.0, "text": "בדיקה שנייה"}
            ]
            
            transcript_jsonl = ""
            for segment in transcript:
                transcript_jsonl += json.dumps(segment, ensure_ascii=False) + "\n"
            
            zip_file.writestr("transcript.jsonl", transcript_jsonl.encode('utf-8'))
            
            # Add metadata
            metadata = {"title": "בדיקה", "duration": 10.0}
            zip_file.writestr("metadata.json", json.dumps(metadata, ensure_ascii=False).encode('utf-8'))
        
        # Test validation
        print(f"✓ is_mp7_file: {is_mp7_file(test_mp7)}")
        
        # Test info
        info = get_mp7_info(test_mp7)
        print(f"✓ MP7 info: {info}")
        
        # Test loading
        mp7_data = load_mp7(test_mp7)
        print(f"✓ Loaded transcript: {len(mp7_data['transcript'])} segments")
        print(f"✓ Metadata title: {mp7_data['metadata'].get('title')}")
        
        # Cleanup
        cleanup_mp7_data(mp7_data)
        os.unlink(test_mp7)
        
        print("✓ MP7 Reader עובד תקין")
        return True
        
    except Exception as e:
        print(f"✗ שגיאה ב-MP7 Reader: {e}")
        return False

def test_directory_indexer():
    """בדיקת Directory Indexer."""
    print("\n=== בדיקת Directory Indexer ===")
    
    try:
        from directory_indexer import DirectoryIndexer
        
        # Create test indexer
        indexer = DirectoryIndexer("test_index.db")
        
        # Test statistics
        stats = indexer.get_statistics()
        print(f"✓ Initial stats: {stats}")
        
        # Test search (empty database)
        results = indexer.search_transcripts("test")
        print(f"✓ Empty search: {len(results)} results")
        
        # Test file list
        files = indexer.get_indexed_files()
        print(f"✓ Indexed files: {len(files)}")
        
        print("✓ Directory Indexer עובד תקין")
        return True
        
    except Exception as e:
        print(f"✗ שגיאה ב-Directory Indexer: {e}")
        return False

def test_user_state():
    """בדיקת User State Manager."""
    print("\n=== בדיקת User State Manager ===")
    
    try:
        from user_state import UserStateManager
        
        # Create test manager
        manager = UserStateManager("test_user_data")
        
        # Test preferences
        manager.set_preference("volume", 75)
        volume = manager.get_preference("volume")
        print(f"✓ Preference test: volume = {volume}")
        
        # Test bookmarks
        bookmark_id = manager.save_bookmark("test_file.mp3", 30.5, "test bookmark")
        bookmarks = manager.get_bookmarks("test_file.mp3")
        print(f"✓ Bookmark test: {len(bookmarks)} bookmarks")
        
        # Test history
        manager.add_to_history("test_file.mp3", 25.0, 120.0)
        recent = manager.get_recent_files()
        print(f"✓ History test: {len(recent)} recent files")
        
        # Test statistics
        stats = manager.get_statistics()
        print(f"✓ User stats: {stats}")
        
        print("✓ User State Manager עובד תקין")
        return True
        
    except Exception as e:
        print(f"✗ שגיאה ב-User State Manager: {e}")
        return False

def test_logger():
    """בדיקת Logger System."""
    print("\n=== בדיקת Logger System ===")
    
    try:
        from logger import BinaPlayerLogger, log_event, log_performance, PerformanceTimer
        
        # Create test logger
        logger = BinaPlayerLogger("test_logs")
        
        # Test event logging
        log_event("test_event", {"test": "value"})
        print("✓ Event logging works")
        
        # Test performance logging
        with PerformanceTimer(logger, "test_operation"):
            time.sleep(0.01)  # Short delay
        print("✓ Performance timing works")
        
        # Test error logging
        logger.log_error("test_error", "Test error message", {"component": "test"})
        print("✓ Error logging works")
        
        # Test session summary
        summary = logger.get_session_summary()
        print(f"✓ Session summary: {summary['total_events']} events")
        
        print("✓ Logger System עובד תקין")
        return True
        
    except Exception as e:
        print(f"✗ שגיאה ב-Logger System: {e}")
        return False

def test_integration():
    """בדיקת אינטגרציה בין רכיבים."""
    print("\n=== בדיקת אינטגרציה ===")
    
    try:
        from mp7_reader import load_mp7
        from directory_indexer import DirectoryIndexer
        from user_state import UserStateManager
        from logger import log_event
        
        # Test workflow: Load MP7 -> Index -> Save bookmark -> Log
        
        # 1. Log the start
        log_event("integration_test_start")
        
        # 2. Create user state
        user_manager = UserStateManager("integration_test_data")
        
        # 3. Create indexer
        indexer = DirectoryIndexer("integration_test.db")
        
        # 4. Test file operation simulation
        test_file = "integration_test.mp3"
        user_manager.add_to_history(test_file, 45.0, 180.0)
        bookmark_id = user_manager.save_bookmark(test_file, 67.5, "Integration test bookmark")
        
        # 5. Log the completion
        log_event("integration_test_complete", {
            "file": test_file,
            "bookmark_id": bookmark_id
        })
        
        print("✓ Integration test completed successfully")
        return True
        
    except Exception as e:
        print(f"✗ שגיאה באינטגרציה: {e}")
        return False

def cleanup_test_files():
    """מנקה קבצי בדיקה."""
    print("\n=== ניקוי קבצי בדיקה ===")
    
    test_files = [
        "test_index.db",
        "integration_test.db",
        "test_file.mp7"
    ]
    
    test_dirs = [
        "test_user_data",
        "integration_test_data",
        "test_logs"
    ]
    
    # Remove test files
    for file in test_files:
        try:
            if os.path.exists(file):
                os.unlink(file)
                print(f"✓ נמחק: {file}")
        except:
            pass
    
    # Remove test directories
    import shutil
    for dir_path in test_dirs:
        try:
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)
                print(f"✓ נמחקה תיקייה: {dir_path}")
        except:
            pass
    
    print("✓ ניקוי הושלם")

def main():
    """בדיקה ראשית."""
    print("מתחיל בדיקה מקיפה של כל הרכיבים החדשים...")
    print("=" * 50)
    
    results = []
    
    # Run all tests
    results.append(("MP7 Reader", test_mp7_reader()))
    results.append(("Directory Indexer", test_directory_indexer()))
    results.append(("User State Manager", test_user_state()))
    results.append(("Logger System", test_logger()))
    results.append(("Integration", test_integration()))
    
    # Summary
    print("\n" + "=" * 50)
    print("=== סיכום בדיקות ===")
    
    passed = 0
    failed = 0
    
    for test_name, result in results:
        status = "✓ עבר" if result else "✗ נכשל"
        print(f"{test_name}: {status}")
        
        if result:
            passed += 1
        else:
            failed += 1
    
    print(f"\nסיכום כולל: {passed} עברו, {failed} נכשלו")
    
    # Cleanup
    cleanup_test_files()
    
    if failed == 0:
        print("\n🎉 כל הרכיבים עובדים תקין!")
        print("המערכת המודולרית מוכנה לשימוש")
    else:
        print(f"\n⚠ {failed} בדיקות נכשלו")
        print("נדרשים תיקונים נוספים")
    
    return failed == 0

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)