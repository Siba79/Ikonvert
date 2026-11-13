#!/usr/bin/env python3
"""
Ikonvert - drop any image to make a multi-size .ico,
or drop an .ico to preview every size and extract them as PNGs.

Portable: settings are stored in settings.json next to the program.

Copyright (c) 2026 Stefan Karlsson
Licensed under the MIT License (see LICENSE).
"""

import json
import os
import subprocess
import sys

from PySide6.QtCore import QPoint, QRect, QSize, Qt, QUrl
from PySide6.QtGui import (QColor, QDesktopServices, QIcon, QImage, QPainter,
                           QPalette, QPixmap)
from PySide6.QtWidgets import (QApplication, QComboBox, QFileDialog, QFrame,
                               QHBoxLayout, QLabel, QLayout, QListWidget,
                               QListWidgetItem, QMainWindow, QMessageBox,
                               QPushButton, QScrollArea, QSizePolicy,
                               QVBoxLayout, QWidget)

import ico_core as core
from version import APP_NAME, AUTHOR, LICENSE, __version__ as APP_VERSION


# ----------------------------------------------------------------------------
# Paths & portable settings
# ----------------------------------------------------------------------------
def app_dir() -> str:
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def resource(name: str) -> str:
    return os.path.join(getattr(sys, "_MEIPASS", app_dir()), name)


SETTINGS_FILE = os.path.join(app_dir(), "settings.json")


def load_settings() -> dict:
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_settings(data: dict) -> None:
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass  # read-only folder: just don't remember settings


# ----------------------------------------------------------------------------
# Theme
# ----------------------------------------------------------------------------
THEMES = {
    "light": {
        "window": "#f3f4f6", "base": "#ffffff", "alt": "#f6f7f9",
        "text": "#1f2328", "muted": "#6b7280", "border": "#d1d5db",
        "button": "#ffffff", "button_hover": "#eef0f3",
        "accent": "#3b82f6", "accent_hover": "#2563eb",
        "drop": "#ffffff", "drop_hover": "#eaf2ff",
        "tile": "#ffffff", "check1": "#ffffff", "check2": "#e5e7eb",
        "disabled": "#e5e7eb",
    },
    "dark": {
        "window": "#202124", "base": "#18191c", "alt": "#26272b",
        "text": "#e6e6e6", "muted": "#9aa0a6", "border": "#3c3f44",
        "button": "#2d2e32", "button_hover": "#37383d",
        "accent": "#3b82f6", "accent_hover": "#60a5fa",
        "drop": "#26272b", "drop_hover": "#1e2a3d",
        "tile": "#26272b", "check1": "#3a3b3f", "check2": "#2c2d31",
        "disabled": "#34363a",
    },
}


def make_palette(c: dict) -> QPalette:
    R = QPalette.ColorRole
    p = QPalette()
    p.setColor(R.Window, QColor(c["window"]))
    p.setColor(R.WindowText, QColor(c["text"]))
    p.setColor(R.Base, QColor(c["base"]))
    p.setColor(R.AlternateBase, QColor(c["alt"]))
    p.setColor(R.ToolTipBase, QColor(c["base"]))
    p.setColor(R.ToolTipText, QColor(c["text"]))
    p.setColor(R.Text, QColor(c["text"]))
    p.setColor(R.Button, QColor(c["button"]))
    p.setColor(R.ButtonText, QColor(c["text"]))
    p.setColor(R.Highlight, QColor(c["accent"]))
    p.setColor(R.HighlightedText, QColor("#ffffff"))
    p.setColor(R.PlaceholderText, QColor(c["muted"]))
    p.setColor(R.Link, QColor(c["accent"]))
    for role in (R.Text, R.WindowText, R.ButtonText):
        p.setColor(QPalette.ColorGroup.Disabled, role, QColor(c["muted"]))
    return p


def make_stylesheet(c: dict) -> str:
    return f"""
    QWidget {{ font-size: 10pt; }}
    QLabel#title {{ font-size: 15pt; font-weight: 600; }}
    QLabel#muted, QLabel#caption {{ color: {c['muted']}; }}
    QLabel#info {{ font-size: 10.5pt; }}

    QFrame#dropzone {{
        border: 2px dashed {c['border']}; border-radius: 12px;
        background: {c['drop']};
    }}
    QFrame#dropzone[hover="true"] {{
        border-color: {c['accent']}; background: {c['drop_hover']};
    }}
    QFrame#tile {{
        background: {c['tile']}; border: 1px solid {c['border']};
        border-radius: 8px;
    }}
    QFrame#panel {{
        background: {c['base']}; border: 1px solid {c['border']};
        border-radius: 10px;
    }}

    QPushButton {{
        background: {c['button']}; border: 1px solid {c['border']};
        border-radius: 6px; padding: 6px 14px; color: {c['text']};
    }}
    QPushButton:hover {{ background: {c['button_hover']}; }}
    QPushButton:disabled {{ color: {c['muted']}; background: {c['disabled']}; }}
    QPushButton#primary {{
        background: {c['accent']}; color: white; border: none;
        font-weight: 600; padding: 8px 20px;
    }}
    QPushButton#primary:hover {{ background: {c['accent_hover']}; }}
    QPushButton#primary:disabled {{ background: {c['disabled']}; color: {c['muted']}; }}

    QListWidget {{
        background: {c['base']}; border: 1px solid {c['border']};
        border-radius: 8px; padding: 4px;
    }}
    QListWidget::item {{ padding: 4px; border-radius: 4px; }}
    QScrollArea {{ border: none; background: transparent; }}
    QComboBox {{
        background: {c['button']}; border: 1px solid {c['border']};
        border-radius: 6px; padding: 4px 8px; color: {c['text']};
    }}
    QStatusBar {{ color: {c['muted']}; }}
    """


# ----------------------------------------------------------------------------
# Helpers
# ----------------------------------------------------------------------------
def pil_to_qimage(img) -> QImage:
    img = img.convert("RGBA")
    data = img.tobytes("raw", "RGBA")
    qimg = QImage(data, img.width, img.height, img.width * 4,
                  QImage.Format.Format_RGBA8888)
    return qimg.copy()  # own the memory


def checker_pixmap(w: int, h: int, c1: str, c2: str, cell: int = 8) -> QPixmap:
    pm = QPixmap(w, h)
    pm.fill(QColor(c1))
    p = QPainter(pm)
    col = QColor(c2)
    for y in range(0, h, cell):
        for x in range(0, w, cell):
            if (x // cell + y // cell) % 2:
                p.fillRect(x, y, cell, cell, col)
    p.end()
    return pm


class FlowLayout(QLayout):
    """Wraps widgets onto new rows; items in a row are bottom-aligned."""

    def __init__(self, parent=None, spacing=12):
        super().__init__(parent)
        self._items = []
        self.setSpacing(spacing)
        self.setContentsMargins(12, 12, 12, 12)

    def addItem(self, item):
        self._items.append(item)

    def count(self):
        return len(self._items)

    def itemAt(self, i):
        return self._items[i] if 0 <= i < len(self._items) else None

    def takeAt(self, i):
        return self._items.pop(i) if 0 <= i < len(self._items) else None

    def expandingDirections(self):
        return Qt.Orientation(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._layout(QRect(0, 0, width, 0), apply=False)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._layout(rect, apply=True)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for it in self._items:
            size = size.expandedTo(it.minimumSize())
        m = self.contentsMargins()
        return size + QSize(m.left() + m.right(), m.top() + m.bottom())

    def _layout(self, rect, apply):
        m = self.contentsMargins()
        area = rect.adjusted(m.left(), m.top(), -m.right(), -m.bottom())
        sp = self.spacing()
        rows, row, row_w = [], [], 0
        for it in self._items:
            w = it.sizeHint().width()
            if row and row_w + sp + w > area.width():
                rows.append(row)
                row, row_w = [], 0
            row_w += (sp if row else 0) + w
            row.append(it)
        if row:
            rows.append(row)

        y = area.y()
        for row in rows:
            row_h = max(it.sizeHint().height() for it in row)
            x = area.x()
            for it in row:
                hint = it.sizeHint()
                if apply:
                    it.setGeometry(QRect(QPoint(x, y + row_h - hint.height()), hint))
                x += hint.width() + sp
            y += row_h + sp
        return y - sp - rect.y() + m.bottom() if rows else m.top() + m.bottom()


class PreviewTile(QFrame):
    def __init__(self, img, caption: str, zoom: int, colors: dict):
        super().__init__()
        self.setObjectName("tile")
        w, h = img.width * zoom, img.height * zoom
        pm = checker_pixmap(w, h, colors["check1"], colors["check2"])
        p = QPainter(pm)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)
        p.drawImage(QRect(0, 0, w, h), pil_to_qimage(img))  # crisp pixels
        p.end()

        pic = QLabel()
        pic.setPixmap(pm)
        pic.setFixedSize(w, h)
        cap = QLabel(caption)
        cap.setObjectName("caption")
        cap.setAlignment(Qt.AlignmentFlag.AlignCenter)

        lay = QVBoxLayout(self)
        lay.setContentsMargins(10, 10, 10, 8)
        lay.setSpacing(6)
        lay.addWidget(pic, 0, Qt.AlignmentFlag.AlignHCenter)
        lay.addWidget(cap)
        self.setMinimumWidth(80)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)


class DropZone(QFrame):
    def __init__(self, on_click):
        super().__init__()
        self.setObjectName("dropzone")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setMinimumHeight(150)
        self._on_click = on_click

        big = QLabel("⬇")
        big.setAlignment(Qt.AlignmentFlag.AlignCenter)
        big.setStyleSheet("font-size: 26pt; background: transparent;")
        txt = QLabel("Drop images or .ico files here")
        txt.setAlignment(Qt.AlignmentFlag.AlignCenter)
        txt.setStyleSheet("font-weight: 600; background: transparent;")
        sub = QLabel("or click to browse")
        sub.setObjectName("muted")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet("background: transparent;")

        lay = QVBoxLayout(self)
        lay.addStretch()
        lay.addWidget(big)
        lay.addWidget(txt)
        lay.addWidget(sub)
        lay.addStretch()

    def set_hover(self, on: bool):
        self.setProperty("hover", on)
        self.style().unpolish(self)
        self.style().polish(self)

    def mousePressEvent(self, e):
        if e.button() == Qt.MouseButton.LeftButton:
            self._on_click()


# ----------------------------------------------------------------------------
# Main window
# ----------------------------------------------------------------------------
class MainWindow(QMainWindow):
    def __init__(self, files):
        super().__init__()
        self.settings = load_settings()
        self.theme = "dark" if self.settings.get("theme") == "dark" else "light"
        zoom = self.settings.get("zoom", 1)
        self.zoom = zoom if zoom in (1, 2, 4) else 1
        self.cache = {}          # path -> loaded data
        self.last_output = None  # last saved file/folder

        self.setWindowTitle(f"{APP_NAME} {APP_VERSION}")
        icon_file = resource(os.path.join("assets", "app.ico"))
        if os.path.exists(icon_file):
            self.setWindowIcon(QIcon(icon_file))
        self.resize(1080, 700)
        self.setMinimumSize(820, 560)
        self.setAcceptDrops(True)

        self._build_ui()
        self.apply_theme()
        self.add_files(files)
        self._update_buttons()

    # -- UI -------------------------------------------------------------------
    def _build_ui(self):
        root = QWidget()
        self.setCentralWidget(root)
        outer = QVBoxLayout(root)
        outer.setContentsMargins(16, 12, 16, 8)
        outer.setSpacing(12)

        # Header
        head = QHBoxLayout()
        title = QLabel(APP_NAME)
        title.setObjectName("title")
        subtitle = QLabel("Images → .ico  ·  .ico → PNGs")
        subtitle.setObjectName("muted")
        self.theme_btn = QPushButton()
        self.theme_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.theme_btn.clicked.connect(self.toggle_theme)
        head.addWidget(title)
        head.addSpacing(10)
        head.addWidget(subtitle)
        head.addStretch()
        about_btn = QPushButton("ⓘ  About")
        about_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        about_btn.clicked.connect(self.show_about)
        head.addWidget(about_btn)
        head.addWidget(self.theme_btn)
        outer.addLayout(head)

        body = QHBoxLayout()
        body.setSpacing(14)
        outer.addLayout(body, 1)

        # Left side: drop zone + file list
        left = QVBoxLayout()
        left.setSpacing(8)
        self.drop_zone = DropZone(self.browse)
        browse_btn = QPushButton("📂  Browse…")
        browse_btn.clicked.connect(self.browse)
        self.file_list = QListWidget()
        self.file_list.setAcceptDrops(False)
        self.file_list.setIconSize(QSize(24, 24))
        self.file_list.currentItemChanged.connect(lambda *_: self.show_preview())
        list_btns = QHBoxLayout()
        self.remove_btn = QPushButton("Remove")
        self.remove_btn.clicked.connect(self.remove_selected)
        self.clear_btn = QPushButton("Clear all")
        self.clear_btn.clicked.connect(self.clear_all)
        list_btns.addWidget(self.remove_btn)
        list_btns.addWidget(self.clear_btn)

        files_lbl = QLabel("Files")
        files_lbl.setObjectName("muted")
        left.addWidget(self.drop_zone)
        left.addWidget(browse_btn)
        left.addSpacing(4)
        left.addWidget(files_lbl)
        left.addWidget(self.file_list, 1)
        left.addLayout(list_btns)
        left_w = QWidget()
        left_w.setLayout(left)
        left_w.setFixedWidth(290)
        body.addWidget(left_w)

        # Right side: preview panel
        panel = QFrame()
        panel.setObjectName("panel")
        right = QVBoxLayout(panel)
        right.setContentsMargins(14, 12, 14, 12)
        right.setSpacing(8)

        top = QHBoxLayout()
        self.name_lbl = QLabel("No file selected")
        self.name_lbl.setStyleSheet("font-weight: 600; font-size: 11pt;")
        zoom_lbl = QLabel("Zoom")
        zoom_lbl.setObjectName("muted")
        self.zoom_box = QComboBox()
        self.zoom_box.addItems(["100%", "200%", "400%"])
        self.zoom_box.setCurrentIndex({1: 0, 2: 1, 4: 2}[self.zoom])
        self.zoom_box.currentIndexChanged.connect(self.change_zoom)
        top.addWidget(self.name_lbl, 1)
        top.addWidget(zoom_lbl)
        top.addWidget(self.zoom_box)
        right.addLayout(top)

        self.info_lbl = QLabel("Drop an image to create an icon, or an .ico to see every size inside it.")
        self.info_lbl.setObjectName("info")
        self.info_lbl.setWordWrap(True)
        right.addWidget(self.info_lbl)

        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll.setAcceptDrops(False)
        self.preview_host = QWidget()
        self.flow = FlowLayout(self.preview_host)
        self.scroll.setWidget(self.preview_host)
        right.addWidget(self.scroll, 1)

        actions = QHBoxLayout()
        self.open_btn = QPushButton("📁  Open output folder")
        self.open_btn.clicked.connect(self.open_output)
        self.all_btn = QPushButton("Convert all")
        self.all_btn.clicked.connect(self.convert_all)
        self.main_btn = QPushButton("Create ICO")
        self.main_btn.setObjectName("primary")
        self.main_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.main_btn.clicked.connect(self.convert_current)
        actions.addWidget(self.open_btn)
        actions.addStretch()
        actions.addWidget(self.all_btn)
        actions.addWidget(self.main_btn)
        right.addLayout(actions)

        body.addWidget(panel, 1)
        self.statusBar().showMessage(f"Icon sizes: {', '.join(map(str, core.SIZES))} px")

    # -- About ----------------------------------------------------------------
    def show_about(self):
        box = QMessageBox(self)
        box.setWindowTitle(f"About {APP_NAME}")
        icon_file = resource(os.path.join("assets", "app.ico"))
        if os.path.exists(icon_file):
            box.setIconPixmap(QIcon(icon_file).pixmap(64, 64))
        box.setTextFormat(Qt.TextFormat.RichText)
        box.setText(
            f"<h3>{APP_NAME} {APP_VERSION}</h3>"
            "<p>Images → multi-size .ico, and .ico → PNGs.</p>"
            f"<p>© 2026 {AUTHOR}<br>Free and open source under the {LICENSE} License.</p>"
            "<p style='font-size:9pt'>Built with Python, "
            "<a href='https://www.qt.io/qt-for-python'>Qt for Python (PySide6)</a> "
            "under the LGPLv3, and "
            "<a href='https://python-pillow.github.io/'>Pillow</a>.<br>"
            "See LICENSE and THIRD_PARTY_NOTICES.md for details.</p>")
        box.exec()

    # -- Theme ----------------------------------------------------------------
    def colors(self) -> dict:
        return THEMES[self.theme]

    def apply_theme(self):
        app = QApplication.instance()
        hints = app.styleHints()
        if hasattr(hints, "setColorScheme"):  # Qt 6.8+: matching title bar
            try:
                hints.setColorScheme(Qt.ColorScheme.Dark if self.theme == "dark"
                                     else Qt.ColorScheme.Light)
            except Exception:
                pass
        app.setPalette(make_palette(self.colors()))
        app.setStyleSheet(make_stylesheet(self.colors()))
        self.theme_btn.setText("☀️  Light mode" if self.theme == "dark" else "🌙  Dark mode")
        self.show_preview()  # redraw checkerboards

    def toggle_theme(self):
        self.theme = "light" if self.theme == "dark" else "dark"
        self.settings["theme"] = self.theme
        save_settings(self.settings)
        self.apply_theme()

    def change_zoom(self, index):
        self.zoom = (1, 2, 4)[index]
        self.settings["zoom"] = self.zoom
        save_settings(self.settings)
        self.show_preview()

    # -- Drag & drop ----------------------------------------------------------
    def dragEnterEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()
            self.drop_zone.set_hover(True)

    def dragMoveEvent(self, e):
        if e.mimeData().hasUrls():
            e.acceptProposedAction()

    def dragLeaveEvent(self, e):
        self.drop_zone.set_hover(False)

    def dropEvent(self, e):
        self.drop_zone.set_hover(False)
        paths = [u.toLocalFile() for u in e.mimeData().urls() if u.isLocalFile()]
        e.acceptProposedAction()
        self.add_files(paths)

    # -- Files ----------------------------------------------------------------
    def browse(self):
        exts = " ".join(f"*{x}" for x in sorted(core.IMAGE_EXTS))
        start = self.settings.get("last_dir", "")
        if not os.path.isdir(start):
            start = ""
        paths, _ = QFileDialog.getOpenFileNames(
            self, "Choose images or icons", start,
            f"Images and icons ({exts});;All files (*)")
        if paths:
            self.settings["last_dir"] = os.path.dirname(paths[0])
            save_settings(self.settings)
            self.add_files(paths)

    def add_files(self, paths):
        expanded = []
        for p in paths:
            if os.path.isdir(p):
                for name in sorted(os.listdir(p)):
                    full = os.path.join(p, name)
                    if os.path.isfile(full) and core.is_supported(full):
                        expanded.append(full)
            elif os.path.isfile(p):
                expanded.append(p)

        added, skipped, failed = [], 0, []
        for p in expanded:
            p = os.path.normpath(os.path.abspath(p))
            if p in self.cache:
                continue
            if not core.is_supported(p):
                skipped += 1
                continue
            try:
                self.cache[p] = self._load(p)
            except Exception as ex:
                failed.append(f"{os.path.basename(p)}: {ex}")
                continue
            item = QListWidgetItem(os.path.basename(p))
            item.setToolTip(p)
            item.setData(Qt.ItemDataRole.UserRole, p)
            item.setIcon(QIcon(QPixmap.fromImage(pil_to_qimage(self.cache[p]["thumb"]))))
            self.file_list.addItem(item)
            added.append(item)

        if added:
            self.file_list.setCurrentItem(added[0])
        msg = f"Added {len(added)} file(s)"
        if skipped:
            msg += f" · skipped {skipped} unsupported"
        if failed:
            msg += f" · {len(failed)} could not be opened"
            QMessageBox.warning(self, "Could not open",
                                "These files could not be opened:\n\n" + "\n".join(failed[:15]))
        if expanded:
            self.statusBar().showMessage(msg)
        self._update_buttons()

    def _load(self, path: str) -> dict:
        if core.is_ico(path):
            frames = core.read_ico(path)
            thumb = min(frames, key=lambda f: abs(f["width"] - 32))["image"]
            return {"kind": "ico", "frames": frames, "thumb": thumb}
        data = core.load_image(path)
        frames = core.build_frames(data["image"])
        return {"kind": "image", "frames": frames, "thumb": frames[core.SIZES.index(32)] if 32 in core.SIZES else frames[0],
                "has_alpha": data["has_alpha"], "size": data["size"],
                "format": data["format"]}

    def current_path(self):
        item = self.file_list.currentItem()
        return item.data(Qt.ItemDataRole.UserRole) if item else None

    def remove_selected(self):
        row = self.file_list.currentRow()
        if row < 0:
            return
        item = self.file_list.takeItem(row)
        self.cache.pop(item.data(Qt.ItemDataRole.UserRole), None)
        self.show_preview()
        self._update_buttons()

    def clear_all(self):
        self.file_list.clear()
        self.cache.clear()
        self.show_preview()
        self._update_buttons()

    # -- Preview --------------------------------------------------------------
    def _clear_tiles(self):
        while self.flow.count():
            it = self.flow.takeAt(0)
            if it.widget():
                it.widget().deleteLater()

    def show_preview(self):
        if not hasattr(self, "flow"):
            return
        self._clear_tiles()
        path = self.current_path()
        if not path or path not in self.cache:
            self.name_lbl.setText("No file selected")
            self.info_lbl.setText("Drop an image to create an icon, or an .ico to see every size inside it.")
            self._update_buttons()
            return

        d = self.cache[path]
        self.name_lbl.setText(os.path.basename(path))
        c = self.colors()

        if d["kind"] == "ico":
            n = len(d["frames"])
            self.info_lbl.setText(f"🔷 Icon file · {n} image{'s' if n != 1 else ''} inside. "
                                  f"Extracting saves them to “{os.path.basename(core.png_dir_for(path))}”.")
            for f in d["frames"]:
                cap = f"{f['width']} × {f['height']}\n{f['bpp']}-bit"
                self.flow.addWidget(PreviewTile(f["image"], cap, self.zoom, c))
        else:
            w, h = d["size"]
            parts = [f"🖼 {d['format']} · {w} × {h}"]
            parts.append("✅ Transparency found and kept" if d["has_alpha"]
                         else "⬜ No transparency, the icon will be opaque")
            if w != h:
                parts.append("↔ Not square, centred on a transparent square")
            if max(w, h) < max(core.SIZES):
                parts.append(f"⚠️ Smaller than {max(core.SIZES)} px, big sizes are upscaled")
            self.info_lbl.setText("  ·  ".join(parts))
            for f in reversed(d["frames"]):
                self.flow.addWidget(PreviewTile(f, f"{f.width} × {f.height}", self.zoom, c))

        self._update_buttons()

    def _update_buttons(self):
        if not hasattr(self, "main_btn"):
            return
        path = self.current_path()
        has_any = self.file_list.count() > 0
        kind = self.cache.get(path, {}).get("kind") if path else None
        self.main_btn.setEnabled(kind is not None)
        self.main_btn.setText("Extract PNGs" if kind == "ico" else "Create ICO")
        self.all_btn.setEnabled(self.file_list.count() > 1)
        self.all_btn.setText(f"Convert all ({self.file_list.count()})" if has_any else "Convert all")
        self.remove_btn.setEnabled(path is not None)
        self.clear_btn.setEnabled(has_any)
        self.open_btn.setEnabled(self.last_output is not None)

    # -- Convert --------------------------------------------------------------
    def _target_for(self, path: str) -> str:
        if self.cache[path]["kind"] == "ico":
            return core.png_dir_for(path)
        return core.ico_path_for(path)

    def _exists(self, target: str) -> bool:
        if os.path.isdir(target):
            return len(os.listdir(target)) > 0
        return os.path.exists(target)

    def _convert(self, path: str, state: dict, batch: bool) -> str:
        """Returns 'ok', 'skipped' or 'cancel'. Raises on errors."""
        d = self.cache[path]
        target = self._target_for(path)

        if self._exists(target) and not state.get("all"):
            btns = QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
            if batch:
                btns |= QMessageBox.StandardButton.YesToAll | QMessageBox.StandardButton.Cancel
            what = "folder" if d["kind"] == "ico" else "file"
            r = QMessageBox.question(
                self, "Already exists",
                f"The {what} “{os.path.basename(target)}” already exists.\n\nReplace it?",
                btns, QMessageBox.StandardButton.No)
            if r == QMessageBox.StandardButton.Cancel:
                return "cancel"
            if r == QMessageBox.StandardButton.No:
                return "skipped"
            if r == QMessageBox.StandardButton.YesToAll:
                state["all"] = True

        if d["kind"] == "ico":
            core.save_pngs(path, d["frames"], target)
        else:
            core.save_ico(d["frames"], target)
        self.last_output = target
        return "ok"

    def convert_current(self):
        path = self.current_path()
        if not path:
            return
        try:
            result = self._convert(path, {}, batch=False)
        except Exception as ex:
            QMessageBox.warning(self, "Error", f"Could not convert {os.path.basename(path)}:\n\n{ex}")
            return
        if result == "ok":
            self.statusBar().showMessage(f"✅ Saved: {self.last_output}")
        else:
            self.statusBar().showMessage("Skipped, nothing was replaced")
        self._update_buttons()

    def convert_all(self):
        state, ok, skipped, errors = {}, 0, 0, []
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            for i in range(self.file_list.count()):
                path = self.file_list.item(i).data(Qt.ItemDataRole.UserRole)
                QApplication.restoreOverrideCursor()
                try:
                    result = self._convert(path, state, batch=True)
                except Exception as ex:
                    errors.append(f"{os.path.basename(path)}: {ex}")
                    continue
                finally:
                    QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
                if result == "cancel":
                    break
                if result == "ok":
                    ok += 1
                else:
                    skipped += 1
                QApplication.processEvents()
        finally:
            QApplication.restoreOverrideCursor()

        msg = f"✅ Converted {ok} file(s)"
        if skipped:
            msg += f" · skipped {skipped}"
        if errors:
            msg += f" · {len(errors)} error(s)"
            QMessageBox.warning(self, "Some files failed", "\n".join(errors[:15]))
        self.statusBar().showMessage(msg)
        self._update_buttons()

    def open_output(self):
        target = self.last_output
        if not target or not os.path.exists(target):
            return
        if os.name == "nt":
            subprocess.Popen(["explorer", "/select,", os.path.normpath(target)])
        else:
            folder = target if os.path.isdir(target) else os.path.dirname(target)
            QDesktopServices.openUrl(QUrl.fromLocalFile(folder))


def main():
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setStyle("Fusion")
    win = MainWindow(sys.argv[1:])  # files dropped on the .exe open directly
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
