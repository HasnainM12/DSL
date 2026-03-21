"""
gui — DSL Tree Visualizer package (PyQt6 version).
Provides a ``main()`` entry point for launching the application.
"""

import sys


def main():
    from PyQt6.QtWidgets import QApplication
    from PyQt6.QtGui import QFont
    from gui.app import DSLVisualizerApp

    app = QApplication(sys.argv)

    # Inter is a clean modern font; fall back gracefully if absent.
    app.setFont(QFont("Inter", 13))

    window = DSLVisualizerApp()
    window.show()

    sys.exit(app.exec())
