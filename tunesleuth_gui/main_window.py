"""
TuneSleuth Main Window

The primary application window providing folder selection,
scanning progress, and navigation to analysis results.
"""

from pathlib import Path

from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import (
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QStackedWidget,
    QStatusBar,
    QVBoxLayout,
    QWidget,
)

from tunesleuth_core import Library, PatternAnalysis, PatternDetector, Scanner, ScanProgress
from tunesleuth_gui.styles import COLORS, STYLESHEET


class ScanWorker(QThread):
    """Background worker for scanning music libraries."""

    progress = pyqtSignal(ScanProgress)
    finished = pyqtSignal(Library)
    error = pyqtSignal(str)

    def __init__(self, path: Path):
        super().__init__()
        self.path = path

    def run(self):
        try:
            scanner = Scanner(progress_callback=self._on_progress)
            library = scanner.scan(self.path)
            self.finished.emit(library)
        except Exception as e:
            self.error.emit(str(e))

    def _on_progress(self, progress: ScanProgress):
        self.progress.emit(progress)


class AnalyzeWorker(QThread):
    """Background worker for analyzing patterns."""

    finished = pyqtSignal(PatternAnalysis)
    error = pyqtSignal(str)

    def __init__(self, library: Library):
        super().__init__()
        self.library = library

    def run(self):
        try:
            detector = PatternDetector()
            analysis = detector.analyze(self.library)
            self.finished.emit(analysis)
        except Exception as e:
            self.error.emit(str(e))


class WelcomeView(QWidget):
    """Welcome/onboarding view shown on first launch."""

    folder_selected = pyqtSignal(Path)

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(60, 80, 60, 60)
        layout.setSpacing(0)

        # Spacer at top
        layout.addStretch(1)

        # Logo/Title area
        title_container = QWidget()
        title_layout = QVBoxLayout(title_container)
        title_layout.setContentsMargins(0, 0, 0, 0)
        title_layout.setSpacing(8)
        title_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        # App icon placeholder (magnifying glass + waveform concept)
        icon_label = QLabel("🔍")
        icon_label.setStyleSheet(f"""
            font-size: 64px;
            color: {COLORS['amber']};
        """)
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(icon_label)

        # Title
        title = QLabel("TuneSleuth")
        title.setStyleSheet(f"""
            font-size: 42px;
            font-weight: 700;
            color: {COLORS['text_primary']};
            letter-spacing: -1px;
        """)
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(title)

        # Tagline
        tagline = QLabel("Your music library's private investigator")
        tagline.setStyleSheet(f"""
            font-size: 16px;
            font-style: italic;
            color: {COLORS['text_muted']};
            margin-bottom: 20px;
        """)
        tagline.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_layout.addWidget(tagline)

        layout.addWidget(title_container)
        layout.addSpacing(40)

        # Description
        desc = QLabel(
            "Point TuneSleuth at your music folder and let it detect\n"
            "naming patterns, analyze metadata, and suggest organization."
        )
        desc.setStyleSheet(f"""
            font-size: 14px;
            color: {COLORS['text_secondary']};
            line-height: 1.6;
        """)
        desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc.setWordWrap(True)
        layout.addWidget(desc)

        layout.addSpacing(40)

        # Select folder button
        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        select_btn = QPushButton("Select Music Folder")
        select_btn.setProperty("class", "primary")
        select_btn.setMinimumSize(200, 48)
        select_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        select_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {COLORS['amber']};
                color: {COLORS['navy_dark']};
                border: none;
                border-radius: 8px;
                padding: 12px 32px;
                font-size: 15px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background-color: {COLORS['amber_light']};
            }}
            QPushButton:pressed {{
                background-color: {COLORS['amber_dark']};
            }}
        """)
        select_btn.clicked.connect(self._on_select_folder)
        btn_layout.addWidget(select_btn)

        layout.addWidget(btn_container)

        # Spacer at bottom
        layout.addStretch(2)

        # Footer hints
        hints = QLabel(
            "Supports MP3 files • Analyzes folder structure & filenames • Non-destructive"
        )
        hints.setStyleSheet(f"""
            font-size: 12px;
            color: {COLORS['text_muted']};
        """)
        hints.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(hints)

    def _on_select_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Music Folder",
            str(Path.home() / "Music"),
            QFileDialog.Option.ShowDirsOnly,
        )
        if folder:
            self.folder_selected.emit(Path(folder))


class ScanningView(QWidget):
    """View shown while scanning a music library."""

    def __init__(self):
        super().__init__()
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(60, 60, 60, 60)
        layout.setSpacing(0)

        layout.addStretch(1)

        # Scanning indicator
        scanning_label = QLabel("🔍")
        scanning_label.setStyleSheet("font-size: 48px;")
        scanning_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(scanning_label)

        layout.addSpacing(20)

        # Title
        self.title_label = QLabel("Scanning Library...")
        self.title_label.setStyleSheet(f"""
            font-size: 24px;
            font-weight: 600;
            color: {COLORS['text_primary']};
        """)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.title_label)

        layout.addSpacing(8)

        # Current file
        self.file_label = QLabel("Preparing...")
        self.file_label.setStyleSheet(f"""
            font-size: 13px;
            color: {COLORS['text_muted']};
            font-family: 'JetBrains Mono', 'SF Mono', monospace;
        """)
        self.file_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.file_label.setWordWrap(True)
        layout.addWidget(self.file_label)

        layout.addSpacing(30)

        # Progress bar
        progress_container = QWidget()
        progress_layout = QHBoxLayout(progress_container)
        progress_layout.setContentsMargins(100, 0, 100, 0)

        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setMinimumHeight(8)
        progress_layout.addWidget(self.progress_bar)

        layout.addWidget(progress_container)

        layout.addSpacing(16)

        # Stats
        self.stats_label = QLabel("0 / 0 files")
        self.stats_label.setStyleSheet(f"""
            font-size: 13px;
            color: {COLORS['text_secondary']};
        """)
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.stats_label)

        layout.addStretch(2)

    def update_progress(self, progress: ScanProgress):
        """Update the UI with scan progress."""
        if progress.total_files_found > 0:
            percent = int(progress.progress_percent)
            self.progress_bar.setValue(percent)
            self.stats_label.setText(
                f"{progress.files_scanned} / {progress.total_files_found} files"
            )

        if progress.current_file:
            # Show just the filename, not the full path
            filename = Path(progress.current_file).name
            if len(filename) > 50:
                filename = filename[:47] + "..."
            self.file_label.setText(filename)

    def set_analyzing(self):
        """Switch to analyzing state."""
        self.title_label.setText("Analyzing Patterns...")
        self.file_label.setText("Detecting naming conventions...")
        self.progress_bar.setMaximum(0)  # Indeterminate


class MainWindow(QMainWindow):
    """Main application window for TuneSleuth."""

    def __init__(self):
        super().__init__()
        self.library: Library | None = None
        self.analysis: PatternAnalysis | None = None
        self.scan_worker: ScanWorker | None = None
        self.analyze_worker: AnalyzeWorker | None = None

        self._setup_window()
        self._setup_menu()
        self._setup_ui()
        self._setup_status_bar()

    def _setup_window(self):
        """Configure main window properties."""
        self.setWindowTitle("TuneSleuth")
        self.setMinimumSize(900, 700)
        self.resize(1100, 800)

        # Apply stylesheet
        self.setStyleSheet(STYLESHEET)

    def _setup_menu(self):
        """Create the menu bar."""
        menubar = self.menuBar()

        # File menu
        file_menu = menubar.addMenu("File")

        open_action = QAction("Open Folder...", self)
        open_action.setShortcut("Ctrl+O")
        open_action.triggered.connect(self._on_open_folder)
        file_menu.addAction(open_action)

        file_menu.addSeparator()

        quit_action = QAction("Quit", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        # Help menu
        help_menu = menubar.addMenu("Help")

        about_action = QAction("About TuneSleuth", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _setup_ui(self):
        """Set up the main UI."""
        # Central widget with stacked views
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)

        # Welcome view
        self.welcome_view = WelcomeView()
        self.welcome_view.folder_selected.connect(self._start_scan)
        self.stack.addWidget(self.welcome_view)

        # Scanning view
        self.scanning_view = ScanningView()
        self.stack.addWidget(self.scanning_view)

        # Results view (will be created dynamically)
        self.results_view: QWidget | None = None

    def _setup_status_bar(self):
        """Set up the status bar."""
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage("Ready")

    def _on_open_folder(self):
        """Handle File > Open Folder action."""
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Music Folder",
            str(Path.home() / "Music"),
            QFileDialog.Option.ShowDirsOnly,
        )
        if folder:
            self._start_scan(Path(folder))

    def _start_scan(self, path: Path):
        """Start scanning a music folder."""
        self.stack.setCurrentWidget(self.scanning_view)
        self.status_bar.showMessage(f"Scanning: {path}")

        # Start background scan
        self.scan_worker = ScanWorker(path)
        self.scan_worker.progress.connect(self._on_scan_progress)
        self.scan_worker.finished.connect(self._on_scan_finished)
        self.scan_worker.error.connect(self._on_scan_error)
        self.scan_worker.start()

    def _on_scan_progress(self, progress: ScanProgress):
        """Handle scan progress updates."""
        self.scanning_view.update_progress(progress)

    def _on_scan_finished(self, library: Library):
        """Handle scan completion."""
        self.library = library
        self.status_bar.showMessage(f"Scanned {len(library)} tracks. Analyzing...")

        # Switch to analyzing state
        self.scanning_view.set_analyzing()

        # Start pattern analysis
        self.analyze_worker = AnalyzeWorker(library)
        self.analyze_worker.finished.connect(self._on_analyze_finished)
        self.analyze_worker.error.connect(self._on_analyze_error)
        self.analyze_worker.start()

    def _on_scan_error(self, error: str):
        """Handle scan error."""
        QMessageBox.critical(self, "Scan Error", f"Failed to scan library:\n{error}")
        self.stack.setCurrentWidget(self.welcome_view)
        self.status_bar.showMessage("Scan failed")

    def _on_analyze_finished(self, analysis: PatternAnalysis):
        """Handle analysis completion."""
        self.analysis = analysis
        self.status_bar.showMessage(
            f"Analysis complete: {len(self.library)} tracks, "
            f"{len(analysis.all_patterns)} patterns detected"
        )

        # Create and show results view
        self._show_results()

    def _on_analyze_error(self, error: str):
        """Handle analysis error."""
        QMessageBox.warning(
            self, "Analysis Error",
            f"Pattern analysis encountered an error:\n{error}\n\n"
            "Showing basic scan results."
        )
        self._show_results()

    def _show_results(self):
        """Show the results view."""
        # Import here to avoid circular import
        from tunesleuth_gui.results_view import ResultsView

        # Remove old results view if exists
        if self.results_view:
            self.stack.removeWidget(self.results_view)
            self.results_view.deleteLater()

        # Create new results view
        self.results_view = ResultsView(self.library, self.analysis)
        self.results_view.rescan_requested.connect(self._on_rescan)
        self.stack.addWidget(self.results_view)
        self.stack.setCurrentWidget(self.results_view)

    def _on_rescan(self):
        """Handle rescan request."""
        if self.library:
            self._start_scan(self.library.root_path)

    def _show_about(self):
        """Show about dialog."""
        QMessageBox.about(
            self,
            "About TuneSleuth",
            "<h2>TuneSleuth</h2>"
            "<p><i>Your music library's private investigator</i></p>"
            "<p>Version 0.1.0</p>"
            "<p>TuneSleuth analyzes folder structures and filenames, "
            "infers conventions, enriches tracks with accurate metadata, "
            "and organizes your music into a clean, logical library—"
            "without guesswork or heavy-handed renaming.</p>"
            "<p>© 2024 TuneSleuth Team</p>"
        )
