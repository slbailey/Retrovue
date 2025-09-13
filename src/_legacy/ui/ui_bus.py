# ui_bus.py
from PySide6.QtCore import QObject, Signal

class UiBus(QObject):
    sync_started   = Signal(int, int)           # server_id, library_id
    page_progress  = Signal(int, int, int, int, int, int)  # server, lib, processed, changed, skipped, errors
    sync_completed = Signal(int, int, dict)     # server_id, library_id, summary
