# ui_v2/pages/libraries_page.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableWidget, QTableWidgetItem, QPushButton, QAbstractItemView
from PySide6.QtCore import Qt

def _conn(db):
    return getattr(db, "connection", None) or getattr(db, "conn", None)

class LibrariesPage(QWidget):
    def __init__(self, database):
        super().__init__()
        self.db = database
        self._build()

    def _build(self):
        v = QVBoxLayout(self)

        # servers
        v.addWidget(QLabel("Plex Servers"))
        self.tblServers = QTableWidget(0, 2, self)
        self.tblServers.setHorizontalHeaderLabels(["ID", "Name"])
        self.tblServers.setSelectionBehavior(QAbstractItemView.SelectRows)
        v.addWidget(self.tblServers)

        # libraries
        hl = QHBoxLayout()
        hl.addWidget(QLabel("Libraries on selected server"))
        self.btnDiscover = QPushButton("Discover & Save")
        self.btnDiscover.setToolTip("Fetch libraries from the selected server and persist")
        self.btnDiscover.clicked.connect(self._discover)
        hl.addStretch(); hl.addWidget(self.btnDiscover)
        v.addLayout(hl)

        self.tblLibs = QTableWidget(0, 4, self)
        self.tblLibs.setHorizontalHeaderLabels(["ID", "Section Key", "Name", "Selected"])
        self.tblLibs.setSelectionBehavior(QAbstractItemView.SelectRows)
        v.addWidget(self.tblLibs)

    def refresh(self):
        self._load_servers()
        self._load_libs()

    def current_server_id(self):
        r = self.tblServers.currentRow()
        if r < 0: return None
        return int(self.tblServers.item(r,0).text())

    # ---- internals ----
    def _load_servers(self):
        c = _conn(self.db).cursor()
        try:
            c.execute("SELECT id, name FROM plex_servers ORDER BY id")
            rows = c.fetchall()
        except Exception:
            rows = []
        self.tblServers.setRowCount(len(rows))
        for i, r in enumerate(rows):
            idv = r[0] if not isinstance(r, dict) else r["id"]
            name = r[1] if not isinstance(r, dict) else r["name"]
            self.tblServers.setItem(i, 0, QTableWidgetItem(str(idv)))
            self.tblServers.setItem(i, 1, QTableWidgetItem(name or ""))
        self.tblServers.resizeColumnsToContents()

    def _load_libs(self):
        sid = self.current_server_id()
        if sid is None:
            self.tblLibs.setRowCount(0)
            return
        c = _conn(self.db).cursor()
        try:
            c.execute("""
                SELECT id, library_key, library_name, COALESCE(sync_enabled,1) as sync_enabled
                FROM libraries
                WHERE server_id = ?
                ORDER BY library_name
            """, (sid,))
            rows = c.fetchall()
        except Exception:
            rows = []
        self.tblLibs.setRowCount(len(rows))
        for i, r in enumerate(rows):
            idv = r[0] if not isinstance(r, dict) else r["id"]
            key = r[1] if not isinstance(r, dict) else r["library_key"]
            name = r[2] if not isinstance(r, dict) else r["library_name"]
            sel  = r[3] if not isinstance(r, dict) else r["sync_enabled"]
            self.tblLibs.setItem(i, 0, QTableWidgetItem(str(idv)))
            self.tblLibs.setItem(i, 1, QTableWidgetItem(str(key)))
            self.tblLibs.setItem(i, 2, QTableWidgetItem(name or ""))
            self.tblLibs.setItem(i, 3, QTableWidgetItem("Yes" if int(sel or 0) else "No"))
        self.tblLibs.resizeColumnsToContents()

    def _discover(self):
        # optional: you can wire your existing create_plex_importer here to refresh/persist libraries
        # For now we just requery DB (assuming your CLI/Sync already persisted them)
        self.refresh()
