# Ghost Files

<p align="center">
  <img src="assets/ghost-files.png" alt="Ghost Files Dashboard" width="250">
</p>

<p align="center">
  <strong>A lightweight file-analysis and cleanup utility for Windows and Linux.</strong>
</p>

<p align="center">
  Detect ghost files, duplicates, large files, cache directories, logs, empty folders, and broken symbolic links.
</p>

<p align="center">
  <a href="https://github.com/Pavn31/GhostFiles/releases/latest">Latest Release</a>
  ·
  <a href="https://github.com/Pavn31/GhostFiles/issues">Issues</a>
</p>

---

## Overview

**Ghost Files** is a desktop utility designed to analyze folders and identify files and directories that may be unnecessary, duplicated, outdated, or consuming significant storage.

It provides a graphical interface built with **Python and PySide6**, with configurable detection rules, scan exclusions, recursive scanning, duplicate detection, storage analytics, health scoring, and desktop integration.

The project is designed to remain simple, lightweight, and useful for everyday storage maintenance.

---

## Features

### File Detection

- Ghost file detection
- Temporary file detection
- Backup and old file detection
- Log file detection
- Cache directory detection
- Empty directory detection
- Broken symbolic-link detection
- Large-file detection
- Duplicate-file detection

### Scanning

- Configurable detection thresholds
- Recursive scan controls
- Scan exclusions
- File and folder pattern exclusions
- Fast directory traversal
- Size-based duplicate pre-filtering
- SHA-256 duplicate verification
- Permission-error handling
- Large-folder support

### File Analysis

- File preview
- File size information
- Sorting
- Filtering
- Duplicate group analysis
- Extension statistics
- Storage analytics
- Duplicate wasted-space calculation

### History & Health

- Scan history
- Historical scan results
- Configurable health-score weights
- Improved health scoring
- Total file statistics
- Ghost-file statistics
- Duplicate statistics
- Large-file statistics
- Empty-directory statistics

### Cleanup

- Additional cleanup categories
- Safe trash-based deletion
- Linux trash integration
- Windows trash integration
- Configurable detection categories

### Desktop Integration

- Linux desktop entry installation
- Windows desktop shortcut creation
- Linux desktop notifications
- Windows integration
- Portable packaging improvements
- Installer package support

---

## Dashboard

<p align="center">
  <img src="assets/main-dashboard.png" alt="Ghost Files Dashboard" width="900">
</p>

The dashboard provides a quick overview of:

- Total files scanned
- Detected ghost files
- Duplicate files
- Large files
- Empty directories
- Storage usage
- Health score
- Scan history

---

## Supported Platforms

| Platform | Status |
|---|---|
| Linux | Supported |
| Windows | Supported |

macOS is currently not a primary target.

---

## Requirements

### Python

Python **3.10+** is recommended.

### Dependencies

```bash
pip install PySide6
```

For Windows trash/shortcut integration:

```bash
pip install send2trash pywin32 winshell
```

Linux desktop integration may use:

```text
gio
notify-send
update-desktop-database
```

These are normally available through the desktop environment or distribution packages.

---

## Running From Source

Clone the repository:

```bash
git clone https://github.com/Pavn31/GhostFiles.git
cd GhostFiles
```

Install dependencies:

```bash
python -m pip install PySide6
```

Run:

```bash
python main.py
```

---

## Configuration

Ghost Files stores user configuration in:

```text
~/.ghostfiles/config.json
```

Scan history is stored in:

```text
~/.ghostfiles/history.json
```

The application automatically creates these files when required.

---

## Detection Configuration

The application allows users to configure:

### Large File Threshold

Set the minimum file size that should be classified as a large file.

Example:

```text
100 MB
```

### Ghost Extensions

Default examples:

```text
.tmp
.bak
.old
.swp
```

### Ghost Keywords

Default examples:

```text
backup
temp
old
```

### Log Extensions

Example:

```text
.log
```

### Cache Directories

Example:

```text
__pycache__
.cache
node_modules
.pytest_cache
.mypy_cache
```

---

## Scan Exclusions

Folders and files can be excluded from scanning.

Default exclusions include:

```text
.git
node_modules
__pycache__
.venv
venv
.cache
Thumbs.db
```

Custom patterns can also be added.

Examples:

```text
*.iso
build
dist
node_modules
```

---

## Recursive Scanning

Ghost Files supports both:

```text
Top-level scan
```

and:

```text
Recursive scan
```

Recursive scanning analyzes nested directories while respecting configured exclusions.

---

## Duplicate Detection

Duplicate detection uses a two-stage approach.

### Stage 1 — File Size

Files are first grouped by file size.

Files with unique sizes cannot be duplicates and therefore do not require hashing.

### Stage 2 — SHA-256

Files sharing the same size are then hashed using SHA-256.

This reduces unnecessary hashing and improves scanning performance on large directory trees.

---

## Health Score

Ghost Files calculates a health score from:

- Ghost-file ratio
- Duplicate wasted-space ratio
- Large-file ratio

The weighting can be configured from the Settings interface.

The score is normalized to:

```text
0 – 100
```

A higher score represents a cleaner storage state.

---

## Storage Analytics

The analytics section provides information about file distribution and storage usage.

It can display:

- File counts
- File sizes
- Extension statistics
- Duplicate waste
- Large-file usage
- Storage distribution

---

## File Preview

Ghost Files supports previews for common text and image formats.

### Text

Examples:

```text
.txt
.md
.py
.json
.yaml
.yml
.ini
.cfg
.csv
.log
.xml
.html
.css
.js
.ts
.sh
.c
.cpp
.h
.java
.rs
.go
.rb
.toml
```

### Images

Examples:

```text
.png
.jpg
.jpeg
.gif
.bmp
.webp
```

---

## Scan History

Ghost Files keeps a local history of recent scans.

Each history entry can contain:

- Folder scanned
- Scan timestamp
- Total files
- Ghost files
- Duplicate files
- Large files
- Health score

The application keeps the most recent scan history entries.

---

## Cleanup

Detected files can be moved to the system trash instead of being permanently deleted.

This provides a safer cleanup workflow.

On Linux, Ghost Files attempts to use:

```bash
gio trash
```

On Windows, the application can use the Windows-compatible trash mechanism.

---

## Desktop Integration

### Linux

Ghost Files can install a desktop entry into:

```text
~/.local/share/applications/
```

The application can also use Linux desktop notifications.

### Windows

Ghost Files supports creating a desktop shortcut and provides Windows-specific integration.

---

## Project Structure

```text
GhostFiles/
├── assets/
│   ├── Ghost-Dashboard.png
│   └── ...
│
├── main.py
├── README.md
├── .gitignore
└── ...
```

---

## Technology Stack

| Technology | Purpose |
|---|---|
| Python | Application logic |
| PySide6 | Desktop GUI |
| pathlib | File-system operations |
| hashlib | SHA-256 hashing |
| JSON | Configuration and history |
| subprocess | Platform integration |
| shutil | File operations |

---

## Performance

Ghost Files is designed to avoid unnecessary work during scanning.

Duplicate detection uses file-size grouping before hashing, meaning the application does not calculate hashes for every file.

For example:

```text
File
 ↓
Read metadata
 ↓
Collect size
 ↓
Group by size
 ↓
Only matching-size files
 ↓
SHA-256 verification
 ↓
Duplicate groups
```

Very large directories can still take time because the application must inspect the underlying filesystem.

---

# Releases

## v1.1.0

**Latest release**

Released with:

- Improved scanning performance
- Improved duplicate detection
- Duplicate detection optimizations
- Updated detection features
- Configurable scanning behaviour
- Improved health scoring
- Scan exclusions
- Recursive scanning controls
- File preview
- Sorting and filtering
- Scan history
- Storage analytics
- Desktop integration improvements
- Windows integration improvements
- Portable packaging improvements
- Additional cleanup categories

### Downloads

**Linux**

```text
GhostFiles-Linux.tar.gz
```

**Windows**

```text
GhostFiles-Windows.zip
```

[Download Ghost Files v1.1.0](https://github.com/Pavn31/GhostFiles/releases/tag/v1.1.0)

---

## Version History

| Version | Status | Highlights |
|---|---|---|
| v1.1.0 | Latest | Performance, scanning, duplicate detection and feature improvements |
| v1.0.0 | Previous | Initial stable release |

---

## Roadmap

Planned improvements include:

- More Linux desktop integration
- Improved Windows integration
- Installer packages
- Portable packaging improvements
- Additional cleanup categories
- Further scanning optimizations
- Improved file analysis
- Additional preview formats
- More storage analytics
- UI improvements
- More platform-specific integrations

---

## Safety

Ghost Files is designed as an analysis and cleanup utility.

Before deleting files:

1. Review the detected item.
2. Confirm that it is unnecessary.
3. Check its location.
4. Use the trash-based cleanup mechanism when possible.

Do not automatically delete system files or files whose purpose you do not understand.

---

## Development

Check the repository status:

```bash
git status
```

Run syntax validation:

```bash
python -m py_compile main.py
```

Run the application:

```bash
python main.py
```

---

## Contributing

Contributions, bug reports, feature requests, and improvements are welcome.

Before submitting a pull request:

1. Test the application.
2. Check for Python syntax errors.
3. Keep changes focused.
4. Update documentation when required.

---

## License

This project is currently maintained by **Pavn31**.

See the repository for the current licensing information.

---

## Author

**Pavan Badiger**

GitHub:

https://github.com/Pavn31

---

<p align="center">
  Built with Python, PySide6, and a lot of filesystem scanning.
</p>
