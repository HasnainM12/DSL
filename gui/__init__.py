"""
gui — DSL Tree Visualizer package.
Provides a ``main()`` entry point for launching the application.
"""

from gui.app import DSLVisualizerApp


def main():
    """Create and run the DSL Tree Visualizer application."""
    app = DSLVisualizerApp()
    app.run()
