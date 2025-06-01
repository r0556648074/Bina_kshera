"""
Core audio engine for audio processing, decoding, and playback management.

This module handles FFmpeg integration, PCM stream generation, and audio format processing.
"""

import os
import sys
import subprocess
import logging
import threading
import time
from pathlib import Path
from typing import Optional, Generator, Tuple, Dict, Any
from dataclasses import dataclass

import numpy as np
from PySide6.QtCore import QObject, Signal, QIODevice, QByteArray, QTimer
from PySide6.QtMultimedia import QAudioFormat, QAudioSink, QMediaDevices

logger = logging.getLogger(__name__)

@dataclass
class AudioMetadata:
    """Container for audio file metadata."""
    duration: float
    sample_rate: int
    channels: int
    format: str
    bitrate: Optional[int] = None
    title: Optional[str] = None
    artist: Optional[str] = None

class PCMStreamDevice(QIODevice):
    """QIODevice that provides PCM audio data from a generator."""
    
    def __init__(self, pcm_generator: Generator[bytes, None, None], parent=None):
        super().__init__(parent)
        self.pcm_generator = pcm_generator
        self.buffer = QByteArray()
        self.position = 0
        self.is_finished = False
        
    def isSequential(self) -> bool:
        return True
    
    def readData(self, max_size: int) -> bytes:
        """Read PCM data for audio playback."""
        try:
            # Fill buffer if needed
            while len(self.buffer) < max_size and not self.is_finished:
                try:
                    chunk = next(self.pcm_generator)
                    self.buffer.append(QByteArray(chunk))
                except StopIteration:
                    self.is_finished = True
                    break
            
            # Return requested amount of data
            if len(self.buffer) > 0:
                data = self.buffer.left(max_size)
                self.buffer = self.buffer.mid(max_size)
                return bytes(data)
            
            return b''
            
        except Exception as e:
            logger.error(f"Error reading PCM data: {e}")
            return b''
    
    def writeData(self, data: bytes) -> int:
        """Not implemented for read-only device."""
        return -1

class AudioEngine(QObject):
    """Core audio engine for processing and playback."""
    
    # Signals
    position_changed = Signal(float)  # Current playback position in seconds
    duration_changed = Signal(float)  # Total duration in seconds
    state_changed = Signal(str)       # Playback state: 'playing', 'paused', 'stopped'
    error_occurred = Signal(str)      # Error message
    audio_data_ready = Signal(np.ndarray, int)  # Audio samples and sample rate for visualization
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.ffmpeg_path: Optional[str] = None
        self.audio_sink: Optional[QAudioSink] = None
        self.pcm_device: Optional[PCMStreamDevice] = None
        self.current_file: Optional[str] = None
        self.metadata: Optional[AudioMetadata] = None
        self.position_timer = QTimer()
        self.position_timer.timeout.connect(self._update_position)
        self.current_position = 0.0
        self._pcm_process: Optional[subprocess.Popen] = None
        
    def initialize(self) -> bool:
        """Initialize the audio engine."""
        try:
            # Find FFmpeg executable
            self.ffmpeg_path = self._find_ffmpeg()
            if not self.ffmpeg_path:
                logger.error("FFmpeg not found")
                return False
            
            logger.info(f"Using FFmpeg at: {self.ffmpeg_path}")
            
            # Test FFmpeg
            if not self._test_ffmpeg():
                logger.error("FFmpeg test failed")
                return False
            
            # Initialize audio system
            if not self._initialize_audio_system():
                logger.error("Failed to initialize audio system")
                return False
            
            logger.info("Audio engine initialized successfully")
            return True
            
        except Exception as e:
            logger.exception(f"Failed to initialize audio engine: {e}")
            return False
    
    def _find_ffmpeg(self) -> Optional[str]:
        """Find FFmpeg executable."""
        # Check if running as PyInstaller executable
        if getattr(sys, 'frozen', False):
            # Running as executable
            exe_dir = Path(sys.executable).parent
            ffmpeg_path = exe_dir / "ffmpeg.exe"
            if ffmpeg_path.exists():
                return str(ffmpeg_path)
        
        # Check relative to script
        script_dir = Path(__file__).parent.parent
        ffmpeg_path = script_dir / "resources" / "ffmpeg" / "ffmpeg.exe"
        if ffmpeg_path.exists():
            return str(ffmpeg_path)
        
        # Check system PATH
        try:
            result = subprocess.run(['ffmpeg', '-version'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=5)
            if result.returncode == 0:
                return 'ffmpeg'
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return None
    
    def _test_ffmpeg(self) -> bool:
        """Test FFmpeg functionality."""
        try:
            result = subprocess.run([self.ffmpeg_path, '-version'], 
                                  capture_output=True, 
                                  text=True, 
                                  timeout=10)
            return result.returncode == 0
        except Exception as e:
            logger.error(f"FFmpeg test failed: {e}")
            return False
    
    def _initialize_audio_system(self) -> bool:
        """Initialize Qt audio system."""
        try:
            # Get default audio output device
            default_device = QMediaDevices.defaultAudioOutput()
            if not default_device.isNull():
                logger.info(f"Default audio device: {default_device.description()}")
            
            return True
        except Exception as e:
            logger.error(f"Audio system initialization failed: {e}")
            return False
    
    def load_file(self, file_path: str) -> bool:
        """Load an audio file for playback."""
        try:
            if not os.path.exists(file_path):
                self.error_occurred.emit(f"File not found: {file_path}")
                return False
            
            # Stop current playback
            self.stop()
            
            # Get metadata
            metadata = self._get_audio_metadata(file_path)
            if not metadata:
                self.error_occurred.emit(f"Failed to read audio metadata: {file_path}")
                return False
            
            self.current_file = file_path
            self.metadata = metadata
            self.current_position = 0.0
            
            # Emit signals
            self.duration_changed.emit(metadata.duration)
            self.position_changed.emit(0.0)
            
            # Load audio data for visualization
            self._load_audio_visualization_data(file_path)
            
            logger.info(f"Loaded audio file: {file_path}")
            logger.info(f"Duration: {metadata.duration:.2f}s, Sample Rate: {metadata.sample_rate}Hz")
            
            return True
            
        except Exception as e:
            logger.exception(f"Failed to load file {file_path}: {e}")
            self.error_occurred.emit(f"Failed to load file: {str(e)}")
            return False
    
    def _get_audio_metadata(self, file_path: str) -> Optional[AudioMetadata]:
        """Extract audio metadata using FFprobe."""
        try:
            cmd = [
                self.ffmpeg_path.replace('ffmpeg', 'ffprobe') if 'ffprobe' not in self.ffmpeg_path else self.ffmpeg_path,
                '-v', 'quiet',
                '-print_format', 'json',
                '-show_format',
                '-show_streams',
                file_path
            ]
            
            # If ffprobe doesn't exist, use ffmpeg
            try:
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            except FileNotFoundError:
                cmd[0] = self.ffmpeg_path
                cmd.insert(1, '-i')
                cmd.insert(2, file_path)
                cmd.extend(['-f', 'null', '-'])
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                return self._parse_ffmpeg_metadata(result.stderr)
            
            if result.returncode != 0:
                logger.error(f"FFprobe failed: {result.stderr}")
                return None
            
            import json
            data = json.loads(result.stdout)
            
            # Find audio stream
            audio_stream = None
            for stream in data.get('streams', []):
                if stream.get('codec_type') == 'audio':
                    audio_stream = stream
                    break
            
            if not audio_stream:
                logger.error("No audio stream found")
                return None
            
            # Extract metadata
            duration = float(data.get('format', {}).get('duration', 0))
            sample_rate = int(audio_stream.get('sample_rate', 44100))
            channels = int(audio_stream.get('channels', 2))
            format_name = data.get('format', {}).get('format_name', 'unknown')
            
            return AudioMetadata(
                duration=duration,
                sample_rate=sample_rate,
                channels=channels,
                format=format_name
            )
            
        except Exception as e:
            logger.error(f"Failed to get metadata: {e}")
            return None
    
    def _parse_ffmpeg_metadata(self, stderr_output: str) -> Optional[AudioMetadata]:
        """Parse metadata from FFmpeg stderr output."""
        try:
            lines = stderr_output.split('\n')
            duration = 0.0
            sample_rate = 44100
            channels = 2
            
            for line in lines:
                if 'Duration:' in line:
                    # Parse duration from "Duration: 00:03:24.65"
                    duration_str = line.split('Duration:')[1].split(',')[0].strip()
                    time_parts = duration_str.split(':')
                    duration = float(time_parts[0]) * 3600 + float(time_parts[1]) * 60 + float(time_parts[2])
                elif 'Audio:' in line:
                    # Parse "Audio: mp3, 44100 Hz, stereo"
                    if 'Hz' in line:
                        hz_part = line.split('Hz')[0].split()[-1]
                        sample_rate = int(hz_part)
                    if 'stereo' in line:
                        channels = 2
                    elif 'mono' in line:
                        channels = 1
            
            return AudioMetadata(
                duration=duration,
                sample_rate=sample_rate,
                channels=channels,
                format='unknown'
            )
            
        except Exception as e:
            logger.error(f"Failed to parse FFmpeg metadata: {e}")
            return None
    
    def _load_audio_visualization_data(self, file_path: str):
        """Load audio data for waveform visualization."""
        try:
            # Use FFmpeg to decode audio to raw PCM for analysis
            cmd = [
                self.ffmpeg_path,
                '-i', file_path,
                '-f', 's16le',
                '-acodec', 'pcm_s16le',
                '-ar', '44100',
                '-ac', '1',  # Mono for visualization
                '-'
            ]
            
            result = subprocess.run(cmd, capture_output=True, timeout=30)
            
            if result.returncode != 0:
                logger.error(f"Failed to decode audio for visualization: {result.stderr}")
                return
            
            # Convert PCM data to numpy array
            audio_data = np.frombuffer(result.stdout, dtype=np.int16)
            audio_data = audio_data.astype(np.float32) / 32768.0  # Normalize to [-1, 1]
            
            # Emit signal with audio data
            self.audio_data_ready.emit(audio_data, 44100)
            
        except Exception as e:
            logger.error(f"Failed to load visualization data: {e}")
    
    def play(self) -> bool:
        """Start audio playback."""
        try:
            if not self.current_file:
                self.error_occurred.emit("No file loaded")
                return False
            
            if self.audio_sink and self.audio_sink.state() == self.audio_sink.State.SuspendedState:
                # Resume paused playback
                self.audio_sink.resume()
                self.position_timer.start(100)  # Update position every 100ms
                self.state_changed.emit('playing')
                logger.info("Resumed audio playback")
                return True
            
            # Start new playback
            pcm_generator = self._create_pcm_stream(self.current_file, self.current_position)
            if not pcm_generator:
                return False
            
            # Create PCM device
            self.pcm_device = PCMStreamDevice(pcm_generator)
            self.pcm_device.open(QIODevice.OpenModeFlag.ReadOnly)
            
            # Create audio sink
            audio_format = QAudioFormat()
            audio_format.setSampleRate(44100)
            audio_format.setChannelCount(2)
            audio_format.setSampleFormat(QAudioFormat.SampleFormat.Int16)
            
            self.audio_sink = QAudioSink(audio_format)
            self.audio_sink.start(self.pcm_device)
            
            # Start position timer
            self.position_timer.start(100)
            self.state_changed.emit('playing')
            
            logger.info("Started audio playback")
            return True
            
        except Exception as e:
            logger.exception(f"Failed to start playback: {e}")
            self.error_occurred.emit(f"Playback failed: {str(e)}")
            return False
    
    def pause(self):
        """Pause audio playback."""
        try:
            if self.audio_sink:
                self.audio_sink.suspend()
                self.position_timer.stop()
                self.state_changed.emit('paused')
                logger.info("Paused audio playback")
        except Exception as e:
            logger.error(f"Failed to pause: {e}")
    
    def stop(self):
        """Stop audio playback."""
        try:
            if self.audio_sink:
                self.audio_sink.stop()
                self.audio_sink = None
            
            if self.pcm_device:
                self.pcm_device.close()
                self.pcm_device = None
            
            if self._pcm_process:
                self._pcm_process.terminate()
                self._pcm_process = None
            
            self.position_timer.stop()
            self.current_position = 0.0
            self.position_changed.emit(0.0)
            self.state_changed.emit('stopped')
            
            logger.info("Stopped audio playback")
            
        except Exception as e:
            logger.error(f"Failed to stop: {e}")
    
    def seek(self, position: float):
        """Seek to a specific position in seconds."""
        try:
            if not self.current_file or not self.metadata:
                return
            
            # Clamp position to valid range
            position = max(0.0, min(position, self.metadata.duration))
            self.current_position = position
            
            # If playing, restart from new position
            was_playing = (self.audio_sink and 
                          self.audio_sink.state() == self.audio_sink.State.ActiveState)
            
            self.stop()
            self.position_changed.emit(position)
            
            if was_playing:
                self.play()
            
            logger.info(f"Seeked to position: {position:.2f}s")
            
        except Exception as e:
            logger.error(f"Failed to seek: {e}")
    
    def _create_pcm_stream(self, file_path: str, start_time: float = 0.0) -> Optional[Generator[bytes, None, None]]:
        """Create a PCM stream generator using FFmpeg."""
        try:
            cmd = [
                self.ffmpeg_path,
                '-ss', str(start_time),  # Start time
                '-i', file_path,
                '-f', 's16le',
                '-acodec', 'pcm_s16le',
                '-ar', '44100',
                '-ac', '2',
                '-'
            ]
            
            self._pcm_process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                bufsize=0
            )
            
            def pcm_generator():
                try:
                    chunk_size = 4096
                    while True:
                        chunk = self._pcm_process.stdout.read(chunk_size)
                        if not chunk:
                            break
                        yield chunk
                except Exception as e:
                    logger.error(f"PCM generator error: {e}")
                finally:
                    if self._pcm_process:
                        self._pcm_process.terminate()
            
            return pcm_generator()
            
        except Exception as e:
            logger.error(f"Failed to create PCM stream: {e}")
            return None
    
    def _update_position(self):
        """Update current playback position."""
        try:
            if self.audio_sink and self.audio_sink.state() == self.audio_sink.State.ActiveState:
                # Estimate position based on processed bytes and time
                # This is a simplified approach; for accurate timing, 
                # we'd need to track actual audio timing
                self.current_position += 0.1  # 100ms timer
                
                if self.metadata and self.current_position >= self.metadata.duration:
                    self.stop()
                else:
                    self.position_changed.emit(self.current_position)
                    
        except Exception as e:
            logger.error(f"Error updating position: {e}")
    
    def get_position(self) -> float:
        """Get current playback position in seconds."""
        return self.current_position
    
    def get_duration(self) -> float:
        """Get total duration in seconds."""
        return self.metadata.duration if self.metadata else 0.0
    
    def get_metadata(self) -> Optional[AudioMetadata]:
        """Get current file metadata."""
        return self.metadata
    
    def cleanup(self):
        """Cleanup resources."""
        try:
            self.stop()
            logger.info("Audio engine cleanup completed")
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
