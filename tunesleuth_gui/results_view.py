"""
TuneSleuth Results View

Displays scan results and pattern analysis with confidence visualization.
"""

from pathlib import Path
from typing import Optional

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFrame,
    QScrollArea,
    QSplitter,
    QTreeWidget,
    QTreeWidgetItem,
    QHeaderView,
    QSizePolicy,
    QGroupBox,
)

from tunesleuth_core import Library, PatternAnalysis, PatternMatch
from tunesleuth_gui.styles import COLORS, get_confidence_color, get_confidence_badge_style


class StatCard(QFrame):
    """A card displaying a single statistic."""

    def __init__(self, title: str, value: str, subtitle: str = ""):
        super().__init__()
        self._setup_ui(title, value, subtitle)

    def _setup_ui(self, title: str, value: str, subtitle: str):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
                padding: 16px;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(4)

        # Title
        title_label = QLabel(title)
        title_label.setStyleSheet(f"""
            font-size: 12px;
            font-weight: 500;
            color: {COLORS['text_muted']};
            text-transform: uppercase;
            letter-spacing: 1px;
        """)
        layout.addWidget(title_label)

        # Value
        value_label = QLabel(value)
        value_label.setStyleSheet(f"""
            font-size: 32px;
            font-weight: 700;
            color: {COLORS['amber']};
        """)
        layout.addWidget(value_label)

        # Subtitle
        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setStyleSheet(f"""
                font-size: 12px;
                color: {COLORS['text_secondary']};
            """)
            layout.addWidget(subtitle_label)


class PatternCard(QFrame):
    """A card displaying a detected pattern with confidence badge."""

    def __init__(self, pattern: PatternMatch):
        super().__init__()
        self.pattern = pattern
        self._setup_ui()

    def _setup_ui(self):
        self.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 10px;
            }}
            QFrame:hover {{
                border-color: {COLORS['amber']};
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(8)

        # Header row with title and badge
        header = QHBoxLayout()
        header.setSpacing(12)

        # Pattern description
        title = QLabel(self.pattern.description)
        title.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 600;
            color: {COLORS['text_primary']};
        """)
        header.addWidget(title)

        header.addStretch()

        # Confidence badge
        confidence_color = get_confidence_color(self.pattern.confidence)
        badge = QLabel(f"{self.pattern.confidence_percent:.0f}%")
        badge.setStyleSheet(f"""
            background-color: {confidence_color};
            color: {COLORS['navy_dark']};
            padding: 3px 10px;
            border-radius: 12px;
            font-weight: 700;
            font-size: 12px;
        """)
        header.addWidget(badge)

        layout.addLayout(header)

        # Stats row
        stats = QLabel(
            f"{self.pattern.matching_tracks} of {self.pattern.total_tracks} files match"
        )
        stats.setStyleSheet(f"""
            font-size: 12px;
            color: {COLORS['text_secondary']};
        """)
        layout.addWidget(stats)

        # Explanation
        explanation = QLabel(self.pattern.explanation)
        explanation.setStyleSheet(f"""
            font-size: 12px;
            color: {COLORS['text_muted']};
        """)
        explanation.setWordWrap(True)
        layout.addWidget(explanation)

        # Examples
        if self.pattern.examples:
            examples_container = QWidget()
            examples_container.setStyleSheet(f"""
                background-color: {COLORS['navy_dark']};
                border-radius: 6px;
                padding: 8px;
            """)
            examples_layout = QVBoxLayout(examples_container)
            examples_layout.setContentsMargins(10, 8, 10, 8)
            examples_layout.setSpacing(2)

            for example in self.pattern.examples[:3]:
                # Truncate long examples
                display_text = example if len(example) <= 60 else example[:57] + "..."
                example_label = QLabel(f"• {display_text}")
                example_label.setStyleSheet(f"""
                    font-size: 11px;
                    font-family: 'JetBrains Mono', 'SF Mono', monospace;
                    color: {COLORS['text_secondary']};
                """)
                examples_layout.addWidget(example_label)

            layout.addWidget(examples_container)


class ResultsView(QWidget):
    """Main results view showing scan results and pattern analysis."""

    rescan_requested = pyqtSignal()

    def __init__(self, library: Library, analysis: Optional[PatternAnalysis] = None):
        super().__init__()
        self.library = library
        self.analysis = analysis
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header bar
        header = self._create_header()
        layout.addWidget(header)

        # Main content area
        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(20)

        # Left panel: Stats and patterns
        left_panel = self._create_left_panel()
        left_panel.setMinimumWidth(400)

        # Right panel: File browser
        right_panel = self._create_right_panel()

        # Use splitter for resizable panels
        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        splitter.setSizes([450, 600])

        content_layout.addWidget(splitter)
        layout.addWidget(content)

    def _create_header(self) -> QWidget:
        """Create the header bar."""
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['navy_dark']};
                border-bottom: 1px solid {COLORS['border']};
            }}
        """)

        layout = QHBoxLayout(header)
        layout.setContentsMargins(24, 16, 24, 16)

        # Library path
        path_container = QVBoxLayout()
        path_container.setSpacing(4)

        title = QLabel("Library Analysis")
        title.setStyleSheet(f"""
            font-size: 18px;
            font-weight: 600;
            color: {COLORS['text_primary']};
        """)
        path_container.addWidget(title)

        path_label = QLabel(str(self.library.root_path))
        path_label.setStyleSheet(f"""
            font-size: 12px;
            font-family: 'JetBrains Mono', 'SF Mono', monospace;
            color: {COLORS['text_muted']};
        """)
        path_container.addWidget(path_label)

        layout.addLayout(path_container)
        layout.addStretch()

        # Action buttons
        rescan_btn = QPushButton("Rescan")
        rescan_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        rescan_btn.clicked.connect(self.rescan_requested.emit)
        layout.addWidget(rescan_btn)

        new_folder_btn = QPushButton("New Folder")
        new_folder_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        new_folder_btn.clicked.connect(self._on_new_folder)
        layout.addWidget(new_folder_btn)

        return header

    def _create_left_panel(self) -> QWidget:
        """Create the left panel with stats and patterns."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(f"""
            QScrollArea {{
                background-color: transparent;
                border: none;
            }}
        """)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 10, 0)
        layout.setSpacing(20)

        # Stats cards
        stats = self.library.calculate_stats()

        stats_section = QLabel("Overview")
        stats_section.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 600;
            color: {COLORS['amber']};
        """)
        layout.addWidget(stats_section)

        stats_grid = QHBoxLayout()
        stats_grid.setSpacing(12)

        stats_grid.addWidget(StatCard(
            "Tracks",
            f"{stats.total_tracks:,}",
            f"{stats.total_duration_hours:.1f} hours"
        ))

        stats_grid.addWidget(StatCard(
            "Size",
            f"{stats.total_size_gb:.1f} GB" if stats.total_size_gb >= 1 else f"{stats.total_size_mb:.0f} MB",
            f"{stats.folder_count} folders"
        ))

        stats_grid.addWidget(StatCard(
            "Tag Coverage",
            f"{stats.tag_coverage_percent:.0f}%",
            f"{stats.tracks_with_tags} tagged"
        ))

        layout.addLayout(stats_grid)

        # Patterns section
        if self.analysis:
            # Filename patterns
            if self.analysis.filename_patterns:
                section_label = QLabel("Filename Patterns")
                section_label.setStyleSheet(f"""
                    font-size: 14px;
                    font-weight: 600;
                    color: {COLORS['amber']};
                    margin-top: 8px;
                """)
                layout.addWidget(section_label)

                for pattern in self.analysis.filename_patterns:
                    if pattern.confidence >= 0.1:
                        layout.addWidget(PatternCard(pattern))

            # Folder patterns
            if self.analysis.folder_patterns:
                section_label = QLabel("Folder Structure")
                section_label.setStyleSheet(f"""
                    font-size: 14px;
                    font-weight: 600;
                    color: {COLORS['amber']};
                    margin-top: 8px;
                """)
                layout.addWidget(section_label)

                for pattern in self.analysis.folder_patterns:
                    if pattern.confidence >= 0.1:
                        layout.addWidget(PatternCard(pattern))

            # Special patterns
            if self.analysis.special_patterns:
                section_label = QLabel("Special Patterns")
                section_label.setStyleSheet(f"""
                    font-size: 14px;
                    font-weight: 600;
                    color: {COLORS['amber']};
                    margin-top: 8px;
                """)
                layout.addWidget(section_label)

                for pattern in self.analysis.special_patterns:
                    if pattern.confidence >= 0.1:
                        layout.addWidget(PatternCard(pattern))

        layout.addStretch()
        scroll.setWidget(container)
        return scroll

    def _create_right_panel(self) -> QWidget:
        """Create the right panel with file browser."""
        panel = QFrame()
        panel.setStyleSheet(f"""
            QFrame {{
                background-color: {COLORS['surface']};
                border: 1px solid {COLORS['border']};
                border-radius: 12px;
            }}
        """)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Panel header
        header = QWidget()
        header.setStyleSheet(f"""
            background-color: {COLORS['navy_light']};
            border-top-left-radius: 12px;
            border-top-right-radius: 12px;
        """)
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 12, 16, 12)

        header_title = QLabel("Files")
        header_title.setStyleSheet(f"""
            font-size: 14px;
            font-weight: 600;
            color: {COLORS['text_primary']};
        """)
        header_layout.addWidget(header_title)

        header_layout.addStretch()

        track_count = QLabel(f"{len(self.library)} tracks")
        track_count.setStyleSheet(f"""
            font-size: 12px;
            color: {COLORS['text_muted']};
        """)
        header_layout.addWidget(track_count)

        layout.addWidget(header)

        # File tree
        tree = QTreeWidget()
        tree.setHeaderLabels(["Name", "Artist", "Album", "Tags"])
        tree.setAlternatingRowColors(False)
        tree.setIndentation(20)
        tree.setStyleSheet(f"""
            QTreeWidget {{
                background-color: transparent;
                border: none;
                outline: none;
            }}
            QTreeWidget::item {{
                padding: 6px 4px;
            }}
            QTreeWidget::item:hover {{
                background-color: {COLORS['navy_light']};
            }}
            QTreeWidget::item:selected {{
                background-color: {COLORS['amber']};
                color: {COLORS['navy_dark']};
            }}
            QHeaderView::section {{
                background-color: {COLORS['surface']};
                color: {COLORS['text_secondary']};
                padding: 8px;
                border: none;
                border-bottom: 1px solid {COLORS['border']};
                font-weight: 600;
                font-size: 12px;
            }}
        """)

        # Set column widths
        header = tree.header()
        header.setStretchLastSection(False)
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed)
        header.resizeSection(3, 60)

        # Populate tree by folder
        folders = self.library.get_folders()
        for folder_path in sorted(folders.keys()):
            tracks = folders[folder_path]

            # Create folder item
            try:
                rel_path = folder_path.relative_to(self.library.root_path)
                folder_name = str(rel_path) if str(rel_path) != "." else "Root"
            except ValueError:
                folder_name = folder_path.name

            folder_item = QTreeWidgetItem([f"📁 {folder_name}", "", "", ""])
            folder_item.setExpanded(False)

            # Add tracks under folder
            for track in sorted(tracks, key=lambda t: (t.track_number or 999, t.filename)):
                tag_status = "✅" if track.has_complete_tags else "⚠️"
                track_item = QTreeWidgetItem([
                    track.filename,
                    track.display_artist,
                    track.display_album,
                    tag_status,
                ])
                folder_item.addChild(track_item)

            tree.addTopLevelItem(folder_item)

        layout.addWidget(tree)
        return panel

    def _on_new_folder(self):
        """Handle new folder button click."""
        from PyQt6.QtWidgets import QFileDialog

        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Music Folder",
            str(Path.home() / "Music"),
            QFileDialog.Option.ShowDirsOnly,
        )
        if folder:
            # Signal parent to start new scan
            # For now, we'll just emit rescan with the understanding
            # that the main window will handle this
            self.rescan_requested.emit()
