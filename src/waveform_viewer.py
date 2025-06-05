"""
Waveform Viewer - תצוגת גלי קול אינטראקטיבית

מציג waveform אינטראקטיבי עם:
- קו אדום חי שמתעדכן לפי זמן ניגון
- אפשרות לחיצה לקפיצה למיקום
- זום ופאן
- הדגשת קטעי תמלול
"""

import numpy as np
import librosa
import pyqtgraph as pg
from pyqtgraph import PlotWidget, mkPen, mkBrush
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QSlider
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont
import logging
from typing import List, Dict, Any, Optional, Callable

class WaveformViewer(QWidget):
    """Widget לתצוגת waveform אינטראקטיבית."""
    
    # Signals
    position_clicked = Signal(float)  # נקלח על זמן ספציפי
    zoom_changed = Signal(float, float)  # טווח זום השתנה
    
    def __init__(self, parent=None):
        super().__init__(parent)
        
        self.audio_data = None
        self.sample_rate = 22050
        self.duration = 0.0
        self.current_position = 0.0
        self.transcript_segments = []
        
        # UI Components
        self.plot_widget = None
        self.position_line = None
        self.waveform_item = None
        self.segment_items = []
        
        # Configuration
        self.waveform_color = (0, 150, 255)  # כחול
        self.position_color = (255, 0, 0)    # אדום
        self.segment_color = (255, 255, 0, 100)  # צהוב שקוף
        
        self._setup_ui()
        self._setup_interaction()
        
        logging.info("Waveform Viewer אותחל")
    
    def _setup_ui(self):
        """יוצר את הממשק."""
        layout = QVBoxLayout()
        
        # כותרת
        title = QLabel("תצוגת גלי קול")
        title.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)
        
        # Plot widget
        self.plot_widget = PlotWidget()
        self.plot_widget.setBackground('white')
        self.plot_widget.setLabel('left', 'עוצמה')
        self.plot_widget.setLabel('bottom', 'זמן (שניות)')
        self.plot_widget.showGrid(x=True, y=True, alpha=0.3)
        
        # הגדרות עיצוב
        self.plot_widget.getAxis('left').setTextPen('black')
        self.plot_widget.getAxis('bottom').setTextPen('black')
        self.plot_widget.getAxis('left').setPen('black')
        self.plot_widget.getAxis('bottom').setPen('black')
        
        layout.addWidget(self.plot_widget)
        
        # בקרות
        controls_layout = QHBoxLayout()
        
        # כפתור זום איפוס
        self.reset_zoom_btn = QPushButton("איפוס זום")
        self.reset_zoom_btn.clicked.connect(self.reset_zoom)
        controls_layout.addWidget(self.reset_zoom_btn)
        
        # כפתור הצג קטעים
        self.toggle_segments_btn = QPushButton("הצג קטעי תמלול")
        self.toggle_segments_btn.setCheckable(True)
        self.toggle_segments_btn.setChecked(True)
        self.toggle_segments_btn.toggled.connect(self.toggle_segments)
        controls_layout.addWidget(self.toggle_segments_btn)
        
        # מידע נוכחי
        self.info_label = QLabel("לא נטען אודיו")
        self.info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        controls_layout.addWidget(self.info_label)
        
        controls_layout.addStretch()
        layout.addLayout(controls_layout)
        
        self.setLayout(layout)
    
    def _setup_interaction(self):
        """מגדיר אינטראקציה עם המשתמש."""
        # חיבור לקליקים
        self.plot_widget.scene().sigMouseClicked.connect(self._on_plot_clicked)
        
        # חיבור לשינויי טווח
        self.plot_widget.sigRangeChanged.connect(self._on_range_changed)
    
    def load_audio_file(self, file_path: str):
        """טוען קובץ אודיו ומציג את ה-waveform."""
        try:
            logging.info(f"טוען אודיו לתצוגת waveform: {file_path}")
            
            # טעינת אודיו
            self.audio_data, self.sample_rate = librosa.load(file_path, sr=None)
            self.duration = len(self.audio_data) / self.sample_rate
            
            logging.info(f"אודיו נטען: {self.duration:.1f}s, {self.sample_rate}Hz")
            
            # יצירת waveform
            self._create_waveform()
            
            # עדכון מידע
            self.info_label.setText(f"משך: {self.duration:.1f}s | דגימה: {self.sample_rate}Hz")
            
        except Exception as e:
            logging.error(f"שגיאה בטעינת אודיו לwaveform: {e}")
            self.info_label.setText(f"שגיאה: {e}")
    
    def _create_waveform(self):
        """יוצר תצוגת waveform."""
        if self.audio_data is None:
            return
        
        # ניקוי תצוגה קודמת
        self.plot_widget.clear()
        self.segment_items = []
        
        # דגימה למטה לביצועים טובים
        downsample_factor = max(1, len(self.audio_data) // 10000)
        downsampled_audio = self.audio_data[::downsample_factor]
        
        # יצירת ציר זמן
        time_axis = np.linspace(0, self.duration, len(downsampled_audio))
        
        # יצירת waveform
        self.waveform_item = self.plot_widget.plot(
            time_axis, 
            downsampled_audio,
            pen=mkPen(color=self.waveform_color, width=1)
        )
        
        # יצירת קו מיקום
        self.position_line = self.plot_widget.addLine(
            x=0, 
            pen=mkPen(color=self.position_color, width=2)
        )
        
        # הוספת קטעי תמלול אם יש
        if self.transcript_segments:
            self._add_transcript_segments()
        
        # הגדרת טווח תצוגה
        self.plot_widget.setXRange(0, self.duration)
        self.plot_widget.setYRange(np.min(downsampled_audio), np.max(downsampled_audio))
        
        logging.info("Waveform נוצר בהצלחה")
    
    def load_transcript(self, segments: List[Dict[str, Any]]):
        """טוען קטעי תמלול להצגה."""
        self.transcript_segments = segments
        
        if self.audio_data is not None:
            self._add_transcript_segments()
        
        logging.info(f"נטענו {len(segments)} קטעי תמלול לwaveform")
    
    def _add_transcript_segments(self):
        """מוסיף קטעי תמלול לתצוגה."""
        if not self.transcript_segments:
            return
        
        # ניקוי קטעים קודמים
        for item in self.segment_items:
            self.plot_widget.removeItem(item)
        self.segment_items = []
        
        # הוספת קטעים חדשים
        y_min, y_max = self.plot_widget.getViewBox().viewRange()[1]
        
        for segment in self.transcript_segments:
            start_time = segment["start_time"]
            end_time = segment["end_time"]
            
            # יצירת רקע לקטע
            segment_item = pg.LinearRegionItem(
                values=[start_time, end_time],
                brush=mkBrush(color=self.segment_color),
                movable=False
            )
            
            self.plot_widget.addItem(segment_item)
            self.segment_items.append(segment_item)
    
    def update_position(self, position_seconds: float):
        """מעדכן את מיקום הקו האדום."""
        self.current_position = position_seconds
        
        if self.position_line is not None:
            self.position_line.setValue(position_seconds)
    
    def _on_plot_clicked(self, event):
        """מטפל בלחיצה על הגרף."""
        if event.double():
            return  # מתעלם מלחיצה כפולה
        
        # המרת קואורדינטות לזמן
        view_box = self.plot_widget.getViewBox()
        scene_pos = event.scenePos()
        
        if self.plot_widget.sceneBoundingRect().contains(scene_pos):
            mouse_point = view_box.mapSceneToView(scene_pos)
            clicked_time = mouse_point.x()
            
            # וידוא שהזמן בטווח תקין
            if 0 <= clicked_time <= self.duration:
                logging.info(f"נלחץ על זמן: {clicked_time:.2f}s")
                self.position_clicked.emit(clicked_time)
    
    def _on_range_changed(self, view_box, range_info):
        """מטפל בשינוי טווח התצוגה."""
        x_range = range_info[0]
        start_time, end_time = x_range
        
        # עדכון קטעי תמלול לפי הזום
        if self.segment_items:
            for item in self.segment_items:
                item.setRegion([item.getRegion()[0], item.getRegion()[1]])
        
        self.zoom_changed.emit(start_time, end_time)
    
    def reset_zoom(self):
        """מאפס את הזום להצגה מלאה."""
        if self.audio_data is not None:
            self.plot_widget.setXRange(0, self.duration)
            downsampled_audio = self.audio_data[::max(1, len(self.audio_data) // 10000)]
            self.plot_widget.setYRange(np.min(downsampled_audio), np.max(downsampled_audio))
            
            logging.info("זום אופס")
    
    def toggle_segments(self, show_segments: bool):
        """מחליף הצגת קטעי תמלול."""
        for item in self.segment_items:
            item.setVisible(show_segments)
        
        logging.info(f"קטעי תמלול: {'מוצגים' if show_segments else 'מוסתרים'}")
    
    def zoom_to_segment(self, segment: Dict[str, Any]):
        """מזם לקטע תמלול ספציפי."""
        start_time = segment["start_time"]
        end_time = segment["end_time"]
        
        # הוספת מרווח קטן לפני ואחרי
        margin = (end_time - start_time) * 0.1
        zoom_start = max(0, start_time - margin)
        zoom_end = min(self.duration, end_time + margin)
        
        self.plot_widget.setXRange(zoom_start, zoom_end)
        logging.info(f"זום לקטע: {start_time:.1f}s - {end_time:.1f}s")
    
    def get_visible_segments(self) -> List[Dict[str, Any]]:
        """מחזיר קטעי תמלול הנראים בתצוגה הנוכחית."""
        if not self.transcript_segments:
            return []
        
        x_range = self.plot_widget.getViewBox().viewRange()[0]
        start_time, end_time = x_range
        
        visible_segments = []
        for segment in self.transcript_segments:
            seg_start = segment["start_time"]
            seg_end = segment["end_time"]
            
            # בדיקה אם הקטע חופף עם התצוגה
            if seg_start <= end_time and seg_end >= start_time:
                visible_segments.append(segment)
        
        return visible_segments
    
    def highlight_segment(self, segment: Dict[str, Any], duration: float = 2.0):
        """מדגיש קטע תמלול זמנית."""
        start_time = segment["start_time"]
        end_time = segment["end_time"]
        
        # יצירת הדגשה זמנית
        highlight_item = pg.LinearRegionItem(
            values=[start_time, end_time],
            brush=mkBrush(color=(255, 0, 0, 150)),  # אדום שקוף
            movable=False
        )
        
        self.plot_widget.addItem(highlight_item)
        
        # הסרה אוטומטית
        def remove_highlight():
            self.plot_widget.removeItem(highlight_item)
        
        QTimer.singleShot(int(duration * 1000), remove_highlight)
        logging.info(f"הודגש קטע: {start_time:.1f}s - {end_time:.1f}s")
    
    def clear(self):
        """מנקה את התצוגה."""
        self.plot_widget.clear()
        self.audio_data = None
        self.transcript_segments = []
        self.segment_items = []
        self.waveform_item = None
        self.position_line = None
        
        self.info_label.setText("לא נטען אודיו")
        logging.info("Waveform Viewer נוקה")

class WaveformWindow(QWidget):
    """חלון נפרד לתצוגת waveform."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("תצוגת גלי קול - נגן בינה כשרה")
        self.setGeometry(100, 100, 1000, 400)
        
        layout = QVBoxLayout()
        
        self.waveform_viewer = WaveformViewer()
        layout.addWidget(self.waveform_viewer)
        
        self.setLayout(layout)
    
    def load_audio_file(self, file_path: str):
        """טוען קובץ אודיו."""
        self.waveform_viewer.load_audio_file(file_path)
    
    def load_transcript(self, segments: List[Dict[str, Any]]):
        """טוען תמלול."""
        self.waveform_viewer.load_transcript(segments)
    
    def update_position(self, position_seconds: float):
        """מעדכן מיקום."""
        self.waveform_viewer.update_position(position_seconds)

# פונקציות עזר
def create_waveform_viewer() -> WaveformViewer:
    """יוצר viewer חדש."""
    return WaveformViewer()

def create_waveform_window() -> WaveformWindow:
    """יוצר חלון waveform חדש."""
    return WaveformWindow()

if __name__ == "__main__":
    import sys
    from PySide6.QtWidgets import QApplication
    
    app = QApplication(sys.argv)
    
    # בדיקה בסיסית
    window = WaveformWindow()
    window.show()
    
    # אם יש קובץ אודיו לבדיקה
    test_audio = "test_audio.wav"
    if os.path.exists(test_audio):
        window.load_audio_file(test_audio)
        
        # הוספת תמלול דמה
        test_segments = [
            {"start_time": 10.0, "end_time": 15.0, "text": "קטע ראשון"},
            {"start_time": 20.0, "end_time": 25.0, "text": "קטע שני"},
        ]
        window.load_transcript(test_segments)
    
    sys.exit(app.exec())