"""
Unit tests for the AudioEngine class.

This module contains comprehensive tests for audio engine functionality
including FFmpeg integration, audio loading, playback control, and metadata extraction.
"""

import unittest
import tempfile
import os
import sys
import logging
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import numpy as np

# Setup test environment
test_dir = Path(__file__).parent
src_dir = test_dir.parent / "src"
sys.path.insert(0, str(src_dir))

from PySide6.QtCore import QCoreApplication, QEventLoop, QTimer
from PySide6.QtTest import QTest

from engine.audio_engine import AudioEngine, AudioMetadata, PCMStreamDevice
from utils.audio_utils import validate_audio_data

# Disable logging during tests to reduce noise
logging.disable(logging.CRITICAL)

class TestAudioEngine(unittest.TestCase):
    """Test cases for AudioEngine class."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class."""
        # Create QApplication if it doesn't exist
        if not QCoreApplication.instance():
            cls.app = QCoreApplication([])
        else:
            cls.app = QCoreApplication.instance()
    
    def setUp(self):
        """Set up test case."""
        self.audio_engine = AudioEngine()
        self.temp_dir = tempfile.mkdtemp()
        
        # Mock FFmpeg path for testing
        self.mock_ffmpeg_path = "/fake/path/to/ffmpeg"
    
    def tearDown(self):
        """Clean up test case."""
        if self.audio_engine:
            self.audio_engine.cleanup()
        
        # Clean up temp directory
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_initialization(self):
        """Test audio engine initialization."""
        engine = AudioEngine()
        
        # Check initial state
        self.assertIsNone(engine.ffmpeg_path)
        self.assertIsNone(engine.audio_sink)
        self.assertIsNone(engine.current_file)
        self.assertIsNone(engine.metadata)
        self.assertEqual(engine.current_position, 0.0)
    
    @patch('subprocess.run')
    def test_find_ffmpeg_success(self, mock_run):
        """Test successful FFmpeg detection."""
        # Mock successful FFmpeg execution
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "ffmpeg version 4.4.0"
        mock_run.return_value = mock_result
        
        # Test system PATH detection
        engine = AudioEngine()
        ffmpeg_path = engine._find_ffmpeg()
        
        # Should find ffmpeg in PATH
        self.assertEqual(ffmpeg_path, 'ffmpeg')
    
    @patch('subprocess.run')
    def test_find_ffmpeg_failure(self, mock_run):
        """Test FFmpeg detection failure."""
        # Mock failed FFmpeg execution
        mock_run.side_effect = FileNotFoundError()
        
        engine = AudioEngine()
        ffmpeg_path = engine._find_ffmpeg()
        
        # Should return None when not found
        self.assertIsNone(ffmpeg_path)
    
    @patch('subprocess.run')
    def test_test_ffmpeg_success(self, mock_run):
        """Test FFmpeg functionality test."""
        # Mock successful FFmpeg version check
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        engine = AudioEngine()
        engine.ffmpeg_path = self.mock_ffmpeg_path
        
        result = engine._test_ffmpeg()
        self.assertTrue(result)
    
    @patch('subprocess.run')
    def test_test_ffmpeg_failure(self, mock_run):
        """Test FFmpeg functionality test failure."""
        # Mock failed FFmpeg version check
        mock_result = Mock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result
        
        engine = AudioEngine()
        engine.ffmpeg_path = self.mock_ffmpeg_path
        
        result = engine._test_ffmpeg()
        self.assertFalse(result)
    
    def test_audio_metadata_creation(self):
        """Test AudioMetadata dataclass creation."""
        metadata = AudioMetadata(
            duration=120.5,
            sample_rate=44100,
            channels=2,
            format="mp3",
            bitrate=320,
            title="Test Song",
            artist="Test Artist"
        )
        
        self.assertEqual(metadata.duration, 120.5)
        self.assertEqual(metadata.sample_rate, 44100)
        self.assertEqual(metadata.channels, 2)
        self.assertEqual(metadata.format, "mp3")
        self.assertEqual(metadata.bitrate, 320)
        self.assertEqual(metadata.title, "Test Song")
        self.assertEqual(metadata.artist, "Test Artist")
    
    @patch('subprocess.run')
    def test_get_audio_metadata_json(self, mock_run):
        """Test metadata extraction using JSON output."""
        # Mock ffprobe JSON response
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = '''
        {
            "streams": [
                {
                    "codec_type": "audio",
                    "sample_rate": "44100",
                    "channels": 2
                }
            ],
            "format": {
                "duration": "180.25",
                "format_name": "mp3"
            }
        }
        '''
        mock_run.return_value = mock_result
        
        engine = AudioEngine()
        engine.ffmpeg_path = self.mock_ffmpeg_path
        
        metadata = engine._get_audio_metadata("/fake/file.mp3")
        
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata.duration, 180.25)
        self.assertEqual(metadata.sample_rate, 44100)
        self.assertEqual(metadata.channels, 2)
        self.assertEqual(metadata.format, "mp3")
    
    @patch('subprocess.run')
    def test_get_audio_metadata_stderr_parsing(self, mock_run):
        """Test metadata extraction from stderr output."""
        # Mock ffmpeg stderr output (fallback method)
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stderr = '''
        Input #0, mp3, from 'test.mp3':
          Duration: 00:03:24.65, start: 0.000000, bitrate: 320 kb/s
            Stream #0:0: Audio: mp3, 44100 Hz, stereo, fltp, 320 kb/s
        '''
        mock_run.side_effect = [FileNotFoundError(), mock_result]
        
        engine = AudioEngine()
        engine.ffmpeg_path = self.mock_ffmpeg_path
        
        metadata = engine._get_audio_metadata("/fake/file.mp3")
        
        self.assertIsNotNone(metadata)
        self.assertAlmostEqual(metadata.duration, 204.65, places=1)  # 3:24.65 = 204.65s
        self.assertEqual(metadata.sample_rate, 44100)
        self.assertEqual(metadata.channels, 2)
    
    def test_parse_ffmpeg_metadata(self):
        """Test parsing metadata from FFmpeg stderr output."""
        stderr_output = '''
        Input #0, wav, from 'test.wav':
          Duration: 00:02:30.50, start: 0.000000, bitrate: 1411 kb/s
            Stream #0:0: Audio: pcm_s16le ([1][0][0][0] / 0x0001), 44100 Hz, stereo, s16, 1411 kb/s
        '''
        
        engine = AudioEngine()
        metadata = engine._parse_ffmpeg_metadata(stderr_output)
        
        self.assertIsNotNone(metadata)
        self.assertEqual(metadata.duration, 150.5)  # 2:30.50 = 150.5s
        self.assertEqual(metadata.sample_rate, 44100)
        self.assertEqual(metadata.channels, 2)
    
    def test_position_time_conversion(self):
        """Test position and time conversion methods."""
        engine = AudioEngine()
        engine.metadata = AudioMetadata(
            duration=180.0,
            sample_rate=44100,
            channels=2,
            format="test"
        )
        
        # Test getting duration
        self.assertEqual(engine.get_duration(), 180.0)
        
        # Test position (initially 0)
        self.assertEqual(engine.get_position(), 0.0)
    
    def test_signals_connection(self):
        """Test that audio engine signals are properly defined."""
        engine = AudioEngine()
        
        # Check that signals exist
        self.assertTrue(hasattr(engine, 'position_changed'))
        self.assertTrue(hasattr(engine, 'duration_changed'))
        self.assertTrue(hasattr(engine, 'state_changed'))
        self.assertTrue(hasattr(engine, 'error_occurred'))
        self.assertTrue(hasattr(engine, 'audio_data_ready'))
    
    def test_pcm_stream_device_creation(self):
        """Test PCMStreamDevice creation and basic functionality."""
        # Create a simple generator
        def test_generator():
            yield b'test_data_1'
            yield b'test_data_2'
            yield b'test_data_3'
        
        device = PCMStreamDevice(test_generator())
        
        # Test device properties
        self.assertTrue(device.isSequential())
        
        # Test opening device
        result = device.open(device.OpenModeFlag.ReadOnly)
        self.assertTrue(result)
        
        # Test reading data
        data = device.readData(100)
        self.assertIsInstance(data, bytes)
        
        device.close()
    
    def test_invalid_file_handling(self):
        """Test handling of invalid file paths."""
        engine = AudioEngine()
        engine.ffmpeg_path = self.mock_ffmpeg_path
        
        # Test with non-existent file
        result = engine.load_file("/non/existent/file.mp3")
        self.assertFalse(result)
    
    @patch('subprocess.run')
    def test_load_file_success(self, mock_run):
        """Test successful file loading."""
        # Create a temporary test file
        test_file = os.path.join(self.temp_dir, "test.mp3")
        with open(test_file, 'wb') as f:
            f.write(b'fake_audio_data')
        
        # Mock metadata extraction
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = '''
        {
            "streams": [{"codec_type": "audio", "sample_rate": "44100", "channels": 2}],
            "format": {"duration": "60.0", "format_name": "mp3"}
        }
        '''
        mock_run.return_value = mock_result
        
        engine = AudioEngine()
        engine.ffmpeg_path = self.mock_ffmpeg_path
        
        # Mock the visualization data loading
        with patch.object(engine, '_load_audio_visualization_data'):
            result = engine.load_file(test_file)
        
        self.assertTrue(result)
        self.assertEqual(engine.current_file, test_file)
        self.assertIsNotNone(engine.metadata)
    
    def test_cleanup(self):
        """Test engine cleanup."""
        engine = AudioEngine()
        
        # Should not raise any exceptions
        engine.cleanup()
        
        # Test cleanup with active components
        engine.current_file = "/fake/file.mp3"
        engine.cleanup()
        
        self.assertIsNone(engine.current_file)
    
    def test_seek_validation(self):
        """Test seek position validation."""
        engine = AudioEngine()
        
        # Test seek without loaded file
        engine.seek(30.0)  # Should not crash
        
        # Test seek with loaded metadata
        engine.metadata = AudioMetadata(
            duration=120.0,
            sample_rate=44100,
            channels=2,
            format="test"
        )
        
        # Test valid seek
        engine.seek(60.0)
        self.assertEqual(engine.current_position, 60.0)
        
        # Test seek beyond duration (should clamp)
        engine.seek(200.0)
        self.assertEqual(engine.current_position, 120.0)
        
        # Test negative seek (should clamp to 0)
        engine.seek(-10.0)
        self.assertEqual(engine.current_position, 0.0)
    
    def test_state_management(self):
        """Test audio engine state management."""
        engine = AudioEngine()
        
        # Test initial state
        self.assertEqual(engine.current_position, 0.0)
        self.assertIsNone(engine.current_file)
        self.assertIsNone(engine.metadata)
        
        # Test position updates
        engine.current_position = 45.0
        self.assertEqual(engine.get_position(), 45.0)

class TestAudioEngineIntegration(unittest.TestCase):
    """Integration tests for AudioEngine with Qt components."""
    
    @classmethod
    def setUpClass(cls):
        """Set up test class."""
        if not QCoreApplication.instance():
            cls.app = QCoreApplication([])
        else:
            cls.app = QCoreApplication.instance()
    
    def setUp(self):
        """Set up test case."""
        self.audio_engine = AudioEngine()
    
    def tearDown(self):
        """Clean up test case."""
        if self.audio_engine:
            self.audio_engine.cleanup()
    
    def test_timer_functionality(self):
        """Test timer-based position updates."""
        engine = AudioEngine()
        
        # Test timer creation and configuration
        self.assertIsNotNone(engine.position_timer)
        self.assertFalse(engine.position_timer.isActive())
        
        # Test timer signal connection
        signal_emitted = False
        
        def on_timeout():
            nonlocal signal_emitted
            signal_emitted = True
        
        engine.position_timer.timeout.connect(on_timeout)
        engine.position_timer.start(10)  # 10ms timer
        
        # Wait for timer to fire
        QTest.qWait(50)
        
        engine.position_timer.stop()
        self.assertTrue(signal_emitted)
    
    def test_signal_emission(self):
        """Test that signals are properly emitted."""
        engine = AudioEngine()
        
        # Track signal emissions
        signals_received = {
            'position_changed': False,
            'duration_changed': False,
            'state_changed': False,
            'error_occurred': False,
            'audio_data_ready': False
        }
        
        # Connect signal handlers
        engine.position_changed.connect(lambda pos: signals_received.update({'position_changed': True}))
        engine.duration_changed.connect(lambda dur: signals_received.update({'duration_changed': True}))
        engine.state_changed.connect(lambda state: signals_received.update({'state_changed': True}))
        engine.error_occurred.connect(lambda err: signals_received.update({'error_occurred': True}))
        engine.audio_data_ready.connect(lambda data, rate: signals_received.update({'audio_data_ready': True}))
        
        # Emit test signals
        engine.position_changed.emit(30.0)
        engine.duration_changed.emit(180.0)
        engine.state_changed.emit('playing')
        engine.error_occurred.emit('test error')
        
        # Create test audio data
        test_data = np.array([0.1, 0.2, 0.3], dtype=np.float32)
        engine.audio_data_ready.emit(test_data, 44100)
        
        # Process events
        QCoreApplication.processEvents()
        
        # Verify signals were received
        self.assertTrue(signals_received['position_changed'])
        self.assertTrue(signals_received['duration_changed'])
        self.assertTrue(signals_received['state_changed'])
        self.assertTrue(signals_received['error_occurred'])
        self.assertTrue(signals_received['audio_data_ready'])

if __name__ == '__main__':
    # Run tests
    unittest.main(verbosity=2)
