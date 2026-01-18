"""
TuneSleuth GUI Styles

Defines the visual style and theming for the application.
Color palette: Deep navy (#1a1f36) + warm amber accents (#f59e0b)
"""

# Color Palette
COLORS = {
    # Primary colors
    "navy_dark": "#0f1219",
    "navy": "#1a1f36",
    "navy_light": "#252b45",
    "navy_lighter": "#323a5a",

    # Accent colors
    "amber": "#f59e0b",
    "amber_light": "#fbbf24",
    "amber_dark": "#d97706",

    # Semantic colors
    "success": "#10b981",
    "warning": "#f59e0b",
    "error": "#ef4444",
    "info": "#3b82f6",

    # Text colors
    "text_primary": "#f8fafc",
    "text_secondary": "#94a3b8",
    "text_muted": "#64748b",

    # Surface colors
    "surface": "#1e2538",
    "surface_elevated": "#283046",
    "border": "#334155",
}

# Main application stylesheet
STYLESHEET = f"""
/* Global Styles */
QWidget {{
    background-color: {COLORS['navy']};
    color: {COLORS['text_primary']};
    font-family: 'Inter', 'SF Pro Display', -apple-system, BlinkMacSystemFont, sans-serif;
    font-size: 13px;
}}

QMainWindow {{
    background-color: {COLORS['navy_dark']};
}}

/* Labels */
QLabel {{
    color: {COLORS['text_primary']};
    background: transparent;
}}

QLabel[class="title"] {{
    font-size: 24px;
    font-weight: 600;
    color: {COLORS['text_primary']};
}}

QLabel[class="subtitle"] {{
    font-size: 14px;
    color: {COLORS['text_secondary']};
}}

QLabel[class="tagline"] {{
    font-size: 13px;
    font-style: italic;
    color: {COLORS['text_muted']};
}}

QLabel[class="section-header"] {{
    font-size: 16px;
    font-weight: 600;
    color: {COLORS['amber']};
    padding-top: 8px;
}}

QLabel[class="filepath"] {{
    font-family: 'JetBrains Mono', 'SF Mono', 'Menlo', monospace;
    font-size: 12px;
    color: {COLORS['text_secondary']};
    background-color: {COLORS['surface']};
    padding: 4px 8px;
    border-radius: 4px;
}}

/* Buttons */
QPushButton {{
    background-color: {COLORS['navy_light']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 6px;
    padding: 8px 16px;
    font-weight: 500;
    min-height: 20px;
}}

QPushButton:hover {{
    background-color: {COLORS['navy_lighter']};
    border-color: {COLORS['amber']};
}}

QPushButton:pressed {{
    background-color: {COLORS['surface']};
}}

QPushButton:disabled {{
    background-color: {COLORS['navy_dark']};
    color: {COLORS['text_muted']};
    border-color: {COLORS['navy_light']};
}}

QPushButton[class="primary"] {{
    background-color: {COLORS['amber']};
    color: {COLORS['navy_dark']};
    border: none;
    font-weight: 600;
}}

QPushButton[class="primary"]:hover {{
    background-color: {COLORS['amber_light']};
}}

QPushButton[class="primary"]:pressed {{
    background-color: {COLORS['amber_dark']};
}}

/* Progress Bars */
QProgressBar {{
    border: none;
    border-radius: 4px;
    background-color: {COLORS['surface']};
    height: 8px;
    text-align: center;
}}

QProgressBar::chunk {{
    background-color: {COLORS['amber']};
    border-radius: 4px;
}}

/* Scroll Bars */
QScrollBar:vertical {{
    border: none;
    background-color: {COLORS['navy_dark']};
    width: 10px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background-color: {COLORS['navy_lighter']};
    border-radius: 5px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background-color: {COLORS['border']};
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar:horizontal {{
    border: none;
    background-color: {COLORS['navy_dark']};
    height: 10px;
    margin: 0;
}}

QScrollBar::handle:horizontal {{
    background-color: {COLORS['navy_lighter']};
    border-radius: 5px;
    min-width: 30px;
}}

QScrollBar::handle:horizontal:hover {{
    background-color: {COLORS['border']};
}}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{
    width: 0;
}}

/* Tree and List Views */
QTreeView, QListView, QTableView {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 4px;
    outline: none;
}}

QTreeView::item, QListView::item, QTableView::item {{
    padding: 6px 8px;
    border-radius: 4px;
}}

QTreeView::item:hover, QListView::item:hover, QTableView::item:hover {{
    background-color: {COLORS['navy_light']};
}}

QTreeView::item:selected, QListView::item:selected, QTableView::item:selected {{
    background-color: {COLORS['amber']};
    color: {COLORS['navy_dark']};
}}

QHeaderView::section {{
    background-color: {COLORS['navy_light']};
    color: {COLORS['text_secondary']};
    padding: 8px;
    border: none;
    border-bottom: 1px solid {COLORS['border']};
    font-weight: 600;
}}

/* Group Box */
QGroupBox {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    margin-top: 16px;
    padding: 16px;
    font-weight: 600;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    top: 4px;
    color: {COLORS['amber']};
    background-color: {COLORS['surface']};
    padding: 0 8px;
}}

/* Frames and Panels */
QFrame[class="panel"] {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
}}

QFrame[class="card"] {{
    background-color: {COLORS['surface_elevated']};
    border: 1px solid {COLORS['border']};
    border-radius: 12px;
    padding: 16px;
}}

/* Status Bar */
QStatusBar {{
    background-color: {COLORS['navy_dark']};
    color: {COLORS['text_muted']};
    border-top: 1px solid {COLORS['border']};
}}

/* Menu Bar */
QMenuBar {{
    background-color: {COLORS['navy_dark']};
    color: {COLORS['text_primary']};
    border-bottom: 1px solid {COLORS['border']};
    padding: 4px;
}}

QMenuBar::item {{
    padding: 6px 12px;
    border-radius: 4px;
}}

QMenuBar::item:selected {{
    background-color: {COLORS['navy_light']};
}}

QMenu {{
    background-color: {COLORS['surface_elevated']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 4px;
}}

QMenu::item {{
    padding: 8px 24px;
    border-radius: 4px;
}}

QMenu::item:selected {{
    background-color: {COLORS['amber']};
    color: {COLORS['navy_dark']};
}}

QMenu::separator {{
    height: 1px;
    background-color: {COLORS['border']};
    margin: 4px 8px;
}}

/* Tool Tips */
QToolTip {{
    background-color: {COLORS['surface_elevated']};
    color: {COLORS['text_primary']};
    border: 1px solid {COLORS['border']};
    border-radius: 4px;
    padding: 6px 10px;
}}

/* Splitter */
QSplitter::handle {{
    background-color: {COLORS['border']};
}}

QSplitter::handle:horizontal {{
    width: 2px;
}}

QSplitter::handle:vertical {{
    height: 2px;
}}

/* Tab Widget */
QTabWidget::pane {{
    background-color: {COLORS['surface']};
    border: 1px solid {COLORS['border']};
    border-radius: 8px;
    padding: 8px;
}}

QTabBar::tab {{
    background-color: {COLORS['navy_light']};
    color: {COLORS['text_secondary']};
    border: 1px solid {COLORS['border']};
    border-bottom: none;
    border-top-left-radius: 6px;
    border-top-right-radius: 6px;
    padding: 8px 16px;
    margin-right: 2px;
}}

QTabBar::tab:selected {{
    background-color: {COLORS['surface']};
    color: {COLORS['amber']};
    font-weight: 600;
}}

QTabBar::tab:hover:!selected {{
    background-color: {COLORS['navy_lighter']};
}}
"""


def get_confidence_color(confidence: float) -> str:
    """Get color for confidence level."""
    if confidence >= 0.9:
        return COLORS["success"]
    elif confidence >= 0.75:
        return "#22c55e"  # Slightly lighter green
    elif confidence >= 0.5:
        return COLORS["warning"]
    elif confidence >= 0.25:
        return "#fb923c"  # Orange
    else:
        return COLORS["error"]


def get_confidence_badge_style(confidence: float) -> str:
    """Get badge style for confidence level."""
    color = get_confidence_color(confidence)
    return f"""
        background-color: {color};
        color: {COLORS['navy_dark']};
        padding: 2px 8px;
        border-radius: 10px;
        font-weight: 600;
        font-size: 11px;
    """
