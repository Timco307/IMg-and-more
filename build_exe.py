import os
import subprocess
import sys
import shutil

SCRIPT = "file_finder_gui.py"
EXE_NAME = "FileFinder.exe"

def ensure_pyinstaller():
    try:
        subprocess.check_call([sys.executable, "-m", "pyinstaller", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        print("PyInstaller not found. Installing...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])

def check_python_shared_lib():
    """
    Check if the required Python shared library exists.
    If not, print an error and exit.
    """
    import sysconfig
    import glob

    libdir = sysconfig.get_config_var('LIBDIR')
    ver = f"{sys.version_info.major}.{sys.version_info.minor}"
    candidates = [
        f"libpython{ver}.so",
        f"libpython{ver}.so.1.0"
    ]
    found = False
    if libdir:
        for candidate in candidates:
            if os.path.exists(os.path.join(libdir, candidate)):
                found = True
                break
    # Also check LD_LIBRARY_PATH
    if not found:
        for path in os.environ.get("LD_LIBRARY_PATH", "").split(":"):
            for candidate in candidates:
                if os.path.exists(os.path.join(path, candidate)):
                    found = True
                    break
    # Try a last-resort search in /usr/lib and /usr/local/lib
    if not found:
        for base in ["/usr/lib", "/usr/local/lib"]:
            for candidate in candidates:
                if glob.glob(os.path.join(base, f"*{candidate}")):
                    found = True
                    break
    if not found:
        print(
            f"ERROR: Python shared library not found (libpython{ver}.so or libpython{ver}.so.1.0).\n"
            "PyInstaller requires the Python shared library to be present.\n"
            "On Debian/Ubuntu, try: sudo apt-get install python3-dev\n"
            "If you built Python yourself, rebuild with --enable-shared.\n"
            "Aborting build."
        )
        sys.exit(1)

def cleanup():
    """Remove build, dist, __pycache__, and .spec file if present."""
    for folder in ["build", "dist", "__pycache__"]:
        if os.path.exists(folder):
            shutil.rmtree(folder)
    spec_file = os.path.splitext(SCRIPT)[0] + ".spec"
    if os.path.exists(spec_file):
        os.remove(spec_file)

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

def find_and_move_exe():
    """Move the built EXE to the current directory if found."""
    dist_path = os.path.join("dist", EXE_NAME)
    if not os.path.exists(dist_path):
        # PyInstaller may use script name if --name fails
        alt_name = os.path.splitext(SCRIPT)[0] + ".exe"
        dist_path = os.path.join("dist", alt_name)
    if os.path.exists(dist_path):
        shutil.move(dist_path, EXE_NAME)
        print(f"EXE created: {EXE_NAME}")
        return True
    else:
        print("Build failed: EXE not found.")
        return False

if __name__ == "__main__":
    print("Cleaning up previous build artifacts...")
    cleanup()
    ensure_pyinstaller()
    check_python_shared_lib()
    build()
    if find_and_move_exe():
        cleanup()
        print("Build complete and cleaned up.")
    else:
        print("Build failed. See above for errors.")
