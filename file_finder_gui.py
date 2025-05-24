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
        self.dest_folder = tk.StringVar()
        self.current_step = 0
        self.steps = []
        self.step_frames = []
        self.build_gui()
        self.show_step(0)

    def build_gui(self):
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)
        self.main_frame = ttk.Frame(self.root, padding=10)
        self.main_frame.grid(row=0, column=0, sticky="nsew")
        self.main_frame.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)

        # Step 0: Folder selection
        step0 = ttk.Frame(self.main_frame)
        ttk.Label(step0, text="1. Choose a drive or folder:").grid(row=0, column=0, sticky="w")
        ttk.Entry(step0, textvariable=self.selected_folder, width=40).grid(row=0, column=1, sticky="ew")
        ttk.Button(step0, text="Browse", command=self.browse_folder).grid(row=0, column=2)
        step0.columnconfigure(1, weight=1)
        self.steps.append(step0)

        # Step 1: File type selection
        step1 = ttk.Frame(self.main_frame)
        ttk.Label(step1, text="2. Choose file types:").grid(row=0, column=0, sticky="w")
        presets = list(PRESETS.keys()) + ["Custom"]
        ttk.OptionMenu(step1, self.selected_preset, presets[0], *presets, command=self.preset_changed).grid(row=0, column=1, sticky="w")
        self.custom_entry = ttk.Entry(step1, textvariable=self.custom_types, width=30, state="disabled")
        self.custom_entry.grid(row=0, column=2, sticky="w")
        self.custom_entry.insert(0, ".txt,.pdf")
        step1.columnconfigure(1, weight=1)
        self.steps.append(step1)

        # Step 2: Find files and show results
        step2 = ttk.Frame(self.main_frame)
        ttk.Button(step2, text="Find Files!", command=self.find_files).grid(row=0, column=0, pady=10, sticky="w")
        self.progress = ttk.Label(step2, text="")
        self.progress.grid(row=1, column=0, columnspan=3, sticky="w")
        self.result_list = tk.Listbox(step2, width=90, height=20)
        self.result_list.grid(row=2, column=0, columnspan=3, sticky="nsew", pady=5)
        step2.rowconfigure(2, weight=1)
        step2.columnconfigure(0, weight=1)
        self.steps.append(step2)

        # Step 3: Duplicate handling
        step3 = ttk.Frame(self.main_frame)
        self.dup_label = ttk.Label(step3, text="")
        self.dup_label.grid(row=0, column=0, sticky="w")
        self.dup_choice = ttk.Combobox(step3, state="readonly", width=80)
        self.dup_choice.grid(row=0, column=1, sticky="ew")
        self.dup_keep_btn = ttk.Button(step3, text="Keep This", command=self.keep_duplicate)
        self.dup_keep_btn.grid(row=0, column=2, sticky="e")
        step3.columnconfigure(1, weight=1)
        self.steps.append(step3)

        # Step 4: Copy options
        step4 = ttk.Frame(self.main_frame)
        ttk.Label(step4, text="4. Copy found files to:").grid(row=0, column=0, sticky="w")
        ttk.Entry(step4, textvariable=self.dest_folder, width=40).grid(row=0, column=1, sticky="ew")
        ttk.Button(step4, text="Browse", command=self.browse_dest).grid(row=0, column=2)
        ttk.Checkbutton(step4, text="Keep folder structure", variable=self.keep_structure).grid(row=1, column=0, columnspan=2, sticky="w")
        ttk.Button(step4, text="Copy Files", command=self.copy_files).grid(row=1, column=2, pady=10, sticky="e")
        step4.columnconfigure(1, weight=1)
        self.steps.append(step4)

        # Navigation buttons
        nav_frame = ttk.Frame(self.main_frame)
        self.back_btn = ttk.Button(nav_frame, text="Back", command=self.prev_step)
        self.next_btn = ttk.Button(nav_frame, text="Next", command=self.next_step)
        self.back_btn.pack(side="left", padx=5)
        self.next_btn.pack(side="right", padx=5)
        nav_frame.grid(row=1, column=0, sticky="ew", pady=(10,0))
        self.nav_frame = nav_frame

        # Hide all steps initially
        for step in self.steps:
            step.grid(row=0, column=0, sticky="nsew")
            step.grid_remove()

    def show_step(self, idx):
        # Hide all steps
        for step in self.steps:
            step.grid_remove()
        self.current_step = idx
        self.steps[idx].grid()
        # Navigation button logic
        self.back_btn["state"] = "normal" if idx > 0 else "disabled"
        if idx == len(self.steps) - 1:
            self.next_btn["state"] = "disabled"
        else:
            self.next_btn["state"] = "normal"
        # Special logic for steps
        if idx == 2:
            self.progress.config(text="")
            self.result_list.delete(0, tk.END)
        if idx == 3:
            self.update_duplicate_ui()
        self.root.update_idletasks()

    def next_step(self):
        if self.current_step == 0:
            folder = self.selected_folder.get()
            if not folder or not os.path.isdir(folder):
                messagebox.showerror("Error", "Please select a valid folder.")
                return
        if self.current_step == 1:
            types = self.get_selected_types()
            if not types:
                messagebox.showerror("Error", "Please select at least one file type.")
                return
        if self.current_step == 2:
            self.find_files()
            if self.duplicates:
                self.show_step(3)
                return
        if self.current_step < len(self.steps) - 1:
            self.show_step(self.current_step + 1)

    def prev_step(self):
        if self.current_step > 0:
            self.show_step(self.current_step - 1)

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
        types = self.get_selected_types()
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

    def update_duplicate_ui(self):
        if not self.duplicates:
            self.dup_label.config(text="No duplicates found.")
            self.dup_choice["values"] = []
            self.dup_choice.set("")
            self.dup_keep_btn["state"] = "disabled"
        else:
            dups = self.duplicates[0]
            self.dup_label.config(text=f"Duplicate found: {os.path.basename(dups[0])}")
            self.dup_choice["values"] = dups
            self.dup_choice.current(0)
            self.dup_keep_btn["state"] = "normal"

    def keep_duplicate(self):
        if not self.duplicates:
            return
        keep = self.dup_choice.get()
        for f in self.duplicates[0]:
            if f != keep and f in self.files_found:
                self.files_found.remove(f)
        self.duplicates.pop(0)
        self.update_duplicate_ui()

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
    root.minsize(800, 600)
    root.mainloop()
