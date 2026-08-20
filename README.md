# Ghost Files

<p align="center">
  <img src="assets/ghost-files.png" width="180" alt="Ghost Files">
</p>

<h3 align="center">Find the files your system forgot about.</h3>

<p align="center">
  A lightweight cross-platform desktop utility for finding unnecessary,
  duplicate, temporary, and large files.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/platform-Linux%20%7C%20Windows-informational" alt="Platforms">
  <img src="https://img.shields.io/badge/Python-3.x-blue" alt="Python">
  <img src="https://img.shields.io/badge/PySide6-Qt-green" alt="PySide6">
  <img src="https://img.shields.io/github/license/Pavn31/GhostFiles" alt="License">
</p>

---

## Overview

**Ghost Files** is a lightweight desktop application built with **Python and PySide6**.

It scans a selected folder and identifies files that may be wasting storage or are no longer useful.

Ghost Files can detect:

- Empty files
- Temporary files
- Suspicious files
- Duplicate files
- Large files

Instead of permanently deleting files, Ghost Files moves selected files to the operating system's trash/recycle system.

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

This avoids hashing every file unnecessarily.

For duplicate groups, Ghost Files displays:

- Number of duplicate files
- File paths
- Estimated wasted storage

### Large File Detection

Files equal to or larger than the configured threshold are displayed separately.

Current threshold:

```text
100 MB
```

The threshold can be changed in `main.py`.

### Safe Trash Support

Ghost Files does not permanently delete selected files.

**Linux**

Uses:

```text
gio trash
```

with a fallback to the standard Linux Trash directory when `gio` is unavailable.

**Windows**

Uses the Python `send2trash` library to move files to the Windows Recycle Bin.

This provides a safer alternative to permanent deletion.

### Project Health

Ghost Files calculates a simple health score based on detected:

- Ghost files
- Duplicate files
- Large files

---

## Interface

The application provides:

- Folder scanning
- File statistics
- Project health score
- Ghost file detection
- Duplicate detection
- Large file detection
- File selection
- Move to Trash / Recycle Bin
- Automatic rescanning
- Cross-platform support

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

## Installation

### Linux

#### Requirements

- Linux
- Python 3
- PySide6
- `gio` recommended

Clone the repository:

```bash
git clone https://github.com/Pavn31/GhostFiles.git
cd GhostFiles
```

Create a virtual environment:

```bash
python -m venv .venv
```

Activate it:

```bash
source .venv/bin/activate
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Run:

```bash
python main.py
```

### Windows

#### Requirements

- Windows 10 or newer
- Python 3
- PySide6
- send2trash

Clone the repository:

```powershell
git clone https://github.com/Pavn31/GhostFiles.git
cd GhostFiles
```

Create a virtual environment:

```powershell
py -m venv .venv
```

Activate it:

```powershell
.venv\Scripts\activate
```

Install dependencies:

```powershell
pip install -r requirements.txt
```

Run:

```powershell
python main.py
```

---

## Download

Pre-built releases are available on the GitHub Releases page.

Each release can provide builds for:

| Platform | File |
|---|---|
| Linux | GhostFiles |
| Windows | GhostFiles.exe |

The Linux build is packaged with PyInstaller.

The Windows build is generated automatically using GitHub Actions.

### Running the Linux Release

Download the Linux release and make it executable:

```bash
chmod +x GhostFiles
```

Run:

```bash
./GhostFiles
```

If the release is distributed as a PyInstaller one-folder package, keep the `_internal` directory alongside the executable.

Structure:

```text
GhostFiles/
├── GhostFiles
└── _internal/
```

### Running the Windows Release

Download:

```text
GhostFiles.exe
```

Run the executable normally.

The Windows build uses `send2trash` to move deleted files to the Windows Recycle Bin.

---

## Building From Source

### Linux Build

Install PyInstaller:

```bash
pip install pyinstaller
```

Build:

```bash
pyinstaller --noconfirm --clean --windowed --name GhostFiles main.py
```

Output:

```text
dist/GhostFiles/
├── GhostFiles
└── _internal/
```

### Windows Build

On Windows:

```powershell
pip install -r requirements.txt
pip install pyinstaller
```

Build:

```powershell
pyinstaller --noconfirm --clean --windowed --name GhostFiles main.py
```

Output:

```text
dist/
└── GhostFiles/
    ├── GhostFiles.exe
    └── _internal/
```

### Automated Windows Build

Ghost Files includes a GitHub Actions workflow for building the Windows version.

The workflow runs on:

```text
windows-latest
```

It:

- Checks out the repository
- Installs Python
- Installs project dependencies
- Installs PyInstaller
- Builds GhostFiles.exe
- Uploads the Windows build as a workflow artifact

The workflow is located at:

```text
.github/workflows/build-windows.yml
```

Windows builds can therefore be produced without requiring a local Windows development machine.

---

## Desktop Launcher

### Linux

Ghost Files can be added to the Linux application menu using a `.desktop` launcher.

Example:

```ini
[Desktop Entry]
Name=Ghost Files
Comment=Find and clean unnecessary files
Exec=/home/USERNAME/GhostFiles/dist/GhostFiles/GhostFiles
Icon=/home/USERNAME/GhostFiles/assets/ghost-files.png
Terminal=false
Type=Application
Categories=Utility;
StartupNotify=true
```

Replace `USERNAME` with your Linux username.

---

## Project Structure

```text
GhostFiles/
├── .github/
│   └── workflows/
│       └── build-windows.yml
├── assets/
│   └── ghost-files.png
├── main.py
├── GhostFiles.spec
├── README.md
├── requirements.txt
└── .gitignore
```

Generated build directories such as:

```text
build/
dist/
```

and local virtual environments are excluded from Git.

---

## How It Works

```text
                  Selected Folder
                         │
                         ▼
                    Scan Files
                         │
          ┌──────────────┼──────────────┐
          │              │              │
          ▼              ▼              ▼
   Ghost Detection   Large Files   Duplicate Detection
          │              │              │
          │              │              ▼
          │              │         Size Grouping
          │              │              │
          │              │              ▼
          │              │         SHA-256 Hash
          │              │              │
          └──────────────┼──────────────┘
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
              ┌──────────┴──────────┐
              ▼                     ▼
            Linux                Windows
              │                     │
              ▼                     ▼
        Linux Trash           Recycle Bin
```

---

## Detection Logic

### Empty Files

Files with:

```text
0 bytes
```

are classified as empty ghost files.

### Temporary Files

Known temporary extensions are automatically detected:

```text
.tmp
.bak
.old
.swp
```

### Suspicious Names

Files containing configured keywords such as:

```text
backup
temp
old
```

can be flagged.

### Duplicate Files

Files are initially grouped by size.

Files with matching sizes are then hashed using SHA-256.

Only files with matching hashes are considered duplicates.

This reduces unnecessary hashing work.

### Large Files

Files equal to or larger than:

```text
LARGE_FILE_SIZE
```

are displayed in the Large Files section.

The current configured threshold is:

```text
10 MB
```

---

## Safety

Ghost Files moves selected files to the operating system's trash/recycle system rather than permanently deleting them.

However, users should still review detected files before moving them.

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
| send2trash | Windows Recycle Bin integration |
| PyInstaller | Application packaging |
| GitHub Actions | Windows builds |

### Requirements

`requirements.txt`:

```text
PySide6
send2trash
```

---

## Current Status

**Version:** 1.0.0
**Status:** Initial Release

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
- [x] Windows Recycle Bin support
- [x] Automatic rescanning
- [x] PyInstaller packaging
- [x] Linux executable
- [x] Windows executable build workflow
- [x] Desktop launcher support
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
- [ ] More Linux desktop integration
- [ ] Improved Windows integration
- [ ] Portable packaging
- [ ] Installer packages

---

## Contributing

Contributions, suggestions, and bug reports are welcome.

When reporting a bug, include:

- Operating system
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
