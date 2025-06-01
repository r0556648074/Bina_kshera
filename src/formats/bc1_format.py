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
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict

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
    tags: List[str] = None
    speaker_info: Dict[str, str] = None

@dataclass
class BC1Manifest:
    """BC1 file manifest."""
    version: str = "1.0"
    encrypted: bool = False
    audio_format: str = "opus"
    transcript_format: str = "jsonl"
    checksum_audio: str = ""
    checksum_transcript: str = ""
    flags: Dict[str, Any] = None

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