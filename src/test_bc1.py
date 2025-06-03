"""
Test BC1 format loading with the new specification.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__)))

from formats.bc1_format import create_demo_bc1, open_bc1
from io import BytesIO

def test_bc1_format():
    """Test the BC1 format implementation."""
    print("יוצר קובץ BC1 דמו...")
    
    # Create demo BC1
    bc1_bytes = create_demo_bc1()
    print(f"נוצר BC1 בגודל: {len(bc1_bytes)} bytes")
    
    # Test loading
    print("טוען BC1...")
    bundle = open_bc1(BytesIO(bc1_bytes))
    
    print(f"נטען אודיו: {bundle.audio_file}")
    print(f"מספר קטעי תמלול: {len(bundle.segments)}")
    
    if bundle.metadata:
        print(f"כותרת: {bundle.metadata.get('title', 'ללא כותרת')}")
    
    for i, segment in enumerate(bundle.segments[:3]):
        print(f"קטע {i+1}: {segment['start_time']:.1f}-{segment['end_time']:.1f}s: {segment['text'][:50]}...")
    
    print("בדיקת BC1 הושלמה בהצלחה!")
    
    # Cleanup
    bundle.cleanup()

if __name__ == "__main__":
    test_bc1_format()