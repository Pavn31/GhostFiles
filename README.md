# Ghost Files

<p align="center">
  <img src="assets/ghost-files.png" width="180" alt="Ghost Files">
</p>

<h3 align="center">Find the files your system forgot about.</h3>

<p align="center">
  A lightweight Linux desktop utility for detecting unnecessary, duplicate, temporary, and large files.
</p>

---

## Overview

**Ghost Files** is a lightweight Linux desktop application built with Python and PySide6.

It scans a selected folder and identifies files that may be wasting storage or no longer be useful.

Instead of permanently deleting files, Ghost Files moves selected files to the **Linux Trash**, providing a safer way to clean up storage.

---

## Features

### Ghost File Detection

Detects potentially unnecessary files such as:

- Empty files
- Temporary files
- Backup files
- Old files
- Swap files
- Suspicious filenames

Supported extensions:

```text
.tmp
.bak
.old
.swp
```

Suspicious filename keywords include:

```text
backup
temp
old
```

### Duplicate Detection

Ghost Files detects identical files using:

- File size grouping
- SHA-256 hashing

For each duplicate group, it displays:

- Number of identical files
- File paths
- Estimated wasted storage

### Large File Detection

Detects files larger than the configured threshold.

Current threshold:

```text
10 MB
```

This can be changed in `main.py`.

### Safe Trash Support

Ghost Files does not permanently delete selected files.

Instead, it moves them to the Linux Trash using:

```text
gio trash
```

If `gio` is unavailable, the application falls back to the standard user Trash directory.

### Project Health

Ghost Files calculates a simple health score based on detected:

- Ghost files
- Duplicate files
- Large files

---

## Interface

The application includes:

- File statistics
- Project health score
- Ghost detection
- Duplicate detection
- Large file detection
- Folder scanning
- File selection
- Move to Trash functionality
- Automatic rescanning

---

## Screenshots

### Main Dashboard
*Add screenshot here.*

### Ghost Detection
*Add screenshot here.*

### Duplicate Detection
*Add screenshot here.*

### Large File Detection
*Add screenshot here.*

---

## Requirements

- Linux
- Python 3
- PySide6
- `gio` recommended for Trash integration

---

## Installation

### Clone the Repository

```bash
git clone https://github.com/Pavn31/GhostFiles.git
cd GhostFiles
```

### Create a Virtual Environment

```bash
python -m venv .venv
```

### Activate the Environment

```bash
source .venv/bin/activate
```

### Install Dependencies

```bash
pip install PySide6
```

### Run Ghost Files

```bash
python main.py
```

---

## Linux Executable

Pre-built Linux releases are available through the GitHub Releases page.

Download the latest GhostFiles executable and run:

```bash
chmod +x GhostFiles
./GhostFiles
```

The PyInstaller build requires the accompanying `_internal` directory.

---

## Building From Source

Install PyInstaller:

```bash
pip install pyinstaller
```

Build the application:

```bash
pyinstaller --noconfirm --clean --windowed --name GhostFiles main.py
```

The packaged application will be created inside:

```text
dist/GhostFiles/
```

Structure:

```text
dist/GhostFiles/
├── GhostFiles
└── _internal/
```

Do not delete the `_internal` directory.

---

## Desktop Launcher

Ghost Files can be launched from the Linux application menu using a `.desktop` launcher.

Example:

```ini
[Desktop Entry]
Name=Ghost Files
Comment=Find and clean unnecessary files
Exec=/home/pavan/GhostFiles/dist/GhostFiles/GhostFiles
Icon=/home/pavan/GhostFiles/assets/ghost-files.png
Terminal=false
Type=Application
Categories=Utility;
StartupNotify=true
```

---

## Project Structure

```text
GhostFiles/
├── assets/
│   └── ghost-files.png
├── main.py
├── GhostFiles.spec
├── README.md
└── .gitignore
```

Build directories, virtual environments, and test files are excluded from Git.

---

## How It Works

```text
Selected Folder
       │
       ▼
   Scan Files
       │
       ├───────────────┐
       ▼               ▼
Ghost Detection    Size Analysis
       │               │
       │               ├──────────────┐
       │               ▼              ▼
       │         Large Files     Duplicate Groups
       │                              │
       │                              ▼
       │                         SHA-256 Hash
       │
       ▼
 Results Dashboard
       │
       ▼
 Select File
       │
       ▼
 Move to Trash
       │
       ▼
 Linux Trash
```

---

## Detection Logic

### Empty Files

Files with a size of:

```text
0 bytes
```

are classified as empty ghost files.

### Temporary Files

Known temporary extensions are automatically detected.

### Suspicious Names

Files containing configured keywords such as:

```text
backup
temp
old
```

can be flagged.

### Duplicates

Files are first grouped by size.

Files with matching sizes are then hashed using SHA-256.

Only files with matching hashes are considered duplicates.

### Large Files

Files equal to or larger than `LARGE_FILE_SIZE` are listed as large files.

---

## Safety

Ghost Files moves selected files to the Linux Trash instead of permanently deleting them.

Always review detected files before moving them to Trash.

Do not blindly remove files from system directories.

---

## Tech Stack

| Technology | Purpose |
|---|---|
| Python | Application logic |
| PySide6 | Desktop GUI |
| SHA-256 | Duplicate detection |
| pathlib | File system operations |
| subprocess | Linux Trash integration |
| PyInstaller | Application packaging |

---

## Current Status

**Version:** 1.0.0
**Status:** MVP / Initial Release

### Implemented

- [x] Folder scanning
- [x] Empty file detection
- [x] Temporary file detection
- [x] Suspicious filename detection
- [x] Ghost file detection
- [x] Duplicate detection
- [x] SHA-256 duplicate verification
- [x] Duplicate wasted-space calculation
- [x] Large file detection
- [x] Project health score
- [x] File selection
- [x] Linux Trash support
- [x] Automatic rescanning
- [x] PyInstaller executable
- [x] Desktop launcher
- [x] Custom application icon

### Roadmap

Future versions may include:

- [ ] Configurable detection thresholds
- [ ] Scan exclusions
- [ ] Recursive scan controls
- [ ] File preview
- [ ] Sorting and filtering
- [ ] Scan history
- [ ] Storage analytics
- [ ] Improved health scoring
- [ ] Additional Linux desktop integration
- [ ] More polished release packaging

---

## Contributing

Contributions, suggestions, and bug reports are welcome.

When reporting a bug, include:

- Linux distribution
- Python version
- Ghost Files version
- Steps to reproduce
- Relevant error output

---

## License

This project is licensed under the MIT License.

---

## Author

**Pavan**

GitHub: [@Pavn31](https://github.com/Pavn31)
