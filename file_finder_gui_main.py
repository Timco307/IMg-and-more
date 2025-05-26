import os
import shutil
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from collections import defaultdict
from datetime import datetime
import traceback

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

def format_size(size):
    for unit in ['bytes', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            break
        size /= 1024.0
    return f"{size:.2f} {unit}"

class FileFinderApp:
    def __init__(self, root, use_threading=False):
        self.root = root
        self.root.title("Super Easy File Finder")
        self.selected_folders = []
        self.folder_entries = []
        self.selected_folder_idx = tk.IntVar(value=0)
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
        self.is_running = False
        self.is_paused = False
        self.stop_flag = False
        # No threading at all
        self.executor = None
        self.use_threading = False
        self.build_gui()
        self.show_step(0)

    def pause_resume(self):
        # Dummy pause/resume for compatibility (no threading)
        messagebox.showinfo("Pause/Resume", "Pause/Resume is not available in this version.")

    def stop_operation(self):
        # Dummy stop for compatibility (no threading)
        self.stop_flag = True
        messagebox.showinfo("Stop", "Stop is not available in this version.")

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
        ttk.Label(step0, text="1. Choose drives or folders:").grid(row=0, column=0, sticky="w")
        self.folder_rows_frame = ttk.Frame(step0)
        self.folder_rows_frame.grid(row=1, column=0, columnspan=5, sticky="ew")
        # "+" button to add folder row
        ttk.Button(step0, text="+", width=2, command=self.add_folder_row).grid(row=2, column=1, sticky="w")
        # "-" button to remove selected folder row
        ttk.Button(step0, text="-", width=2, command=self.remove_selected_folder_row).grid(row=2, column=2, sticky="w")
        # Add quick access to Desktop/Documents/Drives
        quick_frame = ttk.Frame(step0)
        quick_frame.grid(row=3, column=0, columnspan=5, sticky="w", pady=(5,0))
        ttk.Button(quick_frame, text="Desktop", command=lambda: self.set_quick_folder("Desktop")).pack(side="left", padx=2)
        ttk.Button(quick_frame, text="Documents", command=lambda: self.set_quick_folder("Documents")).pack(side="left", padx=2)
        ttk.Button(quick_frame, text="C:\\", command=lambda: self.set_quick_folder("C:\\")).pack(side="left", padx=2)
        ttk.Button(quick_frame, text="D:\\", command=lambda: self.set_quick_folder("D:\\")).pack(side="left", padx=2)
        step0.columnconfigure(0, weight=1)
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
        # Add right-click menu
        self.result_list.bind("<Button-3>", self.show_context_menu)
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
        # Add keep all button
        self.dup_keep_all_btn = ttk.Button(step3, text="Keep All", command=self.keep_all_duplicates)
        self.dup_keep_all_btn.grid(row=1, column=1, sticky="w", pady=(5,0))
        # Add skip all duplicates button
        self.dup_skip_btn = ttk.Button(step3, text="Skip All Duplicates", command=self.skip_all_duplicates)
        self.dup_skip_btn.grid(row=1, column=0, sticky="w", pady=(5,0))
        step3.columnconfigure(1, weight=1)
        self.steps.append(step3)

        # Step 4: Copy options
        step4 = ttk.Frame(self.main_frame)
        ttk.Label(step4, text="4. Copy/Move found files to:").grid(row=0, column=0, sticky="w")
        ttk.Entry(step4, textvariable=self.dest_folder, width=40).grid(row=0, column=1, sticky="ew")
        ttk.Button(step4, text="Browse", command=self.browse_dest).grid(row=0, column=2)
        ttk.Checkbutton(step4, text="Keep folder structure", variable=self.keep_structure).grid(row=1, column=0, columnspan=2, sticky="w")
        # Add overwrite/skip/cancel options
        self.overwrite_mode = tk.StringVar(value="skip")
        ttk.Label(step4, text="If file exists:").grid(row=2, column=0, sticky="w")
        ttk.Radiobutton(step4, text="Skip", variable=self.overwrite_mode, value="skip").grid(row=2, column=1, sticky="w")
        ttk.Radiobutton(step4, text="Overwrite", variable=self.overwrite_mode, value="overwrite").grid(row=2, column=2, sticky="w")
        # Add auto-rename option
        ttk.Radiobutton(step4, text="Auto-rename (add (1), (2), ...)", variable=self.overwrite_mode, value="autorename").grid(row=2, column=3, sticky="w")
        # Add copy and move buttons
        self.copy_btn = ttk.Button(step4, text="Copy Files", command=lambda: self.start_copy_move(move=False))
        self.move_btn = ttk.Button(step4, text="Move Files", command=lambda: self.start_copy_move(move=True))
        self.copy_btn.grid(row=3, column=2, pady=10, sticky="e")
        self.move_btn.grid(row=3, column=3, pady=10, sticky="e")
        # Add pause/resume and stop buttons
        self.pause_resume_btn = ttk.Button(step4, text="Pause", command=self.pause_resume)
        self.stop_btn = ttk.Button(step4, text="Stop", command=self.stop_operation, state="disabled")
        self.pause_resume_btn.grid(row=3, column=0, pady=10, sticky="w")
        self.stop_btn.grid(row=3, column=1, pady=10, sticky="w")
        # Progress bar
        self.progress_bar = ttk.Progressbar(step4, orient="horizontal", length=300, mode="determinate")
        self.progress_bar.grid(row=4, column=0, columnspan=4, pady=10, sticky="ew")
        self.progress_label = ttk.Label(step4, text="")
        self.progress_label.grid(row=5, column=0, columnspan=4, sticky="w")
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

        # Fix geometry: use int() to avoid float error
        self.root.update_idletasks()
        width = int(max(self.root.winfo_screenwidth() // 1.2, 900))
        height = int(max(self.root.winfo_screenheight() // 1.5, 600))
        self.root.geometry(f"{width}x{height}")
        self.root.minsize(900, 600)
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)

    def on_close(self):
        # Clean up and close safely
        try:
            self.root.destroy()
        except Exception:
            sys.exit(0)

    def show_context_menu(self, event):
        selection = self.result_list.curselection()
        if not selection:
            return
        self.context_menu = tk.Menu(self.root, tearoff=0)
        self.context_menu.add_command(label="Delete from list", command=self.delete_from_list)
        self.context_menu.add_command(label="Delete from system", command=self.delete_from_system)
        self.context_menu.post(event.x_root, event.y_root)

    def delete_from_list(self):
        selection = self.result_list.curselection()
        if selection:
            files_to_delete = [self.result_list.get(i).split("  [")[0] for i in selection]
            for f in files_to_delete:
                self.files_found.remove(f)
            for i in reversed(selection):
                self.result_list.delete(i)
            self.update_progress()

    def delete_from_system(self):
        selection = self.result_list.curselection()
        if selection:
            files_to_delete = [self.result_list.get(i).split("  [")[0] for i in selection]
            if messagebox.askyesno("Delete Files", f"Are you sure you want to permanently delete {len(files_to_delete)} files from your system?"):
                errors = []
                for f in files_to_delete:
                    try:
                        os.remove(f)
                        self.files_found.remove(f)
                    except Exception as e:
                        errors.append(f"{f}: {e}")
                for i in reversed(selection):
                    self.result_list.delete(i)
                self.update_progress()
                if errors:
                    messagebox.showerror("Error", "\n".join(errors))

    def add_folder_row(self, path=""):
        idx = len(self.folder_entries)
        var = tk.StringVar(value=path)
        entry = ttk.Entry(self.folder_rows_frame, textvariable=var, width=40)
        entry.grid(row=idx, column=0, sticky="ew", pady=2)
        entry.bind("<Button-1>", lambda e, i=idx: self.browse_folder_row(i))
        browse_btn = ttk.Button(self.folder_rows_frame, text="Browse", command=lambda i=idx: self.browse_folder_row(i))
        browse_btn.grid(row=idx, column=1, padx=2)
        radio = ttk.Radiobutton(self.folder_rows_frame, variable=self.selected_folder_idx, value=idx)
        radio.grid(row=idx, column=2, padx=2)
        self.folder_entries.append((var, entry, browse_btn, radio))
        self.selected_folders.append(path)
        print(f"[DEBUG] Added folder row at index {idx} (path='{path}')")
        self.update_folder_rows()

    def remove_selected_folder_row(self):
        idx = self.selected_folder_idx.get()
        if 0 <= idx < len(self.folder_entries):
            print(f"[DEBUG] Removing folder row at index {idx} (path='{self.selected_folders[idx]}')")
            for widget in self.folder_entries[idx][1:]:
                widget.destroy()
            del self.folder_entries[idx]
            del self.selected_folders[idx]
            self.selected_folder_idx.set(0)
            self.update_folder_rows()

    def update_folder_rows(self):
        for i, (var, entry, browse_btn, radio) in enumerate(self.folder_entries):
            entry.grid(row=i, column=0, sticky="ew", pady=2)
            browse_btn.grid(row=i, column=1, padx=2)
            radio.grid(row=i, column=2, padx=2)
            self.selected_folders[i] = var.get()
            radio.config(value=i)

    def browse_folder_row(self, idx):
        folder = filedialog.askdirectory()
        if folder:
            self.folder_entries[idx][0].set(folder)
            self.selected_folders[idx] = folder
            print(f"[DEBUG] Browsed folder for row {idx}: {folder}")
            self.update_folder_rows()

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
        # Set to first empty row or add new row
        for i, (var, *_rest) in enumerate(self.folder_entries):
            if not var.get():
                var.set(path)
                self.selected_folders[i] = path
                self.update_folder_rows()
                return
        self.add_folder_row(path)

    def next_step(self):
        # Only keep non-empty folders
        self.selected_folders = [v[0].get() for v in self.folder_entries]
        if self.current_step == 0:
            if not self.selected_folders or not all(os.path.isdir(f) for f in self.selected_folders):
                messagebox.showerror("Error", "Please select at least one valid folder.")
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
        # Only keep non-empty folders
        self.selected_folders = [v[0].get() for v in self.folder_entries]
        if self.current_step == 0:
            if not self.selected_folders or not all(os.path.isdir(f) for f in self.selected_folders):
                messagebox.showerror("Error", "Please select at least one valid folder.")
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
        types = self.get_selected_types()
        self.progress.config(text="Searching...")
        self.root.update()
        found = []
        print(f"[DEBUG] Searching in folders: {self.selected_folders} for types: {types}")
        for folder in self.selected_folders:
            for rootdir, _, files in os.walk(folder):
                for f in files:
                    ext = os.path.splitext(f)[1].lower()
                    if ext in types:
                        full_path = os.path.join(rootdir, f)
                        found.append(full_path)
        print(f"[DEBUG] Found {len(found)} files")
        self.files_found = found
        self.total_size = sum(get_file_size(f) for f in found)
        self.result_list.delete(0, tk.END)
        for f in found:
            size = get_file_size(f)
            self.result_list.insert(tk.END, f"{f}  [{format_size(size)}]")
        self.update_progress()
        self.check_duplicates()
        if not found:
            messagebox.showinfo("No Files Found", "No files matching your criteria were found. Try a different folder or file type.")

    def update_progress(self):
        self.total_size = sum(get_file_size(f) for f in self.files_found)
        self.progress.config(text=f"Found {len(self.files_found)} files, total size: {format_size(self.total_size)}")

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

    def keep_all_duplicates(self):
        # Keep the first file in each duplicate group, remove others from self.files_found
        for group in self.duplicates:
            keep = group[0]
            for f in group[1:]:
                if f in self.files_found:
                    self.files_found.remove(f)
        self.duplicates = []
        self.update_duplicate_ui()

    def start_copy_move(self, move=False):
        if self.is_running:
            messagebox.showerror("Error", "An operation is already running.")
            return
        self.is_running = True
        self.is_paused = False
        self.stop_flag = False
        self.pause_resume_btn["text"] = "Pause"
        self.stop_btn["state"] = "normal"
        dest = self.dest_folder.get()
        if not dest or not os.path.isdir(dest):
            messagebox.showerror("Error", "Please select a valid destination folder.")
            self.reset_ui()
            return

        keep_struct = self.keep_structure.get()
        overwrite = self.overwrite_mode.get()
        selected = self.result_list.curselection()
        files_to_copy = [self.result_list.get(i).split("  [")[0] for i in selected] if selected else self.files_found
        if not files_to_copy:
            messagebox.showerror("Error", "No files selected to copy.")
            self.reset_ui()
            return

        total_files = len(files_to_copy)
        self.progress_bar["maximum"] = total_files
        self.copy_btn["state"] = "disabled"
        self.move_btn["state"] = "disabled"

        # No threading: just call directly
        self.copy_move_task(files_to_copy, dest, keep_struct, overwrite, move)

    def copy_move_task(self, files_to_copy, dest, keep_struct, overwrite, move):
        errors = []
        copied = 0
        # Find base folder for each file (for structure)
        base_folders = sorted(self.selected_folders, key=lambda x: -len(x))
        def get_base_folder(f):
            for b in base_folders:
                if f.startswith(b):
                    return b
            return base_folders[0] if base_folders else ""

        total_files = len(files_to_copy)
        print(f"[DEBUG] Copying {len(files_to_copy)} files to {dest} (overwrite mode: {overwrite}, move: {move})")
        for i, f in enumerate(files_to_copy):
            if self.stop_flag:
                print("[DEBUG] Operation stopped by user.")
                break

            while self.is_paused:
                self.root.update()
                import time
                time.sleep(0.1)  # Check every 100ms

            base_folder = get_base_folder(f)
            rel_path = os.path.relpath(f, base_folder) if keep_struct else os.path.basename(f)
            if keep_struct:
                last_folder = os.path.basename(base_folder)
                rel_path = os.path.join(last_folder, rel_path)
            else:
                rel_path = os.path.basename(f) # Only filename

            dest_path = os.path.join(dest, rel_path)
            try:
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)
            except Exception as e:
                errors.append(f"Error creating directory for {dest_path}: {e}")
                print(f"[DEBUG] Error creating directory: {e}")
                continue

            try:
                if os.path.exists(dest_path):
                    if overwrite == "skip":
                        print(f"[DEBUG] Skipping (exists): {dest_path}")
                        continue
                    elif overwrite == "overwrite":
                        if move:
                            shutil.move(f, dest_path)
                        else:
                            shutil.copy2(f, dest_path)
                        copied += 1
                        print(f"[DEBUG] Overwrote: {dest_path}")
                    elif overwrite == "autorename":
                        dest_path = self.get_autorename_path(dest_path)
                        if move:
                            shutil.move(f, dest_path)
                        else:
                            shutil.copy2(f, dest_path)
                        copied += 1
                        print(f"[DEBUG] Auto-renamed and copied: {dest_path}")
                    else:
                        continue
                else:
                    if move:
                        shutil.move(f, dest_path)
                    else:
                        shutil.copy2(f, dest_path)
                    copied += 1
                    print(f"[DEBUG] Copied: {dest_path}")
            except Exception as e:
                errors.append(f"{f}: {e}")
                print(f"[DEBUG] Error copying {dest_path}: {e}")
                print(traceback.format_exc()) # Print full traceback

            # Update progress bar and label (thread-safe)
            self.root.after(0, lambda: self.update_progress_bar(i + 1, total_files))
            if self.use_threading:
                self.root.update_idletasks()

        # After the loop, reset the UI (thread-safe)
        self.root.after(0, self.reset_ui)
        msg = f"Copied {copied} files."
        if errors:
            msg += f"\n{len(errors)} errors occurred."
        self.root.after(0, lambda: messagebox.showinfo("Done", msg))
        if errors:
            errfile = filedialog.asksaveasfilename(defaultextension=".txt", filetypes=[("Text files","*.txt")], title="Save error log?")
            if errfile:
                with open(errfile, "w", encoding="utf-8") as f:
                    for line in errors:
                        f.write(line + "\n")
        if move and not errors:
            self.root.after(0, self.find_files)

    def update_progress_bar(self, value, total):
        self.progress_bar["value"] = value
        self.progress_label.config(text=f"Processed: {value}/{total}")

    def get_autorename_path(self, path):
        base, ext = os.path.splitext(path)
        i = 1
        new_path = f"{base} ({i}){ext}"
        while os.path.exists(new_path):
            i += 1
            new_path = f"{base} ({i}){ext}"
        return new_path

    def reset_ui(self):
        self.is_running = False
        self.is_paused = False
        self.stop_flag = False
        self.copy_btn["state"] = "normal"
        self.move_btn["state"] = "normal"
        self.pause_resume_btn["text"] = "Pause"
        self.stop_btn["state"] = "disabled"

if __name__ == "__main__":
    try:
        root = tk.Tk()
    except Exception as e:
        print("Could not start GUI. Error:", e)
        print("This program requires a graphical environment to run.")
        input("Press Enter to exit...")
        sys.exit(1)

    try:
        app = FileFinderApp(root, use_threading=False)
        # Open maximized/fullscreen if possible, else fallback to geometry
        try:
            root.state('zoomed')  # Windows
        except Exception:
            try:
                root.attributes('-zoomed', True)  # Linux
            except Exception:
                pass  # Already set geometry above
        root.mainloop()
    except Exception as e:
        print("An error occurred while running the app:")
        traceback.print_exc()
        input("Press Enter to exit...")
        sys.exit(1)