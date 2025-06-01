"""
Transcript display widget with synchronized highlighting and navigation.

This widget displays transcript text with time-synchronized highlighting,
clickable segments for navigation, and search functionality.
"""

import logging
from typing import Optional, List, Dict, Any
import bisect

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, QLabel, 
    QLineEdit, QPushButton, QScrollArea, QFrame, QSizePolicy
)
from PySide6.QtCore import Qt, Signal, QTimer, pyqtSignal
from PySide6.QtGui import (
    QTextCursor, QTextCharFormat, QColor, QFont, 
    QTextDocument, QTextOption, QPalette
)

from engine.file_handler import TranscriptData, TranscriptSegment

logger = logging.getLogger(__name__)

class TranscriptSegmentWidget(QFrame):
    """Widget for displaying a single transcript segment."""
    
    clicked = Signal(float)  # Emitted with start time when clicked
    
    def __init__(self, segment: TranscriptSegment, parent=None):
        super().__init__(parent)
        
        self.segment = segment
        self.is_active = False
        
        # Setup frame
        self.setFrameStyle(QFrame.Shape.Box)
        self.setLineWidth(1)
        self.setContentsMargins(5, 5, 5, 5)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        
        # Layout
        layout = QVBoxLayout(self)
        layout.setSpacing(2)
        
        # Time info
        time_label = QLabel(self._format_time_range(segment.start_time, segment.end_time))
        time_label.setFont(QFont("Arial", 9))
        time_label.setStyleSheet("color: #666666;")
        layout.addWidget(time_label)
        
        # Speaker info (if available)
        if segment.speaker:
            speaker_label = QLabel(f"Speaker: {segment.speaker}")
            speaker_label.setFont(QFont("Arial", 9, QFont.Weight.Bold))
            speaker_label.setStyleSheet("color: #333333;")
            layout.addWidget(speaker_label)
        
        # Text content
        text_label = QLabel(segment.text)
        text_label.setWordWrap(True)
        text_label.setFont(QFont("Arial", 10))
        text_label.setStyleSheet("color: #000000;")
        layout.addWidget(text_label)
        
        # Confidence info (if available)
        if segment.confidence is not None:
            conf_label = QLabel(f"Confidence: {segment.confidence:.1%}")
            conf_label.setFont(QFont("Arial", 8))
            conf_label.setStyleSheet("color: #888888;")
            layout.addWidget(conf_label)
        
        # Update appearance
        self._update_appearance()
    
    def _format_time_range(self, start: float, end: float) -> str:
        """Format time range for display."""
        start_str = self._format_time(start)
        end_str = self._format_time(end)
        return f"{start_str} - {end_str}"
    
    def _format_time(self, seconds: float) -> str:
        """Format seconds to MM:SS format."""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
    
    def set_active(self, active: bool):
        """Set whether this segment is currently active."""
        if self.is_active != active:
            self.is_active = active
            self._update_appearance()
    
    def _update_appearance(self):
        """Update visual appearance based on state."""
        if self.is_active:
            self.setStyleSheet("""
                QFrame {
                    background-color: #E3F2FD;
                    border: 2px solid #2196F3;
                    border-radius: 4px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: #FFFFFF;
                    border: 1px solid #CCCCCC;
                    border-radius: 4px;
                }
                QFrame:hover {
                    background-color: #F5F5F5;
                    border: 1px solid #999999;
                }
            """)
    
    def mousePressEvent(self, event):
        """Handle mouse click to emit seek signal."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.clicked.emit(self.segment.start_time)
        super().mousePressEvent(event)

class TranscriptWidget(QWidget):
    """Widget for displaying transcript with synchronized highlighting."""
    
    # Signals
    seek_requested = Signal(float)  # Emitted when user clicks on a segment
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        # Data
        self.transcript_data: Optional[TranscriptData] = None
        self.segment_widgets: List[TranscriptSegmentWidget] = []
        self.current_position: float = 0.0
        self.active_segment_index: Optional[int] = None
        
        # Setup UI
        self.setMinimumWidth(300)
        self._setup_ui()
        
        logger.info("Transcript widget initialized")
    
    def _setup_ui(self):
        """Setup the user interface."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Header
        header_layout = QHBoxLayout()
        
        self.title_label = QLabel("Transcript")
        self.title_label.setFont(QFont("Arial", 12, QFont.Weight.Bold))
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # Segment count label
        self.count_label = QLabel("No transcript")
        self.count_label.setFont(QFont("Arial", 9))
        self.count_label.setStyleSheet("color: #666666;")
        header_layout.addWidget(self.count_label)
        
        layout.addLayout(header_layout)
        
        # Search box (for future implementation)
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search transcript...")
        self.search_input.setVisible(False)  # Hide for now
        search_layout.addWidget(self.search_input)
        
        self.search_button = QPushButton("Search")
        self.search_button.setVisible(False)  # Hide for now
        search_layout.addWidget(self.search_button)
        
        layout.addLayout(search_layout)
        
        # Scroll area for transcript segments
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Container widget for segments
        self.segments_container = QWidget()
        self.segments_layout = QVBoxLayout(self.segments_container)
        self.segments_layout.setSpacing(8)
        self.segments_layout.addStretch()  # Push segments to top
        
        self.scroll_area.setWidget(self.segments_container)
        layout.addWidget(self.scroll_area, 1)  # Take remaining space
        
        # No transcript message
        self.no_transcript_label = QLabel("No transcript available.\n\nLoad an audio file with an associated transcript file.")
        self.no_transcript_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.no_transcript_label.setStyleSheet("color: #999999;")
        self.no_transcript_label.setWordWrap(True)
        layout.addWidget(self.no_transcript_label)
        
        # Initially show no transcript message
        self._show_no_transcript(True)
    
    def set_transcript(self, transcript_data: TranscriptData):
        """Set transcript data for display."""
        try:
            self.transcript_data = transcript_data
            self._rebuild_transcript_display()
            logger.info(f"Transcript set with {len(transcript_data.segments)} segments")
            
        except Exception as e:
            logger.error(f"Error setting transcript: {e}")
    
    def clear_transcript(self):
        """Clear the transcript display."""
        self.transcript_data = None
        self.segment_widgets.clear()
        self.active_segment_index = None
        self._clear_segments()
        self._show_no_transcript(True)
        logger.info("Transcript cleared")
    
    def set_position(self, position: float):
        """Update current position and highlight active segment."""
        self.current_position = position
        self._update_active_segment()
    
    def _rebuild_transcript_display(self):
        """Rebuild the transcript display with current data."""
        if not self.transcript_data:
            self.clear_transcript()
            return
        
        # Clear existing segments
        self._clear_segments()
        
        # Create segment widgets
        self.segment_widgets = []
        
        for segment in self.transcript_data.segments:
            segment_widget = TranscriptSegmentWidget(segment)
            segment_widget.clicked.connect(self._on_segment_clicked)
            
            self.segment_widgets.append(segment_widget)
            
            # Insert before the stretch
            self.segments_layout.insertWidget(
                self.segments_layout.count() - 1, 
                segment_widget
            )
        
        # Update UI state
        segment_count = len(self.transcript_data.segments)
        self.count_label.setText(f"{segment_count} segments")
        
        # Show transcript area
        self._show_no_transcript(False)
        
        # Update active segment
        self._update_active_segment()
    
    def _clear_segments(self):
        """Clear all segment widgets."""
        # Remove all widgets except the stretch
        while self.segments_layout.count() > 1:
            item = self.segments_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.segment_widgets.clear()
    
    def _show_no_transcript(self, show: bool):
        """Show or hide the no transcript message."""
        self.no_transcript_label.setVisible(show)
        self.scroll_area.setVisible(not show)
        
        if show:
            self.count_label.setText("No transcript")
    
    def _update_active_segment(self):
        """Update which segment is currently active based on position."""
        if not self.transcript_data or not self.segment_widgets:
            return
        
        # Find the segment that contains the current position
        active_index = None
        
        for i, segment in enumerate(self.transcript_data.segments):
            if segment.start_time <= self.current_position <= segment.end_time:
                active_index = i
                break
        
        # Update segment highlighting
        if active_index != self.active_segment_index:
            # Deactivate previous segment
            if (self.active_segment_index is not None and 
                0 <= self.active_segment_index < len(self.segment_widgets)):
                self.segment_widgets[self.active_segment_index].set_active(False)
            
            # Activate new segment
            self.active_segment_index = active_index
            if (self.active_segment_index is not None and 
                0 <= self.active_segment_index < len(self.segment_widgets)):
                self.segment_widgets[self.active_segment_index].set_active(True)
                
                # Scroll to active segment
                self._scroll_to_segment(self.active_segment_index)
    
    def _scroll_to_segment(self, segment_index: int):
        """Scroll to make the specified segment visible."""
        if 0 <= segment_index < len(self.segment_widgets):
            segment_widget = self.segment_widgets[segment_index]
            
            # Ensure the widget is visible in the scroll area
            self.scroll_area.ensureWidgetVisible(
                segment_widget, 
                50,  # xMargin
                50   # yMargin
            )
    
    def _on_segment_clicked(self, start_time: float):
        """Handle segment click for seeking."""
        self.seek_requested.emit(start_time)
        logger.debug(f"Seek requested to time: {start_time:.2f}s")
    
    def search_text(self, query: str) -> List[int]:
        """Search for text in transcript segments."""
        if not self.transcript_data or not query.strip():
            return []
        
        query = query.lower()
        matching_indices = []
        
        for i, segment in enumerate(self.transcript_data.segments):
            if query in segment.text.lower():
                matching_indices.append(i)
        
        return matching_indices
    
    def highlight_search_results(self, query: str):
        """Highlight search results in transcript."""
        # TODO: Implement search highlighting
        # This would involve modifying the segment widgets to highlight matching text
        pass
    
    def get_segment_at_time(self, time: float) -> Optional[TranscriptSegment]:
        """Get the transcript segment at a specific time."""
        if not self.transcript_data:
            return None
        
        for segment in self.transcript_data.segments:
            if segment.start_time <= time <= segment.end_time:
                return segment
        
        return None
    
    def get_current_segment(self) -> Optional[TranscriptSegment]:
        """Get the currently active segment."""
        return self.get_segment_at_time(self.current_position)
