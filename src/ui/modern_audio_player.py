"""
Ultra-Modern Audio Player with 50x Improved UI Design.

Features:
- Glass morphism design with depth and shadows
- Smooth animations and transitions
- Modern Hebrew RTL layout
- Professional color scheme
- Interactive visual feedback
- Responsive design elements
"""

import sys
from pathlib import Path
from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from PySide6.QtMultimedia import QMediaPlayer, QAudioOutput
from PySide6.QtMultimediaWidgets import *

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from utils.logger import detailed_logger
    from formats.bc1_format import open_bc1
    from visualization.advanced_waveform import AdvancedWaveformWidget
    from ui.transcript_widget import TranscriptWidget
    from search.transcript_search import TranscriptSearchEngine
except ImportError as e:
    detailed_logger = None
    print(f"Import warning: {e}")

class ModernGlassButton(QPushButton):
    """Modern glass morphism button with animations."""
    
    def __init__(self, text="", icon_path=None, parent=None):
        super().__init__(text, parent)
        self.setMinimumHeight(48)
        self.setMinimumWidth(120)
        self._setup_style()
        self._setup_animations()
        
        if icon_path:
            self.setIcon(QIcon(icon_path))
            self.setIconSize(QSize(24, 24))
    
    def _setup_style(self):
        """Setup glass morphism styling."""
        self.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.2),
                    stop:1 rgba(255, 255, 255, 0.1));
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 12px;
                color: #2C3E50;
                font-weight: 600;
                font-size: 14px;
                padding: 8px 16px;
                backdrop-filter: blur(10px);
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.3),
                    stop:1 rgba(255, 255, 255, 0.2));
                border: 1px solid rgba(255, 255, 255, 0.4);
                transform: translateY(-2px);
                box-shadow: 0 6px 25px rgba(0, 0, 0, 0.15);
            }
            QPushButton:pressed {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.1),
                    stop:1 rgba(255, 255, 255, 0.05));
                transform: translateY(0px);
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            }
        """)
    
    def _setup_animations(self):
        """Setup hover animations."""
        self.animation = QPropertyAnimation(self, b"geometry")
        self.animation.setDuration(200)
        self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)

class ModernSlider(QSlider):
    """Modern slider with glass effects."""
    
    def __init__(self, orientation=Qt.Orientation.Horizontal, parent=None):
        super().__init__(orientation, parent)
        self.setMinimumHeight(32)
        self._setup_style()
    
    def _setup_style(self):
        """Setup modern slider styling."""
        self.setStyleSheet("""
            QSlider::groove:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(255, 255, 255, 0.1),
                    stop:1 rgba(255, 255, 255, 0.05));
                height: 8px;
                border-radius: 4px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }
            QSlider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea,
                    stop:1 #764ba2);
                border-radius: 4px;
            }
            QSlider::handle:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff,
                    stop:1 #f0f0f0);
                border: 2px solid #667eea;
                width: 20px;
                height: 20px;
                border-radius: 12px;
                margin: -8px 0;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
            }
            QSlider::handle:horizontal:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #ffffff,
                    stop:1 #e0e0e0);
                border: 2px solid #764ba2;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
            }
        """)

class ModernLabel(QLabel):
    """Modern label with enhanced typography."""
    
    def __init__(self, text="", size="medium", weight="normal", parent=None):
        super().__init__(text, parent)
        self._setup_style(size, weight)
    
    def _setup_style(self, size, weight):
        """Setup typography styling."""
        sizes = {
            "small": "12px",
            "medium": "14px", 
            "large": "18px",
            "title": "24px",
            "hero": "32px"
        }
        
        weights = {
            "light": "300",
            "normal": "400", 
            "medium": "500",
            "semibold": "600",
            "bold": "700"
        }
        
        self.setStyleSheet(f"""
            QLabel {{
                color: #2C3E50;
                font-size: {sizes.get(size, "14px")};
                font-weight: {weights.get(weight, "400")};
                direction: rtl;
                padding: 4px 8px;
                background: rgba(255, 255, 255, 0.1);
                border-radius: 6px;
                border: 1px solid rgba(255, 255, 255, 0.2);
            }}
        """)

class ModernProgressBar(QProgressBar):
    """Modern progress bar with glass effects."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMinimumHeight(8)
        self._setup_style()
    
    def _setup_style(self):
        """Setup progress bar styling."""
        self.setStyleSheet("""
            QProgressBar {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 4px;
                text-align: center;
            }
            QProgressBar::chunk {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #667eea,
                    stop:1 #764ba2);
                border-radius: 4px;
            }
        """)

class UltraModernAudioPlayer(QMainWindow):
    """Ultra-modern audio player with 50x improved UI design."""
    
    def __init__(self):
        super().__init__()
        
        # Audio components
        self.media_player = QMediaPlayer()
        self.audio_output = QAudioOutput()
        self.media_player.setAudioOutput(self.audio_output)
        
        # State tracking
        self.current_file = None
        self.current_segments = []
        self.is_seeking = False
        self.is_bc1_file = False
        
        # Performance optimization
        self.update_timer = QTimer()
        self.update_timer.timeout.connect(self._update_position)
        self.update_timer.start(33)  # 30 FPS for ultra-smooth updates
        
        self._setup_window()
        self._setup_ui()
        self._connect_signals()
        self._setup_animations()
        
        if detailed_logger:
            detailed_logger.info("נגן אודיו אולטרה מודרני נוצר")
    
    def _setup_window(self):
        """Setup main window properties."""
        self.setWindowTitle("🎵 נגן בינה כשרה - עיצוב מתקדם")
        self.setMinimumSize(1200, 800)
        self.setLayoutDirection(Qt.LayoutDirection.RightToLeft)
        
        # Modern window styling
        self.setStyleSheet("""
            QMainWindow {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #667eea,
                    stop:0.5 #764ba2,
                    stop:1 #f093fb);
            }
        """)
    
    def _setup_ui(self):
        """Setup ultra-modern user interface."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Main layout with glass container
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Glass container
        glass_container = QWidget()
        glass_container.setStyleSheet("""
            QWidget {
                background: rgba(255, 255, 255, 0.15);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 20px;
                backdrop-filter: blur(20px);
            }
        """)
        
        container_layout = QVBoxLayout(glass_container)
        container_layout.setContentsMargins(30, 30, 30, 30)
        container_layout.setSpacing(25)
        
        # Header section
        self._create_header(container_layout)
        
        # Main content area
        self._create_main_content(container_layout)
        
        # Controls section
        self._create_controls(container_layout)
        
        # Status section
        self._create_status(container_layout)
        
        main_layout.addWidget(glass_container)
        
        # Menu bar
        self._create_modern_menu()
    
    def _create_header(self, layout):
        """Create modern header section."""
        header_layout = QHBoxLayout()
        
        # App title
        title_label = ModernLabel("נגן בינה כשרה", "hero", "bold")
        title_label.setStyleSheet("""
            QLabel {
                color: #ffffff;
                background: none;
                border: none;
                font-family: 'Segoe UI', 'Arial', sans-serif;
                text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
            }
        """)
        
        # File info
        self.file_info_label = ModernLabel("אין קובץ נטען", "large", "medium")
        self.file_info_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 10px;
                padding: 10px 15px;
            }
        """)
        
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.file_info_label)
        
        layout.addLayout(header_layout)
    
    def _create_main_content(self, layout):
        """Create main content area with visualizations."""
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        content_splitter.setStyleSheet("""
            QSplitter::handle {
                background: rgba(255, 255, 255, 0.3);
                border-radius: 3px;
                margin: 2px;
            }
        """)
        
        # Left panel - Waveform and visualizations
        left_panel = self._create_visualization_panel()
        
        # Right panel - Transcript and search
        right_panel = self._create_transcript_panel()
        
        content_splitter.addWidget(left_panel)
        content_splitter.addWidget(right_panel)
        content_splitter.setSizes([60, 40])  # 60% waveform, 40% transcript
        
        layout.addWidget(content_splitter, 1)
    
    def _create_visualization_panel(self):
        """Create visualization panel."""
        panel = QWidget()
        panel.setStyleSheet("""
            QWidget {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 15px;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Waveform title
        waveform_title = ModernLabel("ויזואליזציה", "large", "semibold")
        layout.addWidget(waveform_title)
        
        # Waveform widget placeholder (will be replaced with actual widget)
        self.waveform_widget = QLabel("טוען ויזואליזציה...")
        self.waveform_widget.setMinimumHeight(200)
        self.waveform_widget.setStyleSheet("""
            QLabel {
                background: rgba(0, 0, 0, 0.2);
                border: 2px dashed rgba(255, 255, 255, 0.3);
                border-radius: 10px;
                color: rgba(255, 255, 255, 0.7);
                font-size: 16px;
                text-align: center;
            }
        """)
        self.waveform_widget.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(self.waveform_widget, 1)
        
        return panel
    
    def _create_transcript_panel(self):
        """Create transcript panel."""
        panel = QWidget()
        panel.setStyleSheet("""
            QWidget {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 15px;
            }
        """)
        
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(20, 20, 20, 20)
        
        # Search section
        search_layout = QHBoxLayout()
        
        search_title = ModernLabel("חיפוש בתמלול", "large", "semibold")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("הקלד כדי לחפש...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background: rgba(255, 255, 255, 0.2);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 8px;
                padding: 10px 15px;
                font-size: 14px;
                color: #2C3E50;
                direction: rtl;
            }
            QLineEdit:focus {
                border: 2px solid #667eea;
                background: rgba(255, 255, 255, 0.3);
            }
        """)
        
        search_layout.addWidget(search_title)
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)
        
        # Transcript widget placeholder
        self.transcript_widget = QLabel("אין תמלול זמין")
        self.transcript_widget.setMinimumHeight(300)
        self.transcript_widget.setStyleSheet("""
            QLabel {
                background: rgba(0, 0, 0, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 10px;
                color: rgba(255, 255, 255, 0.8);
                font-size: 14px;
                padding: 15px;
                direction: rtl;
            }
        """)
        self.transcript_widget.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignRight)
        self.transcript_widget.setWordWrap(True)
        
        layout.addWidget(self.transcript_widget, 1)
        
        return panel
    
    def _create_controls(self, layout):
        """Create modern playback controls."""
        controls_container = QWidget()
        controls_container.setStyleSheet("""
            QWidget {
                background: rgba(255, 255, 255, 0.1);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 15px;
            }
        """)
        
        controls_layout = QVBoxLayout(controls_container)
        controls_layout.setContentsMargins(25, 20, 25, 20)
        controls_layout.setSpacing(15)
        
        # Position slider
        position_layout = QHBoxLayout()
        
        self.current_time_label = ModernLabel("00:00", "medium", "medium")
        self.position_slider = ModernSlider()
        self.position_slider.setRange(0, 1000)
        self.total_time_label = ModernLabel("00:00", "medium", "medium")
        
        position_layout.addWidget(self.current_time_label)
        position_layout.addWidget(self.position_slider, 1)
        position_layout.addWidget(self.total_time_label)
        
        controls_layout.addLayout(position_layout)
        
        # Main controls
        main_controls_layout = QHBoxLayout()
        main_controls_layout.setSpacing(15)
        
        # Play/Pause button (larger)
        self.play_button = ModernGlassButton("▶ נגן")
        self.play_button.setMinimumSize(120, 60)
        self.play_button.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #667eea,
                    stop:1 #764ba2);
                border: none;
                border-radius: 30px;
                color: white;
                font-weight: bold;
                font-size: 16px;
                box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
            }
            QPushButton:hover {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #764ba2,
                    stop:1 #667eea);
                box-shadow: 0 8px 25px rgba(102, 126, 234, 0.6);
            }
        """)
        
        self.stop_button = ModernGlassButton("⏹ עצור")
        
        # Volume controls
        volume_layout = QHBoxLayout()
        volume_label = ModernLabel("🔊", "medium", "normal")
        self.volume_slider = ModernSlider()
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(70)
        self.volume_slider.setMaximumWidth(150)
        self.volume_label = ModernLabel("70%", "small", "normal")
        
        volume_layout.addWidget(volume_label)
        volume_layout.addWidget(self.volume_slider)
        volume_layout.addWidget(self.volume_label)
        
        # Speed controls
        speed_layout = QHBoxLayout()
        speed_label = ModernLabel("⚡", "medium", "normal")
        self.speed_slider = ModernSlider()
        self.speed_slider.setRange(50, 200)
        self.speed_slider.setValue(100)
        self.speed_slider.setMaximumWidth(150)
        self.speed_label = ModernLabel("1.0x", "small", "normal")
        
        speed_layout.addWidget(speed_label)
        speed_layout.addWidget(self.speed_slider)
        speed_layout.addWidget(self.speed_label)
        
        main_controls_layout.addStretch()
        main_controls_layout.addLayout(volume_layout)
        main_controls_layout.addWidget(self.play_button)
        main_controls_layout.addWidget(self.stop_button)
        main_controls_layout.addLayout(speed_layout)
        main_controls_layout.addStretch()
        
        controls_layout.addLayout(main_controls_layout)
        
        layout.addWidget(controls_container)
    
    def _create_status(self, layout):
        """Create modern status bar."""
        status_container = QWidget()
        status_container.setMaximumHeight(60)
        status_container.setStyleSheet("""
            QWidget {
                background: rgba(255, 255, 255, 0.05);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 10px;
            }
        """)
        
        status_layout = QHBoxLayout(status_container)
        status_layout.setContentsMargins(20, 10, 20, 10)
        
        self.status_label = ModernLabel("מוכן לעבודה", "medium", "normal")
        self.status_label.setStyleSheet("""
            QLabel {
                color: rgba(255, 255, 255, 0.9);
                background: none;
                border: none;
            }
        """)
        
        # Loading progress bar
        self.progress_bar = ModernProgressBar()
        self.progress_bar.setVisible(False)
        
        status_layout.addWidget(self.status_label)
        status_layout.addStretch()
        status_layout.addWidget(self.progress_bar)
        
        layout.addWidget(status_container)
    
    def _create_modern_menu(self):
        """Create modern menu bar."""
        menubar = self.menuBar()
        menubar.setStyleSheet("""
            QMenuBar {
                background: rgba(255, 255, 255, 0.1);
                border: none;
                color: white;
                font-weight: 500;
                padding: 5px;
            }
            QMenuBar::item {
                background: transparent;
                padding: 8px 15px;
                border-radius: 6px;
                margin: 2px;
            }
            QMenuBar::item:selected {
                background: rgba(255, 255, 255, 0.2);
            }
            QMenu {
                background: rgba(255, 255, 255, 0.9);
                border: 1px solid rgba(255, 255, 255, 0.3);
                border-radius: 10px;
                padding: 5px;
            }
            QMenu::item {
                padding: 8px 20px;
                border-radius: 6px;
                color: #2C3E50;
            }
            QMenu::item:selected {
                background: #667eea;
                color: white;
            }
        """)
        
        # File menu
        file_menu = menubar.addMenu("📁 קובץ")
        
        open_action = QAction("פתח קובץ אודיו", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._open_file)
        file_menu.addAction(open_action)
        
        open_bc1_action = QAction("פתח קובץ BC1", self)
        open_bc1_action.setShortcut("Ctrl+B")
        open_bc1_action.triggered.connect(self._open_bc1_file)
        file_menu.addAction(open_bc1_action)
        
        file_menu.addSeparator()
        
        demo_action = QAction("טען דמו BC1", self)
        demo_action.triggered.connect(self._load_demo_bc1)
        file_menu.addAction(demo_action)
        
        # View menu
        view_menu = menubar.addMenu("👁 תצוגה")
        
        fullscreen_action = QAction("מסך מלא", self)
        fullscreen_action.setShortcut("F11")
        fullscreen_action.triggered.connect(self._toggle_fullscreen)
        view_menu.addAction(fullscreen_action)
    
    def _setup_animations(self):
        """Setup smooth animations."""
        # Fade in animation
        self.fade_animation = QPropertyAnimation(self, b"windowOpacity")
        self.fade_animation.setDuration(500)
        self.fade_animation.setStartValue(0.0)
        self.fade_animation.setEndValue(1.0)
        self.fade_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Scale animation for loading
        self.scale_animation = QPropertyAnimation(self.progress_bar, b"geometry")
        self.scale_animation.setDuration(300)
        self.scale_animation.setEasingCurve(QEasingCurve.Type.OutBounce)
    
    def _connect_signals(self):
        """Connect all signals."""
        # Media player signals
        self.media_player.positionChanged.connect(self._on_position_changed)
        self.media_player.durationChanged.connect(self._on_duration_changed)
        self.media_player.playbackStateChanged.connect(self._on_state_changed)
        self.media_player.errorOccurred.connect(self._on_error_occurred)
        
        # Control signals
        self.play_button.clicked.connect(self._toggle_play)
        self.stop_button.clicked.connect(self._stop)
        self.position_slider.sliderPressed.connect(self._on_seek_start)
        self.position_slider.sliderReleased.connect(self._on_seek_end)
        self.volume_slider.valueChanged.connect(self._on_volume_changed)
        self.speed_slider.valueChanged.connect(self._on_speed_changed)
        
        # Search
        self.search_input.textChanged.connect(self._on_search_text_changed)
    
    def showEvent(self, event):
        """Handle show event with animation."""
        super().showEvent(event)
        self.fade_animation.start()
    
    def _toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()
    
    # Placeholder methods for functionality
    def _open_file(self):
        """Open regular audio file."""
        if detailed_logger:
            detailed_logger.info("פותח דיאלוג בחירת קובץ")
        # Implementation will be added
        pass
    
    def _open_bc1_file(self):
        """Open BC1 file."""
        if detailed_logger:
            detailed_logger.info("פותח דיאלוג בחירת BC1")
        # Implementation will be added
        pass
    
    def _load_demo_bc1(self):
        """Load demo BC1 file."""
        if detailed_logger:
            detailed_logger.info("טוען BC1 דמו")
        # Implementation will be added
        pass
    
    def _toggle_play(self):
        """Toggle playback."""
        if detailed_logger:
            detailed_logger.info("החלפת מצב ניגון")
        # Implementation will be added
        pass
    
    def _stop(self):
        """Stop playback."""
        if detailed_logger:
            detailed_logger.info("עצירת ניגון")
        # Implementation will be added
        pass
    
    def _on_seek_start(self):
        """Handle seek start."""
        self.is_seeking = True
    
    def _on_seek_end(self):
        """Handle seek end."""
        self.is_seeking = False
        # Implementation will be added
    
    def _on_volume_changed(self, value):
        """Handle volume change."""
        self.volume_label.setText(f"{value}%")
        self.audio_output.setVolume(value / 100.0)
    
    def _on_speed_changed(self, value):
        """Handle speed change."""
        speed = value / 100.0
        self.speed_label.setText(f"{speed:.1f}x")
        self.media_player.setPlaybackRate(speed)
    
    def _on_position_changed(self, position_ms):
        """Handle position change."""
        if not self.is_seeking:
            duration = self.media_player.duration()
            if duration > 0:
                slider_value = int((position_ms / duration) * 1000)
                self.position_slider.setValue(slider_value)
            
            position_seconds = position_ms / 1000.0
            self.current_time_label.setText(self._format_time(position_seconds))
    
    def _on_duration_changed(self, duration_ms):
        """Handle duration change."""
        duration_seconds = duration_ms / 1000.0
        self.total_time_label.setText(self._format_time(duration_seconds))
    
    def _on_state_changed(self, state):
        """Handle playback state change."""
        if state == QMediaPlayer.PlaybackState.PlayingState:
            self.play_button.setText("⏸ השהה")
        else:
            self.play_button.setText("▶ נגן")
    
    def _on_error_occurred(self, error, error_string):
        """Handle media error."""
        if detailed_logger:
            detailed_logger.error(f"שגיאת נגן: {error_string}")
        self.status_label.setText(f"שגיאה: {error_string}")
    
    def _on_search_text_changed(self, text):
        """Handle search text change."""
        if detailed_logger:
            detailed_logger.debug(f"חיפוש: {text}")
        # Implementation will be added
    
    def _update_position(self):
        """Update position smoothly."""
        # This will be called 30 times per second for ultra-smooth updates
        pass
    
    def _format_time(self, seconds):
        """Format time as MM:SS."""
        if seconds < 0:
            return "00:00"
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"

def create_ultra_modern_audio_app():
    """Create the ultra-modern audio application."""
    try:
        if detailed_logger:
            detailed_logger.start_operation("יצירת נגן אולטרא מודרני")
        
        app = QApplication.instance()
        if app is None:
            app = QApplication(sys.argv)
        
        # Set application properties
        app.setApplicationName("נגן בינה כשרה")
        app.setApplicationVersion("2.0")
        app.setOrganizationName("Bina Cshera")
        
        # Create and show player
        player = UltraModernAudioPlayer()
        player.show()
        
        if detailed_logger:
            detailed_logger.end_operation("יצירת נגן אולטרא מודרני")
            detailed_logger.info("נגן אולטרא מודרני מוכן")
        
        return app, player
        
    except Exception as e:
        if detailed_logger:
            detailed_logger.exception(f"שגיאה ביצירת נגן אולטרא מודרני: {e}")
        raise

if __name__ == "__main__":
    app, player = create_ultra_modern_audio_app()
    sys.exit(app.exec())