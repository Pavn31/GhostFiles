# Ghost Files

A lightweight Linux utility for finding unnecessary files and reclaiming disk space.

Ghost Files scans a selected directory and identifies:

- Empty files
- Temporary and backup files
- Suspicious old files
- Duplicate files
- Large files
- Duplicate wasted storage

It provides a simple dark desktop interface and lets you move selected files directly to the Linux Trash.

## Features

### Ghost Detection

Detects files that may no longer be useful:

- Empty files
- `.tmp`
- `.bak`
- `.old`
- `.swp`
- Files containing keywords such as `backup`, `temp`, or `old`

### Duplicate Detection

Uses SHA-256 hashing to identify identical files.

The application also calculates the amount of storage that could be recovered by removing duplicate copies.

### Large File Detection

Finds files above the configured size threshold.

The current release uses a 10 MB threshold for testing and demonstration.

### Safe File Removal

Files are moved to the Linux Trash instead of being permanently deleted.

### Project Health

Ghost Files calculates a simple health score based on detected issues.

## Screenshots

Add screenshots here.

## Installation

### Run from source

```bash
git clone https://github.com/Pavn31/GhostFiles.git
cd GhostFiles

python -m venv .venv
source .venv/bin/activate

pip install PySide6
python main.py
