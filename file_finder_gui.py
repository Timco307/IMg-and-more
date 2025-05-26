import sys
import subprocess
import os

def main():
    gui_file = os.path.join(os.path.dirname(__file__), "file_finder_gui_main.py")
    if not os.path.exists(gui_file):
        print("Error: file_finder_gui_main.py not found.")
        input("Press Enter to exit...")
        sys.exit(1)
    try:
        subprocess.run([sys.executable, gui_file])
    except Exception as e:
        print("Failed to launch GUI:", e)
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
