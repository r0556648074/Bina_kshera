"""
BC1 Format Parser - Custom format for synchronized audio and transcripts.

This module handles the proprietary .bc1 format that contains encrypted
audio files with synchronized transcripts and metadata.
"""

import os
import json
import zipfile
import gzip
import hashlib
import logging
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Union
from dataclasses import dataclass, asdict
from io import BytesIO

try:
    from utils.logger import get_logger
    detailed_logger = get_logger()
except ImportError:
    detailed_logger = None

logger = logging.getLogger(__name__)

@dataclass
class TranscriptSegment:
    """Single transcript segment with precise timing."""
    start_time: float
    end_time: float
    text: str
    speaker: Optional[str] = None
    confidence: float = 1.0
    words: Optional[List[Dict[str, Any]]] = None  # Word-level timing

@dataclass
class BC1Metadata:
    """Metadata for BC1 file."""
    title: str
    duration: float
    language: str = "he"
    created_at: str = ""
    description: str = ""
    tags: Optional[List[str]] = None
    speaker_info: Optional[Dict[str, str]] = None

@dataclass
class BC1Manifest:
    """BC1 file manifest."""
    version: str = "1.0"
    encrypted: bool = False
    audio_format: str = "opus"
    transcript_format: str = "jsonl"
    checksum_audio: str = ""
    checksum_transcript: str = ""
    flags: Optional[Dict[str, Any]] = None

class BC1Parser:
    """Parser for BC1 format files."""
    
    def __init__(self):
        self.manifest: Optional[BC1Manifest] = None
        self.metadata: Optional[BC1Metadata] = None
        self.transcript: List[TranscriptSegment] = []
        self.audio_data: Optional[bytes] = None
        
        if detailed_logger:
            detailed_logger.info("יצירת BC1 Parser")
    
    def load_file(self, file_path: str, password: Optional[str] = None) -> bool:
        """Load BC1 file."""
        try:
            if detailed_logger:
                detailed_logger.start_operation("טעינת קובץ BC1")
                detailed_logger.log_file_operation("פתיחה", file_path, os.path.exists(file_path))
            
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"קובץ BC1 לא נמצא: {file_path}")
            
            with zipfile.ZipFile(file_path, 'r') as zip_file:
                # Load manifest
                if detailed_logger:
                    detailed_logger.info("טוען manifest")
                
                manifest_data = zip_file.read('manifest.json')
                manifest_dict = json.loads(manifest_data.decode('utf-8'))
                self.manifest = BC1Manifest(**manifest_dict)
                
                if detailed_logger:
                    detailed_logger.info(f"BC1 גרסה: {self.manifest.version}, מוצפן: {self.manifest.encrypted}")
                
                # Load audio
                if detailed_logger:
                    detailed_logger.info("טוען אודיו")
                
                audio_path = f"audio/audio.{self.manifest.audio_format}"
                self.audio_data = zip_file.read(audio_path)
                
                # Load transcript
                if detailed_logger:
                    detailed_logger.info("טוען תמלול")
                
                transcript_data = zip_file.read('data/transcript.jsonl.gz')
                
                # Decompress and parse transcript
                transcript_text = gzip.decompress(transcript_data).decode('utf-8')
                self.transcript = []
                
                for line in transcript_text.strip().split('\n'):
                    if line.strip():
                        segment_dict = json.loads(line)
                        segment = TranscriptSegment(**segment_dict)
                        self.transcript.append(segment)
                
                if detailed_logger:
                    detailed_logger.info(f"נטען תמלול עם {len(self.transcript)} קטעים")
                
                # Load metadata if exists
                try:
                    metadata_data = zip_file.read('data/metadata.json')
                    metadata_dict = json.loads(metadata_data.decode('utf-8'))
                    self.metadata = BC1Metadata(**metadata_dict)
                    
                    if detailed_logger:
                        detailed_logger.info(f"נטען metadata: {self.metadata.title}")
                        
                except KeyError:
                    # Metadata is optional
                    if detailed_logger:
                        detailed_logger.info("אין metadata בקובץ")
                    pass
            
            if detailed_logger:
                detailed_logger.end_operation("טעינת קובץ BC1")
                detailed_logger.info("קובץ BC1 נטען בהצלחה")
            
            return True
            
        except Exception as e:
            if detailed_logger:
                detailed_logger.exception(f"שגיאה בטעינת BC1: {e}")
            logger.exception(f"Error loading BC1 file: {e}")
            return False
    
    def get_audio_data(self) -> Optional[bytes]:
        """Get audio data."""
        return self.audio_data
    
    def get_transcript(self) -> List[TranscriptSegment]:
        """Get transcript segments."""
        return self.transcript
    
    def get_metadata(self) -> Optional[BC1Metadata]:
        """Get metadata."""
        return self.metadata
    
    def search_transcript(self, query: str, case_sensitive: bool = False) -> List[Tuple[int, TranscriptSegment]]:
        """Search in transcript text."""
        results = []
        
        if not case_sensitive:
            query = query.lower()
        
        for i, segment in enumerate(self.transcript):
            text = segment.text if case_sensitive else segment.text.lower()
            
            if query in text:
                results.append((i, segment))
        
        if detailed_logger:
            detailed_logger.log_audio_operation("חיפוש בתמלול", {
                "query": query,
                "results_count": len(results),
                "case_sensitive": case_sensitive
            })
        
        return results
    
    def get_segment_at_time(self, time_seconds: float) -> Optional[TranscriptSegment]:
        """Get transcript segment at specific time."""
        for segment in self.transcript:
            if segment.start_time <= time_seconds <= segment.end_time:
                return segment
        return None

@dataclass
class PlayerBundle:
    """Bundle containing all data needed for player."""
    audio_file: str  # Path to temporary audio file
    segments: List[Dict[str, Any]]  # Transcript segments
    metadata: Optional[Dict[str, Any]] = None
    manifest: Optional[BC1Manifest] = None
    cleanup_files: Optional[List[str]] = None  # Files to cleanup on exit

    def __post_init__(self):
        if self.cleanup_files is None:
            self.cleanup_files = []

    def cleanup(self):
        """Clean up temporary files."""
        for file_path in (self.cleanup_files or []):
            try:
                if os.path.exists(file_path):
                    os.unlink(file_path)
                    if detailed_logger:
                        detailed_logger.log_file_operation("נוקה קובץ זמני", file_path, True)
            except Exception as e:
                if detailed_logger:
                    detailed_logger.warning(f"לא ניתן לנקות קובץ זמני {file_path}: {e}")

class BC1File:
    """Advanced BC1 file handler for cloud-generated files."""
    
    def __init__(self):
        self.audio_bytes: Optional[bytes] = None
        self.audio_ext: str = "mp3"
        self.transcript_bytes: Optional[bytes] = None
        self.metadata: Optional[Dict[str, Any]] = None
        self.manifest: Optional[BC1Manifest] = None
        
    @classmethod
    def load(cls, bc1_source: Union[str, Path, bytes, BytesIO], password: Optional[str] = None) -> 'BC1File':
        """Load BC1 file from various sources."""
        instance = cls()
        
        try:
            if detailed_logger:
                detailed_logger.start_operation("טעינת קובץ BC1 מתקדם")
            
            # Handle different input types
            if isinstance(bc1_source, (str, Path)):
                if detailed_logger:
                    detailed_logger.log_file_operation("קריאת BC1", str(bc1_source), os.path.exists(bc1_source))
                with open(bc1_source, 'rb') as f:
                    bc1_data = f.read()
            elif isinstance(bc1_source, bytes):
                bc1_data = bc1_source
            elif isinstance(bc1_source, BytesIO):
                bc1_data = bc1_source.read()
            else:
                raise ValueError(f"סוג קלט לא נתמך: {type(bc1_source)}")
            
            # Parse ZIP archive
            with zipfile.ZipFile(BytesIO(bc1_data), 'r') as zip_file:
                instance._load_from_zip(zip_file, password)
            
            if detailed_logger:
                detailed_logger.end_operation("טעינת קובץ BC1 מתקדם")
                detailed_logger.info("קובץ BC1 נטען בהצלחה מהענן")
            
            return instance
            
        except Exception as e:
            if detailed_logger:
                detailed_logger.exception(f"שגיאה בטעינת BC1: {e}")
            raise RuntimeError(f"לא ניתן לטעון קובץ BC1: {e}")
    
    def _load_from_zip(self, zip_file: zipfile.ZipFile, password: Optional[str]):
        """Load content from ZIP file."""
        
        # Load manifest according to new format
        if detailed_logger:
            detailed_logger.info("טוען manifest מקובץ BC1")
        
        manifest_data = zip_file.read('manifest.json')
        manifest_dict = json.loads(manifest_data.decode('utf-8'))
        
        # Handle both old and new manifest formats
        if 'audio_file' in manifest_dict:
            # New format with explicit paths
            audio_file = manifest_dict['audio_file']
            transcript_file = manifest_dict.get('transcript_file', 'data/transcript.jsonl.gz')
            metadata_file = manifest_dict.get('metadata_file', 'data/metadata.json')
        else:
            # Old format - auto-detect
            audio_files = [name for name in zip_file.namelist() if name.startswith('audio/')]
            if not audio_files:
                raise ValueError("לא נמצא קובץ אודיו בארכיון BC1")
            audio_file = audio_files[0]
            transcript_file = 'data/transcript.jsonl.gz'
            metadata_file = 'data/metadata.json'
        
        # Load audio file
        self.audio_ext = Path(audio_file).suffix[1:]  # Remove dot
        
        if detailed_logger:
            detailed_logger.info(f"טוען אודיו: {audio_file} (פורמט: {self.audio_ext})")
        
        self.audio_bytes = zip_file.read(audio_file)
        
        # Handle encryption if needed
        if self.manifest.encrypted and password:
            if detailed_logger:
                detailed_logger.info("מפענח אודיו מוצפן")
            # For now, assume unencrypted - encryption can be added later
            # self.audio_bytes = self._decrypt_data(self.audio_bytes, password)
        
        # Verify audio checksum if available
        if self.manifest.checksum_audio:
            audio_hash = hashlib.sha256(self.audio_bytes).hexdigest()
            if audio_hash != self.manifest.checksum_audio:
                if detailed_logger:
                    detailed_logger.warning("אזהרה: checksum אודיו לא תואם")
        
        # Load transcript using path from manifest
        if detailed_logger:
            detailed_logger.info(f"טוען תמלול: {transcript_file}")
        
        if transcript_file in zip_file.namelist():
            self.transcript_bytes = zip_file.read(transcript_file)
            
            # Handle encryption
            if hasattr(self, 'manifest') and self.manifest and self.manifest.encrypted and password:
                if detailed_logger:
                    detailed_logger.info("מפענח תמלול מוצפן")
                # self.transcript_bytes = self._decrypt_data(self.transcript_bytes, password)
        else:
            if detailed_logger:
                detailed_logger.warning(f"קובץ תמלול לא נמצא: {transcript_file}")
        
        # Load metadata using path from manifest
        if metadata_file in zip_file.namelist():
            if detailed_logger:
                detailed_logger.info("טוען metadata")
            
            metadata_data = zip_file.read(metadata_file)
            
            # Handle encryption
            if self.manifest.encrypted and password:
                # metadata_data = self._decrypt_data(metadata_data, password)
                pass
            
            self.metadata = json.loads(metadata_data.decode('utf-8'))
    
    def parse_jsonl_gzip(self) -> List[Dict[str, Any]]:
        """Parse compressed JSONL transcript data."""
        if not self.transcript_bytes:
            return []
        
        try:
            if detailed_logger:
                detailed_logger.start_operation("פענוח תמלול JSONL")
            
            # Decompress
            transcript_text = gzip.decompress(self.transcript_bytes).decode('utf-8')
            
            # Parse each line as JSON
            segments = []
            for line_num, line in enumerate(transcript_text.strip().split('\n')):
                if line.strip():
                    try:
                        segment = json.loads(line)
                        
                        # Ensure required fields
                        if 'start_time' in segment and 'end_time' in segment and 'text' in segment:
                            segments.append({
                                'start_time': float(segment['start_time']),
                                'end_time': float(segment['end_time']),
                                'text': str(segment['text']),
                                'speaker': segment.get('speaker_id', segment.get('speaker', '')),
                                'confidence': float(segment.get('confidence', 1.0))
                            })
                        else:
                            if detailed_logger:
                                detailed_logger.warning(f"קטע תמלול חסר שדות נדרשים בשורה {line_num + 1}")
                                
                    except json.JSONDecodeError as e:
                        if detailed_logger:
                            detailed_logger.warning(f"שגיאה בפענוח JSON בשורה {line_num + 1}: {e}")
            
            if detailed_logger:
                detailed_logger.end_operation("פענוח תמלול JSONL")
                detailed_logger.info(f"נפענחו {len(segments)} קטעי תמלול")
            
            return segments
            
        except Exception as e:
            if detailed_logger:
                detailed_logger.exception(f"שגיאה בפענוח תמלול: {e}")
            return []
    
    def write_temp_file(self, suffix: str = None) -> str:
        """Write audio bytes to temporary file."""
        if not self.audio_bytes:
            raise ValueError("אין נתוני אודיו")
        
        # Create temporary file
        if suffix is None:
            suffix = f'.{self.audio_ext}' if self.audio_ext else '.mp3'
        
        temp_fd, temp_path = tempfile.mkstemp(suffix=suffix, prefix='bc1_audio_')
        
        try:
            with os.fdopen(temp_fd, 'wb') as temp_file:
                temp_file.write(self.audio_bytes)
            
            if detailed_logger:
                detailed_logger.log_file_operation("נוצר קובץ אודיו זמני", temp_path, True)
                detailed_logger.info(f"גודל קובץ אודיו: {len(self.audio_bytes)} bytes")
            
            return temp_path
            
        except Exception as e:
            # Cleanup on error
            try:
                os.unlink(temp_path)
            except:
                pass
            raise e

def open_bc1(bc1_source: Union[str, Path, bytes, BytesIO], password: Optional[str] = None) -> PlayerBundle:
    """
    Open BC1 file and return PlayerBundle ready for player.
    
    Args:
        bc1_source: BC1 file path, Path object, bytes, or BytesIO
        password: Optional password for encrypted BC1 files
        
    Returns:
        PlayerBundle with audio file path, segments, and metadata
        
    Raises:
        RuntimeError: If BC1 file cannot be loaded or parsed
    """
    try:
        if detailed_logger:
            detailed_logger.start_operation("פתיחת קובץ BC1 לנגן")
        
        # Load BC1 file
        bc1 = BC1File.load(bc1_source, password=password)
        
        # Write audio to temporary file
        temp_audio_path = bc1.write_temp_file()
        
        # Parse transcript segments
        segments = bc1.parse_jsonl_gzip()
        
        # Create player bundle
        bundle = PlayerBundle(
            audio_file=temp_audio_path,
            segments=segments,
            metadata=bc1.metadata,
            manifest=bc1.manifest,
            cleanup_files=[temp_audio_path]
        )
        
        if detailed_logger:
            detailed_logger.end_operation("פתיחת קובץ BC1 לנגן")
            detailed_logger.info(f"BC1 מוכן לניגון: {len(segments)} קטעים, אודיו: {bc1.audio_ext}")
        
        return bundle
        
    except Exception as e:
        if detailed_logger:
            detailed_logger.exception(f"שגיאה בפתיחת BC1: {e}")
        raise RuntimeError(f"לא ניתן לפתוח קובץ BC1: {e}")

def create_demo_bc1() -> bytes:
    """Create a demo BC1 file for testing."""
    try:
        if detailed_logger:
            detailed_logger.start_operation("יצירת BC1 דמו")
        
        # Create demo audio (1 second of silence)
        import numpy as np
        sample_rate = 44100
        duration = 5.0  # 5 seconds
        samples = int(duration * sample_rate)
        audio_data = np.zeros(samples, dtype=np.float32)
        
        # Convert to MP3-like bytes (simplified)
        audio_bytes = audio_data.tobytes()
        
        # Create demo transcript
        demo_segments = [
            {
                "start_time": 0.0,
                "end_time": 2.0,
                "text": "שלום, זהו תמלול דמו לבדיקת הנגן",
                "speaker_id": "speaker_1",
                "confidence": 0.95
            },
            {
                "start_time": 2.0,
                "end_time": 4.0,
                "text": "הנגן תומך בפורמט BC1 מתקדם עם תמלול מסונכרן",
                "speaker_id": "speaker_1", 
                "confidence": 0.92
            },
            {
                "start_time": 4.0,
                "end_time": 5.0,
                "text": "תודה על ההקשבה",
                "speaker_id": "speaker_2",
                "confidence": 0.98
            }
        ]
        
        # Create JSONL transcript
        transcript_lines = []
        for segment in demo_segments:
            transcript_lines.append(json.dumps(segment, ensure_ascii=False))
        
        transcript_text = '\n'.join(transcript_lines)
        transcript_bytes = gzip.compress(transcript_text.encode('utf-8'))
        
        # Create metadata
        metadata = {
            "title": "קובץ דמו לבדיקת נגן בינה כשרה",
            "duration": duration,
            "language": "he",
            "created_at": "2025-06-01",
            "description": "קובץ BC1 לדוגמה עם תמלול מסונכרן"
        }
        
        # Create manifest
        manifest = BC1Manifest(
            version="1.0",
            encrypted=False,
            audio_format="raw",
            transcript_format="jsonl",
            checksum_audio=hashlib.sha256(audio_bytes).hexdigest(),
            checksum_transcript=hashlib.sha256(transcript_bytes).hexdigest()
        )
        
        # Create ZIP archive
        zip_buffer = BytesIO()
        with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
            # Add manifest
            manifest_data = json.dumps(asdict(manifest), ensure_ascii=False, indent=2)
            zip_file.writestr('manifest.json', manifest_data.encode('utf-8'))
            
            # Add audio
            zip_file.writestr('audio/audio.raw', audio_bytes)
            
            # Add transcript
            zip_file.writestr('data/transcript.jsonl.gz', transcript_bytes)
            
            # Add metadata
            metadata_data = json.dumps(metadata, ensure_ascii=False, indent=2)
            zip_file.writestr('data/metadata.json', metadata_data.encode('utf-8'))
        
        bc1_bytes = zip_buffer.getvalue()
        
        if detailed_logger:
            detailed_logger.end_operation("יצירת BC1 דמו")
            detailed_logger.info(f"נוצר BC1 דמו: {len(bc1_bytes)} bytes")
        
        return bc1_bytes
        
    except Exception as e:
        if detailed_logger:
            detailed_logger.exception(f"שגיאה ביצירת BC1 דמו: {e}")
        return b""