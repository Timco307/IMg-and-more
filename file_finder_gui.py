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

        # Add a help/info button
        help_btn = ttk.Button(self.main_frame, text="Help / Info", command=self.show_help)
        help_btn.grid(row=2, column=0, sticky="e", pady=(0, 5))

        # Step 0: Folder selection
        step0 = ttk.Frame(self.main_frame)
        ttk.Label(step0, text="1. Choose a drive or folder:").grid(row=0, column=0, sticky="w")
        ttk.Entry(step0, textvariable=self.selected_folder, width=40).grid(row=0, column=1, sticky="ew")
        ttk.Button(step0, text="Browse", command=self.browse_folder).grid(row=0, column=2)
        # Add quick access to Desktop/Documents/Drives
        quick_frame = ttk.Frame(step0)
        quick_frame.grid(row=1, column=0, columnspan=3, sticky="w", pady=(5,0))
        ttk.Button(quick_frame, text="Desktop", command=lambda: self.set_quick_folder("Desktop")).pack(side="left", padx=2)
        ttk.Button(quick_frame, text="Documents", command=lambda: self.set_quick_folder("Documents")).pack(side="left", padx=2)
        ttk.Button(quick_frame, text="C:\\", command=lambda: self.set_quick_folder("C:\\")).pack(side="left", padx=2)
        ttk.Button(quick_frame, text="D:\\", command=lambda: self.set_quick_folder("D:\\")).pack(side="left", padx=2)
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
        # Add tooltips for presets
        preset_tip = ttk.Label(step1, text="Presets: Images, Videos, or both. Custom: comma-separated extensions (e.g. .docx,.pdf)", foreground="gray")
        preset_tip.grid(row=1, column=0, columnspan=3, sticky="w")
        step1.columnconfigure(1, weight=1)
        self.steps.append(step1)

        # Step 2: Find files and show results
        step2 = ttk.Frame(self.main_frame)
        ttk.Button(step2, text="Find Files!", command=self.find_files).grid(row=0, column=0, pady=10, sticky="w")
        self.progress = ttk.Label(step2, text="")
        self.progress.grid(row=1, column=0, columnspan=3, sticky="w")
        # Add a frame for the listbox and scrollbar
        listbox_frame = ttk.Frame(step2)
        listbox_frame.grid(row=2, column=0, columnspan=3, sticky="nsew", pady=5)
        step2.rowconfigure(2, weight=1)
        step2.columnconfigure(0, weight=1)
        # Listbox and scrollbar
        self.result_list = tk.Listbox(listbox_frame, width=90, height=20, selectmode="extended")
        self.result_list.pack(side="left", fill="both", expand=True)
        scrollbar = ttk.Scrollbar(listbox_frame, orient="vertical", command=self.result_list.yview)
        scrollbar.pack(side="right", fill="y")
        self.result_list.config(yscrollcommand=scrollbar.set)
        # Add "Select All" and "Deselect All" buttons
        sel_frame = ttk.Frame(step2)
        sel_frame.grid(row=3, column=0, columnspan=3, sticky="w")
        ttk.Button(sel_frame, text="Select All", command=lambda: self.result_list.select_set(0, tk.END)).pack(side="left", padx=2)
        ttk.Button(sel_frame, text="Deselect All", command=lambda: self.result_list.select_clear(0, tk.END)).pack(side="left", padx=2)
        # Add export list button
        ttk.Button(sel_frame, text="Export List", command=self.export_file_list).pack(side="left", padx=2)
        self.steps.append(step2)

        # Step 3: Duplicate handling
        step3 = ttk.Frame(self.main_frame)
        self.dup_label = ttk.Label(step3, text="")
        self.dup_label.grid(row=0, column=0, sticky="w")
        self.dup_choice = ttk.Combobox(step3, state="readonly", width=80)
        self.dup_choice.grid(row=0, column=1, sticky="ew")
        self.dup_keep_btn = ttk.Button(step3, text="Keep This", command=self.keep_duplicate)
        self.dup_keep_btn.grid(row=0, column=2, sticky="e")
        # Add skip all duplicates button
        self.dup_skip_btn = ttk.Button(step3, text="Skip All Duplicates", command=self.skip_all_duplicates)
        self.dup_skip_btn.grid(row=1, column=0, columnspan=3, sticky="w", pady=(5,0))
        step3.columnconfigure(1, weight=1)
        self.steps.append(step3)

        # Step 4: Copy options
        step4 = ttk.Frame(self.main_frame)
        ttk.Label(step4, text="4. Copy found files to:").grid(row=0, column=0, sticky="w")
        ttk.Entry(step4, textvariable=self.dest_folder, width=40).grid(row=0, column=1, sticky="ew")
        ttk.Button(step4, text="Browse", command=self.browse_dest).grid(row=0, column=2)
        ttk.Checkbutton(step4, text="Keep folder structure", variable=self.keep_structure).grid(row=1, column=0, columnspan=2, sticky="w")
        # Add overwrite/skip/cancel options
        self.overwrite_mode = tk.StringVar(value="skip")
        ttk.Label(step4, text="If file exists:").grid(row=2, column=0, sticky="w")
        ttk.Radiobutton(step4, text="Skip", variable=self.overwrite_mode, value="skip").grid(row=2, column=1, sticky="w")
        ttk.Radiobutton(step4, text="Overwrite", variable=self.overwrite_mode, value="overwrite").grid(row=2, column=2, sticky="w")
        ttk.Button(step4, text="Copy Files", command=self.copy_files).grid(row=3, column=2, pady=10, sticky="e")
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

    def show_help(self):
        messagebox.showinfo(
            "Help / Info",
            "Welcome to Super Easy File Finder!\n\n"
            "1. Choose a folder or drive to search.\n"
            "2. Select file types (use presets or custom extensions).\n"
            "3. Click 'Find Files!' to search. You can select/deselect files and export the list.\n"
            "4. Handle duplicates if found.\n"
            "5. Choose where to copy files and how to handle existing files.\n"
            "6. Click 'Copy Files' to finish.\n\n"
            "Tips:\n"
            "- Use the quick access buttons for Desktop/Documents.\n"
            "- Use 'Select All'/'Deselect All' for easy selection.\n"
            "- If you get stuck, just go Back and try again!"
        )

    def set_quick_folder(self, which):
        import pathlib
        if which == "Desktop":
            path = str(pathlib.Path.home() / "Desktop")
        elif which == "Documents":
            path = str(pathlib.Path.home() / "Documents")
        else:
            path = which
        if os.path.isdir(path):
            self.selected_folder.set(path)
        else:
            messagebox.showerror("Error", f"Folder not found: {path}")

    def export_file_list(self):
        if not self.files_found:
            messagebox.showinfo("Export", "No files to export.")
            return
        file = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files","*.txt")])
        if file:
            with open(file, "w", encoding="utf-8") as f:
                for item in self.files_found:
                    f.write(item + "\n")
            messagebox.showinfo("Export", f"File list exported to {file}")

    def skip_all_duplicates(self):
        # Remove all duplicates except the first in each group
        for group in self.duplicates:
            keep = group[0]
            for f in group[1:]:
                if f in self.files_found:
                    self.files_found.remove(f)
        self.duplicates = []
        self.update_duplicate_ui()

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
        if not found:
            messagebox.showinfo("No Files Found", "No files matching your criteria were found. Try a different folder or file type.")

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
        overwrite = self.overwrite_mode.get()
        # Only copy selected files if user made a selection, else all
        selected = self.result_list.curselection()
        files_to_copy = [self.result_list.get(i) for i in selected] if selected else self.files_found
        if not files_to_copy:
            messagebox.showerror("Error", "No files selected to copy.")
            return
        errors = []
        copied = 0
        for f in files_to_copy:
            rel_path = os.path.relpath(f, base_folder) if keep_struct else os.path.basename(f)
            dest_path = os.path.join(dest, rel_path)
            os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            if os.path.exists(dest_path):
                if overwrite == "skip":
                    continue
                elif overwrite == "overwrite":
                    try:
                        shutil.copy2(f, dest_path)
                        copied += 1
                    except Exception as e:
                        errors.append(f"{f}: {e}")
                else:
                    continue
            else:
                try:
                    shutil.copy2(f, dest_path)
                    copied += 1
                except Exception as e:
                    errors.append(f"{f}: {e}")
        msg = f"Copied {copied} files."
        if errors:
            msg += f"\n{len(errors)} errors occurred."
        messagebox.showinfo("Done", msg)
        if errors:
            errfile = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files","*.txt")], title="Save error log?")
            if errfile:
                with open(errfile, "w", encoding="utf-8") as f:
                    for line in errors:
                        f.write(line + "\n")

if __name__ == "__main__":
    root = tk.Tk()
    app = FileFinderApp(root)
    root.minsize(800, 600)
    root.mainloop()
