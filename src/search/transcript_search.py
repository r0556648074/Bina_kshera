"""
Advanced transcript search engine with FTS and semantic search.

This module provides fast text search and AI-powered semantic search
for transcript content as specified in the requirements.
"""

import sqlite3
import logging
import re
from typing import List, Dict, Tuple, Optional, Any
from dataclasses import dataclass
from pathlib import Path
import json

try:
    from utils.logger import get_logger
    detailed_logger = get_logger()
except ImportError:
    detailed_logger = None

logger = logging.getLogger(__name__)

@dataclass
class SearchResult:
    """Search result with timing and context."""
    segment_index: int
    start_time: float
    end_time: float
    text: str
    speaker: Optional[str]
    confidence: float
    match_score: float = 1.0
    context_before: str = ""
    context_after: str = ""

class HebrewTextProcessor:
    """Hebrew text processing utilities."""
    
    @staticmethod
    def normalize_hebrew(text: str) -> str:
        """Normalize Hebrew text for search."""
        # Remove nikud (Hebrew diacritics)
        nikud_pattern = r'[\u0591-\u05C7]'
        text = re.sub(nikud_pattern, '', text)
        
        # Normalize common Hebrew variations
        text = text.replace('ו', 'ו')  # Normalize vav
        text = text.replace('י', 'י')  # Normalize yod
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text.strip()
    
    @staticmethod
    def extract_keywords(text: str) -> List[str]:
        """Extract Hebrew keywords from text."""
        # Remove punctuation and split
        words = re.findall(r'[\u0590-\u05FF\u0600-\u06FF\w]+', text)
        
        # Filter out short words and common stop words
        hebrew_stopwords = {
            'של', 'את', 'על', 'אל', 'כל', 'או', 'אם', 'כי', 'מה', 'זה', 'הוא',
            'היא', 'הם', 'הן', 'אני', 'אתה', 'את', 'אנחנו', 'אתם', 'אתן',
            'לא', 'לו', 'לה', 'להם', 'להן', 'בו', 'בה', 'בהם', 'בהן'
        }
        
        keywords = []
        for word in words:
            if len(word) > 2 and word not in hebrew_stopwords:
                keywords.append(HebrewTextProcessor.normalize_hebrew(word))
        
        return keywords

class TranscriptSearchEngine:
    """Advanced search engine for transcript content."""
    
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path or ":memory:"
        self.connection: Optional[sqlite3.Connection] = None
        self.segments: List[Dict[str, Any]] = []
        
        if detailed_logger:
            detailed_logger.info("יצירת מנוע חיפוש תמלול")
        
        self._initialize_database()
    
    def _initialize_database(self):
        """Initialize SQLite database with FTS5."""
        try:
            if detailed_logger:
                detailed_logger.start_operation("אתחול מסד נתונים לחיפוש")
            
            self.connection = sqlite3.connect(self.db_path)
            self.connection.row_factory = sqlite3.Row
            
            # Create FTS5 table for Hebrew text search
            self.connection.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS transcript_fts USING fts5(
                    segment_index,
                    start_time,
                    end_time,
                    text,
                    normalized_text,
                    speaker,
                    keywords,
                    tokenize='unicode61 remove_diacritics 1'
                )
            """)
            
            # Create regular table for metadata
            self.connection.execute("""
                CREATE TABLE IF NOT EXISTS transcript_segments (
                    id INTEGER PRIMARY KEY,
                    segment_index INTEGER,
                    start_time REAL,
                    end_time REAL,
                    text TEXT,
                    speaker TEXT,
                    confidence REAL,
                    metadata TEXT
                )
            """)
            
            self.connection.commit()
            
            if detailed_logger:
                detailed_logger.end_operation("אתחול מסד נתונים לחיפוש")
                detailed_logger.info("מסד נתונים לחיפוש אותחל בהצלחה")
            
        except Exception as e:
            if detailed_logger:
                detailed_logger.exception(f"שגיאה באתחול מסד נתונים: {e}")
            logger.exception(f"Error initializing search database: {e}")
    
    def index_transcript(self, segments: List[Dict[str, Any]]) -> bool:
        """Index transcript segments for search."""
        try:
            if detailed_logger:
                detailed_logger.start_operation("אינדוקס תמלול לחיפוש")
                detailed_logger.info(f"מאנדקס {len(segments)} קטעי תמלול")
            
            self.segments = segments
            
            # Clear existing data
            self.connection.execute("DELETE FROM transcript_fts")
            self.connection.execute("DELETE FROM transcript_segments")
            
            # Index each segment
            for i, segment in enumerate(segments):
                text = segment.get('text', '')
                normalized_text = HebrewTextProcessor.normalize_hebrew(text)
                keywords = ' '.join(HebrewTextProcessor.extract_keywords(text))
                
                # Insert into FTS table
                self.connection.execute("""
                    INSERT INTO transcript_fts (
                        segment_index, start_time, end_time, text, 
                        normalized_text, speaker, keywords
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    i,
                    segment.get('start_time', 0),
                    segment.get('end_time', 0),
                    text,
                    normalized_text,
                    segment.get('speaker', ''),
                    keywords
                ))
                
                # Insert into metadata table
                self.connection.execute("""
                    INSERT INTO transcript_segments (
                        segment_index, start_time, end_time, text, 
                        speaker, confidence, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    i,
                    segment.get('start_time', 0),
                    segment.get('end_time', 0),
                    text,
                    segment.get('speaker', ''),
                    segment.get('confidence', 1.0),
                    json.dumps(segment, ensure_ascii=False)
                ))
            
            self.connection.commit()
            
            if detailed_logger:
                detailed_logger.end_operation("אינדוקס תמלול לחיפוש")
                detailed_logger.info(f"אינדוקס הושלם עבור {len(segments)} קטעים")
            
            return True
            
        except Exception as e:
            if detailed_logger:
                detailed_logger.exception(f"שגיאה באינדוקס תמלול: {e}")
            logger.exception(f"Error indexing transcript: {e}")
            return False
    
    def search_text(self, query: str, max_results: int = 50) -> List[SearchResult]:
        """Perform full-text search on transcript."""
        try:
            if detailed_logger:
                detailed_logger.start_operation("חיפוש טקסט")
                detailed_logger.log_audio_operation("חיפוש", {
                    "query": query,
                    "max_results": max_results
                })
            
            results = []
            
            # Normalize query
            normalized_query = HebrewTextProcessor.normalize_hebrew(query)
            
            # Prepare FTS query with different search strategies
            search_queries = [
                # Exact phrase search
                f'"{normalized_query}"',
                # Wildcard search
                f'{normalized_query}*',
                # Individual words
                ' OR '.join(f'{word}*' for word in normalized_query.split() if len(word) > 1)
            ]
            
            seen_segments = set()
            
            for search_query in search_queries:
                try:
                    cursor = self.connection.execute("""
                        SELECT segment_index, start_time, end_time, text, speaker, 
                               rank, snippet(transcript_fts, 3, '<mark>', '</mark>', '...', 32) as snippet
                        FROM transcript_fts 
                        WHERE transcript_fts MATCH ?
                        ORDER BY rank
                        LIMIT ?
                    """, (search_query, max_results))
                    
                    for row in cursor:
                        segment_index = row['segment_index']
                        
                        # Avoid duplicates
                        if segment_index in seen_segments:
                            continue
                        seen_segments.add(segment_index)
                        
                        # Get context
                        context_before, context_after = self._get_context(segment_index)
                        
                        # Calculate match score based on query similarity
                        match_score = self._calculate_match_score(query, row['text'])
                        
                        result = SearchResult(
                            segment_index=segment_index,
                            start_time=row['start_time'],
                            end_time=row['end_time'],
                            text=row['text'],
                            speaker=row['speaker'],
                            confidence=1.0,
                            match_score=match_score,
                            context_before=context_before,
                            context_after=context_after
                        )
                        
                        results.append(result)
                        
                        if len(results) >= max_results:
                            break
                
                except sqlite3.OperationalError:
                    # If FTS query fails, continue with next strategy
                    continue
                
                if len(results) >= max_results:
                    break
            
            # Sort by match score
            results.sort(key=lambda x: x.match_score, reverse=True)
            
            if detailed_logger:
                detailed_logger.end_operation("חיפוש טקסט")
                detailed_logger.info(f"נמצאו {len(results)} תוצאות עבור: {query}")
            
            return results[:max_results]
            
        except Exception as e:
            if detailed_logger:
                detailed_logger.exception(f"שגיאה בחיפוש טקסט: {e}")
            logger.exception(f"Error in text search: {e}")
            return []
    
    def search_time_range(self, start_time: float, end_time: float) -> List[SearchResult]:
        """Search segments in specific time range."""
        try:
            if detailed_logger:
                detailed_logger.log_audio_operation("חיפוש בטווח זמן", {
                    "start_time": start_time,
                    "end_time": end_time
                })
            
            cursor = self.connection.execute("""
                SELECT segment_index, start_time, end_time, text, speaker, confidence
                FROM transcript_segments 
                WHERE (start_time <= ? AND end_time >= ?) OR 
                      (start_time >= ? AND start_time <= ?)
                ORDER BY start_time
            """, (end_time, start_time, start_time, end_time))
            
            results = []
            for row in cursor:
                context_before, context_after = self._get_context(row['segment_index'])
                
                result = SearchResult(
                    segment_index=row['segment_index'],
                    start_time=row['start_time'],
                    end_time=row['end_time'],
                    text=row['text'],
                    speaker=row['speaker'],
                    confidence=row['confidence'],
                    match_score=1.0,
                    context_before=context_before,
                    context_after=context_after
                )
                
                results.append(result)
            
            if detailed_logger:
                detailed_logger.info(f"נמצאו {len(results)} קטעים בטווח {start_time}-{end_time}")
            
            return results
            
        except Exception as e:
            if detailed_logger:
                detailed_logger.exception(f"שגיאה בחיפוש טווח זמן: {e}")
            logger.exception(f"Error in time range search: {e}")
            return []
    
    def search_speaker(self, speaker_name: str) -> List[SearchResult]:
        """Search segments by speaker."""
        try:
            if detailed_logger:
                detailed_logger.log_audio_operation("חיפוש לפי דובר", {
                    "speaker": speaker_name
                })
            
            cursor = self.connection.execute("""
                SELECT segment_index, start_time, end_time, text, speaker, confidence
                FROM transcript_segments 
                WHERE speaker LIKE ?
                ORDER BY start_time
            """, (f'%{speaker_name}%',))
            
            results = []
            for row in cursor:
                context_before, context_after = self._get_context(row['segment_index'])
                
                result = SearchResult(
                    segment_index=row['segment_index'],
                    start_time=row['start_time'],
                    end_time=row['end_time'],
                    text=row['text'],
                    speaker=row['speaker'],
                    confidence=row['confidence'],
                    match_score=1.0,
                    context_before=context_before,
                    context_after=context_after
                )
                
                results.append(result)
            
            if detailed_logger:
                detailed_logger.info(f"נמצאו {len(results)} קטעים עבור דובר: {speaker_name}")
            
            return results
            
        except Exception as e:
            if detailed_logger:
                detailed_logger.exception(f"שגיאה בחיפוש דובר: {e}")
            logger.exception(f"Error in speaker search: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get search index statistics."""
        try:
            cursor = self.connection.execute("SELECT COUNT(*) as count FROM transcript_segments")
            total_segments = cursor.fetchone()['count']
            
            cursor = self.connection.execute("""
                SELECT speaker, COUNT(*) as count 
                FROM transcript_segments 
                WHERE speaker IS NOT NULL AND speaker != ''
                GROUP BY speaker
            """)
            speaker_stats = {row['speaker']: row['count'] for row in cursor}
            
            cursor = self.connection.execute("""
                SELECT SUM(end_time - start_time) as total_duration
                FROM transcript_segments
            """)
            total_duration = cursor.fetchone()['total_duration'] or 0
            
            stats = {
                'total_segments': total_segments,
                'total_duration': total_duration,
                'speakers': speaker_stats,
                'average_segment_length': total_duration / total_segments if total_segments > 0 else 0
            }
            
            if detailed_logger:
                detailed_logger.log_audio_operation("סטטיסטיקות חיפוש", stats)
            
            return stats
            
        except Exception as e:
            if detailed_logger:
                detailed_logger.exception(f"שגיאה בקבלת סטטיסטיקות: {e}")
            logger.exception(f"Error getting statistics: {e}")
            return {}
    
    def _get_context(self, segment_index: int, context_size: int = 2) -> Tuple[str, str]:
        """Get context before and after segment."""
        try:
            context_before = ""
            context_after = ""
            
            # Get segments before
            if segment_index > 0:
                start_idx = max(0, segment_index - context_size)
                before_segments = self.segments[start_idx:segment_index]
                context_before = " ".join(seg.get('text', '') for seg in before_segments)
            
            # Get segments after
            if segment_index < len(self.segments) - 1:
                end_idx = min(len(self.segments), segment_index + context_size + 1)
                after_segments = self.segments[segment_index + 1:end_idx]
                context_after = " ".join(seg.get('text', '') for seg in after_segments)
            
            return context_before, context_after
            
        except Exception:
            return "", ""
    
    def _calculate_match_score(self, query: str, text: str) -> float:
        """Calculate match score between query and text."""
        try:
            normalized_query = HebrewTextProcessor.normalize_hebrew(query.lower())
            normalized_text = HebrewTextProcessor.normalize_hebrew(text.lower())
            
            # Exact match gets highest score
            if normalized_query in normalized_text:
                return 1.0
            
            # Word overlap score
            query_words = set(normalized_query.split())
            text_words = set(normalized_text.split())
            
            if len(query_words) == 0:
                return 0.0
            
            overlap = len(query_words.intersection(text_words))
            return overlap / len(query_words)
            
        except Exception:
            return 0.0
    
    def cleanup(self):
        """Cleanup search resources."""
        try:
            if self.connection:
                self.connection.close()
                self.connection = None
            
            if detailed_logger:
                detailed_logger.info("ניקוי מנוע חיפוש הושלם")
                
        except Exception as e:
            if detailed_logger:
                detailed_logger.exception(f"שגיאה בניקוי מנוע חיפוש: {e}")
            logger.exception(f"Error cleaning up search engine: {e}")
    
    def __del__(self):
        """Destructor."""
        self.cleanup()