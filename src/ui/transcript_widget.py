"""
Advanced transcript widget with real-time highlighting and search.

This widget displays synchronized transcript with word-level highlighting,
search capabilities, and speaker diarization as specified in requirements.
"""

import logging
from typing import List, Dict, Optional, Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLineEdit, 
    QPushButton, QLabel, QScrollArea, QFrame, QSplitter
)
from PySide6.QtCore import Qt, Signal, QTimer, QRect
from PySide6.QtGui import (
    QTextCursor, QTextCharFormat, QColor, QFont, QTextDocument, 
    QPalette, QTextBlockFormat, QPainter, QLinearGradient, QBrush
)

try:
    from utils.logger import get_logger
    detailed_logger = get_logger()
except ImportError:
    detailed_logger = None

logger = logging.getLogger(__name__)

class TranscriptDisplay(QTextEdit):
    """Custom text display for transcript with highlighting."""
    
    segmentClicked = Signal(float)  # Emit start time when segment clicked
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Setup display properties
        self.setReadOnly(True)
        self.setLineWrapMode(QTextEdit.LineWrapMode.WidgetWidth)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        
        # Transcript data
        self.segments: List[Dict[str, Any]] = []
        self.current_segment_index: int = -1
        self.search_results: List[int] = []
        self.current_search_index: int = -1
        
        # Highlighting formats
        self.setup_formats()
        
        # Auto-scroll settings
        self.auto_scroll_enabled = True
        self.free_scroll_mode = False
        
        if detailed_logger:
            detailed_logger.info("יצירת תצוגת תמלול מתקדמת")
    
    def setup_formats(self):
        """Setup text formatting for different states."""
        # Normal text format
        self.normal_format = QTextCharFormat()
        self.normal_format.setForeground(QColor(200, 200, 200))
        self.normal_format.setFont(QFont("Arial", 12))
        
        # Current segment format (highlighted)
        self.current_format = QTextCharFormat()
        self.current_format.setForeground(QColor(255, 255, 255))
        self.current_format.setBackground(QColor(78, 205, 196, 150))
        self.current_format.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        
        # Search highlight format
        self.search_format = QTextCharFormat()
        self.search_format.setForeground(QColor(0, 0, 0))
        self.search_format.setBackground(QColor(255, 255, 0, 200))
        self.search_format.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        
        # Speaker name format
        self.speaker_format = QTextCharFormat()
        self.speaker_format.setForeground(QColor(199, 125, 255))
        self.speaker_format.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        
        # Time format
        self.time_format = QTextCharFormat()
        self.time_format.setForeground(QColor(150, 150, 150))
        self.time_format.setFont(QFont("Courier", 9))
    
    def set_transcript_segments(self, segments: List[Dict[str, Any]]):
        """Set transcript segments and rebuild display."""
        try:
            if detailed_logger:
                detailed_logger.start_operation("הגדרת קטעי תמלול")
                detailed_logger.info(f"מגדיר {len(segments)} קטעי תמלול")
            
            self.segments = segments
            self.rebuild_display()
            
            if detailed_logger:
                detailed_logger.end_operation("הגדרת קטעי תמלול")
            
        except Exception as e:
            if detailed_logger:
                detailed_logger.exception(f"שגיאה בהגדרת תמלול: {e}")
            logger.exception(f"Error setting transcript segments: {e}")
    
    def rebuild_display(self):
        """Rebuild the entire transcript display."""
        try:
            self.clear()
            
            if not self.segments:
                self.setPlainText("אין תמלול זמין.\nטען קובץ עם תמלול מסונכרן כדי לראות את הטקסט כאן.")
                return
            
            cursor = self.textCursor()
            
            for i, segment in enumerate(self.segments):
                # Store segment index in the text
                cursor.insertText(f"[{i}]", self.time_format)
                
                # Add time stamp
                start_time = segment.get('start_time', 0)
                end_time = segment.get('end_time', 0)
                time_text = f" [{self._format_time(start_time)} - {self._format_time(end_time)}]"
                cursor.insertText(time_text, self.time_format)
                
                # Add speaker if available
                speaker = segment.get('speaker', '')
                if speaker:
                    cursor.insertText(f" {speaker}: ", self.speaker_format)
                else:
                    cursor.insertText(" ", self.normal_format)
                
                # Add segment text
                text = segment.get('text', '')
                cursor.insertText(text, self.normal_format)
                
                # Add line break
                cursor.insertText("\n\n", self.normal_format)
            
            # Scroll to top
            self.moveCursor(QTextCursor.MoveOperation.Start)
            
            if detailed_logger:
                detailed_logger.info(f"תצוגת תמלול נבנתה מחדש עם {len(self.segments)} קטעים")
            
        except Exception as e:
            if detailed_logger:
                detailed_logger.exception(f"שגיאה בבניית תצוגה: {e}")
            logger.exception(f"Error rebuilding display: {e}")
    
    def highlight_current_segment(self, current_time: float):
        """Highlight current segment based on playback time."""
        try:
            # Find current segment
            new_segment_index = -1
            for i, segment in enumerate(self.segments):
                start_time = segment.get('start_time', 0)
                end_time = segment.get('end_time', 0)
                
                if start_time <= current_time <= end_time:
                    new_segment_index = i
                    break
            
            # Only update if segment changed
            if new_segment_index != self.current_segment_index:
                # Remove previous highlighting
                if self.current_segment_index >= 0:
                    self._unhighlight_segment(self.current_segment_index)
                
                # Highlight new segment
                if new_segment_index >= 0:
                    self._highlight_segment(new_segment_index)
                    
                    # Auto-scroll to current segment
                    if self.auto_scroll_enabled and not self.free_scroll_mode:
                        self._scroll_to_segment(new_segment_index)
                
                self.current_segment_index = new_segment_index
                
                if detailed_logger:
                    detailed_logger.log_audio_operation("הדגשת קטע נוכחי", {
                        "current_time": current_time,
                        "segment_index": new_segment_index,
                        "auto_scroll": self.auto_scroll_enabled
                    })
        
        except Exception as e:
            if detailed_logger:
                detailed_logger.exception(f"שגיאה בהדגשת קטע: {e}")
            logger.exception(f"Error highlighting segment: {e}")
    
    def _highlight_segment(self, segment_index: int):
        """Highlight specific segment."""
        try:
            document = self.document()
            cursor = QTextCursor(document)
            
            # Find segment in text by looking for [segment_index] marker
            text = document.toPlainText()
            marker = f"[{segment_index}]"
            start_pos = text.find(marker)
            
            if start_pos == -1:
                return
            
            # Find the actual text start (after time and speaker info)
            cursor.setPosition(start_pos)
            
            # Move to start of actual text content
            line_text = cursor.block().text()
            text_start = line_text.find(']', line_text.find(']') + 1)  # Find second ']'
            if text_start != -1:
                # Find speaker separator or use position after time
                if ':' in line_text[text_start:]:
                    text_start = line_text.find(':', text_start) + 1
                else:
                    text_start += 1
                
                # Move cursor to text start
                cursor.setPosition(start_pos + text_start)
                
                # Find text end (before next segment or end)
                next_marker = f"[{segment_index + 1}]"
                next_pos = text.find(next_marker, start_pos + 1)
                
                if next_pos == -1:
                    next_pos = len(text)
                
                # Select text content only
                text_content = text[cursor.position():next_pos].strip()
                cursor.setPosition(cursor.position())
                cursor.setPosition(cursor.position() + len(text_content), QTextCursor.MoveMode.KeepAnchor)
                
                # Apply highlighting
                cursor.setCharFormat(self.current_format)
        
        except Exception as e:
            logger.exception(f"Error highlighting segment {segment_index}: {e}")
    
    def _unhighlight_segment(self, segment_index: int):
        """Remove highlighting from specific segment."""
        try:
            document = self.document()
            cursor = QTextCursor(document)
            
            # Find segment in text
            text = document.toPlainText()
            marker = f"[{segment_index}]"
            start_pos = text.find(marker)
            
            if start_pos == -1:
                return
            
            # Similar logic to highlighting but apply normal format
            cursor.setPosition(start_pos)
            line_text = cursor.block().text()
            text_start = line_text.find(']', line_text.find(']') + 1)
            
            if text_start != -1:
                if ':' in line_text[text_start:]:
                    text_start = line_text.find(':', text_start) + 1
                else:
                    text_start += 1
                
                cursor.setPosition(start_pos + text_start)
                
                next_marker = f"[{segment_index + 1}]"
                next_pos = text.find(next_marker, start_pos + 1)
                
                if next_pos == -1:
                    next_pos = len(text)
                
                text_content = text[cursor.position():next_pos].strip()
                cursor.setPosition(cursor.position())
                cursor.setPosition(cursor.position() + len(text_content), QTextCursor.MoveMode.KeepAnchor)
                
                # Apply normal formatting
                cursor.setCharFormat(self.normal_format)
        
        except Exception as e:
            logger.exception(f"Error unhighlighting segment {segment_index}: {e}")
    
    def _scroll_to_segment(self, segment_index: int):
        """Scroll to make segment visible."""
        try:
            document = self.document()
            text = document.toPlainText()
            marker = f"[{segment_index}]"
            start_pos = text.find(marker)
            
            if start_pos != -1:
                cursor = QTextCursor(document)
                cursor.setPosition(start_pos)
                self.setTextCursor(cursor)
                self.ensureCursorVisible()
        
        except Exception as e:
            logger.exception(f"Error scrolling to segment {segment_index}: {e}")
    
    def search_text(self, query: str, highlight_all: bool = True) -> int:
        """Search for text and highlight results."""
        try:
            if detailed_logger:
                detailed_logger.start_operation("חיפוש בתמלול")
                detailed_logger.log_audio_operation("חיפוש טקסט", {"query": query})
            
            # Clear previous search results
            self.clear_search_highlights()
            self.search_results = []
            self.current_search_index = -1
            
            if not query.strip():
                return 0
            
            document = self.document()
            cursor = QTextCursor(document)
            
            # Find all occurrences
            while True:
                cursor = document.find(query, cursor)
                if cursor.isNull():
                    break
                
                # Store position
                self.search_results.append(cursor.position())
                
                # Highlight if requested
                if highlight_all:
                    cursor.setCharFormat(self.search_format)
            
            if detailed_logger:
                detailed_logger.end_operation("חיפוש בתמלול")
                detailed_logger.info(f"נמצאו {len(self.search_results)} תוצאות עבור: {query}")
            
            return len(self.search_results)
            
        except Exception as e:
            if detailed_logger:
                detailed_logger.exception(f"שגיאה בחיפוש: {e}")
            logger.exception(f"Error searching text: {e}")
            return 0
    
    def navigate_search_results(self, direction: int = 1) -> bool:
        """Navigate through search results."""
        try:
            if not self.search_results:
                return False
            
            # Update current index
            if self.current_search_index == -1:
                self.current_search_index = 0 if direction > 0 else len(self.search_results) - 1
            else:
                self.current_search_index += direction
                
                # Wrap around
                if self.current_search_index >= len(self.search_results):
                    self.current_search_index = 0
                elif self.current_search_index < 0:
                    self.current_search_index = len(self.search_results) - 1
            
            # Scroll to current result
            position = self.search_results[self.current_search_index]
            cursor = self.textCursor()
            cursor.setPosition(position)
            self.setTextCursor(cursor)
            self.ensureCursorVisible()
            
            if detailed_logger:
                detailed_logger.log_ui_operation("ניווט תוצאות חיפוש", "search_navigation",
                                               index=self.current_search_index,
                                               total=len(self.search_results))
            
            return True
            
        except Exception as e:
            if detailed_logger:
                detailed_logger.exception(f"שגיאה בניווט חיפוש: {e}")
            logger.exception(f"Error navigating search results: {e}")
            return False
    
    def clear_search_highlights(self):
        """Clear all search highlighting."""
        try:
            # Reset formatting by rebuilding - simple but effective
            if self.segments:
                self.rebuild_display()
                
                # Re-highlight current segment if any
                if self.current_segment_index >= 0:
                    self._highlight_segment(self.current_segment_index)
            
            if detailed_logger:
                detailed_logger.info("ניקוי הדגשות חיפוש")
                
        except Exception as e:
            logger.exception(f"Error clearing search highlights: {e}")
    
    def set_auto_scroll(self, enabled: bool):
        """Enable/disable auto-scroll."""
        self.auto_scroll_enabled = enabled
        if detailed_logger:
            detailed_logger.log_ui_operation("הגדרת גלילה אוטומטית", "auto_scroll", enabled=enabled)
    
    def set_free_scroll_mode(self, enabled: bool):
        """Enable/disable free scroll mode."""
        self.free_scroll_mode = enabled
        if detailed_logger:
            detailed_logger.log_ui_operation("מצב גלילה חופשית", "free_scroll", enabled=enabled)
    
    def mousePressEvent(self, event):
        """Handle mouse clicks on segments."""
        if event.button() == Qt.MouseButton.LeftButton:
            cursor = self.cursorForPosition(event.position().toPoint())
            position = cursor.position()
            
            # Find which segment was clicked
            text = self.document().toPlainText()
            
            # Find the segment index
            segment_index = self._find_segment_at_position(position, text)
            
            if segment_index >= 0 and segment_index < len(self.segments):
                start_time = self.segments[segment_index].get('start_time', 0)
                
                if detailed_logger:
                    detailed_logger.log_ui_operation("לחיצה על קטע תמלול", "segment_click",
                                                   segment_index=segment_index,
                                                   start_time=start_time)
                
                self.segmentClicked.emit(start_time)
        
        super().mousePressEvent(event)
    
    def _find_segment_at_position(self, position: int, text: str) -> int:
        """Find segment index at text position."""
        try:
            # Find all segment markers before this position
            text_before = text[:position]
            segment_markers = []
            
            for i in range(len(self.segments)):
                marker = f"[{i}]"
                marker_pos = text_before.rfind(marker)
                if marker_pos != -1:
                    segment_markers.append((i, marker_pos))
            
            # Return the highest segment index found
            if segment_markers:
                segment_markers.sort(key=lambda x: x[1], reverse=True)
                return segment_markers[0][0]
            
            return -1
            
        except Exception:
            return -1
    
    def _format_time(self, seconds: float) -> str:
        """Format time as MM:SS."""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"

class TranscriptWidget(QWidget):
    """Complete transcript widget with search and controls."""
    
    segmentClicked = Signal(float)
    searchRequested = Signal(str)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.transcript_display = TranscriptDisplay()
        self.search_line = QLineEdit()
        self.search_count_label = QLabel("0 תוצאות")
        
        self._setup_ui()
        self._connect_signals()
        
        if detailed_logger:
            detailed_logger.info("יצירת ווידג'ט תמלול מלא")
    
    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        
        # Search section
        search_frame = QFrame()
        search_frame.setFrameStyle(QFrame.Shape.StyledPanel)
        search_layout = QHBoxLayout(search_frame)
        
        search_label = QLabel("חיפוש:")
        self.search_line.setPlaceholderText("הקלד טקסט לחיפוש...")
        
        self.prev_button = QPushButton("◄")
        self.next_button = QPushButton("►")
        self.clear_button = QPushButton("נקה")
        
        self.auto_scroll_button = QPushButton("גלילה אוטומטית")
        self.auto_scroll_button.setCheckable(True)
        self.auto_scroll_button.setChecked(True)
        
        search_layout.addWidget(search_label)
        search_layout.addWidget(self.search_line)
        search_layout.addWidget(self.search_count_label)
        search_layout.addWidget(self.prev_button)
        search_layout.addWidget(self.next_button)
        search_layout.addWidget(self.clear_button)
        search_layout.addWidget(self.auto_scroll_button)
        
        # Style buttons
        button_style = """
            QPushButton {
                background-color: #E0D6F5;
                border: 1px solid #CFF0E8;
                border-radius: 6px;
                padding: 4px 8px;
                font-size: 11px;
                color: #2C3E50;
            }
            QPushButton:hover {
                background-color: #CFF0E8;
            }
            QPushButton:checked {
                background-color: #4CAF50;
                color: white;
            }
        """
        
        for btn in [self.prev_button, self.next_button, self.clear_button, self.auto_scroll_button]:
            btn.setStyleSheet(button_style)
        
        layout.addWidget(search_frame)
        layout.addWidget(self.transcript_display)
        
        # Set RTL layout
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
    
    def _connect_signals(self):
        """Connect widget signals."""
        self.search_line.textChanged.connect(self._on_search_text_changed)
        self.search_line.returnPressed.connect(self._on_search_enter)
        self.prev_button.clicked.connect(lambda: self.transcript_display.navigate_search_results(-1))
        self.next_button.clicked.connect(lambda: self.transcript_display.navigate_search_results(1))
        self.clear_button.clicked.connect(self._clear_search)
        self.auto_scroll_button.clicked.connect(self._toggle_auto_scroll)
        
        self.transcript_display.segmentClicked.connect(self.segmentClicked)
    
    def _on_search_text_changed(self, text: str):
        """Handle search text change."""
        if text.strip():
            count = self.transcript_display.search_text(text)
            self.search_count_label.setText(f"{count} תוצאות")
            
            # Enable/disable navigation buttons
            self.prev_button.setEnabled(count > 0)
            self.next_button.setEnabled(count > 0)
        else:
            self.transcript_display.clear_search_highlights()
            self.search_count_label.setText("0 תוצאות")
            self.prev_button.setEnabled(False)
            self.next_button.setEnabled(False)
    
    def _on_search_enter(self):
        """Handle enter key in search."""
        self.transcript_display.navigate_search_results(1)
    
    def _clear_search(self):
        """Clear search."""
        self.search_line.clear()
        self.transcript_display.clear_search_highlights()
    
    def _toggle_auto_scroll(self):
        """Toggle auto-scroll mode."""
        enabled = self.auto_scroll_button.isChecked()
        self.transcript_display.set_auto_scroll(enabled)
    
    def set_transcript_segments(self, segments: List[Dict[str, Any]]):
        """Set transcript segments."""
        self.transcript_display.set_transcript_segments(segments)
    
    def highlight_current_segment(self, current_time: float):
        """Highlight current segment."""
        self.transcript_display.highlight_current_segment(current_time)
    
    def search_text(self, query: str) -> int:
        """Search for text."""
        self.search_line.setText(query)
        return self.transcript_display.search_text(query)