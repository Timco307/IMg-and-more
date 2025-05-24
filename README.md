# Super Easy File Finder

A user-friendly GUI tool to find, deduplicate, and copy images/videos (or any file type) from a drive or folder.

## Features

- Choose drive/folder to search
- Presets for Images, Videos, or both, or custom file types
- Shows total data size found
- Detects duplicates (same name and date), lets you pick which to keep
- Copy files to a folder/drive, keeping original structure or flattening
- Designed to be super user-friendly

## Usage

1. Run `python file_finder_gui.py`
2. Follow the on-screen steps

## Windows EXE Launcher

A simple Windows launcher (`FileFinderLauncher.exe`) is provided. It will:
- Check if Python is installed.
- If Python is found, it runs the GUI.
- If not, it offers to open the Python download page or run a bundled installer.

### How to build the launcher

1. Install [.NET SDK](https://dotnet.microsoft.com/download).
2. Open a terminal in this folder.
3. Run:
   ```
   dotnet new console -n FileFinderLauncher
   // Replace the generated Program.cs with FileFinderLauncher.cs content
   dotnet publish -c Release -r win-x64 --self-contained false
   ```
4. Distribute `FileFinderLauncher.exe` with your Python script and (optionally) a Python installer named `python-installer.exe`.

### One-file EXE (no Python needed)

Alternatively, use [PyInstaller](https://pyinstaller.org/) to bundle everything:
```
pip install pyinstaller
pyinstaller --onefile file_finder_gui.py
```
This creates a standalone EXE that does not require Python to be installed.