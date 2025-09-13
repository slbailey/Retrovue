# run_ui_v2.py
import sys
import os
from PySide6.QtWidgets import QApplication

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from retrovue.core.database import RetrovueDatabase
from retrovue.ui_v2.main_window_v2 import MainWindowV2

def main(db_path="retrovue.db"):
    app = QApplication(sys.argv)
    db = RetrovueDatabase(db_path)
    w = MainWindowV2(db)
    w.resize(1200, 800)
    w.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "retrovue.db")

