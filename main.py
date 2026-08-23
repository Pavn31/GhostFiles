import os
import sys
import json
import shutil
import hashlib
import fnmatch
import subprocess
import platform
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QListWidget,
    QListWidgetItem,
    QFrame,
    QTabWidget,
    QSplitter,
    QLineEdit,
    QComboBox,
    QCheckBox,
    QSpinBox,
    QDialog,
    QDialogButtonBox,
    QMenu,
    QMessageBox,
    QTextEdit,
    QGroupBox,
    QScrollArea,
)

from PySide6.QtGui import QPixmap, QIcon, QAction
from PySide6.QtCore import Qt, QThread, QObject, Signal

# ============================================================
# Paths / Config / History
# ============================================================

APP_DIR = Path(__file__).resolve().parent
ASSETS_DIR = APP_DIR / "assets"

CONFIG_DIR = Path.home() / ".ghostfiles"
CONFIG_FILE = CONFIG_DIR / "config.json"
HISTORY_FILE = CONFIG_DIR / "history.json"

MAX_HISTORY_ENTRIES = 50

DEFAULT_CONFIG = {
    "ghost_extensions": [".tmp", ".bak", ".old", ".swp"],
    "ghost_keywords": ["backup", "temp", "old"],
    "large_file_mb": 10,
    "exclusions": [".git", "node_modules", "__pycache__", ".venv", "venv", ".cache", "Thumbs.db"],
    "recursive": True,
    "detect_cache": True,
    "detect_logs": True,
    "detect_empty_dirs": True,
    "detect_broken_links": True,
    "cache_dir_names": ["__pycache__", ".cache", "node_modules", ".pytest_cache", ".mypy_cache"],
    "log_extensions": [".log"],
    "health_weight_ghost": 1.0,
    "health_weight_duplicate": 1.5,
    "health_weight_large": 0.5,
    "notify_on_scan": True,
}

TEXT_PREVIEW_EXTENSIONS = {
    ".txt", ".md", ".py", ".json", ".yaml", ".yml", ".ini", ".cfg",
    ".csv", ".log", ".xml", ".html", ".css", ".js", ".ts", ".sh",
    ".c", ".cpp", ".h", ".java", ".rs", ".go", ".rb", ".toml",
}

IMAGE_PREVIEW_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}


def load_config():
    config = dict(DEFAULT_CONFIG)
    try:
        if CONFIG_FILE.exists():
            with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            config.update(saved)
    except (json.JSONDecodeError, OSError):
        pass
    return config


def save_config(config):
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2)
    except OSError:
        pass


def load_history():
    try:
        if HISTORY_FILE.exists():
            with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except (json.JSONDecodeError, OSError):
        pass
    return []


def save_history(history):
    try:
        CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        with open(HISTORY_FILE, "w", encoding="utf-8") as f:
            json.dump(history[-MAX_HISTORY_ENTRIES:], f, indent=2)
    except OSError:
        pass


def format_size(size):
    if size < 1024:
        return f"{size} B"
    if size < 1024 ** 2:
        return f"{size / 1024:.1f} KB"
    if size < 1024 ** 3:
        return f"{size / (1024 ** 2):.1f} MB"
    if size < 1024 ** 4:
        return f"{size / (1024 ** 3):.1f} GB"
    return f"{size / (1024 ** 4):.1f} TB"


# ============================================================
# Settings Dialog
# ============================================================

class SettingsDialog(QDialog):

    def __init__(self, config, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.resize(520, 640)
        self.config = dict(config)

        outer = QVBoxLayout(self)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        scroll.setWidget(content)
        layout = QVBoxLayout(content)

        # ---------------- Thresholds ----------------
        thresholds_box = QGroupBox("Detection Thresholds")
        form = QFormLayout(thresholds_box)

        self.large_file_spin = QSpinBox()
        self.large_file_spin.setRange(1, 100000)
        self.large_file_spin.setValue(int(self.config.get("large_file_mb", 10)))
        self.large_file_spin.setSuffix(" MB")
        form.addRow("Large file threshold:", self.large_file_spin)

        self.ghost_ext_edit = QLineEdit(", ".join(self.config.get("ghost_extensions", [])))
        form.addRow("Ghost extensions:", self.ghost_ext_edit)

        self.ghost_kw_edit = QLineEdit(", ".join(self.config.get("ghost_keywords", [])))
        form.addRow("Ghost name keywords:", self.ghost_kw_edit)

        self.log_ext_edit = QLineEdit(", ".join(self.config.get("log_extensions", [])))
        form.addRow("Log file extensions:", self.log_ext_edit)

        self.cache_dirs_edit = QLineEdit(", ".join(self.config.get("cache_dir_names", [])))
        form.addRow("Cache folder names:", self.cache_dirs_edit)

        layout.addWidget(thresholds_box)

        # ---------------- Cleanup categories ----------------
        categories_box = QGroupBox("Cleanup Categories")
        cat_layout = QVBoxLayout(categories_box)

        self.detect_cache_check = QCheckBox("Detect cache folders")
        self.detect_cache_check.setChecked(self.config.get("detect_cache", True))
        cat_layout.addWidget(self.detect_cache_check)

        self.detect_logs_check = QCheckBox("Detect log files")
        self.detect_logs_check.setChecked(self.config.get("detect_logs", True))
        cat_layout.addWidget(self.detect_logs_check)

        self.detect_empty_check = QCheckBox("Detect empty folders")
        self.detect_empty_check.setChecked(self.config.get("detect_empty_dirs", True))
        cat_layout.addWidget(self.detect_empty_check)

        self.detect_broken_check = QCheckBox("Detect broken symlinks")
        self.detect_broken_check.setChecked(self.config.get("detect_broken_links", True))
        cat_layout.addWidget(self.detect_broken_check)

        layout.addWidget(categories_box)

        # ---------------- Scan behaviour ----------------
        scan_box = QGroupBox("Scan Behaviour")
        scan_layout = QVBoxLayout(scan_box)

        self.recursive_check = QCheckBox("Recursive scan by default")
        self.recursive_check.setChecked(self.config.get("recursive", True))
        scan_layout.addWidget(self.recursive_check)

        self.notify_check = QCheckBox("Show desktop notification when scan finishes")
        self.notify_check.setChecked(self.config.get("notify_on_scan", True))
        scan_layout.addWidget(self.notify_check)

        layout.addWidget(scan_box)

        # ---------------- Exclusions ----------------
        excl_box = QGroupBox("Scan Exclusions (folder / file name patterns)")
        excl_layout = QVBoxLayout(excl_box)

        self.excl_list = QListWidget()
        self.excl_list.addItems(self.config.get("exclusions", []))
        excl_layout.addWidget(self.excl_list)

        excl_add_row = QHBoxLayout()
        self.excl_input = QLineEdit()
        self.excl_input.setPlaceholderText("e.g. *.iso or build")
        add_excl_btn = QPushButton("Add")
        add_excl_btn.clicked.connect(self.add_exclusion)
        remove_excl_btn = QPushButton("Remove Selected")
        remove_excl_btn.clicked.connect(self.remove_exclusion)
        excl_add_row.addWidget(self.excl_input)
        excl_add_row.addWidget(add_excl_btn)
        excl_add_row.addWidget(remove_excl_btn)
        excl_layout.addLayout(excl_add_row)

        layout.addWidget(excl_box)

        # ---------------- Health scoring weights ----------------
        weight_box = QGroupBox("Health Score Weights")
        weight_form = QFormLayout(weight_box)

        self.w_ghost_spin = QSpinBox()
        self.w_ghost_spin.setRange(0, 10)
        self.w_ghost_spin.setValue(int(self.config.get("health_weight_ghost", 1)))
        weight_form.addRow("Ghost files weight:", self.w_ghost_spin)

        self.w_dup_spin = QSpinBox()
        self.w_dup_spin.setRange(0, 10)
        self.w_dup_spin.setValue(int(self.config.get("health_weight_duplicate", 1)))
        weight_form.addRow("Duplicate waste weight:", self.w_dup_spin)

        self.w_large_spin = QSpinBox()
        self.w_large_spin.setRange(0, 10)
        self.w_large_spin.setValue(int(self.config.get("health_weight_large", 1)))
        weight_form.addRow("Large files weight:", self.w_large_spin)

        layout.addWidget(weight_box)

        # ---------------- Desktop integration ----------------
        integration_box = QGroupBox("Desktop Integration")
        integration_layout = QVBoxLayout(integration_box)

        if sys.platform.startswith("linux"):
            install_desktop_btn = QPushButton("Install Desktop Entry (Linux)")
            install_desktop_btn.clicked.connect(self.install_linux_desktop_entry)
            integration_layout.addWidget(install_desktop_btn)
        elif sys.platform.startswith("win"):
            shortcut_btn = QPushButton("Create Desktop Shortcut (Windows)")
            shortcut_btn.clicked.connect(self.create_windows_shortcut)
            integration_layout.addWidget(shortcut_btn)

        layout.addWidget(integration_box)

        layout.addStretch()

        outer.addWidget(scroll)

        buttons = QDialogButtonBox(QDialogButtonBox.Save | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        outer.addWidget(buttons)

    def add_exclusion(self):
        text = self.excl_input.text().strip()
        if text:
            self.excl_list.addItem(text)
            self.excl_input.clear()

    def remove_exclusion(self):
        for item in self.excl_list.selectedItems():
            self.excl_list.takeItem(self.excl_list.row(item))

    def install_linux_desktop_entry(self):
        ok, message = install_linux_desktop_entry()
        box = QMessageBox(self)
        box.setWindowTitle("Desktop Entry")
        box.setText(message)
        box.setIcon(QMessageBox.Information if ok else QMessageBox.Warning)
        box.exec()

    def create_windows_shortcut(self):
        ok, message = create_windows_shortcut()
        box = QMessageBox(self)
        box.setWindowTitle("Desktop Shortcut")
        box.setText(message)
        box.setIcon(QMessageBox.Information if ok else QMessageBox.Warning)
        box.exec()

    def result_config(self):
        config = dict(self.config)
        config["large_file_mb"] = self.large_file_spin.value()
        config["ghost_extensions"] = [e.strip() for e in self.ghost_ext_edit.text().split(",") if e.strip()]
        config["ghost_keywords"] = [k.strip() for k in self.ghost_kw_edit.text().split(",") if k.strip()]
        config["log_extensions"] = [e.strip() for e in self.log_ext_edit.text().split(",") if e.strip()]
        config["cache_dir_names"] = [c.strip() for c in self.cache_dirs_edit.text().split(",") if c.strip()]
        config["detect_cache"] = self.detect_cache_check.isChecked()
        config["detect_logs"] = self.detect_logs_check.isChecked()
        config["detect_empty_dirs"] = self.detect_empty_check.isChecked()
        config["detect_broken_links"] = self.detect_broken_check.isChecked()
        config["recursive"] = self.recursive_check.isChecked()
        config["notify_on_scan"] = self.notify_check.isChecked()
        config["exclusions"] = [self.excl_list.item(i).text() for i in range(self.excl_list.count())]
        config["health_weight_ghost"] = self.w_ghost_spin.value()
        config["health_weight_duplicate"] = self.w_dup_spin.value()
        config["health_weight_large"] = self.w_large_spin.value()
        return config


# ============================================================
# Desktop integration helpers
# ============================================================

def get_launch_target():
    """Best-effort path/command used to relaunch the app (frozen exe or script)."""
    if getattr(sys, "frozen", False):
        return sys.executable
    return f'{sys.executable} "{Path(__file__).resolve()}"'


def install_linux_desktop_entry():
    try:
        apps_dir = Path.home() / ".local" / "share" / "applications"
        icons_dir = Path.home() / ".local" / "share" / "icons" / "hicolor" / "256x256" / "apps"
        apps_dir.mkdir(parents=True, exist_ok=True)
        icons_dir.mkdir(parents=True, exist_ok=True)

        icon_src = ASSETS_DIR / "icon.png"
        icon_dest = icons_dir / "ghostfiles.png"
        if icon_src.exists():
            shutil.copyfile(icon_src, icon_dest)

        exec_line = get_launch_target()

        desktop_entry = (
            "[Desktop Entry]\n"
            "Type=Application\n"
            "Name=Ghost Files\n"
            "Comment=Find ghost files, duplicates and large files\n"
            f"Exec={exec_line}\n"
            "Icon=ghostfiles\n"
            "Terminal=false\n"
            "Categories=Utility;FileTools;\n"
        )

        (apps_dir / "ghostfiles.desktop").write_text(desktop_entry, encoding="utf-8")

        try:
            subprocess.run(
                ["update-desktop-database", str(apps_dir)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        except FileNotFoundError:
            pass

        return True, f"Desktop entry installed to {apps_dir / 'ghostfiles.desktop'}"

    except OSError as exc:
        return False, f"Could not install desktop entry: {exc}"


def create_windows_shortcut():
    try:
        import winshell  # type: ignore
        from win32com.client import Dispatch  # type: ignore

        desktop = winshell.desktop()
        path = os.path.join(desktop, "Ghost Files.lnk")
        target = sys.executable if getattr(sys, "frozen", False) else sys.executable
        args = "" if getattr(sys, "frozen", False) else f'"{Path(__file__).resolve()}"'

        shell = Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(path)
        shortcut.Targetpath = target
        shortcut.Arguments = args
        shortcut.WorkingDirectory = str(Path(__file__).resolve().parent)
        icon_path = ASSETS_DIR / "icon.ico"
        if icon_path.exists():
            shortcut.IconLocation = str(icon_path)
        shortcut.save()

        return True, f"Shortcut created at {path}"

    except ImportError:
        return False, (
            "Creating a shortcut requires 'pywin32' and 'winshell'.\n"
            "Install with: pip install pywin32 winshell"
        )
    except Exception as exc:
        return False, f"Could not create shortcut: {exc}"


def notify(title, message):
    try:
        if sys.platform.startswith("linux"):
            subprocess.run(
                ["notify-send", title, message],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False,
            )
        elif sys.platform == "darwin":
            script = f'display notification "{message}" with title "{title}"'
            subprocess.run(["osascript", "-e", script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
        # Windows notifications are skipped here; the taskbar icon + status bar cover it.
    except FileNotFoundError:
        pass


def reveal_in_file_manager(path):
    path = Path(path)
    target = path if path.is_dir() else path.parent
    try:
        if sys.platform.startswith("win"):
            if path.is_file():
                subprocess.run(["explorer", "/select,", str(path)], check=False)
            else:
                subprocess.run(["explorer", str(path)], check=False)
        elif sys.platform == "darwin":
            if path.is_file():
                subprocess.run(["open", "-R", str(path)], check=False)
            else:
                subprocess.run(["open", str(path)], check=False)
        else:
            try:
                subprocess.run(["nautilus", "--select", str(path)], check=True,
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except (FileNotFoundError, subprocess.CalledProcessError):
                subprocess.run(["xdg-open", str(target)], check=False)
    except Exception:
        pass


# ============================================================
# Background scan worker
#
# Everything CPU/IO heavy (walking the tree, stat()-ing files,
# hashing for duplicate detection) lives here so it can run on a
# QThread instead of the GUI thread. This class never touches any
# QWidget — it only computes data and emits it via signals.
# ============================================================

class ScanWorker(QObject):
    finished = Signal(dict)
    error = Signal(str)

    def __init__(self, folder, config, recursive):
        super().__init__()
        self.folder = folder
        self.config = config
        self.recursive = recursive

    def is_excluded(self, name, patterns):
        return any(fnmatch.fnmatch(name, pattern) or name == pattern for pattern in patterns)

    def walk(self, root, exclusions, recursive):
        if recursive:
            for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
                dirnames[:] = [d for d in dirnames if not self.is_excluded(d, exclusions)]
                yield dirpath, dirnames, filenames
        else:
            dirpath = str(root)
            try:
                entries = list(Path(root).iterdir())
            except OSError:
                entries = []
            dirnames = [e.name for e in entries if e.is_dir() and not self.is_excluded(e.name, exclusions)]
            filenames = [e.name for e in entries if not e.is_dir()]
            yield dirpath, dirnames, filenames

    # ------------------------------------------------------------
    # Fast duplicate hashing
    #
    # Files are already grouped by exact size, so we first compare a
    # small signature made from the beginning/end of each file. Only
    # files that survive that cheap test are fully hashed. Hashing is
    # also parallelised because it is mostly disk I/O.
    # ------------------------------------------------------------

    def quick_hash(self, file_path, sample_size=4096):
        """Cheap duplicate pre-check. Only read a tiny head/tail sample."""
        try:
            size = file_path.stat().st_size
            with open(file_path, "rb") as file:
                if size <= sample_size * 2:
                    data = file.read()
                else:
                    first = file.read(sample_size)
                    file.seek(-sample_size, os.SEEK_END)
                    last = file.read(sample_size)
                    data = first + last

            digest = hashlib.blake2b(digest_size=16)
            digest.update(data)
            digest.update(size.to_bytes(8, "little", signed=False))
            return digest.digest()
        except (PermissionError, OSError, OverflowError):
            return None

    def file_hash(self, file_path):
        try:
            digest = hashlib.blake2b(digest_size=32)
            with open(file_path, "rb") as file:
                while chunk := file.read(4 * 1024 * 1024):
                    digest.update(chunk)
            return digest.digest()
        except (PermissionError, OSError):
            return None

    def find_duplicate_groups(self, size_groups):
        """Find exact duplicates with minimal disk I/O and no per-group thread pools."""
        workers = min(8, max(2, os.cpu_count() or 2))

        # Only files sharing an exact size can possibly be duplicates.
        candidates = [
            file
            for files in size_groups.values() if len(files) > 1
            for file in files
        ]
        if not candidates:
            return []

        # Stage 1: tiny head/tail signature.
        quick_groups = defaultdict(list)
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for file, signature in zip(candidates, pool.map(self.quick_hash, candidates, chunksize=32)):
                if signature is not None:
                    quick_groups[signature].append(file)

        # Stage 2: full hash only for actual quick-signature collisions.
        full_candidates = [
            file
            for group in quick_groups.values() if len(group) > 1
            for file in group
        ]
        if not full_candidates:
            return []

        full_groups = defaultdict(list)
        with ThreadPoolExecutor(max_workers=workers) as pool:
            for file, signature in zip(
                full_candidates,
                pool.map(self.file_hash, full_candidates, chunksize=4),
            ):
                if signature is not None:
                    full_groups[signature].append(file)

        return [group for group in full_groups.values() if len(group) > 1]

    def run(self):
        try:
            path = Path(self.folder)
            cfg = self.config
            exclusions = cfg.get("exclusions", [])
            recursive = self.recursive
            large_file_bytes = int(cfg.get("large_file_mb", 10)) * 1024 * 1024
            ghost_extensions = set(e.lower() for e in cfg.get("ghost_extensions", []))
            ghost_keywords = set(k.lower() for k in cfg.get("ghost_keywords", []))
            cache_dir_names = set(cfg.get("cache_dir_names", []))
            log_extensions = set(e.lower() for e in cfg.get("log_extensions", []))

            total_files = 0
            total_size = 0
            ghost_files = []
            large_files = []
            empty_dirs = []
            size_groups = defaultdict(list)
            extension_stats = defaultdict(lambda: {"count": 0, "size": 0})

            for dirpath, dirnames, filenames in self.walk(path, exclusions, recursive):
                dirpath_p = Path(dirpath)

                if cfg.get("detect_empty_dirs", True) and not dirnames and not filenames:
                    if dirpath_p != path:
                        empty_dirs.append(dirpath_p)

                if cfg.get("detect_cache", True):
                    for d in dirnames:
                        if d in cache_dir_names:
                            ghost_files.append((dirpath_p / d, "CACHE"))

                for filename in filenames:
                    item = dirpath_p / filename

                    try:
                        if item.is_symlink() and not item.exists():
                            if cfg.get("detect_broken_links", True):
                                ghost_files.append((item, "BROKEN_LINK"))
                            continue

                        if not item.is_file():
                            continue

                        stat = item.stat()
                        size = stat.st_size

                        total_files += 1
                        total_size += size
                        size_groups[size].append(item)

                        ext = item.suffix.lower()
                        extension_stats[ext or "(no extension)"]["count"] += 1
                        extension_stats[ext or "(no extension)"]["size"] += size

                        name = item.name.lower()

                        if size == 0:
                            ghost_files.append((item, "EMPTY"))
                        elif ext in ghost_extensions:
                            ghost_files.append((item, "TEMP"))
                        elif cfg.get("detect_logs", True) and ext in log_extensions:
                            ghost_files.append((item, "LOG"))
                        elif any(keyword in name for keyword in ghost_keywords):
                            ghost_files.append((item, "SUSPICIOUS"))

                        if size >= large_file_bytes:
                            large_files.append((item, size))

                    except (PermissionError, OSError):
                        continue

            # --------------------------------------------------------
            # Duplicate detection
            # --------------------------------------------------------

            duplicate_groups = self.find_duplicate_groups(size_groups)

            duplicate_count = sum(len(group) - 1 for group in duplicate_groups)
            duplicate_wasted_space = 0
            for group in duplicate_groups:
                try:
                    duplicate_wasted_space += (len(group) - 1) * group[0].stat().st_size
                except OSError:
                    pass

            # --------------------------------------------------------
            # Health score (weighted, ratio-normalised)
            # --------------------------------------------------------

            w_ghost = cfg.get("health_weight_ghost", 1.0)
            w_dup = cfg.get("health_weight_duplicate", 1.5)
            w_large = cfg.get("health_weight_large", 0.5)
            total_weight = max(w_ghost + w_dup + w_large, 0.0001)

            if total_files == 0:
                health_score = 100
            else:
                ghost_ratio = len(ghost_files) / total_files
                dup_ratio = (duplicate_wasted_space / total_size) if total_size else 0
                large_ratio = len(large_files) / total_files

                penalty = 100 * (
                    (w_ghost * ghost_ratio + w_dup * dup_ratio + w_large * large_ratio) / total_weight
                )
                health_score = max(0, round(100 - penalty))

            results = {
                "folder": str(path),
                "recursive": recursive,
                "ghost_files": ghost_files,
                "duplicate_groups": duplicate_groups,
                "large_files": large_files,
                "empty_dirs": empty_dirs,
                "extension_stats": dict(extension_stats),
                "total_size": total_size,
                "total_files": total_files,
                "duplicate_wasted_space": duplicate_wasted_space,
                "duplicate_count": duplicate_count,
                "health_score": health_score,
            }

            self.finished.emit(results)

        except Exception as exc:  # noqa: BLE001 - surface any unexpected error to the UI
            self.error.emit(str(exc))


# ============================================================
# Main Application
# ============================================================


class GhostFiles(QMainWindow):

    def __init__(self):
        super().__init__()

        self.config = load_config()
        self.history = load_history()

        # Background scan state
        self._scan_thread = None
        self._scan_worker = None
        self._preserve_status = False

        self.setWindowTitle("Ghost Files")
        self.resize(1300, 800)

        icon_path = ASSETS_DIR / "icon.png"
        if icon_path.exists():
            self.setWindowIcon(QIcon(str(icon_path)))

        self.current_folder = None
        self.scan_data = {
            "ghost_files": [],
            "duplicate_groups": [],
            "large_files": [],
            "empty_dirs": [],
            "extension_stats": {},
            "total_size": 0,
        }

        central = QWidget()
        self.setCentralWidget(central)

        main_layout = QVBoxLayout(central)
        main_layout.setContentsMargins(45, 35, 45, 35)
        main_layout.setSpacing(20)

        # --------------------------------------------------------
        # Header
        # --------------------------------------------------------

        header = QHBoxLayout()

        title = QLabel("GHOST FILES")
        title.setStyleSheet("QLabel { color: white; font-size: 30px; font-weight: bold; }")

        self.recursive_check = QCheckBox("Recursive")
        self.recursive_check.setChecked(self.config.get("recursive", True))
        self.recursive_check.setStyleSheet("QCheckBox { color: #cccccc; }")

        self.settings_button = QPushButton("SETTINGS")
        self.settings_button.setFixedSize(120, 45)
        self.settings_button.clicked.connect(self.open_settings)

        self.scan_button = QPushButton("SCAN FOLDER")
        self.scan_button.setFixedSize(170, 45)
        self.scan_button.clicked.connect(self.select_folder)

        self.trash_button = QPushButton("MOVE TO TRASH")
        self.trash_button.setFixedSize(170, 45)
        self.trash_button.clicked.connect(self.trash_selected)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.recursive_check)
        header.addWidget(self.settings_button)
        header.addWidget(self.trash_button)
        header.addWidget(self.scan_button)

        main_layout.addLayout(header)

        # --------------------------------------------------------
        # Status
        # --------------------------------------------------------

        self.status = QLabel("Select a folder to scan")
        self.status.setStyleSheet("QLabel { color: #888888; font-size: 14px; }")
        main_layout.addWidget(self.status)

        # --------------------------------------------------------
        # Health
        # --------------------------------------------------------

        self.health = QLabel("—")
        self.health.setAlignment(Qt.AlignCenter)
        self.health.setStyleSheet("QLabel { color: white; font-size: 52px; font-weight: bold; }")

        health_label = QLabel("PROJECT HEALTH")
        health_label.setAlignment(Qt.AlignCenter)
        health_label.setStyleSheet("QLabel { color: #777777; font-size: 12px; letter-spacing: 2px; }")

        main_layout.addWidget(self.health)
        main_layout.addWidget(health_label)

        # --------------------------------------------------------
        # Statistics
        # --------------------------------------------------------

        stats = QHBoxLayout()
        stats.setSpacing(15)

        self.files_card = self.create_card("FILES")
        self.ghost_card = self.create_card("GHOSTS")
        self.duplicate_card = self.create_card("DUPLICATES")
        self.large_card = self.create_card("LARGE FILES")
        self.empty_card = self.create_card("EMPTY DIRS")

        stats.addWidget(self.files_card)
        stats.addWidget(self.ghost_card)
        stats.addWidget(self.duplicate_card)
        stats.addWidget(self.large_card)
        stats.addWidget(self.empty_card)

        main_layout.addLayout(stats)

        # --------------------------------------------------------
        # Filter / Sort toolbar
        # --------------------------------------------------------

        tools_row = QHBoxLayout()

        self.filter_edit = QLineEdit()
        self.filter_edit.setPlaceholderText("Filter results by name…")
        self.filter_edit.textChanged.connect(self.apply_filter)

        self.sort_combo = QComboBox()
        self.sort_combo.addItems(["Name (A-Z)", "Name (Z-A)", "Size (Large-Small)", "Size (Small-Large)"])
        self.sort_combo.currentIndexChanged.connect(self.render_all_tabs)

        tools_row.addWidget(self.filter_edit, 3)
        tools_row.addWidget(self.sort_combo, 1)

        main_layout.addLayout(tools_row)

        # --------------------------------------------------------
        # Results tabs + preview pane
        # --------------------------------------------------------

        self.tabs = QTabWidget()

        self.ghost_list = self.create_list()
        self.duplicate_list = self.create_list()
        self.large_list = self.create_list()
        self.empty_list = self.create_list()
        self.history_list = self.create_list()
        self.analytics_list = self.create_list()

        self.tabs.addTab(self.ghost_list, "Ghosts")
        self.tabs.addTab(self.duplicate_list, "Duplicates")
        self.tabs.addTab(self.large_list, "Large Files")
        self.tabs.addTab(self.empty_list, "Empty Dirs")
        self.tabs.addTab(self.analytics_list, "Analytics")
        self.tabs.addTab(self.history_list, "History")

        self.tabs.currentChanged.connect(lambda _: self.apply_filter())

        for lw in (self.ghost_list, self.duplicate_list, self.large_list, self.empty_list):
            lw.itemSelectionChanged.connect(self.update_preview)
            lw.setContextMenuPolicy(Qt.CustomContextMenu)
            lw.customContextMenuRequested.connect(self.show_context_menu)

        self.history_list.itemDoubleClicked.connect(self.rescan_from_history)

        # Preview panel
        self.preview_panel = QFrame()
        self.preview_panel.setStyleSheet(
            "QFrame { background-color: #111117; border: 1px solid #292934; border-radius: 10px; }"
        )
        preview_layout = QVBoxLayout(self.preview_panel)

        self.preview_image = QLabel("No selection")
        self.preview_image.setAlignment(Qt.AlignCenter)
        self.preview_image.setStyleSheet("QLabel { color: #666666; }")
        self.preview_image.setMinimumHeight(200)

        self.preview_text = QTextEdit()
        self.preview_text.setReadOnly(True)
        self.preview_text.setStyleSheet(
            "QTextEdit { background-color: #0b0b0f; color: #cccccc; border: 1px solid #292934; }"
        )
        self.preview_text.hide()

        self.preview_info = QLabel("")
        self.preview_info.setWordWrap(True)
        self.preview_info.setStyleSheet("QLabel { color: #999999; font-size: 12px; }")

        preview_layout.addWidget(QLabel("PREVIEW", styleSheet="color:#777777; font-size:11px; letter-spacing:2px;"))
        preview_layout.addWidget(self.preview_image)
        preview_layout.addWidget(self.preview_text)
        preview_layout.addWidget(self.preview_info)
        preview_layout.addStretch()

        splitter = QSplitter()
        splitter.addWidget(self.tabs)
        splitter.addWidget(self.preview_panel)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 2)

        main_layout.addWidget(splitter)

        # --------------------------------------------------------
        # Theme
        # --------------------------------------------------------

        self.setStyleSheet("""
            QMainWindow { background-color: #0b0b0f; }
            QPushButton {
                background-color: #191922; color: white; border: 1px solid #444455;
                border-radius: 9px; font-size: 13px; font-weight: bold;
            }
            QPushButton:hover { background-color: #242430; }
            QPushButton:pressed { background-color: #30303d; }
            QPushButton:disabled { color: #666666; border-color: #333340; }
            QTabWidget::pane { border: 1px solid #292934; border-radius: 10px; background-color: #111117; }
            QTabBar::tab { background-color: #111117; color: #777777; padding: 10px 22px; border: none; }
            QTabBar::tab:selected { color: white; }
            QLineEdit, QComboBox, QSpinBox {
                background-color: #191922; color: white; border: 1px solid #444455;
                border-radius: 6px; padding: 6px; font-size: 13px;
            }
            QGroupBox {
                color: #cccccc; border: 1px solid #292934; border-radius: 8px;
                margin-top: 12px; padding-top: 10px; font-weight: bold;
            }
            QGroupBox::title { subcontrol-origin: margin; left: 10px; padding: 0 4px; }
        """)

        self.render_history_tab()

        if sys.platform.startswith("win"):
            try:
                import ctypes
                ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("ghostfiles.app.1.0")
            except Exception:
                pass

    # ============================================================
    # UI Helpers
    # ============================================================

    def create_card(self, name):
        card = QFrame()
        card.setFixedHeight(90)
        layout = QVBoxLayout(card)

        value = QLabel("0")
        value.setAlignment(Qt.AlignCenter)
        value.setStyleSheet("QLabel { color: white; font-size: 26px; font-weight: bold; }")

        label = QLabel(name)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("QLabel { color: #777777; font-size: 11px; }")

        layout.addWidget(value)
        layout.addWidget(label)

        card.setStyleSheet(
            "QFrame { background-color: #111117; border: 1px solid #292934; border-radius: 10px; }"
        )
        card.value_label = value
        return card

    def create_list(self):
        widget = QListWidget()
        widget.setSelectionMode(QListWidget.SingleSelection)
        widget.setStyleSheet("""
            QListWidget { background-color: #111117; color: #dddddd; border: none; padding: 12px; font-size: 13px; }
            QListWidget::item { padding: 7px; }
            QListWidget::item:hover { background-color: #1c1c25; }
            QListWidget::item:selected { background-color: #292934; color: white; }
        """)
        return widget

    # ============================================================
    # Settings
    # ============================================================

    def open_settings(self):
        dialog = SettingsDialog(self.config, self)
        if dialog.exec() == QDialog.Accepted:
            self.config = dialog.result_config()
            save_config(self.config)
            self.recursive_check.setChecked(self.config.get("recursive", True))
            self.status.setText("Settings saved")
            if self.current_folder:
                self.scan_folder(self.current_folder)

    # ============================================================
    # Trash
    # ============================================================

    def move_to_trash(self, file_path):
        file_path = Path(file_path)
        if not file_path.exists():
            return False

        try:
            if sys.platform.startswith("win"):
                try:
                    from send2trash import send2trash
                    send2trash(str(file_path))
                    return True
                except ImportError:
                    return False
                except OSError:
                    return False

            elif sys.platform.startswith("linux"):
                try:
                    subprocess.run(
                        ["gio", "trash", str(file_path)],
                        check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True,
                    )
                    return True
                except FileNotFoundError:
                    try:
                        trash_dir = Path.home() / ".local" / "share" / "Trash"
                        files_dir = trash_dir / "files"
                        info_dir = trash_dir / "info"
                        files_dir.mkdir(parents=True, exist_ok=True)
                        info_dir.mkdir(parents=True, exist_ok=True)

                        destination = files_dir / file_path.name
                        if destination.exists():
                            destination = files_dir / (
                                f"{file_path.stem}_{file_path.stat().st_mtime_ns}{file_path.suffix}"
                            )
                        shutil.move(str(file_path), str(destination))
                        return True
                    except (OSError, shutil.Error):
                        return False
                except subprocess.CalledProcessError:
                    return False
                except (OSError, shutil.Error):
                    return False

            elif sys.platform == "darwin":
                try:
                    script = f'tell application "Finder" to delete POSIX file "{file_path}"'
                    subprocess.run(["osascript", "-e", script], check=True,
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return True
                except (FileNotFoundError, subprocess.CalledProcessError):
                    return False
            else:
                return False

        except Exception:
            return False

    def trash_selected(self):
        current_tab = self.tabs.currentWidget()
        if current_tab is None or current_tab not in (
            self.ghost_list, self.duplicate_list, self.large_list, self.empty_list
        ):
            self.status.setText("Select a file in Ghosts, Duplicates, Large Files or Empty Dirs")
            return

        selected = current_tab.selectedItems()
        if not selected:
            self.status.setText("Select a file first")
            return

        item = selected[0]
        file_path = item.data(Qt.UserRole)
        if not file_path:
            self.status.setText("Select an actual file")
            return

        file_path = Path(file_path)
        if not file_path.exists():
            self.status.setText("File no longer exists")
            return

        if self.move_to_trash(file_path):
            item.setText(f"[MOVED TO TRASH]  {file_path}")
            item.setData(Qt.UserRole, None)
            self.status.setText(f"Moved to Trash: {file_path.name}")
            if self.current_folder:
                self.scan_folder(self.current_folder, preserve_status=True)
        else:
            self.status.setText(f"Could not move to Trash: {file_path.name}")

    # ============================================================
    # Context menu
    # ============================================================

    def show_context_menu(self, pos):
        list_widget = self.sender()
        item = list_widget.itemAt(pos)
        if item is None:
            return
        file_path = item.data(Qt.UserRole)
        if not file_path:
            return

        menu = QMenu(self)
        reveal_action = QAction("Reveal in File Manager", self)
        copy_action = QAction("Copy Path", self)
        trash_action = QAction("Move to Trash", self)

        menu.addAction(reveal_action)
        menu.addAction(copy_action)
        menu.addAction(trash_action)

        chosen = menu.exec(list_widget.mapToGlobal(pos))

        if chosen == reveal_action:
            reveal_in_file_manager(file_path)
        elif chosen == copy_action:
            QApplication.clipboard().setText(str(file_path))
            self.status.setText("Path copied to clipboard")
        elif chosen == trash_action:
            list_widget.setCurrentItem(item)
            self.trash_selected()

    # ============================================================
    # Preview
    # ============================================================

    def update_preview(self):
        list_widget = self.sender()
        selected = list_widget.selectedItems()
        if not selected:
            return
        file_path = selected[0].data(Qt.UserRole)
        if not file_path:
            self.preview_info.setText("")
            self.preview_image.setText("No selection")
            self.preview_image.show()
            self.preview_text.hide()
            return

        path = Path(file_path)
        if not path.exists():
            self.preview_info.setText("File no longer exists")
            return

        ext = path.suffix.lower()

        try:
            stat = path.stat()
            size = format_size(stat.st_size)
            modified = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M")
        except OSError:
            size = "?"
            modified = "?"

        self.preview_info.setText(f"{path.name}\n{path}\n\nSize: {size}\nModified: {modified}")

        if ext in IMAGE_PREVIEW_EXTENSIONS:
            pixmap = QPixmap(str(path))
            if not pixmap.isNull():
                self.preview_image.setPixmap(
                    pixmap.scaled(320, 240, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                )
                self.preview_image.show()
                self.preview_text.hide()
                return

        if ext in TEXT_PREVIEW_EXTENSIONS:
            try:
                with open(path, "r", encoding="utf-8", errors="replace") as f:
                    content = f.read(4000)
                self.preview_text.setPlainText(content)
                self.preview_text.show()
                self.preview_image.hide()
                return
            except OSError:
                pass

        self.preview_image.setText("No preview available")
        self.preview_image.show()
        self.preview_text.hide()

    # ============================================================
    # Folder Selection
    # ============================================================

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folder:
            self.scan_folder(folder)

    def rescan_from_history(self, item):
        folder = item.data(Qt.UserRole)
        if folder and Path(folder).exists():
            self.scan_folder(folder)
        else:
            self.status.setText("That folder is no longer available")

    # ============================================================
    # Main Scanner — launches a background QThread so the GUI
    # thread never blocks on the disk walk / hashing.
    # ============================================================

    def scan_folder(self, folder, preserve_status=False):
        if self._scan_thread is not None and self._scan_thread.isRunning():
            self.status.setText("A scan is already in progress…")
            return

        path = Path(folder)
        self.current_folder = path
        recursive = self.recursive_check.isChecked()

        self._preserve_status = preserve_status
        self.scan_button.setEnabled(False)
        self.scan_button.setText("SCANNING…")
        if not preserve_status:
            self.status.setText(f"Scanning {path.name}…")

        thread = QThread(self)
        worker = ScanWorker(str(path), dict(self.config), recursive)
        worker.moveToThread(thread)

        thread.started.connect(worker.run)
        worker.finished.connect(self._on_scan_finished)
        worker.error.connect(self._on_scan_error)
        worker.finished.connect(thread.quit)
        worker.error.connect(thread.quit)
        worker.finished.connect(worker.deleteLater)
        thread.finished.connect(thread.deleteLater)
        thread.finished.connect(self._clear_scan_thread_ref)

        self._scan_thread = thread
        self._scan_worker = worker
        thread.start()

    def _clear_scan_thread_ref(self):
        self._scan_thread = None
        self._scan_worker = None

    def _on_scan_error(self, message):
        self.status.setText(f"Scan failed: {message}")
        self.scan_button.setEnabled(True)
        self.scan_button.setText("SCAN FOLDER")

    def _on_scan_finished(self, results):
        preserve_status = self._preserve_status
        path = Path(results["folder"])
        recursive = results["recursive"]

        self.scan_data = {
            "ghost_files": results["ghost_files"],
            "duplicate_groups": results["duplicate_groups"],
            "large_files": results["large_files"],
            "empty_dirs": results["empty_dirs"],
            "extension_stats": results["extension_stats"],
            "total_size": results["total_size"],
            "total_files": results["total_files"],
            "duplicate_wasted_space": results["duplicate_wasted_space"],
            "duplicate_count": results["duplicate_count"],
        }

        # --------------------------------------------------------
        # Update statistics cards
        # --------------------------------------------------------

        self.files_card.value_label.setText(str(results["total_files"]))
        self.ghost_card.value_label.setText(str(len(results["ghost_files"])))
        self.duplicate_card.value_label.setText(str(results["duplicate_count"]))
        self.large_card.value_label.setText(str(len(results["large_files"])))
        self.empty_card.value_label.setText(str(len(results["empty_dirs"])))
        self.health.setText(str(results["health_score"]))

        if not preserve_status:
            self.status.setText(
                f"Scanned: {path.name}   •   "
                f"{'Recursive' if recursive else 'Top-level only'}   •   "
                f"Duplicate waste: {format_size(results['duplicate_wasted_space'])}"
            )

        self.render_all_tabs()

        # --------------------------------------------------------
        # History
        # --------------------------------------------------------

        self.history.append({
            "folder": str(path),
            "timestamp": datetime.now().isoformat(timespec="seconds"),
            "total_files": results["total_files"],
            "ghosts": len(results["ghost_files"]),
            "duplicates": results["duplicate_count"],
            "large_files": len(results["large_files"]),
            "health_score": results["health_score"],
        })
        save_history(self.history)
        self.render_history_tab()

        if self.config.get("notify_on_scan", True) and not preserve_status:
            notify("Ghost Files", f"Scan complete: health score {results['health_score']} for {path.name}")

        self.scan_button.setEnabled(True)
        self.scan_button.setText("SCAN FOLDER")

    # ============================================================
    # Rendering (filter + sort applied here, no re-scan needed)
    # ============================================================

    def sort_key_and_reverse(self):
        choice = self.sort_combo.currentText()
        if choice == "Name (A-Z)":
            return (lambda entry: entry[0].name.lower()), False
        if choice == "Name (Z-A)":
            return (lambda entry: entry[0].name.lower()), True
        if choice == "Size (Large-Small)":
            return (lambda entry: entry[1]), True
        return (lambda entry: entry[1]), False

    def entry_size(self, path):
        try:
            return path.stat().st_size
        except OSError:
            return 0

    def render_all_tabs(self):
        self.render_ghost_tab()
        self.render_duplicate_tab()
        self.render_large_tab()
        self.render_empty_tab()
        self.render_analytics_tab()
        self.apply_filter()

    def render_ghost_tab(self):
        self.ghost_list.clear()
        entries = [(f, self.entry_size(f)) for f, _ in self.scan_data["ghost_files"]]
        reasons = {f: r for f, r in self.scan_data["ghost_files"]}
        key, reverse = self.sort_key_and_reverse()
        entries.sort(key=key, reverse=reverse)

        if not entries:
            self.ghost_list.addItem("No ghost files detected.")
            return

        for file, _size in entries:
            reason = reasons.get(file, "?")
            item = QListWidgetItem(f"[{reason}]  {file}")
            item.setData(Qt.UserRole, str(file))
            self.ghost_list.addItem(item)

    def render_duplicate_tab(self):
        self.duplicate_list.clear()
        groups = self.scan_data["duplicate_groups"]

        if not groups:
            self.duplicate_list.addItem("No duplicates detected.")
            return

        groups_sorted = sorted(
            groups,
            key=lambda g: (len(g) - 1) * self.entry_size(g[0]),
            reverse=True,
        )

        for index, group in enumerate(groups_sorted, start=1):
            wasted = (len(group) - 1) * self.entry_size(group[0])
            heading = QListWidgetItem(
                f"GROUP {index}  •  {len(group)} identical files  •  {format_size(wasted)} wasted"
            )
            heading.setData(Qt.UserRole, None)
            self.duplicate_list.addItem(heading)

            for file in group:
                item = QListWidgetItem(f"    {file}")
                item.setData(Qt.UserRole, str(file))
                item.setFlags(item.flags() | Qt.ItemIsSelectable | Qt.ItemIsEnabled)
                self.duplicate_list.addItem(item)

            spacer = QListWidgetItem("")
            spacer.setData(Qt.UserRole, None)
            self.duplicate_list.addItem(spacer)

    def render_large_tab(self):
        self.large_list.clear()
        entries = list(self.scan_data["large_files"])
        key, reverse = self.sort_key_and_reverse()
        entries.sort(key=key, reverse=reverse)

        if not entries:
            self.large_list.addItem("No files larger than the configured threshold.")
            return

        for file, size in entries:
            item = QListWidgetItem(f"{format_size(size)}   {file}")
            item.setData(Qt.UserRole, str(file))
            self.large_list.addItem(item)

    def render_empty_tab(self):
        self.empty_list.clear()
        dirs = list(self.scan_data["empty_dirs"])
        dirs.sort(key=lambda d: str(d).lower())

        if not dirs:
            self.empty_list.addItem("No empty folders detected.")
            return

        for d in dirs:
            item = QListWidgetItem(f"[EMPTY DIR]  {d}")
            item.setData(Qt.UserRole, str(d))
            self.empty_list.addItem(item)

    def render_analytics_tab(self):
        self.analytics_list.clear()
        stats = self.scan_data.get("extension_stats", {})
        total_size = self.scan_data.get("total_size", 0)
        total_files = self.scan_data.get("total_files", 0)

        if not stats:
            self.analytics_list.addItem("Scan a folder to see storage analytics.")
            return

        summary = QListWidgetItem(
            f"TOTAL  •  {total_files} files  •  {format_size(total_size)}"
        )
        summary.setData(Qt.UserRole, None)
        summary.setFlags(Qt.ItemIsEnabled)
        self.analytics_list.addItem(summary)

        ranked = sorted(stats.items(), key=lambda kv: kv[1]["size"], reverse=True)
        max_size = ranked[0][1]["size"] if ranked else 1

        for ext, data in ranked[:40]:
            bar_len = int((data["size"] / max_size) * 30) if max_size else 0
            bar = "█" * max(bar_len, 1)
            text = f"{ext:<16} {bar:<30} {format_size(data['size']):>10}   ({data['count']} files)"
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, None)
            item.setFlags(Qt.ItemIsEnabled)
            self.analytics_list.addItem(item)

    def render_history_tab(self):
        self.history_list.clear()
        if not self.history:
            self.history_list.addItem("No scans yet.")
            return

        for entry in reversed(self.history[-MAX_HISTORY_ENTRIES:]):
            text = (
                f"{entry['timestamp']}   •   {entry['folder']}   •   "
                f"Health {entry['health_score']}   •   {entry['total_files']} files   •   "
                f"{entry['ghosts']} ghosts, {entry['duplicates']} dup, {entry['large_files']} large"
            )
            item = QListWidgetItem(text)
            item.setData(Qt.UserRole, entry["folder"])
            self.history_list.addItem(item)

    # ============================================================
    # Filtering
    # ============================================================

    def apply_filter(self):
        text = self.filter_edit.text().strip().lower()
        current = self.tabs.currentWidget()
        if current is None:
            return
        for i in range(current.count()):
            item = current.item(i)
            item.setHidden(bool(text) and text not in item.text().lower())


# ============================================================
# Application
# ============================================================

def main():
    app = QApplication(sys.argv)
    icon_path = ASSETS_DIR / "icon.png"
    if icon_path.exists():
        app.setWindowIcon(QIcon(str(icon_path)))

    window = GhostFiles()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()