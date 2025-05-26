import sys
import subprocess
import os

def main():
    # Always use the absolute path of the current script's directory
    script_dir = os.path.abspath(os.path.dirname(__file__))
    gui_file = os.path.join(script_dir, "file_finder_gui_main.py")
    if not os.path.isfile(gui_file):
        print(f"Error: file_finder_gui_main.py not found in {script_dir}.")
        input("Press Enter to exit...")
        sys.exit(1)
    try:
        subprocess.run([sys.executable, gui_file])
    except Exception as e:
        print("Failed to launch GUI:", e)
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()
