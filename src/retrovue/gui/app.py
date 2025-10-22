"""
Main Qt application window for Retrovue.
"""

from PySide6.QtWidgets import QMainWindow, QTabWidget, QWidget, QVBoxLayout
from PySide6.QtCore import Qt
from .router import PAGES
from .store import store


class RetrovueApp(QMainWindow):
    """Main application window with tabbed interface."""
    
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Retrovue")
        self.setGeometry(100, 100, 1200, 800)
        
        # Central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        
        # Tab widget for main pages
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)
        
        # Load pages from router
        for page_config in PAGES:
            page_widget = page_config["factory"](self)
            self.tabs.addTab(page_widget, page_config["title"])
    
    def get_store(self):
        """Access to shared application store."""
        return store


def launch():
    """Launch the Retrovue Qt application."""
    from PySide6.QtWidgets import QApplication
    import sys
    
    app = QApplication(sys.argv)
    app.setApplicationName("Retrovue")
    app.setApplicationVersion("2.0.0")
    
    window = RetrovueApp()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    launch()

