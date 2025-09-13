# ui_v2/main_window_v2.py
from PySide6.QtWidgets import QMainWindow, QWidget, QHBoxLayout, QListWidget, QStackedWidget, QToolBar, QCheckBox, QApplication, QMessageBox
from PySide6.QtGui import QAction
from PySide6.QtCore import Qt
import sys
import os

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from retrovue.ui.ui_bus import UiBus
from retrovue.ui.import_worker import ImportWorker
import retrovue.core.plex_integration as sync_api

from .pages.browse_page import BrowsePage
from .pages.libraries_page import LibrariesPage

class MainWindowV2(QMainWindow):
    def __init__(self, database):
        super().__init__()
        self.setWindowTitle("Retrovue v2")
        self.db = database

        # event bus + worker wiring
        self.ui_bus = UiBus()
        self.ui_bus.sync_started.connect(self._on_sync_started)
        self.ui_bus.page_progress.connect(self._on_page_progress)
        self.ui_bus.sync_completed.connect(self._on_sync_completed)

        # left nav + stacked pages
        self.nav = QListWidget()
        self.nav.addItems(["Browse", "Libraries & Sync"])
        self.pages = QStackedWidget()

        self.browse = BrowsePage(self.db)
        self.libs   = LibrariesPage(self.db)

        self.pages.addWidget(self.browse)
        self.pages.addWidget(self.libs)

        container = QWidget(); lay = QHBoxLayout(container); lay.setContentsMargins(0,0,0,0)
        lay.addWidget(self.nav, 1); lay.addWidget(self.pages, 5)
        self.setCentralWidget(container)

        self.nav.currentRowChanged.connect(self._on_nav_changed)
        self.nav.setCurrentRow(0)  # default

        # toolbar
        tb = QToolBar("Main"); self.addToolBar(Qt.TopToolBarArea, tb)
        self.actSyncAll   = QAction("Sync Selected (All Servers)", self)
        self.actSyncSrv   = QAction("Sync Selected (Server)", self)
        self.actRefresh   = QAction("Refresh Browse", self)
        self.chkDeep = QCheckBox("Deep"); self.chkDry = QCheckBox("Dry Run")

        self.actSyncAll.triggered.connect(self._sync_all)
        self.actSyncSrv.triggered.connect(self._sync_server)
        self.actRefresh.triggered.connect(self.browse.refresh)

        tb.addAction(self.actSyncAll)
        tb.addAction(self.actSyncSrv)
        tb.addAction(self.actRefresh)
        tb.addWidget(self.chkDeep); tb.addWidget(self.chkDry)

        # initial data load
        self.browse.refresh()

    # ---------- sync starters ----------
    def _start_worker(self, mode, server_id=None):
        w = ImportWorker(
            db_path=self.db.db_path if hasattr(self.db, 'db_path') else 'retrovue.db',
            ui_bus=self.ui_bus, mode=mode,
            server_id=server_id, library_ref=None,
            deep=self.chkDeep.isChecked(), dry_run=self.chkDry.isChecked(),
            sync_api=sync_api
        )
        w.start()
        self._last_worker = w

    def _sync_all(self):
        self._start_worker("all_selected")

    def _sync_server(self):
        sid = self.libs.current_server_id()
        if sid is None:
            QMessageBox.warning(self, "No server selected", "Pick a server in 'Libraries & Sync'.")
            return
        self._start_worker("server_selected", server_id=sid)

    # ---------- events ----------
    def _on_nav_changed(self, idx: int):
        self.pages.setCurrentIndex(idx)
        if self.pages.currentWidget() is self.browse:
            self.browse.refresh()
        elif self.pages.currentWidget() is self.libs:
            self.libs.refresh()

    def _on_sync_started(self, server_id, library_id):
        self.statusBar().showMessage(f"Sync started: server={server_id}, library={library_id}")

    def _on_page_progress(self, *a):
        pass  # optional: stream to a log view

    def _on_sync_completed(self, server_id, library_id, summary: dict):
        self.statusBar().showMessage(
            f"Sync finished (+{summary.get('changed',0)} ~{summary.get('skipped',0)} !{summary.get('errors',0)})"
        )
        # Always refresh Browse after a sync
        self.browse.refresh()
