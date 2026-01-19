"""
TuneSleuth GUI Entry Point

Launch the TuneSleuth graphical application.
"""

import sys

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QApplication

from tunesleuth_gui.main_window import MainWindow


def main():
    """Launch the TuneSleuth GUI application."""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)

    # Set application metadata
    app.setApplicationName("TuneSleuth")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("TuneSleuth")
    app.setOrganizationDomain("tunesleuth.com")

    # Set default font
    font = QFont()
    font.setFamily("Inter")
    font.setPointSize(13)
    app.setFont(font)

    # Create and show main window
    window = MainWindow()
    window.show()

    # Run event loop
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
