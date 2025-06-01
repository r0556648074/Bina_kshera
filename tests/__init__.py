"""
Test package for Bina Cshera audio player application.

This package contains unit tests, integration tests, and test utilities
for validating the functionality of the audio player components.
"""

import os
import sys
from pathlib import Path

# Add src directory to path for importing application modules
test_dir = Path(__file__).parent
src_dir = test_dir.parent / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

# Test configuration
TEST_DATA_DIR = test_dir / "test_data"
TEMP_DIR = test_dir / "temp"

# Create test directories if they don't exist
TEST_DATA_DIR.mkdir(exist_ok=True)
TEMP_DIR.mkdir(exist_ok=True)

# Test utilities
def get_test_data_path(filename: str) -> Path:
    """Get path to test data file."""
    return TEST_DATA_DIR / filename

def get_temp_path(filename: str) -> Path:
    """Get path to temporary test file."""
    return TEMP_DIR / filename

def cleanup_temp_files():
    """Clean up temporary test files."""
    import shutil
    if TEMP_DIR.exists():
        shutil.rmtree(TEMP_DIR)
        TEMP_DIR.mkdir()
