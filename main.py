import os
import shutil
import sys
import hashlib
import subprocess
from pathlib import Path
from collections import defaultdict

from PySide6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QFileDialog,
    QListWidget,
    QListWidgetItem,
    QFrame,
    QTabWidget,
)

from PySide6.QtCore import Qt

# ============================================================
# Configuration
# ============================================================

GHOST_EXTENSIONS = {
    ".tmp",
    ".bak",
    ".old",
    ".swp",
}

GHOST_KEYWORDS = {
    "backup",
    "temp",
    "old",
}

# Files equal to or larger than 10 MB
LARGE_FILE_SIZE = 10 * 1024 * 1024


# ============================================================
# Main Application
# ============================================================


class GhostFiles(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle("Ghost Files")
        self.resize(1100, 750)

        # Currently scanned folder
        self.current_folder = None

        # --------------------------------------------------------
        # Central widget
        # --------------------------------------------------------

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
        title.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 30px;
                font-weight: bold;
            }
        """)

        self.scan_button = QPushButton("SCAN FOLDER")
        self.scan_button.setFixedSize(170, 45)
        self.scan_button.clicked.connect(self.select_folder)

        self.trash_button = QPushButton("MOVE TO TRASH")
        self.trash_button.setFixedSize(170, 45)
        self.trash_button.clicked.connect(self.trash_selected)

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.trash_button)
        header.addWidget(self.scan_button)

        main_layout.addLayout(header)

        # --------------------------------------------------------
        # Status
        # --------------------------------------------------------

        self.status = QLabel("Select a folder to scan")
        self.status.setStyleSheet("""
            QLabel {
                color: #888888;
                font-size: 14px;
            }
        """)

        main_layout.addWidget(self.status)

        # --------------------------------------------------------
        # Health
        # --------------------------------------------------------

        self.health = QLabel("—")
        self.health.setAlignment(Qt.AlignCenter)
        self.health.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 52px;
                font-weight: bold;
            }
        """)

        health_label = QLabel("PROJECT HEALTH")
        health_label.setAlignment(Qt.AlignCenter)
        health_label.setStyleSheet("""
            QLabel {
                color: #777777;
                font-size: 12px;
                letter-spacing: 2px;
            }
        """)

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

        stats.addWidget(self.files_card)
        stats.addWidget(self.ghost_card)
        stats.addWidget(self.duplicate_card)
        stats.addWidget(self.large_card)

        main_layout.addLayout(stats)

        # --------------------------------------------------------
        # Results tabs
        # --------------------------------------------------------

        self.tabs = QTabWidget()

        self.ghost_list = self.create_list()
        self.duplicate_list = self.create_list()
        self.large_list = self.create_list()

        self.tabs.addTab(self.ghost_list, "Ghosts")
        self.tabs.addTab(self.duplicate_list, "Duplicates")
        self.tabs.addTab(self.large_list, "Large Files")

        main_layout.addWidget(self.tabs)

        # --------------------------------------------------------
        # Theme
        # --------------------------------------------------------

        self.setStyleSheet("""
            QMainWindow {
                background-color: #0b0b0f;
            }

            QPushButton {
                background-color: #191922;
                color: white;
                border: 1px solid #444455;
                border-radius: 9px;
                font-size: 13px;
                font-weight: bold;
            }

            QPushButton:hover {
                background-color: #242430;
            }

            QPushButton:pressed {
                background-color: #30303d;
            }

            QTabWidget::pane {
                border: 1px solid #292934;
                border-radius: 10px;
                background-color: #111117;
            }

            QTabBar::tab {
                background-color: #111117;
                color: #777777;
                padding: 10px 22px;
                border: none;
            }

            QTabBar::tab:selected {
                color: white;
            }
        """)

    # ============================================================
    # UI Helpers
    # ============================================================

    def format_size(self, size):

        if size < 1024:
            return f"{size} B"

        if size < 1024**2:
            return f"{size / 1024:.1f} KB"

        if size < 1024**3:
            return f"{size / (1024 ** 2):.1f} MB"

        if size < 1024**4:
            return f"{size / (1024 ** 3):.1f} GB"

        return f"{size / (1024 ** 4):.1f} TB"

    def create_card(self, name):

        card = QFrame()
        card.setFixedHeight(90)

        layout = QVBoxLayout(card)

        value = QLabel("0")
        value.setAlignment(Qt.AlignCenter)
        value.setStyleSheet("""
            QLabel {
                color: white;
                font-size: 26px;
                font-weight: bold;
            }
        """)

        label = QLabel(name)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("""
            QLabel {
                color: #777777;
                font-size: 11px;
            }
        """)

        layout.addWidget(value)
        layout.addWidget(label)

        card.setStyleSheet("""
            QFrame {
                background-color: #111117;
                border: 1px solid #292934;
                border-radius: 10px;
            }
        """)

        card.value_label = value

        return card

    def create_list(self):

        widget = QListWidget()

        widget.setSelectionMode(QListWidget.SingleSelection)

        widget.setStyleSheet("""
            QListWidget {
                background-color: #111117;
                color: #dddddd;
                border: none;
                padding: 12px;
                font-size: 13px;
            }

            QListWidget::item {
                padding: 7px;
            }

            QListWidget::item:hover {
                background-color: #1c1c25;
            }

            QListWidget::item:selected {
                background-color: #292934;
                color: white;
            }
        """)

        return widget

    # ============================================================
    # Move File To Trash
    # ============================================================

    def move_to_trash(self, file_path):

        file_path = Path(file_path)

        if not file_path.exists():
            return False

        try:

            # ----------------------------------------------------
            # Windows
            # ----------------------------------------------------

            if sys.platform.startswith("win"):

                try:
                    from send2trash import send2trash

                    send2trash(str(file_path))

                    return True

                except ImportError:
                    return False

                except OSError:
                    return False

            # ----------------------------------------------------
            # Linux
            # ----------------------------------------------------

            elif sys.platform.startswith("linux"):

                # Preferred Linux method.
                # gio creates the correct Trash metadata.

                try:

                    subprocess.run(
                        [
                            "gio",
                            "trash",
                            str(file_path),
                        ],
                        check=True,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.PIPE,
                        text=True,
                    )

                    return True

                except FileNotFoundError:

                    # gio is not installed.
                    # Fall back to the standard user Trash directory.

                    try:

                        trash_dir = Path.home() / ".local" / "share" / "Trash"

                        files_dir = trash_dir / "files"
                        info_dir = trash_dir / "info"

                        files_dir.mkdir(
                            parents=True,
                            exist_ok=True,
                        )

                        info_dir.mkdir(
                            parents=True,
                            exist_ok=True,
                        )

                        destination = files_dir / file_path.name

                        if destination.exists():

                            destination = files_dir / (
                                f"{file_path.stem}_"
                                f"{file_path.stat().st_mtime_ns}"
                                f"{file_path.suffix}"
                            )

                        shutil.move(
                            str(file_path),
                            str(destination),
                        )

                        return True

                    except (OSError, shutil.Error):
                        return False

                except subprocess.CalledProcessError:
                    return False

                except (OSError, shutil.Error):
                    return False

            # ----------------------------------------------------
            # Unsupported operating system
            # ----------------------------------------------------

            else:
                return False

        except Exception:
            return False

    # ============================================================
    # Move Selected File
    # ============================================================

    def trash_selected(self):

        current_tab = self.tabs.currentWidget()

        if current_tab is None:
            self.status.setText("No tab selected")
            return

        selected = current_tab.selectedItems()

        if not selected:
            self.status.setText("Select a file first")
            return

        item = selected[0]

        # File path is stored inside the QListWidgetItem.
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

            # Remove stored path so it cannot be moved twice.
            item.setData(Qt.UserRole, None)

            self.status.setText(f"Moved to Trash: {file_path.name}")

            # Refresh scan if possible.
            if self.current_folder:
                self.scan_folder(
                    self.current_folder,
                    preserve_status=True,
                )

        else:

            self.status.setText(f"Could not move to Trash: {file_path.name}")

    # ============================================================
    # Folder Selection
    # ============================================================

    def select_folder(self):

        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Folder",
        )

        if folder:
            self.scan_folder(folder)

    # ============================================================
    # File Hashing
    # ============================================================

    def file_hash(self, file_path):

        sha256 = hashlib.sha256()

        try:

            with open(file_path, "rb") as file:

                while chunk := file.read(1024 * 1024):
                    sha256.update(chunk)

            return sha256.hexdigest()

        except (PermissionError, OSError):
            return None

    # ============================================================
    # Main Scanner
    # ============================================================

    def scan_folder(self, folder, preserve_status=False):

        path = Path(folder)

        self.current_folder = path

        total_files = 0
        ghost_files = []
        large_files = []

        size_groups = defaultdict(list)

        # --------------------------------------------------------
        # Scan files
        # --------------------------------------------------------

        for item in path.rglob("*"):

            try:

                if not item.is_file():
                    continue

                total_files += 1

                size = item.stat().st_size

                size_groups[size].append(item)

                name = item.name.lower()
                extension = item.suffix.lower()

                # ------------------------------------------------
                # Ghost detection
                # ------------------------------------------------

                if size == 0:

                    ghost_files.append((item, "EMPTY"))

                elif extension in GHOST_EXTENSIONS:

                    ghost_files.append((item, "TEMP"))

                elif any(keyword in name for keyword in GHOST_KEYWORDS):

                    ghost_files.append((item, "SUSPICIOUS"))

                # ------------------------------------------------
                # Large files
                # ------------------------------------------------

                if size >= LARGE_FILE_SIZE:

                    large_files.append((item, size))

            except (PermissionError, OSError):
                continue

        # --------------------------------------------------------
        # Duplicate detection
        # --------------------------------------------------------

        duplicate_groups = []

        for files in size_groups.values():

            if len(files) < 2:
                continue

            hashes = defaultdict(list)

            for file in files:

                file_hash = self.file_hash(file)

                if file_hash:
                    hashes[file_hash].append(file)

            for group in hashes.values():

                if len(group) > 1:
                    duplicate_groups.append(group)

        # --------------------------------------------------------
        # Counts
        # --------------------------------------------------------

        duplicate_count = sum(len(group) - 1 for group in duplicate_groups)

        duplicate_wasted_space = sum(
            (len(group) - 1) * group[0].stat().st_size for group in duplicate_groups
        )

        # --------------------------------------------------------
        # Health score
        # --------------------------------------------------------

        problems = len(ghost_files) + duplicate_count + len(large_files)

        if total_files == 0:

            health_score = 100

        else:

            penalty = (problems / total_files) * 100

            health_score = max(
                0,
                round(100 - penalty),
            )

        # --------------------------------------------------------
        # Update statistics
        # --------------------------------------------------------

        self.files_card.value_label.setText(str(total_files))

        self.ghost_card.value_label.setText(str(len(ghost_files)))

        self.duplicate_card.value_label.setText(str(duplicate_count))

        self.large_card.value_label.setText(str(len(large_files)))

        self.health.setText(str(health_score))

        if not preserve_status:

            self.status.setText(
                f"Scanned: {path.name}   •   "
                f"Duplicate waste: "
                f"{self.format_size(duplicate_wasted_space)}"
            )

        # ========================================================
        # Ghost Results
        # ========================================================

        self.ghost_list.clear()

        if not ghost_files:

            self.ghost_list.addItem("No ghost files detected.")

        else:

            for file, reason in ghost_files:

                item = QListWidgetItem(f"[{reason}]  {file}")

                # Store real path internally.
                item.setData(
                    Qt.UserRole,
                    str(file),
                )

                self.ghost_list.addItem(item)

        # ========================================================
        # Duplicate Results
        # ========================================================

        self.duplicate_list.clear()

        if not duplicate_groups:

            self.duplicate_list.addItem("No duplicates detected.")

        else:

            for index, group in enumerate(
                duplicate_groups,
                start=1,
            ):

                heading = QListWidgetItem(
                    f"GROUP {index}  •  "
                    f"{len(group)} identical files  •  "
                    f"{self.format_size((len(group) - 1) * group[0].stat().st_size)} "
                    f"wasted"
                )

                # No file path on heading.
                heading.setData(
                    Qt.UserRole,
                    None,
                )

                self.duplicate_list.addItem(heading)

                for file in group:

                    item = QListWidgetItem(f"    {file}")

                    item.setData(
                        Qt.UserRole,
                        str(file),
                    )

                    item.setFlags(item.flags() | Qt.ItemIsSelectable | Qt.ItemIsEnabled)

                    self.duplicate_list.addItem(item)

                spacer = QListWidgetItem("")

                spacer.setData(
                    Qt.UserRole,
                    None,
                )

                self.duplicate_list.addItem(spacer)

        # ========================================================
        # Large Files
        # ========================================================

        self.large_list.clear()

        large_files.sort(
            key=lambda x: x[1],
            reverse=True,
        )

        if not large_files:

            self.large_list.addItem("No files larger than 10 MB.")

        else:

            for file, size in large_files:

                size_mb = size / (1024 * 1024)

                item = QListWidgetItem(f"{size_mb:.1f} MB   {file}")

                item.setData(
                    Qt.UserRole,
                    str(file),
                )

                self.large_list.addItem(item)


# ============================================================
# Application
# ============================================================

app = QApplication(sys.argv)

window = GhostFiles()
window.show()

sys.exit(app.exec())
