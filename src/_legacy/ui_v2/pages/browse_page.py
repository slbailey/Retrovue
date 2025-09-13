# ui_v2/pages/browse_page.py
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QLineEdit, QTableWidget, QTableWidgetItem
from PySide6.QtCore import Qt

def _conn(db):
    return getattr(db, "connection", None) or getattr(db, "conn", None)

class BrowsePage(QWidget):
    def __init__(self, database):
        super().__init__()
        self.db = database
        self._build()

    def _build(self):
        v = QVBoxLayout(self)

        # filters
        fl = QHBoxLayout()
        fl.addWidget(QLabel("Type:"))
        self.cmbType = QComboBox(); self.cmbType.addItems(["Episodes", "Movies", "All"])
        self.cmbType.currentIndexChanged.connect(self.refresh)
        fl.addWidget(self.cmbType)

        fl.addWidget(QLabel("Show:"))
        self.cmbShow = QComboBox(); self.cmbShow.addItem("All"); self.cmbShow.currentIndexChanged.connect(self.refresh)
        fl.addWidget(self.cmbShow)

        fl.addWidget(QLabel("Search:"))
        self.txtSearch = QLineEdit(); self.txtSearch.setPlaceholderText("title contains…")
        self.txtSearch.returnPressed.connect(self.refresh)
        fl.addWidget(self.txtSearch)

        self.btnReload = QPushButton("Reload Filters")
        self.btnReload.clicked.connect(self._reload_filters)
        fl.addWidget(self.btnReload)
        fl.addStretch()
        v.addLayout(fl)

        # table
        self.tbl = QTableWidget(0, 7, self)
        self.tbl.setHorizontalHeaderLabels(["Show", "S", "E", "Title", "Duration", "Library", "Path (plex)"])
        self.tbl.setSortingEnabled(False)  # Temporarily disable to fix display issue
        v.addWidget(self.tbl)

    # ---------- public API ----------
    def refresh(self):
        try:
            # lazy filter reload if empty
            if self.cmbShow.count() <= 1:
                self._reload_filters()
            self._load_rows()
        except Exception as e:
            print(f"[Browse] refresh error: {e}")

    # ---------- internals ----------
    def _reload_filters(self):
        # load shows list from DB
        c = _conn(self.db).cursor()
        try:
            c.execute("SELECT DISTINCT title FROM shows ORDER BY title COLLATE NOCASE")
            titles = [r[0] if not isinstance(r, dict) else r["title"] for r in c.fetchall()]
        except Exception:
            titles = []
        self.cmbShow.blockSignals(True)
        self.cmbShow.clear(); self.cmbShow.addItem("All")
        for t in titles:
            if t: self.cmbShow.addItem(t)
        self.cmbShow.blockSignals(False)

    def _load_rows(self):
        # fetch rows deterministically (no app-level caching)
        conn = _conn(self.db)
        if conn is None:
            print(f"[Browse] No database connection available")
            return
        
        c = conn.cursor()
        qtype = self.cmbType.currentText()
        show = self.cmbShow.currentText()
        needle = (self.txtSearch.text() or "").strip()

        rows = []
        if qtype in ("Episodes", "All"):
            sql = """
            SELECT s.title AS show_title, e.season_number, e.episode_number,
                   COALESCE(e.episode_title,'') AS title, mf.duration AS duration_ms,
                   COALESCE(mf.library_name,'') AS library_name, COALESCE(mf.plex_path,'') AS plex_path
            FROM episodes e
            JOIN shows s ON s.id = e.show_id
            JOIN media_files mf ON mf.id = e.media_file_id
            WHERE 1=1
            """
            params = []
            if show and show != "All":
                sql += " AND s.title = ?"; params.append(show)
            if needle:
                sql += " AND (e.episode_title LIKE ? OR s.title LIKE ?)"; params.extend([f"%{needle}%", f"%{needle}%"])
            sql += " ORDER BY s.title COLLATE NOCASE, e.season_number, e.episode_number LIMIT 2000"
            c.execute(sql, params)
            episode_rows = c.fetchall()
            rows += [self._coerce_row(r) for r in episode_rows]

        if qtype in ("Movies", "All"):
            sql = """
            SELECT COALESCE(s.title,'') AS show_title, 0 AS season_number, 0 AS episode_number,
                   COALESCE(mf_title.title,'') AS title, mf.duration AS duration_ms,
                   COALESCE(mf.library_name,'') AS library_name, COALESCE(mf.plex_path,'') AS plex_path
            FROM media_files mf
            LEFT JOIN shows s ON 1=0 -- keep schema uniform
            LEFT JOIN (SELECT plex_rating_key, '' AS title FROM media_files) mf_title ON mf_title.plex_rating_key = mf.plex_rating_key
            WHERE mf.media_type='movie'
            """
            params = []
            if needle:
                sql += " AND (mf_title.title LIKE ?)"
                params.append(f"%{needle}%")
            sql += " ORDER BY title COLLATE NOCASE LIMIT 2000"
            try:
                c.execute(sql, params)
                rows += [self._coerce_row(r) for r in c.fetchall()]
            except Exception:
                pass  # if you don't store movie titles yet, skip

        self._fill_table(rows)

    def _coerce_row(self, r):
        # support sqlite3.Row or tuples
        if isinstance(r, dict):
            return r
        if hasattr(r, "keys"):
            return {k: r[k] for k in r.keys()}
        # tuple order matches SELECT columns
        return {
            "show_title": r[0], "season_number": r[1], "episode_number": r[2],
            "title": r[3], "duration_ms": r[4], "library_name": r[5], "plex_path": r[6]
        }

    def _fill_table(self, rows):
        tbl = self.tbl
        tbl.setRowCount(len(rows))
        for i, row in enumerate(rows):
            tbl.setItem(i, 0, QTableWidgetItem(row.get("show_title") or ""))
            tbl.setItem(i, 1, QTableWidgetItem(str(row.get("season_number") or 0)))
            tbl.setItem(i, 2, QTableWidgetItem(str(row.get("episode_number") or 0)))
            tbl.setItem(i, 3, QTableWidgetItem(row.get("title") or ""))
            tbl.setItem(i, 4, QTableWidgetItem(self._fmt_ms(row.get("duration_ms"))))
            tbl.setItem(i, 5, QTableWidgetItem(row.get("library_name") or ""))
            tbl.setItem(i, 6, QTableWidgetItem(row.get("plex_path") or ""))
        tbl.resizeColumnsToContents()
        tbl.viewport().update()  # Force UI refresh

    def _fmt_ms(self, ms):
        try:
            ms = int(ms or 0)
            s = ms // 1000
            h = s // 3600; m = (s % 3600) // 60; ss = s % 60
            return f"{h:d}:{m:02d}:{ss:02d}"
        except Exception:
            return ""
