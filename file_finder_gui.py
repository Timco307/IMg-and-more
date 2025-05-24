import os
import shutil
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from collections import defaultdict
from datetime import datetime

PRESETS = {
    "Images": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff"],
    "Videos": [".mp4", ".avi", ".mov", ".mkv", ".wmv"],
    "Images & Videos": [".jpg", ".jpeg", ".png", ".gif", ".bmp", ".tiff", ".mp4", ".avi", ".mov", ".mkv", ".wmv"]
}

def get_file_size(path):
    try:
        return os.path.getsize(path)
    except Exception:
        return 0

class FileFinderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Super Easy File Finder")
        self.selected_folder = tk.StringVar()
        self.selected_preset = tk.StringVar(value="Images")
        self.custom_types = tk.StringVar()
        self.keep_structure = tk.BooleanVar(value=True)
        self.files_found = []
        self.duplicates = []
        self.total_size = 0

        self.build_gui()

    def build_gui(self):
        frm = ttk.Frame(self.root, padding=10)
        frm.pack(fill="both", expand=True)

        # Folder selection
        ttk.Label(frm, text="1. Choose a drive or folder:").grid(row=0, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.selected_folder, width=40).grid(row=0, column=1)
        ttk.Button(frm, text="Browse", command=self.browse_folder).grid(row=0, column=2)

        # File type selection
        ttk.Label(frm, text="2. Choose file types:").grid(row=1, column=0, sticky="w")
        presets = list(PRESETS.keys()) + ["Custom"]
        ttk.OptionMenu(frm, self.selected_preset, presets[0], *presets, command=self.preset_changed).grid(row=1, column=1, sticky="w")
        self.custom_entry = ttk.Entry(frm, textvariable=self.custom_types, width=30, state="disabled")
        self.custom_entry.grid(row=1, column=2, sticky="w")
        self.custom_entry.insert(0, ".txt,.pdf")

        # Find button
        ttk.Button(frm, text="3. Find Files!", command=self.find_files).grid(row=2, column=0, pady=10)

        # Progress and results
        self.progress = ttk.Label(frm, text="")
        self.progress.grid(row=3, column=0, columnspan=3, sticky="w")
        self.result_list = tk.Listbox(frm, width=70, height=10)
        self.result_list.grid(row=4, column=0, columnspan=3, pady=5)

        # Duplicate handling
        self.dup_frame = ttk.Frame(frm)
        self.dup_frame.grid(row=5, column=0, columnspan=3, sticky="w")
        self.dup_label = ttk.Label(self.dup_frame, text="")
        self.dup_label.pack(side="left")
        self.dup_choice = ttk.Combobox(self.dup_frame, state="readonly")
        self.dup_choice.pack(side="left")
        self.dup_keep_btn = ttk.Button(self.dup_frame, text="Keep This", command=self.keep_duplicate)
        self.dup_keep_btn.pack(side="left")
        self.dup_frame.grid_remove()

        # Copy options
        ttk.Label(frm, text="4. Copy found files to:").grid(row=6, column=0, sticky="w")
        self.dest_folder = tk.StringVar()
        ttk.Entry(frm, textvariable=self.dest_folder, width=40).grid(row=6, column=1)
        ttk.Button(frm, text="Browse", command=self.browse_dest).grid(row=6, column=2)
        ttk.Checkbutton(frm, text="Keep folder structure", variable=self.keep_structure).grid(row=7, column=0, columnspan=2, sticky="w")
        ttk.Button(frm, text="Copy Files", command=self.copy_files).grid(row=7, column=2, pady=10)

    def browse_folder(self):
        folder = filedialog.askdirectory()
        if folder:
            self.selected_folder.set(folder)

    def browse_dest(self):
        folder = filedialog.askdirectory()
        if folder:
            self.dest_folder.set(folder)

    def preset_changed(self, value):
        if value == "Custom":
            self.custom_entry.config(state="normal")
        else:
            self.custom_entry.config(state="disabled")

    def get_selected_types(self):
        preset = self.selected_preset.get()
        if preset == "Custom":
            return [x.strip() for x in self.custom_types.get().split(",") if x.strip()]
        return PRESETS.get(preset, [])

    def find_files(self):
        folder = self.selected_folder.get()
        if not folder or not os.path.isdir(folder):
            messagebox.showerror("Error", "Please select a valid folder.")
            return
        types = self.get_selected_types()
        if not types:
            messagebox.showerror("Error", "Please select at least one file type.")
            return

        self.progress.config(text="Searching...")
        self.root.update()
        found = []
        for rootdir, _, files in os.walk(folder):
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in types:
                    full_path = os.path.join(rootdir, f)
                    found.append(full_path)
        self.files_found = found
        self.total_size = sum(get_file_size(f) for f in found)
        self.result_list.delete(0, tk.END)
        for f in found:
            self.result_list.insert(tk.END, f)
        self.progress.config(text=f"Found {len(found)} files, total size: {self.total_size/1024/1024:.2f} MB")
        self.check_duplicates()

    def check_duplicates(self):
        # Duplicates: same name and modified date
        file_map = defaultdict(list)
        for f in self.files_found:
            name = os.path.basename(f)
            try:
                mtime = os.path.getmtime(f)
            except Exception:
                mtime = 0
            key = (name, mtime)
            file_map[key].append(f)
        self.duplicates = [v for v in file_map.values() if len(v) > 1]
        if self.duplicates:
            self.show_next_duplicate()
        else:
            self.dup_frame.grid_remove()

    def show_next_duplicate(self):
        if not self.duplicates:
            self.dup_frame.grid_remove()
            return
        dups = self.duplicates[0]
        self.dup_label.config(text=f"Duplicate found: {os.path.basename(dups[0])}")
        self.dup_choice['values'] = dups
        self.dup_choice.current(0)
        self.dup_frame.grid()

    def keep_duplicate(self):
        keep = self.dup_choice.get()
        # Remove all other dups from files_found
        for f in self.duplicates[0]:
            if f != keep and f in self.files_found:
                self.files_found.remove(f)
        self.duplicates.pop(0)
        self.show_next_duplicate()

    def copy_files(self):
        dest = self.dest_folder.get()
        if not dest or not os.path.isdir(dest):
            messagebox.showerror("Error", "Please select a valid destination folder.")
            return
        keep_struct = self.keep_structure.get()
        base_folder = self.selected_folder.get()
        for f in self.files_found:
            rel_path = os.path.relpath(f, base_folder) if keep_struct else os.path.basename(f)
            dest_path = os.path.join(dest, rel_path)
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            try:
                shutil.copy2(f, dest_path)
            except Exception as e:
                messagebox.showerror("Copy Error", f"Failed to copy {f}: {e}")
        messagebox.showinfo("Done", f"Copied {len(self.files_found)} files.")

if __name__ == "__main__":
    root = tk.Tk()
    app = FileFinderApp(root)
    root.mainloop()
