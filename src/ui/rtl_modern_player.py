
"""
נגן אודיו מודרני עם עיצוב RTL מלא לעברית.

תכונות:
- פריסה מימין לשמאל (RTL) מלאה
- חיפוש מתקדם בטור שמאל
- ויזואליזציה בטור ימין
- בר נגן אחיד למטה
- עיצוב נקי ומתמחה במשימה
"""

import sys
from pathlib import Path
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from utils.logger import get_logger
    detailed_logger = get_logger()
except ImportError:
    detailed_logger = None

try:
    from formats.bc1_format import open_bc1, create_demo_bc1
except ImportError:
    open_bc1 = None
    create_demo_bc1 = None

try:
    from performance.fast_loader import FastAudioLoader
except ImportError:
    FastAudioLoader = None

class RTLButton(QPushButton):
    """כפתור מותאם לעברית עם עיצוב מודרני."""
    
    def __init__(self, text="", icon="", primary=False, parent=None):
        super().__init__(parent)
        self.setText(f"{icon} {text}" if icon else text)
        self.setMinimumHeight(36)
        self.primary = primary
        self._setup_style()
    
    def _setup_style(self):
        """עיצוב כפתור מודרני."""
        if self.primary:
            self.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #FF6B6B,
                        stop:1 #E74C3C);
                    border: none;
                    border-radius: 8px;
                    color: white;
                    font-weight: 600;
                    font-size: 14px;
                    padding: 8px 16px;
                    direction: rtl;
                }
                QPushButton:hover {
                    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                        stop:0 #FF7979,
                        stop:1 #F55353);
                }
                QPushButton:pressed {
                    background: #E74C3C;
                }
                QPushButton:disabled {
                    background: #BDC3C7;
                    color: #7F8C8D;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background: rgba(255, 255, 255, 0.95);
                    border: 1px solid #E0E6ED;
                    border-radius: 6px;
                    color: #2C3E50;
                    font-weight: 500;
                    font-size: 13px;
                    padding: 6px 12px;
                    direction: rtl;
                }
                QPushButton:hover {
                    background: #F8F9FA;
                    border-color: #00C8B4;
                }
                QPushButton:pressed {
                    background: #ECF0F1;
                }
                QPushButton:disabled {
                    background: #F5F6FA;
                    color: #BDC3C7;
                }
            """)

class RTLSlider(QSlider):
    """סליידר מותאם לעברית (RTL)."""
    
    def __init__(self, orientation=Qt.Orientation.Horizontal, parent=None):
        super().__init__(orientation, parent)
        if orientation == Qt.Orientation.Horizontal:
            self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        self.setMinimumHeight(24)
        self._setup_style()
    
    def _setup_style(self):
        """עיצוב סליידר RTL."""
        self.setStyleSheet("""
            QSlider::groove:horizontal {
                background: #E0E6ED;
                height: 6px;
                border-radius: 3px;
                margin: 9px 0;
            }
            QSlider::handle:horizontal {
                background: #FF6B6B;
                border: 2px solid white;
                width: 16px;
                height: 16px;
                border-radius: 10px;
                margin: -7px 0;
                box-shadow: 0 2px 8px rgba(255, 107, 107, 0.3);
            }
            QSlider::handle:horizontal:hover {
                background: #FF7979;
                box-shadow: 0 3px 12px rgba(255, 107, 107, 0.5);
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #FF6B6B,
                    stop:1 #00C8B4);
                border-radius: 3px;
            }
        """)

class RTLLabel(QLabel):
    """תווית מותאמת לעברית."""
    
    def __init__(self, text="", style="normal", parent=None):
        super().__init__(text, parent)
        self.setAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
        self._setup_style(style)
    
    def _setup_style(self, style):
        """עיצוב תווית לפי סגנון."""
        styles = {
            "title": "font-size: 18px; font-weight: 600; color: #2C3E50;",
            "subtitle": "font-size: 14px; font-weight: 500; color: #34495E;",
            "normal": "font-size: 13px; color: #5D6D7E;",
            "small": "font-size: 11px; color: #85929E;",
            "time": "font-size: 12px; font-weight: 500; color: #2C3E50; font-family: 'Courier New', monospace;"
        }
        
        base_style = f"""
            QLabel {{
                {styles.get(style, styles["normal"])}
                direction: rtl;
                padding: 2px 4px;
            }}
        """
        self.setStyleSheet(base_style)

class RTLSearchWidget(QWidget):
    """ווידג'ט חיפוש מתקדם עם תוצאות."""
    
    searchRequested = Signal(str)
    resultSelected = Signal(float)  # time position
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.search_results = []
        self._setup_ui()
    
    def _setup_ui(self):
        """הגדרת ממשק החיפוש."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # כותרת חיפוש
        title_label = RTLLabel("🔍 חיפוש בתמלול", "title")
        layout.addWidget(title_label)
        
        # תיבת חיפוש
        search_container = QWidget()
        search_container.setStyleSheet("""
            QWidget {
                background: rgba(255, 255, 255, 0.95);
                border: 2px solid #E0E6ED;
                border-radius: 8px;
                padding: 2px;
            }
            QWidget:focus-within {
                border-color: #00C8B4;
                box-shadow: 0 0 8px rgba(0, 200, 180, 0.2);
            }
        """)
        
        search_layout = QHBoxLayout(search_container)
        search_layout.setContentsMargins(8, 4, 8, 4)
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("הקלד לחיפוש...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                border: none;
                background: transparent;
                font-size: 14px;
                color: #2C3E50;
                direction: rtl;
                padding: 4px;
            }
        """)
        self.search_input.textChanged.connect(self._on_search_text_changed)
        self.search_input.returnPressed.connect(self._perform_search)
        
        search_button = RTLButton("", "🔍")
        search_button.clicked.connect(self._perform_search)
        
        search_layout.addWidget(self.search_input, 1)
        search_layout.addWidget(search_button)
        
        layout.addWidget(search_container)
        
        # רשימת תוצאות
        self.results_list = QListWidget()
        self.results_list.setStyleSheet("""
            QListWidget {
                background: rgba(255, 255, 255, 0.95);
                border: 1px solid #E0E6ED;
                border-radius: 6px;
                direction: rtl;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 8px 12px;
                border-bottom: 1px solid #F8F9FA;
                direction: rtl;
            }
            QListWidget::item:hover {
                background: #F8F9FA;
            }
            QListWidget::item:selected {
                background: #00C8B4;
                color: white;
            }
        """)
        self.results_list.itemDoubleClicked.connect(self._on_result_selected)
        
        layout.addWidget(self.results_list, 1)
        
        # סטטוס תוצאות
        self.results_status = RTLLabel("הקלד לחיפוש בתמלול", "small")
        layout.addWidget(self.results_status)
    
    def _on_search_text_changed(self, text):
        """עדכון חיפוש בזמן אמת."""
        if len(text) >= 2:
            QTimer.singleShot(300, self._perform_search)  # חיפוש עם השהיה
    
    def _perform_search(self):
        """ביצוע חיפוש."""
        query = self.search_input.text().strip()
        if query:
            self.searchRequested.emit(query)
    
    def _on_result_selected(self, item):
        """טיפול בבחירת תוצאה."""
        data = item.data(Qt.ItemDataRole.UserRole)
        if data and 'start_time' in data:
            self.resultSelected.emit(data['start_time'])
    
    def update_results(self, results):
        """עדכון תוצאות חיפוש."""
        self.search_results = results
        self.results_list.clear()
        
        if not results:
            self.results_status.setText("אין תוצאות")
            return
        
        for result in results:
            time_str = self._format_time(result.get('start_time', 0))
            text = result.get('text', '')
            snippet = text[:80] + "..." if len(text) > 80 else text
            
            item_text = f"{time_str} • {snippet}"
            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, result)
            self.results_list.addItem(item)
        
        self.results_status.setText(f"נמצאו {len(results)} תוצאות")
    
    def _format_time(self, seconds):
        """פורמט זמן."""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"

class RTLWaveformWidget(QLabel):
    """ווידג'ט ויזואליזציה מתקדם."""
    
    positionClicked = Signal(float)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.audio_data = None
        self.sample_rate = 44100
        self.duration = 0
        self.current_position = 0
        self.search_positions = []
        
        self.setMinimumHeight(200)
        self.setStyleSheet("""
            QLabel {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.95),
                    stop:1 rgba(248, 249, 250, 0.95));
                border: 1px solid #E0E6ED;
                border-radius: 8px;
                direction: rtl;
            }
        """)
        
        self.setText("🎵 ויזואליזציה\nטען קובץ אודיו לתצוגה")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setWordWrap(True)
    
    def mousePressEvent(self, event):
        """טיפול בלחיצה על הוויזואליזציה."""
        if self.duration > 0:
            # חישוב מיקום RTL
            x = self.width() - event.position().x()  # הפיכה ל-RTL
            position = (x / self.width()) * self.duration
            position = max(0, min(position, self.duration))
            self.positionClicked.emit(position)
    
    def set_audio_data(self, data, sample_rate, duration):
        """הגדרת נתוני אודיו."""
        self.audio_data = data
        self.sample_rate = sample_rate
        self.duration = duration
        self.setText(f"🎵 אודיו נטען\n{duration:.1f} שניות\n{sample_rate:,} Hz")
    
    def set_position(self, position):
        """עדכון מיקום נוכחי."""
        self.current_position = position
        self.update()
    
    def set_search_positions(self, positions):
        """הגדרת מיקומי תוצאות חיפוש."""
        self.search_positions = positions
        self.update()

class RTLPlayerBar(QWidget):
    """בר נגן אחיד למטה."""
    
    playRequested = Signal()
    pauseRequested = Signal()
    stopRequested = Signal()
    seekRequested = Signal(float)
    volumeChanged = Signal(int)
    speedChanged = Signal(float)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.duration = 0
        self.current_position = 0
        self.is_seeking = False
        self._setup_ui()
    
    def _setup_ui(self):
        """הגדרת בר הנגן."""
        self.setFixedHeight(80)
        self.setStyleSheet("""
            QWidget {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.98),
                    stop:1 rgba(248, 249, 250, 0.98));
                border: 1px solid #E0E6ED;
                border-radius: 10px;
                direction: rtl;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 8, 15, 8)
        layout.setSpacing(6)
        
        # שורה עליונה - סליידר זמן
        time_layout = QHBoxLayout()
        
        self.current_time_label = RTLLabel("00:00", "time")
        self.position_slider = RTLSlider()
        self.position_slider.setRange(0, 1000)
        self.position_slider.sliderPressed.connect(self._on_seek_start)
        self.position_slider.sliderReleased.connect(self._on_seek_end)
        self.position_slider.valueChanged.connect(self._on_seek_changed)
        self.total_time_label = RTLLabel("00:00", "time")
        
        time_layout.addWidget(self.total_time_label)  # RTL - זמן כולל משמאל
        time_layout.addWidget(self.position_slider, 1)
        time_layout.addWidget(self.current_time_label)  # RTL - זמן נוכחי מימין
        
        layout.addLayout(time_layout)
        
        # שורה תחתונה - כפתורי בקרה
        controls_layout = QHBoxLayout()
        controls_layout.setSpacing(12)
        
        # כפתורי ניגון (מימין)
        self.skip_back_button = RTLButton("", "◄◄")
        self.play_button = RTLButton("נגן", "▶", primary=True)
        self.pause_button = RTLButton("השהה", "⏸")
        self.stop_button = RTLButton("עצור", "⏹")
        self.skip_forward_button = RTLButton("", "►►")
        
        # חיבור אותות
        self.play_button.clicked.connect(self.playRequested.emit)
        self.pause_button.clicked.connect(self.pauseRequested.emit)
        self.stop_button.clicked.connect(self.stopRequested.emit)
        
        # בקרת עוצמה (באמצע)
        volume_layout = QHBoxLayout()
        volume_layout.addWidget(RTLLabel("🔊", "normal"))
        self.volume_slider = RTLSlider()
        self.volume_slider.setMaximumWidth(100)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.valueChanged.connect(self._on_volume_changed)
        self.volume_label = RTLLabel("70%", "small")
        
        volume_layout.addWidget(self.volume_slider)
        volume_layout.addWidget(self.volume_label)
        
        # בקרת מהירות (משמאל)
        speed_layout = QHBoxLayout()
        speed_layout.addWidget(RTLLabel("⚡", "normal"))
        self.speed_combo = QComboBox()
        self.speed_combo.addItems(["0.5x", "0.75x", "1.0x", "1.25x", "1.5x", "2.0x"])
        self.speed_combo.setCurrentText("1.0x")
        self.speed_combo.currentTextChanged.connect(self._on_speed_changed)
        self.speed_combo.setStyleSheet("""
            QComboBox {
                background: rgba(255, 255, 255, 0.95);
                border: 1px solid #E0E6ED;
                border-radius: 4px;
                padding: 4px 8px;
                font-size: 12px;
                direction: rtl;
            }
        """)
        
        speed_layout.addWidget(self.speed_combo)
        
        # סידור מימין לשמאל
        controls_layout.addWidget(self.skip_back_button)
        controls_layout.addWidget(self.play_button)
        controls_layout.addWidget(self.pause_button)
        controls_layout.addWidget(self.stop_button)
        controls_layout.addWidget(self.skip_forward_button)
        controls_layout.addStretch()
        controls_layout.addLayout(volume_layout)
        controls_layout.addStretch()
        controls_layout.addLayout(speed_layout)
        
        layout.addLayout(controls_layout)
    
    def _on_seek_start(self):
        """התחלת גרירת סליידר."""
        self.is_seeking = True
    
    def _on_seek_end(self):
        """סיום גרירת סליידר."""
        self.is_seeking = False
        if self.duration > 0:
            position = (self.position_slider.value() / 1000.0) * self.duration
            self.seekRequested.emit(position)
    
    def _on_seek_changed(self, value):
        """שינוי סליידר זמן."""
        if not self.is_seeking or self.duration <= 0:
            return
        position = (value / 1000.0) * self.duration
        self.current_time_label.setText(self._format_time(position))
    
    def _on_volume_changed(self, value):
        """שינוי עוצמה."""
        self.volume_label.setText(f"{value}%")
        self.volumeChanged.emit(value)
    
    def _on_speed_changed(self, text):
        """שינוי מהירות."""
        speed = float(text.replace('x', ''))
        self.speedChanged.emit(speed)
    
    def set_duration(self, duration):
        """הגדרת משך כולל."""
        self.duration = duration
        self.total_time_label.setText(self._format_time(duration))
    
    def set_position(self, position):
        """עדכון מיקום נוכחי."""
        if not self.is_seeking:
            self.current_position = position
            self.current_time_label.setText(self._format_time(position))
            if self.duration > 0:
                slider_value = int((position / self.duration) * 1000)
                self.position_slider.setValue(slider_value)
    
    def set_playing_state(self, is_playing):
        """עדכון מצב ניגון."""
        self.play_button.setVisible(not is_playing)
        self.pause_button.setVisible(is_playing)
    
    def _format_time(self, seconds):
        """פורמט זמן."""
        if seconds < 0:
            return "00:00"
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"

class RTLModernAudioPlayer(QMainWindow):
    """נגן אודיו מודרני עם פריסה RTL מלאה."""
    
    def __init__(self):
        super().__init__()
        
        # רכיבי אודיו
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        
        # מצב
        self.current_file = None
        self.current_segments = []
        self.current_audio_data = None
        self.temp_audio_file = None
        
        # טיימר עדכון מיקום
        self.position_timer = QTimer()
        self.position_timer.timeout.connect(self._update_position)
        self.position_timer.start(100)  # 10 FPS
        
        self._setup_window()
        self._setup_ui()
        self._connect_signals()
        
        if detailed_logger:
            detailed_logger.info("נגן אודיו RTL מודרני נוצר")
    
    def _setup_window(self):
        """הגדרת חלון ראשי."""
        self.setWindowTitle("🎵 נגן בינה כשרה - עיצוב RTL מתקדם")
        self.setMinimumSize(1200, 800)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        # רקע עדין
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #F3F7FF,
                    stop:1 #E8F3FF);
                direction: rtl;
            }
        """)
    
    def _setup_ui(self):
        """הגדרת ממשק משתמש."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(12, 12, 12, 12)
        main_layout.setSpacing(12)
        
        # Header (5-8%)
        self._create_header(main_layout)
        
        # Body - טור שמאל וימין (65% + 35%)
        self._create_body(main_layout)
        
        # Player Bar (10%)
        self._create_player_bar(main_layout)
        
        # תפריט
        self._create_menu()
    
    def _create_header(self, layout):
        """יצירת כותרת עליונה."""
        header = QWidget()
        header.setFixedHeight(50)
        header.setStyleSheet("""
            QWidget {
                background: rgba(255, 255, 255, 0.95);
                border: 1px solid #E0E6ED;
                border-radius: 8px;
            }
        """)
        
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(15, 8, 15, 8)
        
        # כפתור חזור (מימין)
        back_button = RTLButton("", "◀")
        
        # מידע קובץ
        self.file_info_label = RTLLabel("לא נטען קובץ", "subtitle")
        
        # זמן
        self.header_time_label = RTLLabel("00:00 / 00:00", "time")
        
        # תפריט (משמאל)
        menu_button = RTLButton("", "☰")
        menu_button.clicked.connect(self._show_menu)
        
        # סידור RTL
        header_layout.addWidget(back_button)
        header_layout.addWidget(self.file_info_label, 1)
        header_layout.addStretch()
        header_layout.addWidget(self.header_time_label)
        header_layout.addWidget(menu_button)
        
        layout.addWidget(header)
    
    def _create_body(self, layout):
        """יצירת גוף מרכזי."""
        body_splitter = QSplitter(Qt.Orientation.Horizontal)
        body_splitter.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        # טור שמאל - חיפוש (65%)
        search_container = QWidget()
        search_container.setStyleSheet("""
            QWidget {
                background: rgba(255, 255, 255, 0.95);
                border: 1px solid #E0E6ED;
                border-radius: 8px;
            }
        """)
        
        search_layout = QVBoxLayout(search_container)
        search_layout.setContentsMargins(12, 12, 12, 12)
        
        self.search_widget = RTLSearchWidget()
        search_layout.addWidget(self.search_widget)
        
        # טור ימין - ויזואליזציה (35%)
        viz_container = QWidget()
        viz_container.setStyleSheet("""
            QWidget {
                background: rgba(255, 255, 255, 0.95);
                border: 1px solid #E0E6ED;
                border-radius: 8px;
            }
        """)
        
        viz_layout = QVBoxLayout(viz_container)
        viz_layout.setContentsMargins(12, 12, 12, 12)
        
        viz_title = RTLLabel("ויזואליזציה ודוברים", "title")
        viz_layout.addWidget(viz_title)
        
        self.waveform_widget = RTLWaveformWidget()
        viz_layout.addWidget(self.waveform_widget, 1)
        
        # הוספה לספליטר (בסדר RTL)
        body_splitter.addWidget(search_container)  # שמאל
        body_splitter.addWidget(viz_container)     # ימין
        body_splitter.setSizes([65, 35])  # 65% שמאל, 35% ימין
        
        layout.addWidget(body_splitter, 1)
    
    def _create_player_bar(self, layout):
        """יצירת בר נגן."""
        self.player_bar = RTLPlayerBar()
        layout.addWidget(self.player_bar)
    
    def _create_menu(self):
        """יצירת תפריט."""
        menubar = self.menuBar()
        menubar.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        # תפריט קובץ
        file_menu = menubar.addMenu("📁 קובץ")
        
        open_action = QAction("🎵 פתח קובץ אודיו", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_file)
        file_menu.addAction(open_action)
        
        open_bc1_action = QAction("🔐 פתח קובץ BC1", self)
        open_bc1_action.triggered.connect(self._open_bc1_file)
        file_menu.addAction(open_bc1_action)
        
        file_menu.addSeparator()
        
        demo_action = QAction("⚡ טען דמו", self)
        demo_action.triggered.connect(self._load_demo)
        file_menu.addAction(demo_action)
    
    def _connect_signals(self):
        """חיבור אותות."""
        # נגן מדיה
        self.media_player.positionChanged.connect(self._on_position_changed)
        self.media_player.durationChanged.connect(self._on_duration_changed)
        self.media_player.playbackStateChanged.connect(self._on_state_changed)
        self.media_player.errorOccurred.connect(self._on_error)
        
        # בר נגן
        self.player_bar.playRequested.connect(self._play)
        self.player_bar.pauseRequested.connect(self._pause)
        self.player_bar.stopRequested.connect(self._stop)
        self.player_bar.seekRequested.connect(self._seek)
        self.player_bar.volumeChanged.connect(self._set_volume)
        self.player_bar.speedChanged.connect(self._set_speed)
        
        # חיפוש
        self.search_widget.searchRequested.connect(self._perform_search)
        self.search_widget.resultSelected.connect(self._seek)
        
        # ויזואליזציה
        self.waveform_widget.positionClicked.connect(self._seek)
    
    # פונקציות נגן
    def _open_file(self):
        """פתיחת קובץ אודיו."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "בחר קובץ אודיו",
            "",
            "Audio Files (*.mp3 *.wav *.flac *.ogg *.m4a *.aac);;All Files (*)"
        )
        if file_path:
            self._load_file(file_path, False)
    
    def _open_bc1_file(self):
        """פתיחת קובץ BC1."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "בחר קובץ BC1",
            "",
            "BC1 Files (*.bc1);;All Files (*)"
        )
        if file_path:
            self._load_file(file_path, True)
    
    def _load_demo(self):
        """טעינת דמו."""
        try:
            if create_demo_bc1:
                import tempfile
                bc1_data = create_demo_bc1()
                with tempfile.NamedTemporaryFile(suffix='.bc1', delete=False) as temp_file:
                    temp_file.write(bc1_data)
                    temp_path = temp_file.name
                self._load_file(temp_path, True)
            else:
                QMessageBox.information(self, "מידע", "דמו BC1 לא זמין")
        except Exception as e:
            QMessageBox.critical(self, "שגיאה", f"שגיאה בטעינת דמו: {e}")
    
    def _load_file(self, file_path: str, is_bc1: bool):
        """טעינת קובץ."""
        try:
            self.current_file = file_path
            file_name = Path(file_path).name
            self.file_info_label.setText(f"🎵 {file_name}")
            
            if is_bc1 and open_bc1:
                # טעינת BC1
                with open(file_path, 'rb') as f:
                    bc1_data = f.read()
                from io import BytesIO
                bundle = open_bc1(BytesIO(bc1_data))
                
                self.temp_audio_file = bundle.audio_file
                self.current_segments = bundle.segments or []
                
                # עדכון חיפוש
                if self.current_segments:
                    self.search_widget.update_results(self.current_segments)
            else:
                # טעינת אודיו רגיל
                self.temp_audio_file = file_path
                self.current_segments = []
            
            # טעינה לנגן
            self.media_player.setSource(QUrl.fromLocalFile(self.temp_audio_file))
            
            if detailed_logger:
                detailed_logger.info(f"קובץ נטען: {file_name}")
                
        except Exception as e:
            QMessageBox.critical(self, "שגיאה", f"שגיאה בטעינת קובץ: {e}")
            if detailed_logger:
                detailed_logger.exception(f"שגיאה בטעינת קובץ: {e}")
    
    def _play(self):
        """ניגון."""
        self.media_player.play()
    
    def _pause(self):
        """השהיה."""
        self.media_player.pause()
    
    def _stop(self):
        """עצירה."""
        self.media_player.stop()
    
    def _seek(self, position):
        """מעבר למיקום."""
        if self.media_player.duration() > 0:
            position_ms = int(position * 1000)
            self.media_player.setPosition(position_ms)
    
    def _set_volume(self, volume):
        """הגדרת עוצמה."""
        self.audio_output.setVolume(volume / 100.0)
    
    def _set_speed(self, speed):
        """הגדרת מהירות."""
        self.media_player.setPlaybackRate(speed)
    
    def _perform_search(self, query):
        """ביצוע חיפוש."""
        if not self.current_segments:
            self.search_widget.update_results([])
            return
        
        results = []
        query_lower = query.lower()
        
        for segment in self.current_segments:
            text = segment.get('text', '').lower()
            if query_lower in text:
                results.append(segment)
        
        self.search_widget.update_results(results)
        
        if detailed_logger:
            detailed_logger.info(f"חיפוש '{query}': {len(results)} תוצאות")
    
    def _show_menu(self):
        """הצגת תפריט."""
        pass  # כבר יש תפריט בר
    
    # אותות נגן מדיה
    def _on_position_changed(self, position_ms):
        """שינוי מיקום."""
        position = position_ms / 1000.0
        self.player_bar.set_position(position)
        self.waveform_widget.set_position(position)
        
        # עדכון כותרת
        duration = self.media_player.duration() / 1000.0
        time_str = f"{self._format_time(position)} / {self._format_time(duration)}"
        self.header_time_label.setText(time_str)
    
    def _on_duration_changed(self, duration_ms):
        """שינוי משך."""
        duration = duration_ms / 1000.0
        self.player_bar.set_duration(duration)
    
    def _on_state_changed(self, state):
        """שינוי מצב ניגון."""
        is_playing = (state == QMediaPlayer.PlaybackState.PlayingState)
        self.player_bar.set_playing_state(is_playing)
    
    def _on_error(self, error, error_string):
        """שגיאת נגן."""
        QMessageBox.critical(self, "שגיאת נגן", error_string)
        if detailed_logger:
            detailed_logger.error(f"שגיאת נגן: {error_string}")
    
    def _update_position(self):
        """עדכון מיקום תקופתי."""
        # זה כבר מטופל באותות הנגן
        pass
    
    def _format_time(self, seconds):
        """פורמט זמן."""
        if seconds < 0:
            return "00:00"
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
    
    def closeEvent(self, event):
        """סגירת אפליקציה."""
        try:
            self.media_player.stop()
            self.position_timer.stop()
            
            # ניקוי קבצים זמניים
            if self.temp_audio_file and Path(self.temp_audio_file).exists():
                try:
                    import os
                    os.remove(self.temp_audio_file)
                except:
                    pass
                    
            if detailed_logger:
                detailed_logger.info("נגן RTL נסגר")
        except Exception as e:
            if detailed_logger:
                detailed_logger.exception(f"שגיאה בסגירה: {e}")
        
        super().closeEvent(event)

def create_rtl_audio_app():
    """יצירת אפליקציית נגן RTL."""
    try:
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # הגדרות RTL
        app.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        app.setApplicationName("נגן בינה כשרה RTL")
        app.setApplicationVersion("2.0")
        
        player = RTLModernAudioPlayer()
        player.show()
        
        return app, player
        
    except Exception as e:
        if detailed_logger:
            detailed_logger.exception(f"שגיאה ביצירת נגן RTL: {e}")
        raise

if __name__ == "__main__":
    app, player = create_rtl_audio_app()
    sys.exit(app.exec())
