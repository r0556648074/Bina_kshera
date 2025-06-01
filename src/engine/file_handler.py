"""
File handling for audio files and future .bc1 format support.

This module manages file operations, format detection, and provides
a foundation for the custom .bc1 file format.
"""

import os
import json
import logging
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)

class SupportedFormat(Enum):
    """Supported audio file formats."""
    MP3 = "mp3"
    WAV = "wav"
    FLAC = "flac"
    OGG = "ogg"
    M4A = "m4a"
    BC1 = "bc1"  # Future custom format

@dataclass
class TranscriptSegment:
    """A single transcript segment with timing information."""
    start_time: float
    end_time: float
    text: str
    speaker: Optional[str] = None
    confidence: Optional[float] = None

@dataclass
class TranscriptData:
    """Complete transcript data structure."""
    segments: List[TranscriptSegment]
    metadata: Dict[str, Any]

@dataclass
class FileMetadata:
    """Metadata for audio files."""
    file_path: str
    format: SupportedFormat
    size_bytes: int
    last_modified: float
    has_transcript: bool = False
    transcript_path: Optional[str] = None

class FileHandler:
    """Handles file operations for audio files and transcripts."""
    
    SUPPORTED_AUDIO_EXTENSIONS = {
        '.mp3': SupportedFormat.MP3,
        '.wav': SupportedFormat.WAV,
        '.flac': SupportedFormat.FLAC,
        '.ogg': SupportedFormat.OGG,
        '.m4a': SupportedFormat.M4A,
        '.bc1': SupportedFormat.BC1,
    }
    
    TRANSCRIPT_EXTENSIONS = {'.json', '.jsonl', '.srt', '.vtt'}
    
    def __init__(self):
        self.current_file: Optional[str] = None
        self.current_transcript: Optional[TranscriptData] = None
    
    def is_supported_audio_file(self, file_path: str) -> bool:
        """Check if file is a supported audio format."""
        try:
            file_ext = Path(file_path).suffix.lower()
            return file_ext in self.SUPPORTED_AUDIO_EXTENSIONS
        except Exception as e:
            logger.error(f"Error checking file support: {e}")
            return False
    
    def get_file_format(self, file_path: str) -> Optional[SupportedFormat]:
        """Get the format of an audio file."""
        try:
            file_ext = Path(file_path).suffix.lower()
            return self.SUPPORTED_AUDIO_EXTENSIONS.get(file_ext)
        except Exception as e:
            logger.error(f"Error getting file format: {e}")
            return None
    
    def get_file_metadata(self, file_path: str) -> Optional[FileMetadata]:
        """Get metadata for a file."""
        try:
            if not os.path.exists(file_path):
                logger.error(f"File does not exist: {file_path}")
                return None
            
            file_path_obj = Path(file_path)
            file_format = self.get_file_format(file_path)
            
            if not file_format:
                logger.error(f"Unsupported file format: {file_path}")
                return None
            
            stat = file_path_obj.stat()
            
            # Check for associated transcript file
            transcript_path = self._find_transcript_file(file_path)
            
            return FileMetadata(
                file_path=file_path,
                format=file_format,
                size_bytes=stat.st_size,
                last_modified=stat.st_mtime,
                has_transcript=transcript_path is not None,
                transcript_path=transcript_path
            )
            
        except Exception as e:
            logger.exception(f"Error getting file metadata for {file_path}: {e}")
            return None
    
    def _find_transcript_file(self, audio_file_path: str) -> Optional[str]:
        """Find associated transcript file for an audio file."""
        try:
            audio_path = Path(audio_file_path)
            base_name = audio_path.stem
            directory = audio_path.parent
            
            # Look for transcript files with matching base name
            for ext in self.TRANSCRIPT_EXTENSIONS:
                transcript_path = directory / f"{base_name}{ext}"
                if transcript_path.exists():
                    return str(transcript_path)
            
            # Look for transcript files with similar names
            for transcript_file in directory.glob(f"{base_name}*"):
                if transcript_file.suffix.lower() in self.TRANSCRIPT_EXTENSIONS:
                    return str(transcript_file)
            
            return None
            
        except Exception as e:
            logger.error(f"Error finding transcript file: {e}")
            return None
    
    def load_transcript(self, transcript_path: str) -> Optional[TranscriptData]:
        """Load transcript data from file."""
        try:
            if not os.path.exists(transcript_path):
                logger.error(f"Transcript file does not exist: {transcript_path}")
                return None
            
            file_ext = Path(transcript_path).suffix.lower()
            
            if file_ext == '.json':
                return self._load_json_transcript(transcript_path)
            elif file_ext == '.jsonl':
                return self._load_jsonl_transcript(transcript_path)
            elif file_ext == '.srt':
                return self._load_srt_transcript(transcript_path)
            elif file_ext == '.vtt':
                return self._load_vtt_transcript(transcript_path)
            else:
                logger.error(f"Unsupported transcript format: {file_ext}")
                return None
                
        except Exception as e:
            logger.exception(f"Error loading transcript from {transcript_path}: {e}")
            return None
    
    def _load_json_transcript(self, file_path: str) -> Optional[TranscriptData]:
        """Load JSON format transcript."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            segments = []
            transcript_segments = data.get('segments', data.get('transcripts', []))
            
            for segment_data in transcript_segments:
                segment = TranscriptSegment(
                    start_time=float(segment_data.get('start', segment_data.get('start_time', 0))),
                    end_time=float(segment_data.get('end', segment_data.get('end_time', 0))),
                    text=str(segment_data.get('text', '')).strip(),
                    speaker=segment_data.get('speaker'),
                    confidence=segment_data.get('confidence')
                )
                segments.append(segment)
            
            metadata = {k: v for k, v in data.items() if k not in ['segments', 'transcripts']}
            
            return TranscriptData(segments=segments, metadata=metadata)
            
        except Exception as e:
            logger.error(f"Error loading JSON transcript: {e}")
            return None
    
    def _load_jsonl_transcript(self, file_path: str) -> Optional[TranscriptData]:
        """Load JSONL format transcript."""
        try:
            segments = []
            metadata = {}
            
            with open(file_path, 'r', encoding='utf-8') as f:
                for line_num, line in enumerate(f):
                    line = line.strip()
                    if not line:
                        continue
                    
                    try:
                        data = json.loads(line)
                        
                        if 'text' in data:
                            segment = TranscriptSegment(
                                start_time=float(data.get('start', data.get('start_time', 0))),
                                end_time=float(data.get('end', data.get('end_time', 0))),
                                text=str(data.get('text', '')).strip(),
                                speaker=data.get('speaker'),
                                confidence=data.get('confidence')
                            )
                            segments.append(segment)
                        else:
                            # Metadata line
                            metadata.update(data)
                            
                    except json.JSONDecodeError as e:
                        logger.warning(f"Skipping invalid JSON line {line_num + 1}: {e}")
                        continue
            
            return TranscriptData(segments=segments, metadata=metadata)
            
        except Exception as e:
            logger.error(f"Error loading JSONL transcript: {e}")
            return None
    
    def _load_srt_transcript(self, file_path: str) -> Optional[TranscriptData]:
        """Load SRT format transcript."""
        try:
            segments = []
            
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse SRT format
            srt_blocks = content.strip().split('\n\n')
            
            for block in srt_blocks:
                lines = block.strip().split('\n')
                if len(lines) < 3:
                    continue
                
                try:
                    # Parse timing line (e.g., "00:00:01,234 --> 00:00:05,678")
                    timing_line = lines[1]
                    start_str, end_str = timing_line.split(' --> ')
                    
                    start_time = self._parse_srt_time(start_str)
                    end_time = self._parse_srt_time(end_str)
                    
                    # Join text lines
                    text = '\n'.join(lines[2:]).strip()
                    
                    segment = TranscriptSegment(
                        start_time=start_time,
                        end_time=end_time,
                        text=text
                    )
                    segments.append(segment)
                    
                except Exception as e:
                    logger.warning(f"Skipping invalid SRT block: {e}")
                    continue
            
            return TranscriptData(segments=segments, metadata={'format': 'srt'})
            
        except Exception as e:
            logger.error(f"Error loading SRT transcript: {e}")
            return None
    
    def _parse_srt_time(self, time_str: str) -> float:
        """Parse SRT time format to seconds."""
        # Format: "00:00:01,234"
        time_str = time_str.replace(',', '.')
        parts = time_str.split(':')
        hours = int(parts[0])
        minutes = int(parts[1])
        seconds = float(parts[2])
        
        return hours * 3600 + minutes * 60 + seconds
    
    def _load_vtt_transcript(self, file_path: str) -> Optional[TranscriptData]:
        """Load WebVTT format transcript."""
        try:
            segments = []
            
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            # Skip WEBVTT header
            start_idx = 0
            for i, line in enumerate(lines):
                if line.strip().startswith('WEBVTT'):
                    start_idx = i + 1
                    break
            
            current_segment = []
            for line in lines[start_idx:]:
                line = line.strip()
                
                if not line:
                    if current_segment:
                        self._process_vtt_segment(current_segment, segments)
                        current_segment = []
                else:
                    current_segment.append(line)
            
            # Process last segment
            if current_segment:
                self._process_vtt_segment(current_segment, segments)
            
            return TranscriptData(segments=segments, metadata={'format': 'vtt'})
            
        except Exception as e:
            logger.error(f"Error loading VTT transcript: {e}")
            return None
    
    def _process_vtt_segment(self, segment_lines: List[str], segments: List[TranscriptSegment]):
        """Process a VTT segment."""
        try:
            if len(segment_lines) < 2:
                return
            
            # Find timing line (contains "-->")
            timing_line = None
            text_lines = []
            
            for line in segment_lines:
                if '-->' in line:
                    timing_line = line
                else:
                    # Skip cue identifiers (lines that don't contain "-->")
                    if timing_line is not None:
                        text_lines.append(line)
            
            if not timing_line or not text_lines:
                return
            
            # Parse timing
            start_str, end_str = timing_line.split(' --> ')
            start_time = self._parse_vtt_time(start_str.strip())
            end_time = self._parse_vtt_time(end_str.strip())
            
            text = '\n'.join(text_lines).strip()
            
            segment = TranscriptSegment(
                start_time=start_time,
                end_time=end_time,
                text=text
            )
            segments.append(segment)
            
        except Exception as e:
            logger.warning(f"Error processing VTT segment: {e}")
    
    def _parse_vtt_time(self, time_str: str) -> float:
        """Parse VTT time format to seconds."""
        # Format: "00:00:01.234" or "01:23.456"
        time_str = time_str.strip()
        
        if time_str.count(':') == 2:
            # HH:MM:SS.mmm
            parts = time_str.split(':')
            hours = int(parts[0])
            minutes = int(parts[1])
            seconds = float(parts[2])
            return hours * 3600 + minutes * 60 + seconds
        elif time_str.count(':') == 1:
            # MM:SS.mmm
            parts = time_str.split(':')
            minutes = int(parts[0])
            seconds = float(parts[1])
            return minutes * 60 + seconds
        else:
            # SS.mmm
            return float(time_str)
    
    def save_transcript(self, transcript_data: TranscriptData, file_path: str, format_type: str = 'json') -> bool:
        """Save transcript data to file."""
        try:
            if format_type == 'json':
                return self._save_json_transcript(transcript_data, file_path)
            elif format_type == 'srt':
                return self._save_srt_transcript(transcript_data, file_path)
            elif format_type == 'vtt':
                return self._save_vtt_transcript(transcript_data, file_path)
            else:
                logger.error(f"Unsupported save format: {format_type}")
                return False
                
        except Exception as e:
            logger.exception(f"Error saving transcript to {file_path}: {e}")
            return False
    
    def _save_json_transcript(self, transcript_data: TranscriptData, file_path: str) -> bool:
        """Save transcript in JSON format."""
        try:
            data = {
                'segments': [asdict(segment) for segment in transcript_data.segments],
                **transcript_data.metadata
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving JSON transcript: {e}")
            return False
    
    def _save_srt_transcript(self, transcript_data: TranscriptData, file_path: str) -> bool:
        """Save transcript in SRT format."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                for i, segment in enumerate(transcript_data.segments, 1):
                    start_time = self._format_srt_time(segment.start_time)
                    end_time = self._format_srt_time(segment.end_time)
                    
                    f.write(f"{i}\n")
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"{segment.text}\n\n")
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving SRT transcript: {e}")
            return False
    
    def _format_srt_time(self, seconds: float) -> str:
        """Format seconds to SRT time format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}".replace('.', ',')
    
    def _save_vtt_transcript(self, transcript_data: TranscriptData, file_path: str) -> bool:
        """Save transcript in VTT format."""
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("WEBVTT\n\n")
                
                for segment in transcript_data.segments:
                    start_time = self._format_vtt_time(segment.start_time)
                    end_time = self._format_vtt_time(segment.end_time)
                    
                    f.write(f"{start_time} --> {end_time}\n")
                    f.write(f"{segment.text}\n\n")
            
            return True
            
        except Exception as e:
            logger.error(f"Error saving VTT transcript: {e}")
            return False
    
    def _format_vtt_time(self, seconds: float) -> str:
        """Format seconds to VTT time format."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"
        else:
            return f"{minutes:02d}:{secs:06.3f}"
    
    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions."""
        return list(self.SUPPORTED_AUDIO_EXTENSIONS.keys())
    
    def get_audio_filter_string(self) -> str:
        """Get file filter string for audio files."""
        extensions = []
        for ext in self.SUPPORTED_AUDIO_EXTENSIONS.keys():
            extensions.append(f"*{ext}")
        
        return f"Audio Files ({' '.join(extensions)});;All Files (*)"
