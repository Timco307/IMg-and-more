import os
import subprocess
import sys
import shutil

SCRIPT = "file_finder_gui.py"
EXE_NAME = "FileFinder.exe"

def ensure_pyinstaller():
    try:
        import PyInstaller  # noqa: F401
    except ImportError:
        print("PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

def build():
    print("Building EXE with PyInstaller...")
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--name", EXE_NAME.replace(".exe", ""),
        SCRIPT
    ]
    subprocess.check_call(cmd)

def move_exe():
    dist_path = os.path.join("dist", EXE_NAME)
    if not os.path.exists(dist_path):
        # PyInstaller may use script name if --name fails
        alt_name = os.path.splitext(SCRIPT)[0] + ".exe"
        dist_path = os.path.join("dist", alt_name)
    if os.path.exists(dist_path):
        shutil.move(dist_path, EXE_NAME)
        print(f"EXE created: {EXE_NAME}")
    else:
        print("Build failed: EXE not found.")

def cleanup():
    for folder in ["build", "dist", "__pycache__"]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
    spec_file = os.path.splitext(SCRIPT)[0] + ".spec"
    if os.path.exists(spec_file):
        os.remove(spec_file)

if __name__ == "__main__":
    ensure_pyinstaller()
    build()
    move_exe()
    cleanup()
    print("Done.")
