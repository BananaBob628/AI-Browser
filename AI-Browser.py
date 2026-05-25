import json
import os
import sys
import ctypes
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus, urlparse

from PyQt5.QtCore import QByteArray, QTimer, QUrl, Qt, QSize, pyqtSignal
from PyQt5.QtGui import QIcon, QKeySequence, QPainter, QPixmap
from PyQt5.QtNetwork import QNetworkAccessManager, QNetworkRequest
from PyQt5.QtSvg import QSvgRenderer
from PyQt5.QtWidgets import (
    QAction,
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QShortcut,
    QSizePolicy,
    QSplitter,
    QStyle,
    QTabBar,
    QTabWidget,
    QToolButton,
    QToolBar,
    QVBoxLayout,
    QWidget,
)
from PyQt5.QtWebEngineCore import QWebEngineUrlRequestInterceptor
from PyQt5.QtWebEngineWidgets import (
    QWebEngineDownloadItem,
    QWebEnginePage,
    QWebEngineProfile,
    QWebEngineSettings,
    QWebEngineView,
)


APP_NAME = "AI Browser"
NEW_TAB_URL = "https://ai.browser/new-tab"
HOME_URL = NEW_TAB_URL
SEARCH_ENGINES = {
    "Google": "https://www.google.com/search?q={query}",
    "DuckDuckGo": "https://duckduckgo.com/?q={query}",
    "Bing": "https://www.bing.com/search?q={query}",
    "Brave": "https://search.brave.com/search?q={query}",
}

DEFAULT_FAVORITES = [
    {"title": "GitHub", "url": "https://github.com"},
    {"title": "Bing", "url": "https://www.bing.com"},
    {"title": "YouTube", "url": "https://www.youtube.com"},
    {"title": "Office", "url": "https://www.office.com"},
    {"title": "Google", "url": "https://www.google.com"},
]

BLOCKED_HOST_PARTS = (
    "doubleclick.net",
    "googlesyndication.com",
    "google-analytics.com",
    "adservice.google.",
    "adsystem.com",
    "adnxs.com",
    "taboola.com",
    "outbrain.com",
    "scorecardresearch.com",
    "facebook.net",
    "tracking",
    "analytics",
)

ICON_SVGS = {
    "back": "<path d='M15 6 9 12l6 6'/><path d='M10 12h11'/>",
    "forward": "<path d='m9 6 6 6-6 6'/><path d='M3 12h11'/>",
    "reload": "<path d='M21 12a9 9 0 1 1-2.64-6.36'/><path d='M21 3v6h-6'/>",
    "home": "<path d='m3 11 9-8 9 8'/><path d='M5 10v10h14V10'/><path d='M9 20v-6h6v6'/>",
    "star": "<path d='m12 3 2.72 5.51 6.08.88-4.4 4.29 1.04 6.06L12 16.88l-5.44 2.86 1.04-6.06-4.4-4.29 6.08-.88L12 3Z'/>",
    "tab": "<path d='M4 5h9l3 4h4v10H4z'/><path d='M8 9h4'/><path d='M8 13h8'/>",
    "folder": "<path d='M3 6h6l2 2h10v10a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2Z'/>",
    "menu": "<path d='M5 7h14'/><path d='M5 12h14'/><path d='M5 17h14'/>",
    "find": "<circle cx='11' cy='11' r='7'/><path d='m16.5 16.5 4 4'/>",
    "reader": "<path d='M4 5h7a4 4 0 0 1 4 4v10H8a4 4 0 0 0-4 4Z'/><path d='M20 5h-5a4 4 0 0 0-4 4v10h5a4 4 0 0 1 4 4Z'/>",
    "history": "<path d='M3 12a9 9 0 1 0 3-6.7'/><path d='M3 4v6h6'/><path d='M12 7v5l3 2'/>",
    "zoom_in": "<circle cx='11' cy='11' r='7'/><path d='m16.5 16.5 4 4'/><path d='M11 8v6'/><path d='M8 11h6'/>",
    "zoom_out": "<circle cx='11' cy='11' r='7'/><path d='m16.5 16.5 4 4'/><path d='M8 11h6'/>",
    "open": "<path d='M4 20h16'/><path d='M12 4v11'/><path d='m7 10 5 5 5-5'/>",
    "shield": "<path d='M12 3 5 6v5c0 5 3.3 8.5 7 10 3.7-1.5 7-5 7-10V6Z'/><path d='m9 12 2 2 4-5'/>",
    "trash": "<path d='M4 7h16'/><path d='M10 11v6'/><path d='M14 11v6'/><path d='M6 7l1 14h10l1-14'/><path d='M9 7V4h6v3'/>",
    "settings": "<path d='M12 15.5a3.5 3.5 0 1 0 0-7 3.5 3.5 0 0 0 0 7Z'/><path d='M19.4 15a1.7 1.7 0 0 0 .34 1.88l.06.06a2 2 0 1 1-2.83 2.83l-.06-.06A1.7 1.7 0 0 0 15 19.4a1.7 1.7 0 0 0-1 .6 1.7 1.7 0 0 0-.4 1.1V21a2 2 0 1 1-4 0v-.09A1.7 1.7 0 0 0 8.6 19.4a1.7 1.7 0 0 0-1.88.34l-.06.06a2 2 0 1 1-2.83-2.83l.06-.06A1.7 1.7 0 0 0 4.6 15a1.7 1.7 0 0 0-.6-1 1.7 1.7 0 0 0-1.1-.4H3a2 2 0 1 1 0-4h.09A1.7 1.7 0 0 0 4.6 8.6a1.7 1.7 0 0 0-.34-1.88l-.06-.06a2 2 0 1 1 2.83-2.83l.06.06A1.7 1.7 0 0 0 9 4.6a1.7 1.7 0 0 0 1-.6 1.7 1.7 0 0 0 .4-1.1V3a2 2 0 1 1 4 0v.09A1.7 1.7 0 0 0 15.4 4.6a1.7 1.7 0 0 0 1.88-.34l.06-.06a2 2 0 1 1 2.83 2.83l-.06.06A1.7 1.7 0 0 0 19.4 9a1.7 1.7 0 0 0 .6 1 1.7 1.7 0 0 0 1.1.4H21a2 2 0 1 1 0 4h-.09a1.7 1.7 0 0 0-1.51.6Z'/>",
    "browser": "<rect x='3' y='4' width='18' height='16' rx='4'/><path d='M3 9h18'/><path d='M8 6.5h.01'/><path d='M11 6.5h.01'/><path d='M8 14h8'/><path d='m13 11 3 3-3 3'/>",
    "close": "<path d='M7 7 17 17'/><path d='M17 7 7 17'/>",
    "plus": "<path d='M12 5v14'/><path d='M5 12h14'/>",
}


def modern_icon(name, color="#dce6f2", size=24):
    paths = ICON_SVGS[name]
    svg = (
        f"<svg xmlns='http://www.w3.org/2000/svg' width='{size}' height='{size}' "
        f"viewBox='0 0 24 24' fill='none' stroke='{color}' stroke-width='2' "
        f"stroke-linecap='round' stroke-linejoin='round'>{paths}</svg>"
    )
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    QSvgRenderer(QByteArray(svg.encode("utf-8"))).render(painter)
    painter.end()
    return QIcon(pixmap)


def browser_app_icon():
    icon = QIcon()
    for size in (16, 24, 32, 48, 64, 128, 256):
        icon.addPixmap(modern_icon("browser", color="#77b7ff", size=size).pixmap(size, size))
    return icon


def browser_app_icon_path():
    path = DATA_DIR / "ai-browser.ico"
    if not path.exists():
        browser_app_icon().pixmap(256, 256).save(str(path), "ICO")
    return str(path)


def set_windows_app_id():
    if sys.platform != "win32":
        return
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("Local.AIBrowser.Modern")
    except Exception:
        pass


def force_windows_window_icon(window):
    if sys.platform != "win32":
        return
    try:
        icon_path = browser_app_icon_path()
        hwnd = int(window.winId())
        image_icon = 1
        lr_load_from_file = 0x00000010
        wm_seticon = 0x0080
        icon_small = 0
        icon_big = 1
        hicon = ctypes.windll.user32.LoadImageW(None, icon_path, image_icon, 0, 0, lr_load_from_file)
        if hicon:
            ctypes.windll.user32.SendMessageW(hwnd, wm_seticon, icon_small, hicon)
            ctypes.windll.user32.SendMessageW(hwnd, wm_seticon, icon_big, hicon)
    except Exception:
        pass


def windows_colorref(hex_color):
    value = hex_color.lstrip("#")
    red = int(value[0:2], 16)
    green = int(value[2:4], 16)
    blue = int(value[4:6], 16)
    return red | (green << 8) | (blue << 16)


def apply_windows_title_bar(window, dark):
    if sys.platform != "win32":
        return
    try:
        hwnd = int(window.winId())
        caption = windows_colorref("#0b0f17" if dark else "#f4f7fb")
        text = windows_colorref("#edf3fb" if dark else "#101827")
        dark_value = ctypes.c_int(1 if dark else 0)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(dark_value), ctypes.sizeof(dark_value))
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 19, ctypes.byref(dark_value), ctypes.sizeof(dark_value))
        caption_value = ctypes.c_uint(caption)
        text_value = ctypes.c_uint(text)
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 35, ctypes.byref(caption_value), ctypes.sizeof(caption_value))
        ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 36, ctypes.byref(text_value), ctypes.sizeof(text_value))
    except Exception:
        pass


def icon_file(name, color="#dce6f2", size=18):
    path = DATA_DIR / f"{name}-{color.replace('#', '')}-{size}.png"
    if not path.exists():
        icon = modern_icon(name, color=color, size=size)
        pixmap = icon.pixmap(size, size)
        pixmap.save(str(path), "PNG")
    return path.as_posix()


def favicon_for_url(url):
    host = urlparse(url).netloc or urlparse("https://" + url).netloc
    letter = (host[:1] or "?").upper()
    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' width='24' height='24' viewBox='0 0 24 24'>"
        "<rect width='24' height='24' rx='7' fill='#313a52'/>"
        f"<text x='12' y='16' text-anchor='middle' font-family='Segoe UI, Arial' "
        f"font-size='12' font-weight='700' fill='#f8fbff'>{letter}</text>"
        "</svg>"
    )
    pixmap = QPixmap(24, 24)
    pixmap.fill(Qt.transparent)
    painter = QPainter(pixmap)
    QSvgRenderer(QByteArray(svg.encode("utf-8"))).render(painter)
    painter.end()
    return QIcon(pixmap)


def official_favicon_url(url):
    parsed = urlparse(url)
    if not parsed.scheme:
        parsed = urlparse("https://" + url)
    if not parsed.netloc:
        return None
    return f"{parsed.scheme}://{parsed.netloc}/favicon.ico"


def app_data_dir():
    root = os.environ.get("APPDATA")
    if root:
        base = Path(root)
    else:
        base = Path.home() / ".config"
    path = base / "AI Browser"
    path.mkdir(parents=True, exist_ok=True)
    return path


DATA_DIR = app_data_dir()
BOOKMARKS_FILE = DATA_DIR / "bookmarks.json"
HISTORY_FILE = DATA_DIR / "history.json"
SETTINGS_FILE = DATA_DIR / "settings.json"
DOWNLOADS_DIR = Path.home() / "Downloads"


def load_json(path, default):
    try:
        if path.exists():
            with path.open("r", encoding="utf-8") as handle:
                return json.load(handle)
    except (OSError, json.JSONDecodeError):
        pass
    return default


def save_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, ensure_ascii=False)


def normalized_address(text, search_engine):
    value = text.strip()
    if not value:
        return QUrl(NEW_TAB_URL)

    lower = value.lower()
    if lower.startswith(("about:", "file://", "http://", "https://")):
        return QUrl(value)

    if Path(value).exists():
        return QUrl.fromLocalFile(str(Path(value).resolve()))

    looks_like_domain = "." in value and " " not in value
    if looks_like_domain or lower.startswith(("localhost", "127.0.0.1")):
        return QUrl("https://" + value)

    template = SEARCH_ENGINES.get(search_engine, SEARCH_ENGINES["Google"])
    return QUrl(template.format(query=quote_plus(value)))


def host_label(url):
    parsed = urlparse(url)
    return parsed.netloc or url


def is_new_tab_url(url):
    value = url.toString() if isinstance(url, QUrl) else str(url)
    return value in {"", "about:blank", NEW_TAB_URL} or value.startswith(NEW_TAB_URL)


class PrivacyInterceptor(QWebEngineUrlRequestInterceptor):
    def __init__(self, browser):
        super().__init__()
        self.browser = browser

    def interceptRequest(self, info):
        if not self.browser.settings_data.get("block_trackers", True):
            return

        host = info.requestUrl().host().lower()
        if any(part in host for part in BLOCKED_HOST_PARTS):
            info.block(True)


class BrowserPage(QWebEnginePage):
    def __init__(self, parent_browser, profile, parent=None):
        super().__init__(profile, parent)
        self.parent_browser = parent_browser

    def createWindow(self, _window_type):
        view = self.parent_browser.add_new_tab(QUrl("about:blank"), "New Tab", switch=True)
        return view.page()

    def certificateError(self, error):
        message = (
            "This site has a certificate problem.\n\n"
            f"{error.errorDescription()}\n\n"
            "Continue anyway?"
        )
        result = QMessageBox.warning(
            self.parent_browser,
            "Security Warning",
            message,
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if result == QMessageBox.Yes:
            error.acceptCertificate()
            return True
        return False


class BrowserTab(QWebEngineView):
    status_message = pyqtSignal(str)

    def __init__(self, parent_browser, profile):
        super().__init__()
        self.parent_browser = parent_browser
        self.setPage(BrowserPage(parent_browser, profile, self))
        self.page().linkHovered.connect(self.status_message.emit)


class ListDialog(QDialog):
    def __init__(self, title, items, open_callback, delete_callback, clear_callback=None):
        super().__init__()
        self.setWindowTitle(title)
        self.resize(760, 520)
        self.items = items
        self.open_callback = open_callback
        self.delete_callback = delete_callback
        self.clear_callback = clear_callback

        layout = QVBoxLayout(self)
        self.search = QLineEdit()
        self.search.setPlaceholderText("Filter")
        self.search.textChanged.connect(self.populate)
        layout.addWidget(self.search)

        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(lambda _item: self.open_selected())
        layout.addWidget(self.list_widget)

        buttons = QHBoxLayout()
        self.open_button = QPushButton("Open")
        self.copy_button = QPushButton("Copy URL")
        self.delete_button = QPushButton("Delete")
        self.clear_button = QPushButton("Clear All")
        self.close_button = QPushButton("Close")

        for button in (
            self.open_button,
            self.copy_button,
            self.delete_button,
            self.clear_button,
            self.close_button,
        ):
            buttons.addWidget(button)
        layout.addLayout(buttons)

        self.open_button.clicked.connect(self.open_selected)
        self.copy_button.clicked.connect(self.copy_selected)
        self.delete_button.clicked.connect(self.delete_selected)
        self.clear_button.clicked.connect(self.clear_all)
        self.close_button.clicked.connect(self.close)
        self.clear_button.setEnabled(clear_callback is not None)
        self.populate()

    def populate(self):
        self.list_widget.clear()
        needle = self.search.text().strip().lower()
        for index, item in enumerate(self.items):
            title = item.get("title") or item.get("url", "")
            url = item.get("url", "")
            when = item.get("time", "")
            haystack = f"{title} {url} {when}".lower()
            if needle and needle not in haystack:
                continue
            row = QListWidgetItem(f"{title}\n{url}\n{when}".strip())
            row.setData(Qt.UserRole, index)
            self.list_widget.addItem(row)

    def selected_index(self):
        item = self.list_widget.currentItem()
        if not item:
            return None
        return item.data(Qt.UserRole)

    def open_selected(self):
        index = self.selected_index()
        if index is not None:
            self.open_callback(self.items[index].get("url", ""))

    def copy_selected(self):
        index = self.selected_index()
        if index is not None:
            QApplication.clipboard().setText(self.items[index].get("url", ""))

    def delete_selected(self):
        index = self.selected_index()
        if index is not None:
            self.delete_callback(index)
            self.items.pop(index)
            self.populate()

    def clear_all(self):
        if not self.clear_callback:
            return
        result = QMessageBox.question(
            self,
            "Clear All",
            "Clear every item in this list?",
            QMessageBox.Yes | QMessageBox.No,
        )
        if result == QMessageBox.Yes:
            self.clear_callback()
            self.items.clear()
            self.populate()


class FindBar(QWidget):
    def __init__(self, parent_browser):
        super().__init__()
        self.parent_browser = parent_browser
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Find in page")
        self.previous_button = QPushButton("Previous")
        self.next_button = QPushButton("Next")
        self.close_button = QPushButton("Close")

        layout.addWidget(QLabel("Find"))
        layout.addWidget(self.input, 1)
        layout.addWidget(self.previous_button)
        layout.addWidget(self.next_button)
        layout.addWidget(self.close_button)

        self.input.textChanged.connect(lambda _text: self.find(False))
        self.input.returnPressed.connect(lambda: self.find(False))
        self.previous_button.clicked.connect(lambda: self.find(True))
        self.next_button.clicked.connect(lambda: self.find(False))
        self.close_button.clicked.connect(self.hide)
        self.hide()

    def show_and_focus(self):
        self.show()
        self.input.selectAll()
        self.input.setFocus()

    def find(self, backwards):
        browser = self.parent_browser.current_browser()
        if not browser:
            return
        flags = QWebEnginePage.FindBackward if backwards else QWebEnginePage.FindFlags()
        browser.findText(self.input.text(), flags)


class SettingsDialog(QDialog):
    def __init__(self, parent_browser):
        super().__init__(parent_browser)
        self.parent_browser = parent_browser
        self.setWindowTitle("Settings")
        self.setWindowIcon(modern_icon("settings"))
        self.resize(440, 250)

        layout = QVBoxLayout(self)
        form = QFormLayout()
        layout.addLayout(form)

        self.search_engine = QComboBox()
        self.search_engine.addItems(SEARCH_ENGINES.keys())
        self.search_engine.setCurrentText(parent_browser.settings_data.get("search_engine", "Google"))
        form.addRow("Search engine", self.search_engine)

        self.restore_tabs = QCheckBox("Restore tabs from last session")
        self.restore_tabs.setChecked(parent_browser.settings_data.get("restore_tabs", True))
        form.addRow("Startup", self.restore_tabs)

        self.block_trackers = QCheckBox("Block common trackers and ad hosts")
        self.block_trackers.setChecked(parent_browser.settings_data.get("block_trackers", True))
        form.addRow("Privacy", self.block_trackers)

        self.show_status = QCheckBox("Show status bar")
        self.show_status.setChecked(parent_browser.settings_data.get("show_status_bar", True))
        form.addRow("Interface", self.show_status)

        self.theme = QComboBox()
        self.theme.addItems(("Dark", "Light"))
        self.theme.setCurrentText(parent_browser.settings_data.get("theme", "Dark"))
        form.addRow("Theme", self.theme)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def showEvent(self, event):
        super().showEvent(event)
        apply_windows_title_bar(self, self.parent_browser.settings_data.get("theme", "Dark") == "Dark")

    def accept(self):
        browser = self.parent_browser
        browser.settings_data["search_engine"] = self.search_engine.currentText()
        browser.settings_data["restore_tabs"] = self.restore_tabs.isChecked()
        browser.settings_data["block_trackers"] = self.block_trackers.isChecked()
        browser.settings_data["show_status_bar"] = self.show_status.isChecked()
        browser.settings_data["theme"] = self.theme.currentText()

        browser.blockers_enabled.setChecked(self.block_trackers.isChecked())
        browser.status.setVisible(self.show_status.isChecked())
        browser.apply_theme()
        browser.save_settings()
        browser.status.showMessage("Settings saved", 2500)
        super().accept()


class AIBrowser(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.setWindowIcon(QIcon(browser_app_icon_path()))
        self.resize(1360, 860)

        self.bookmarks = load_json(BOOKMARKS_FILE, [])
        if not self.bookmarks:
            now = datetime.now().isoformat(timespec="seconds")
            self.bookmarks = [{**favorite, "time": now} for favorite in DEFAULT_FAVORITES]
            save_json(BOOKMARKS_FILE, self.bookmarks)
        self.history = load_json(HISTORY_FILE, [])
        self.favicon_cache = {}
        self.pending_favicons = set()
        self.network = QNetworkAccessManager(self)
        self.settings_data = load_json(
            SETTINGS_FILE,
            {
                "search_engine": "Google",
                "block_trackers": True,
                "restore_tabs": True,
                "show_status_bar": True,
                "theme": "Dark",
                "last_tabs": [HOME_URL],
            },
        )

        self.profile = QWebEngineProfile.defaultProfile()
        self.configure_profile()

        self.history_timer = QTimer(self)
        self.history_timer.setSingleShot(True)
        self.history_timer.timeout.connect(self.record_current_page)

        self.setup_ui()
        self.apply_theme()
        self.install_shortcuts()
        self.restore_startup_tabs()

    def configure_profile(self):
        storage_path = str(DATA_DIR / "profile")
        cache_path = str(DATA_DIR / "cache")
        self.profile.setPersistentStoragePath(storage_path)
        self.profile.setCachePath(cache_path)
        self.profile.setPersistentCookiesPolicy(QWebEngineProfile.AllowPersistentCookies)
        self.profile.setHttpCacheType(QWebEngineProfile.DiskHttpCache)
        self.profile.setHttpUserAgent(
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/123.0.0.0 Safari/537.36"
        )
        self.interceptor = PrivacyInterceptor(self)
        self.profile.setRequestInterceptor(self.interceptor)
        self.profile.downloadRequested.connect(self.handle_download)

        settings = self.profile.settings()
        settings.setAttribute(QWebEngineSettings.PluginsEnabled, True)
        settings.setAttribute(QWebEngineSettings.FullScreenSupportEnabled, True)
        settings.setAttribute(QWebEngineSettings.JavascriptCanOpenWindows, True)
        settings.setAttribute(QWebEngineSettings.LocalContentCanAccessRemoteUrls, True)
        settings.setAttribute(QWebEngineSettings.ScrollAnimatorEnabled, True)
        settings.setDefaultTextEncoding("utf-8")

    def setup_ui(self):
        central = QWidget()
        layout = QVBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setCentralWidget(central)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.setTabsClosable(True)
        self.tabs.setMovable(True)
        self.tabs.setElideMode(Qt.ElideRight)
        self.tabs.tabCloseRequested.connect(self.close_tab)
        self.tabs.currentChanged.connect(self.on_current_tab_changed)
        self.plus_tab_index = -1

        self.navbar = QToolBar("Navigation")
        self.navbar.setObjectName("navBar")
        self.navbar.setIconSize(QSize(19, 19))
        self.navbar.setMovable(False)

        self.back_action = self.add_nav_action("back", "Back", self.go_back)
        self.forward_action = self.add_nav_action("forward", "Forward", self.go_forward)
        self.reload_action = self.add_nav_action("reload", "Reload", self.reload_page)
        self.home_action = self.add_nav_action("home", "Home", self.go_home)

        self.address = QLineEdit()
        self.address.setPlaceholderText("Search or enter address")
        self.address.setClearButtonEnabled(True)
        self.address.returnPressed.connect(self.navigate_to_address)
        self.address.setMinimumWidth(360)
        self.address.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.navbar.addWidget(self.address)

        self.progress = QProgressBar()
        self.progress.setMaximumWidth(120)
        self.progress.setTextVisible(False)
        self.progress.hide()
        self.navbar.addWidget(self.progress)

        self.bookmark_action = QAction(modern_icon("star", color=self.chrome_icon_color()), "Add to Favorites", self)
        self.bookmark_action.setData("star")
        self.bookmark_action.triggered.connect(self.add_bookmark)
        self.navbar.addAction(self.bookmark_action)

        self.favorites_button = QToolButton(self)
        self.favorites_button.setIcon(modern_icon("folder", color=self.chrome_icon_color()))
        self.favorites_button.setToolTip("Favorites")
        self.favorites_button.setPopupMode(QToolButton.InstantPopup)
        self.favorites_menu = QMenu(self.favorites_button)
        self.favorites_button.setMenu(self.favorites_menu)
        self.navbar.addWidget(self.favorites_button)

        self.tools_button = QToolButton(self)
        self.tools_button.setIcon(modern_icon("menu", color=self.chrome_icon_color()))
        self.tools_button.setText("Menu")
        self.tools_button.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.tools_button.setToolTip("Open browser menu")
        self.tools_button.setPopupMode(QToolButton.InstantPopup)
        self.tools_menu = QMenu(self.tools_button)
        self.tools_button.setMenu(self.tools_menu)
        self.navbar.addWidget(self.tools_button)

        self.settings_action = QAction(modern_icon("settings", color=self.chrome_icon_color()), "Settings", self)
        self.settings_action.setData("settings")
        self.settings_action.triggered.connect(self.open_settings)
        self.tools_menu.addAction(self.settings_action)
        self.tools_menu.addSeparator()

        self.find_action = QAction(modern_icon("find", color=self.chrome_icon_color()), "Find in Page", self)
        self.find_action.setData("find")
        self.find_action.triggered.connect(lambda: self.find_bar.show_and_focus())
        self.tools_menu.addAction(self.find_action)

        self.reader_action = QAction(modern_icon("reader", color=self.chrome_icon_color()), "Reader Mode", self)
        self.reader_action.setData("reader")
        self.reader_action.triggered.connect(self.reader_mode)
        self.tools_menu.addAction(self.reader_action)

        self.history_action = QAction(modern_icon("history", color=self.chrome_icon_color()), "History", self)
        self.history_action.setData("history")
        self.history_action.triggered.connect(self.open_history)
        self.tools_menu.addAction(self.history_action)

        self.tools_menu.addSeparator()
        self.zoom_out_action = QAction(modern_icon("zoom_out", color=self.chrome_icon_color()), "Zoom Out", self)
        self.zoom_out_action.setData("zoom_out")
        self.zoom_out_action.triggered.connect(lambda: self.adjust_zoom(-0.1))
        self.tools_menu.addAction(self.zoom_out_action)

        self.zoom_in_action = QAction(modern_icon("zoom_in", color=self.chrome_icon_color()), "Zoom In", self)
        self.zoom_in_action.setData("zoom_in")
        self.zoom_in_action.triggered.connect(lambda: self.adjust_zoom(0.1))
        self.tools_menu.addAction(self.zoom_in_action)

        self.tools_menu.addSeparator()
        self.open_file_action = QAction(modern_icon("open", color=self.chrome_icon_color()), "Open File", self)
        self.open_file_action.setData("open")
        self.open_file_action.triggered.connect(self.open_file)
        self.tools_menu.addAction(self.open_file_action)

        self.private_action = QAction(modern_icon("trash", color=self.chrome_icon_color()), "Clear Private Data", self)
        self.private_action.setData("trash")
        self.private_action.triggered.connect(self.clear_private_data)
        self.tools_menu.addAction(self.private_action)

        self.tools_menu.addSeparator()
        self.blockers_enabled = QCheckBox("Block trackers")
        self.blockers_enabled.setChecked(self.settings_data.get("block_trackers", True))
        self.blockers_enabled.stateChanged.connect(self.toggle_blockers)
        blocker_action = self.tools_menu.addAction("Block trackers")
        blocker_action.setCheckable(True)
        blocker_action.setChecked(self.blockers_enabled.isChecked())
        blocker_action.toggled.connect(lambda checked: self.blockers_enabled.setChecked(checked))

        self.favorites_bar = QToolBar("Favorites")
        self.favorites_bar.setObjectName("favoritesBar")
        self.favorites_bar.setIconSize(QSize(16, 16))
        self.favorites_bar.setMovable(False)
        self.favorites_bar.setToolButtonStyle(Qt.ToolButtonTextBesideIcon)
        self.refresh_favorites_bar()

        splitter = QSplitter(Qt.Vertical)
        splitter.addWidget(self.tabs)
        splitter.setStretchFactor(0, 1)
        layout.addWidget(splitter, 1)

        self.find_bar = FindBar(self)
        layout.addWidget(self.find_bar)

        self.status = self.statusBar()
        self.status.showMessage("Ready")
        self.status.setVisible(self.settings_data.get("show_status_bar", True))

    def add_nav_action(self, icon_name, label, callback):
        action = QAction(modern_icon(icon_name, color=self.chrome_icon_color()), label, self)
        action.setData(icon_name)
        action.triggered.connect(callback)
        self.navbar.addAction(action)
        return action

    def chrome_icon_color(self):
        return "#263142" if self.settings_data.get("theme", "Dark") == "Light" else "#dce6f2"

    def update_chrome_icons(self):
        if not hasattr(self, "back_action"):
            return
        color = self.chrome_icon_color()
        for action in (
            self.back_action,
            self.forward_action,
            self.reload_action,
            self.home_action,
            self.bookmark_action,
            self.settings_action,
            self.find_action,
            self.reader_action,
            self.history_action,
            self.zoom_out_action,
            self.zoom_in_action,
            self.open_file_action,
            self.private_action,
        ):
            icon_name = action.data()
            if icon_name:
                action.setIcon(modern_icon(icon_name, color=color))
        self.favorites_button.setIcon(modern_icon("folder", color=color))
        self.tools_button.setIcon(modern_icon("menu", color=color))

    def open_settings(self):
        dialog = SettingsDialog(self)
        dialog.exec_()

    def refresh_favorites_bar(self):
        if not hasattr(self, "favorites_bar"):
            return

        self.favorites_bar.clear()
        self.favorites_menu.clear()

        manage_action = QAction("Manage Favorites", self)
        manage_action.triggered.connect(self.open_bookmarks)
        add_action = QAction("Add Current Page", self)
        add_action.triggered.connect(self.add_bookmark)
        self.favorites_menu.addAction(add_action)
        self.favorites_menu.addAction(manage_action)
        self.favorites_menu.addSeparator()

        if not self.bookmarks:
            empty_action = QAction("No favorites yet", self)
            empty_action.setEnabled(False)
            self.favorites_bar.addAction(empty_action)
            self.favorites_menu.addAction(empty_action)
            return

        for favorite in self.bookmarks[:12]:
            title = favorite.get("title") or host_label(favorite.get("url", ""))
            url = favorite.get("url", "")
            action = QAction(self.icon_for_favorite(url), title[:34], self)
            action.setToolTip(url)
            action.triggered.connect(lambda _checked=False, target=url: self.add_new_tab(QUrl(target), "Favorite"))
            self.favorites_bar.addAction(action)

        for favorite in self.bookmarks:
            title = favorite.get("title") or host_label(favorite.get("url", ""))
            url = favorite.get("url", "")
            action = QAction(self.icon_for_favorite(url), title, self)
            action.setToolTip(url)
            action.triggered.connect(lambda _checked=False, target=url: self.add_new_tab(QUrl(target), "Favorite"))
            self.favorites_menu.addAction(action)

    def attach_browser_bars(self):
        wrapper = self.tabs.currentWidget()
        if not wrapper or not hasattr(wrapper, "browser_layout"):
            return
        if self.navbar.parent() is not wrapper:
            wrapper.browser_layout.insertWidget(0, self.navbar)
        if self.favorites_bar.parent() is not wrapper:
            wrapper.browser_layout.insertWidget(1, self.favorites_bar)
        self.navbar.show()
        self.favorites_bar.show()

    def icon_for_favorite(self, url):
        if url in self.favicon_cache:
            return self.favicon_cache[url]

        if url and url not in self.pending_favicons:
            self.pending_favicons.add(url)
            favicon_url = official_favicon_url(url)
            if favicon_url:
                reply = self.network.get(QNetworkRequest(QUrl(favicon_url)))
                reply.finished.connect(
                    lambda reply=reply, target=url: self.finish_favicon(reply, target, allow_fallback=True)
                )

        return favicon_for_url(url)

    def finish_favicon(self, reply, url, allow_fallback=False):
        self.pending_favicons.discard(url)
        data = bytes(reply.readAll())
        failed = reply.error() != 0
        reply.deleteLater()
        pixmap = QPixmap()
        if not failed and data and pixmap.loadFromData(data):
            self.favicon_cache[url] = QIcon(pixmap)
            self.refresh_favorites_bar()
            return

        if allow_fallback:
            self.pending_favicons.add(url)
            favicon_url = "https://www.google.com/s2/favicons?sz=64&domain_url=" + quote_plus(url)
            fallback = self.network.get(QNetworkRequest(QUrl(favicon_url)))
            fallback.finished.connect(
                lambda reply=fallback, target=url: self.finish_favicon(reply, target, allow_fallback=False)
            )

    def install_shortcuts(self):
        shortcuts = {
            "Ctrl+L": lambda: (self.address.setFocus(), self.address.selectAll()),
            "Ctrl+T": lambda: self.add_new_tab(QUrl(NEW_TAB_URL), "New Tab"),
            "Ctrl+W": lambda: self.close_tab(self.tabs.currentIndex()),
            "Ctrl+R": self.reload_page,
            "Ctrl+F": lambda: self.find_bar.show_and_focus(),
            "Ctrl+D": self.add_bookmark,
            "Ctrl+H": self.open_history,
            "Ctrl+B": self.open_bookmarks,
            "Alt+Left": self.go_back,
            "Alt+Right": self.go_forward,
            "Ctrl++": lambda: self.adjust_zoom(0.1),
            "Ctrl+-": lambda: self.adjust_zoom(-0.1),
            "Ctrl+0": lambda: self.set_zoom(1.0),
        }
        for key, callback in shortcuts.items():
            shortcut = QShortcut(QKeySequence(key), self)
            shortcut.activated.connect(callback)

    def restore_startup_tabs(self):
        urls = self.settings_data.get("last_tabs", [NEW_TAB_URL])
        if not self.settings_data.get("restore_tabs", True):
            urls = [NEW_TAB_URL]
        if not urls:
            urls = [NEW_TAB_URL]
        for url in urls[:12]:
            self.add_new_tab(QUrl(url), "New Tab", switch=False)
        self.ensure_plus_tab()
        self.tabs.setCurrentIndex(0)

    def add_new_tab(self, qurl=None, label="New Tab", switch=True):
        if qurl is None or isinstance(qurl, bool):
            qurl = QUrl(NEW_TAB_URL)
        if isinstance(qurl, str):
            qurl = QUrl(qurl)

        browser = BrowserTab(self, self.profile)
        wrapper = QWidget()
        wrapper.browser = browser
        wrapper.browser_layout = QVBoxLayout(wrapper)
        wrapper.browser_layout.setContentsMargins(0, 0, 0, 0)
        wrapper.browser_layout.setSpacing(0)
        wrapper.browser_layout.addWidget(browser, 1)

        browser.urlChanged.connect(lambda url, b=browser: self.on_url_changed(b, url))
        browser.titleChanged.connect(lambda title, b=browser: self.update_tab_title(b, title))
        browser.iconChanged.connect(lambda _icon, b=browser: self.update_tab_icon(b))
        browser.loadStarted.connect(lambda b=browser: self.on_load_started(b))
        browser.loadProgress.connect(lambda progress, b=browser: self.on_load_progress(b, progress))
        browser.loadFinished.connect(lambda ok, b=browser: self.on_load_finished(b, ok))
        browser.status_message.connect(self.status.showMessage)

        insert_at = self.plus_tab_index if self.plus_tab_index != -1 else self.tabs.count()
        index = self.tabs.insertTab(insert_at, wrapper, label)
        if self.plus_tab_index != -1:
            self.plus_tab_index += 1
        self.tabs.setTabToolTip(index, label)
        if switch:
            self.tabs.setCurrentIndex(index)
        if self.tabs.currentWidget() is wrapper:
            self.attach_browser_bars()
        if is_new_tab_url(qurl):
            self.load_new_tab_page(browser)
        else:
            browser.load(qurl)
        self.save_settings()
        return browser

    def ensure_plus_tab(self):
        if self.plus_tab_index != -1:
            return
        plus_page = QWidget()
        self.plus_tab_index = self.tabs.addTab(plus_page, "+")
        self.tabs.setTabToolTip(self.plus_tab_index, "New tab")
        self.tabs.tabBar().setTabButton(self.plus_tab_index, QTabBar.RightSide, None)
        self.tabs.tabBar().setTabButton(self.plus_tab_index, QTabBar.LeftSide, None)

    def load_new_tab_page(self, browser):
        if not browser:
            return
        browser.setHtml(self.new_tab_html(), QUrl(NEW_TAB_URL))

    def new_tab_html(self):
        cards = []
        for favorite in self.bookmarks[:8]:
            title = self.escape_html(favorite.get("title") or host_label(favorite.get("url", "")))
            url = favorite.get("url", "")
            safe_url = self.escape_html(url)
            favicon = "https://www.google.com/s2/favicons?sz=64&domain_url=" + quote_plus(url)
            cards.append(
                "<a class='favorite' href='{url}'>"
                "<span class='icon'><img src='{favicon}' alt=''></span>"
                "<span>{title}</span>"
                "</a>".format(url=safe_url, favicon=favicon, title=title)
            )

        if not cards:
            cards.append("<div class='hint'>Add favorites with the star button.</div>")

        template = SEARCH_ENGINES.get(self.settings_data.get("search_engine", "Google"), SEARCH_ENGINES["Google"])
        return """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<title>New tab</title>
<style>
    * { box-sizing: border-box; }
    html, body { height: 100%; margin: 0; }
    body {
        color: #fff;
        font-family: "Segoe UI", Arial, sans-serif;
        background:
            radial-gradient(900px 320px at 18% 72%, rgba(19, 34, 45, .92), transparent 62%),
            radial-gradient(780px 260px at 82% 76%, rgba(199, 126, 98, .75), transparent 58%),
            linear-gradient(180deg, #427798 0%, #7694a7 52%, #26495c 100%);
        overflow: hidden;
    }
    body::before {
        content: "";
        position: fixed;
        inset: auto -8vw -10vh -8vw;
        height: 45vh;
        background:
            radial-gradient(60vw 20vh at 11% 18%, #1a2932 0 58%, transparent 59%),
            radial-gradient(55vw 18vh at 86% 62%, #b68563 0 46%, transparent 47%),
            linear-gradient(180deg, rgba(20, 36, 45, .94), rgba(14, 28, 35, .98));
        filter: blur(.2px);
    }
    .top-left {
        position: fixed;
        top: 22px;
        width: 36px;
        height: 36px;
        border-radius: 10px;
        display: grid;
        place-items: center;
        color: rgba(255,255,255,.9);
        background: rgba(0,0,0,.16);
        backdrop-filter: blur(10px);
    }
    .top-left { left: 28px; font-size: 23px; line-height: 10px; }
    main {
        position: relative;
        z-index: 1;
        display: flex;
        min-height: 100%;
        flex-direction: column;
        align-items: center;
        padding-top: 15vh;
    }
    form {
        width: min(760px, calc(100vw - 72px));
        height: 48px;
        display: flex;
        align-items: center;
        gap: 13px;
        border-radius: 24px;
        background: rgba(42, 43, 46, .88);
        box-shadow: 0 12px 26px rgba(0, 0, 0, .24);
        padding: 0 18px;
    }
    .search-icon {
        width: 21px;
        height: 21px;
        opacity: .88;
        flex: 0 0 auto;
    }
    input {
        flex: 1;
        min-width: 0;
        border: 0;
        outline: none;
        color: #fff;
        background: transparent;
        font: 15px "Segoe UI", Arial, sans-serif;
    }
    input::placeholder { color: rgba(255,255,255,.95); }
    .favorites {
        margin-top: 34px;
        display: grid;
        grid-template-columns: repeat(8, minmax(74px, 88px));
        justify-content: center;
        gap: 20px;
        max-width: min(860px, calc(100vw - 72px));
    }
    .favorite {
        color: white;
        text-decoration: none;
        text-align: center;
        font-size: 12px;
        text-shadow: 0 1px 6px rgba(0,0,0,.4);
    }
    .icon {
        width: 38px;
        height: 38px;
        margin: 0 auto 8px;
        display: grid;
        place-items: center;
        border-radius: 12px;
        background: rgba(35, 38, 43, .78);
        box-shadow: 0 8px 20px rgba(0,0,0,.2);
    }
    .icon img { width: 24px; height: 24px; }
    .hint {
        grid-column: 1 / -1;
        opacity: .85;
        text-align: center;
    }
    @media (max-width: 780px) {
        main { padding-top: 12vh; }
        .favorites { grid-template-columns: repeat(4, minmax(70px, 1fr)); }
    }
</style>
</head>
<body>
<div class="top-left">::</div>
<main>
    <form id="searchForm">
        <svg class="search-icon" viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <circle cx="11" cy="11" r="7" stroke="white" stroke-width="2" stroke-linecap="round"/>
            <path d="m16.5 16.5 4 4" stroke="white" stroke-width="2" stroke-linecap="round"/>
        </svg>
        <input id="searchBox" autocomplete="off" autofocus placeholder="Search or enter web address">
    </form>
    <section class="favorites">__CARDS__</section>
</main>
<script>
const template = "__TEMPLATE__";
document.getElementById("searchForm").addEventListener("submit", event => {
    event.preventDefault();
    const value = document.getElementById("searchBox").value.trim();
    if (!value) return;
    if (/^(https?:|file:|about:)/i.test(value)) {
        location.href = value;
    } else if (value.includes(".") && !value.includes(" ")) {
        location.href = "https://" + value;
    } else {
        location.href = template.replace("{query}", encodeURIComponent(value));
    }
});
</script>
</body>
</html>
""".replace("__CARDS__", "\n".join(cards)).replace("__TEMPLATE__", self.escape_html(template))

    def close_tab(self, index):
        if index < 0 or index == self.plus_tab_index:
            return
        real_tab_count = self.tabs.count() - (1 if self.plus_tab_index != -1 else 0)
        if real_tab_count == 1:
            self.close()
            return
        widget = self.tabs.widget(index)
        if self.navbar.parent() is widget:
            self.navbar.setParent(None)
        if self.favorites_bar.parent() is widget:
            self.favorites_bar.setParent(None)
        self.tabs.removeTab(index)
        if self.plus_tab_index != -1 and index < self.plus_tab_index:
            self.plus_tab_index -= 1
        widget.deleteLater()
        self.save_settings()

    def current_browser(self):
        wrapper = self.tabs.currentWidget()
        return getattr(wrapper, "browser", None)

    def on_current_tab_changed(self, _index):
        if _index == self.plus_tab_index:
            self.add_new_tab(QUrl(NEW_TAB_URL), "New Tab", switch=True)
            return
        self.attach_browser_bars()
        self.update_address()
        self.update_nav_state()

    def on_url_changed(self, browser, url):
        if browser is self.current_browser():
            self.address.setText("" if is_new_tab_url(url) else url.toString())
            self.address.setCursorPosition(0)
        self.save_settings()
        self.history_timer.start(1200)

    def on_load_started(self, browser):
        if browser is self.current_browser():
            self.progress.setValue(0)
            self.progress.show()
            self.status.showMessage("Loading...")

    def on_load_progress(self, browser, progress):
        if browser is self.current_browser():
            self.progress.setValue(progress)

    def on_load_finished(self, browser, ok):
        if browser is self.current_browser():
            self.progress.hide()
            self.status.showMessage("Done" if ok else "Load failed", 3000)
            self.update_nav_state()
        self.record_current_page()

    def update_tab_title(self, browser, title):
        index = self.index_for_browser(browser)
        if index == -1 or index == self.plus_tab_index:
            return
        text = title or browser.url().toString() or "New Tab"
        short = text[:28] + ("..." if len(text) > 28 else "")
        self.tabs.setTabText(index, short)
        self.tabs.setTabToolTip(index, text)

    def update_tab_icon(self, browser):
        index = self.index_for_browser(browser)
        if index != -1 and index != self.plus_tab_index:
            self.tabs.setTabIcon(index, browser.icon())

    def index_for_browser(self, browser):
        for index in range(self.tabs.count()):
            if getattr(self.tabs.widget(index), "browser", None) is browser:
                return index
        return -1

    def update_address(self):
        browser = self.current_browser()
        if browser:
            url = browser.url()
            self.address.setText("" if is_new_tab_url(url) else url.toString())
            self.address.setCursorPosition(0)

    def update_nav_state(self):
        browser = self.current_browser()
        if not browser:
            return
        self.back_action.setEnabled(browser.history().canGoBack())
        self.forward_action.setEnabled(browser.history().canGoForward())

    def navigate_to_address(self):
        browser = self.current_browser()
        if browser:
            browser.load(normalized_address(self.address.text(), self.settings_data.get("search_engine", "Google")))

    def go_back(self):
        browser = self.current_browser()
        if browser:
            browser.back()

    def go_forward(self):
        browser = self.current_browser()
        if browser:
            browser.forward()

    def reload_page(self):
        browser = self.current_browser()
        if browser:
            browser.reload()

    def go_home(self):
        browser = self.current_browser()
        if browser:
            self.load_new_tab_page(browser)

    def open_file(self):
        filename, _ = QFileDialog.getOpenFileName(
            self,
            "Open file",
            "",
            "Web files (*.html *.htm *.svg *.pdf);;All files (*.*)",
        )
        if filename:
            self.add_new_tab(QUrl.fromLocalFile(filename), Path(filename).name)

    def add_bookmark(self):
        browser = self.current_browser()
        if not browser:
            return
        url = browser.url().toString()
        if is_new_tab_url(url):
            self.status.showMessage("Open a page before adding it to Favorites", 2500)
            return
        title = browser.title() or host_label(url)
        if any(bookmark.get("url") == url for bookmark in self.bookmarks):
            self.status.showMessage("Already in Favorites", 2500)
            return
        self.bookmarks.insert(0, {"title": title, "url": url, "time": datetime.now().isoformat(timespec="seconds")})
        save_json(BOOKMARKS_FILE, self.bookmarks)
        self.refresh_favorites_bar()
        self.status.showMessage("Added to Favorites", 2500)

    def open_bookmarks(self):
        self.bookmark_window = ListDialog(
            "Favorites",
            list(self.bookmarks),
            lambda url: self.add_new_tab(QUrl(url), "Favorite"),
            self.delete_bookmark,
        )
        self.bookmark_window.show()

    def delete_bookmark(self, index):
        if 0 <= index < len(self.bookmarks):
            del self.bookmarks[index]
            save_json(BOOKMARKS_FILE, self.bookmarks)
            self.refresh_favorites_bar()

    def record_current_page(self):
        browser = self.current_browser()
        if not browser:
            return
        url = browser.url().toString()
        if not url or is_new_tab_url(url):
            return
        title = browser.title() or host_label(url)
        entry = {"title": title, "url": url, "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
        self.history = [item for item in self.history if item.get("url") != url]
        self.history.insert(0, entry)
        self.history = self.history[:1000]
        save_json(HISTORY_FILE, self.history)

    def open_history(self):
        self.history_window = ListDialog(
            "History",
            list(self.history),
            lambda url: self.add_new_tab(QUrl(url), "History"),
            self.delete_history_item,
            self.clear_history,
        )
        self.history_window.show()

    def delete_history_item(self, index):
        if 0 <= index < len(self.history):
            del self.history[index]
            save_json(HISTORY_FILE, self.history)

    def clear_history(self):
        self.history = []
        save_json(HISTORY_FILE, self.history)

    def handle_download(self, download):
        suggested = download.downloadFileName()
        if not suggested:
            suggested = Path(download.url().path()).name or "download"
        target, _ = QFileDialog.getSaveFileName(
            self,
            "Save download",
            str(DOWNLOADS_DIR / suggested),
        )
        if not target:
            download.cancel()
            return

        target_path = Path(target)
        if hasattr(download, "setPath"):
            download.setPath(str(target_path))
        else:
            download.setDownloadDirectory(str(target_path.parent))
            download.setDownloadFileName(target_path.name)

        download.finished.connect(lambda: self.status.showMessage(f"Downloaded {target_path.name}", 5000))
        download.accept()
        self.status.showMessage(f"Downloading {target_path.name}")

    def reader_mode(self):
        browser = self.current_browser()
        if not browser:
            return

        script = """
        (() => {
            const clone = document.body.cloneNode(true);
            clone.querySelectorAll('script,style,nav,header,footer,aside,form,iframe,noscript').forEach(n => n.remove());
            const title = document.title || location.href;
            const text = Array.from(clone.querySelectorAll('article,main,h1,h2,h3,p,li,blockquote,pre'))
                .map(n => n.innerText)
                .filter(Boolean)
                .join('\\n\\n');
            return {title, text: text || document.body.innerText || ''};
        })();
        """
        browser.page().runJavaScript(script, self.open_reader_tab)

    def open_reader_tab(self, data):
        if not data or not data.get("text"):
            QMessageBox.information(self, "Reader", "No readable text was found on this page.")
            return
        title = data.get("title", "Reader")
        body = data.get("text", "")
        html = (
            "<!doctype html><html><head><meta charset='utf-8'>"
            "<style>"
            "body{margin:0;background:#f6f2ea;color:#222;font:19px/1.65 Georgia,serif;}"
            "main{max-width:850px;margin:0 auto;padding:56px 28px;}"
            "h1{font:700 34px/1.2 system-ui,sans-serif;margin:0 0 28px;}"
            "p{white-space:pre-wrap;}"
            "</style></head><body><main>"
            f"<h1>{self.escape_html(title)}</h1><p>{self.escape_html(body)}</p>"
            "</main></body></html>"
        )
        view = self.add_new_tab(QUrl("about:blank"), "Reader", switch=True)
        view.setHtml(html, QUrl("about:reader"))

    @staticmethod
    def escape_html(text):
        return (
            str(text)
            .replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace('"', "&quot;")
        )

    def adjust_zoom(self, delta):
        browser = self.current_browser()
        if browser:
            self.set_zoom(max(0.25, min(5.0, browser.zoomFactor() + delta)))

    def set_zoom(self, value):
        browser = self.current_browser()
        if browser:
            browser.setZoomFactor(value)
            self.status.showMessage(f"Zoom {int(value * 100)}%", 2000)

    def toggle_blockers(self):
        self.settings_data["block_trackers"] = self.blockers_enabled.isChecked()
        self.save_settings()
        self.status.showMessage("Tracker blocking updated. Reload pages to apply everywhere.", 3500)

    def clear_private_data(self):
        result = QMessageBox.question(
            self,
            "Clear Private Data",
            "Clear cookies, HTTP cache, and browsing history?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if result != QMessageBox.Yes:
            return
        self.profile.cookieStore().deleteAllCookies()
        self.profile.clearHttpCache()
        self.clear_history()
        self.status.showMessage("Private data cleared", 4000)

    def save_settings(self):
        if not hasattr(self, "tabs"):
            return
        urls = []
        for index in range(self.tabs.count()):
            if index == self.plus_tab_index:
                continue
            browser = getattr(self.tabs.widget(index), "browser", None)
            if browser:
                url = browser.url().toString()
                if url:
                    urls.append(url)
        self.settings_data["last_tabs"] = urls or [HOME_URL]
        if hasattr(self, "status"):
            self.settings_data["show_status_bar"] = self.status.isVisible()
        save_json(SETTINGS_FILE, self.settings_data)

    def closeEvent(self, event):
        self.save_settings()
        super().closeEvent(event)

    def apply_theme(self):
        light = self.settings_data.get("theme", "Dark") == "Light"
        colors = {
            "window": "#f4f7fb" if light else "#0b0f17",
            "text": "#101827" if light else "#edf3fb",
            "tab_text": "#172033" if light else "#edf3fb",
            "control_text": "#101827" if light else "#edf3fb",
            "toolbar": "#edf2f8" if light else "#242b3d",
            "toolbar_hover": "#dbe5f0" if light else "#34405a",
            "favorites": "#e7eef7" if light else "#22293a",
            "input": "#ffffff" if light else "#111827",
            "input_text": "#101827" if light else "#f8fbff",
            "button": "#e6edf6" if light else "#2d3548",
            "button_border": "#c7d3e0" if light else "#3d4659",
            "menu": "#ffffff" if light else "#1d2433",
            "menu_border": "#c7d3e0" if light else "#3b465d",
            "menu_selected": "#e7eef9" if light else "#32405a",
            "tab_bg": "#d9e3ef" if light else "#252c3e",
            "tab_selected": "#ffffff" if light else "#30384e",
            "tabbar": "#eaf0f7" if light else "#070a10",
            "accent": "#286ef0" if light else "#3976ff",
            "list_bg": "#ffffff" if light else "#111827",
            "status": "#e7eef7" if light else "#1d2433",
            "muted": "#5d6878" if light else "#c6ceda",
            "close_hover": "#d3dde9" if light else "#47536b",
        }
        qss = """
            QMainWindow, QWidget {
                background: {colors["window"]};
                color: {colors["text"]};
                font-family: Segoe UI, Arial, sans-serif;
                font-size: 10pt;
            }
            QToolBar {
                background: {colors["toolbar"]};
                border: 0;
                spacing: 4px;
                padding: 4px 8px;
            }
            QToolBar#favoritesBar {
                background: {colors["favorites"]};
                border-top: 1px solid rgba(255,255,255,.06);
                spacing: 2px;
                padding: 1px 8px 2px 8px;
                min-height: 25px;
                max-height: 27px;
            }
            QToolBar#favoritesBar QToolButton {
                min-width: 118px;
                max-width: 190px;
                min-height: 21px;
                max-height: 23px;
                padding: 1px 8px;
                border-radius: 4px;
                font-size: 8.5pt;
                text-align: left;
            }
            QLineEdit, QComboBox {
                background: {colors["input"]};
                color: {colors["input_text"]};
                border: 1px solid {colors["accent"]};
                border-radius: 14px;
                padding: 6px 12px;
                min-height: 26px;
                selection-background-color: {colors["accent"]};
            }
            QComboBox#searchEngine {
                border-color: #3c4658;
                border-radius: 8px;
                min-width: 94px;
            }
            QPushButton {
                background: {colors["button"]};
                color: {colors["text"]};
                border: 1px solid {colors["button_border"]};
                border-radius: 7px;
                padding: 7px 12px;
            }
            QToolButton {
                background: transparent;
                color: {colors["control_text"]};
                border: 0;
                border-radius: 7px;
                padding: 5px 7px;
                min-width: 26px;
                min-height: 26px;
            }
            QPushButton:hover, QToolButton:hover {
                background: {colors["toolbar_hover"]};
            }
            QMenu {
                background: {colors["menu"]};
                color: {colors["text"]};
                border: 1px solid {colors["menu_border"]};
                border-radius: 8px;
                padding: 6px;
            }
            QMenu::item {
                padding: 7px 28px 7px 12px;
                border-radius: 6px;
            }
            QMenu::item:selected {
                background: {colors["menu_selected"]};
            }
            QMenu::separator {
                height: 1px;
                background: #3a4356;
                margin: 6px 4px;
            }
            QTabWidget::pane {
                border: 0;
            }
            QTabBar {
                background: {colors["tabbar"]};
                min-height: 38px;
            }
            QTabBar::tab {
                background: {colors["tab_bg"]};
                color: {colors["tab_text"]};
                min-width: 150px;
                max-width: 235px;
                min-height: 27px;
                padding: 8px 13px 7px 13px;
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                margin: 4px 2px 0 0;
            }
            QTabBar::tab:selected {
                background: {colors["tab_selected"]};
                color: {colors["tab_text"]};
            }
            QTabBar::tab:last {
                min-width: 34px;
                max-width: 34px;
                min-height: 24px;
                padding: 4px 0 4px 0;
                color: {colors["muted"]};
                font-size: 15pt;
                font-weight: 300;
                background: transparent;
            }
            QTabBar::tab:last:hover {
                background: {colors["toolbar_hover"]};
            }
            QTabBar::tab:last:selected {
                background: transparent;
                color: {colors["muted"]};
            }
            QTabBar::close-button {
                image: url(__CLOSE_ICON__);
                width: 24px;
                height: 24px;
                margin-left: 8px;
                border-radius: 12px;
            }
            QTabBar::close-button:hover {
                background: {colors["close_hover"]};
            }
            QProgressBar {
                background: {colors["input"]};
                border: 0;
                border-radius: 3px;
                height: 6px;
            }
            QProgressBar::chunk {
                background: {colors["accent"]};
                border-radius: 3px;
            }
            QListWidget {
                background: {colors["list_bg"]};
                color: {colors["text"]};
                border: 1px solid {colors["menu_border"]};
                border-radius: 8px;
                padding: 6px;
            }
            QListWidget::item {
                padding: 8px;
            }
            QListWidget::item:selected {
                background: {colors["accent"]};
                color: white;
            }
            QStatusBar {
                background: {colors["status"]};
                color: {colors["text"]};
            }
            QCheckBox {
                padding-left: 6px;
            }
            """
        for key, value in colors.items():
            qss = qss.replace(f'{{colors["{key}"]}}', value)
        qss = qss.replace("__CLOSE_ICON__", icon_file("close", color=("#4b5567" if light else "#aeb7c5"), size=28))
        self.setStyleSheet(qss)
        self.update_chrome_icons()
        apply_windows_title_bar(self, not light)


def main():
    set_windows_app_id()
    QApplication.setApplicationName(APP_NAME)
    QApplication.setOrganizationName("Local")
    app = QApplication(sys.argv)
    app.setWindowIcon(QIcon(browser_app_icon_path()))
    window = AIBrowser()
    window.show()
    force_windows_window_icon(window)
    apply_windows_title_bar(window, window.settings_data.get("theme", "Dark") == "Dark")
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
