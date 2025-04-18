import os
import sys
import json
import time
import shutil
import threading
import queue
from pathlib import Path
from enum import Enum, auto
from typing import List, Dict, Optional, Union, Tuple

import tkinter as tk
from tkinter import ttk, filedialog, colorchooser, messagebox
from PIL import Image, ImageTk, ImageOps

class ProcessedFileOption(Enum):
    NONE = auto()
    DELETE = auto()
    MOVE = auto()

class Profile:
    def __init__(
        self,
        name: str,
        border_width: str,
        border_color: str = "#FFFFFF",
        quality: int = 90,
        resize_width: Optional[str] = None,
        resize_height: Optional[str] = None
    ):
        self.name = name
        self.border_width = border_width
        self.border_color = border_color
        self.quality = quality
        self.resize_width = resize_width
        self.resize_height = resize_height
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Profile':
        return cls(
            name=data["Name"],
            border_width=data["BorderWidth"],
            border_color=data.get("BorderColour", "#FFFFFF"),
            quality=data.get("Quality", 90),
            resize_width=data.get("ResizeWidth"),
            resize_height=data.get("ResizeHeight")
        )
    
    def to_dict(self) -> Dict:
        result = {
            "Name": self.name,
            "BorderWidth": self.border_width,
            "BorderColour": self.border_color,
            "Quality": self.quality
        }
        
        if self.resize_width:
            result["ResizeWidth"] = self.resize_width
        
        if self.resize_height:
            result["ResizeHeight"] = self.resize_height
            
        return result


class Settings:
    def __init__(
        self,
        input_directory: str,
        output_directory: str,
        processed_file_option: ProcessedFileOption = ProcessedFileOption.NONE,
        processed_directory: Optional[str] = None,
        recent_files: List[str] = None,
        max_recent_files: int = 10
    ):
        self.input_directory = input_directory
        self.output_directory = output_directory
        self.processed_file_option = processed_file_option
        self.processed_directory = processed_directory
        self.recent_files = recent_files or []
        self.max_recent_files = max_recent_files
    
    def add_recent_file(self, file_path: str) -> None:
        """Add a file to the recent files list."""
        if file_path in self.recent_files:
            # Move to the top if already exists
            self.recent_files.remove(file_path)
        
        # Add to the beginning of the list
        self.recent_files.insert(0, file_path)
        
        # Trim list if needed
        if len(self.recent_files) > self.max_recent_files:
            self.recent_files = self.recent_files[:self.max_recent_files]
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Settings':
        return cls(
            input_directory=data["InputDirectory"],
            output_directory=data["OutputDirectory"],
            processed_file_option=ProcessedFileOption[data.get("ProcessedFileOption", "NONE").upper()],
            processed_directory=data.get("ProcessedDirectory"),
            recent_files=data.get("RecentFiles", []),
            max_recent_files=data.get("MaxRecentFiles", 10)
        )
    
    def to_dict(self) -> Dict:
        result = {
            "InputDirectory": self.input_directory,
            "OutputDirectory": self.output_directory,
            "ProcessedFileOption": self.processed_file_option.name.capitalize(),
            "RecentFiles": self.recent_files,
            "MaxRecentFiles": self.max_recent_files
        }
        
        if self.processed_directory:
            result["ProcessedDirectory"] = self.processed_directory
            
        return result


class ImageProcessor:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.allowed_extensions = {'.jpg', '.jpeg', '.png', '.tif', '.tiff'}
    
    def process(self, input_path: str, profile: Profile) -> None:
        """Process a single image with a single profile."""
        try:
            # Check file extension
            ext = os.path.splitext(input_path)[1].lower()
            if ext not in self.allowed_extensions:
                raise ValueError(f"Unsupported image format: {ext}")
            
            # Open image
            with Image.open(input_path) as img:
                # Handle resize if specified
                resize_width = 0
                if profile.resize_width:
                    resize_input = profile.resize_width.strip().lower()
                    if resize_input.endswith('%'):
                        try:
                            percent = int(resize_input[:-1].strip())
                            resize_width = img.width * percent // 100
                        except ValueError:
                            resize_width = 0
                    else:
                        if resize_input.endswith("px"):
                            resize_input = resize_input[:-2].strip()
                        try:
                            resize_width = int(resize_input)
                        except ValueError:
                            resize_width = 0
                
                resize_height = 0
                if profile.resize_height:
                    resize_input = profile.resize_height.strip().lower()
                    if resize_input.endswith('%'):
                        try:
                            percent = int(resize_input[:-1].strip())
                            resize_height = img.height * percent // 100
                        except ValueError:
                            resize_height = 0
                    else:
                        if resize_input.endswith("px"):
                            resize_input = resize_input[:-2].strip()
                        try:
                            resize_height = int(resize_input)
                        except ValueError:
                            resize_height = 0
                
                # Apply resize if needed
                if resize_width > 0 or resize_height > 0:
                    # If one dimension is 0, maintain aspect ratio
                    if resize_width == 0:
                        resize_width = int(img.width * (resize_height / img.height))
                    elif resize_height == 0:
                        resize_height = int(img.height * (resize_width / img.width))
                    
                    img = img.resize((resize_width, resize_height), Image.LANCZOS)
                
                # Parse border width
                border_input = profile.border_width.strip().lower()
                border_width = 0
                
                if border_input.endswith('%'):
                    try:
                        percent = int(border_input[:-1].strip())
                        border_width = img.width * percent // 100
                    except ValueError:
                        border_width = 0
                else:
                    if border_input.endswith("px"):
                        border_input = border_input[:-2].strip()
                    try:
                        border_width = int(border_input)
                    except ValueError:
                        border_width = 0
                
                # Apply border
                if border_width > 0:
                    img = ImageOps.expand(img, border=border_width, fill=profile.border_color)
                
                # Create output directory if it doesn't exist
                output_folder = os.path.join(self.settings.output_directory, profile.name)
                os.makedirs(output_folder, exist_ok=True)
                
                # Save the processed image
                filename = os.path.splitext(os.path.basename(input_path))[0]
                output_path = os.path.join(output_folder, f"{filename}_{profile.name}{ext}")
                
                # Save with appropriate quality for JPEGs
                if ext.lower() in ['.jpg', '.jpeg']:
                    img.save(output_path, quality=profile.quality, optimize=True)
                else:
                    img.save(output_path)
                
                return output_path
                
        except Exception as e:
            print(f"Error processing {input_path}: {e}")
            return None
    
    def process_file(self, file_path: str, profiles: List[Profile]) -> List[str]:
        """Process a single file with all profiles."""
        results = []
        for profile in profiles:
            result = self.process(file_path, profile)
            if result:
                results.append(result)
        
        # Handle the original file according to settings
        if self.settings.processed_file_option == ProcessedFileOption.DELETE:
            os.remove(file_path)
        elif self.settings.processed_file_option == ProcessedFileOption.MOVE and self.settings.processed_directory:
            os.makedirs(self.settings.processed_directory, exist_ok=True)
            dest = os.path.join(self.settings.processed_directory, os.path.basename(file_path))
            shutil.move(file_path, dest)
        
        return results
    
    def process_batch(self, file_paths: List[str], profiles: List[Profile], callback=None) -> List[str]:
        """Process multiple files with all profiles."""
        all_results = []
        
        total = len(file_paths) * len(profiles)
        completed = 0
        
        # Process files in batches to optimize memory usage
        batch_size = 5  # Process 5 files at a time
        
        for i in range(0, len(file_paths), batch_size):
            batch = file_paths[i:i+batch_size]
            batch_results = []
            
            for file_path in batch:
                file_results = []
                for profile in profiles:
                    result = self.process(file_path, profile)
                    if result:
                        file_results.append(result)
                    
                    completed += 1
                    if callback:
                        callback(completed, total)
                
                batch_results.extend(file_results)
                
                # Handle the original file according to settings
                if self.settings.processed_file_option == ProcessedFileOption.DELETE:
                    os.remove(file_path)
                elif self.settings.processed_file_option == ProcessedFileOption.MOVE and self.settings.processed_directory:
                    os.makedirs(self.settings.processed_directory, exist_ok=True)
                    dest = os.path.join(self.settings.processed_directory, os.path.basename(file_path))
                    shutil.move(file_path, dest)
            
            all_results.extend(batch_results)
        
        return all_results


class BorderlyApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Borderly")
        self.root.geometry("900x700")
        
        # Set default values
        self.settings = Settings(
            input_directory=str(Path.home()),
            output_directory=str(Path.home() / "Borderly_Output"),
            processed_file_option=ProcessedFileOption.NONE
        )
        
        self.profiles = [
            Profile(
                name="WhiteBorder",
                border_width="50px",
                border_color="#FFFFFF",
                quality=90
            )
        ]
        
        self.current_profile_index = 0
        self.image_processor = ImageProcessor(self.settings)
        self.selected_files = []
        self.preview_image = None
        self.processing = False
        self.task_queue = queue.Queue()
        self.results = []
        
        # Create menu
        self._create_menu()
        
        # Create the main frame
        self.main_frame = ttk.Frame(root, padding=10)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Create tabs
        self.tab_control = ttk.Notebook(self.main_frame)
        self.tab_control.pack(fill=tk.BOTH, expand=True)
        
        # Main tab
        self.main_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.main_tab, text="Process Images")
        
        # Settings tab
        self.settings_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.settings_tab, text="Settings")
        
        # Profiles tab
        self.profiles_tab = ttk.Frame(self.tab_control)
        self.tab_control.add(self.profiles_tab, text="Profiles")
        
        # Setup each tab
        self._setup_main_tab()
        self._setup_settings_tab()
        self._setup_profiles_tab()
        
        # Load settings from file if exists
        self._try_load_settings()
    
    def _try_load_settings(self):
        try:
            if os.path.exists("borderly_settings.json"):
                with open("borderly_settings.json", "r") as f:
                    data = json.load(f)
                    
                    if "Settings" in data:
                        self.settings = Settings.from_dict(data["Settings"])
                    
                    if "Profiles" in data:
                        self.profiles = [Profile.from_dict(p) for p in data["Profiles"]]
                        
                # Update UI with loaded settings
                self._update_settings_ui()
                self._update_profiles_ui()
                
                # Update processor with new settings
                self.image_processor = ImageProcessor(self.settings)
        except Exception as e:
            messagebox.showerror("Error", f"Failed to load settings: {e}")
    
    def _save_settings(self):
        try:
            data = {
                "Settings": self.settings.to_dict(),
                "Profiles": [p.to_dict() for p in self.profiles]
            }
            
            with open("borderly_settings.json", "w") as f:
                json.dump(data, f, indent=2)
                
            messagebox.showinfo("Success", "Settings saved successfully")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save settings: {e}")
    
    def _setup_main_tab(self):
        # File selection frame
        file_frame = ttk.LabelFrame(self.main_tab, text="Select Images", padding=10)
        file_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Add buttons for file selection
        browse_btn = ttk.Button(file_frame, text="Select Files", command=self._browse_files)
        browse_btn.grid(row=0, column=0, padx=5, pady=5)
        
        # Add button for directory selection
        browse_dir_btn = ttk.Button(file_frame, text="Select Directory", command=self._browse_directory)
        browse_dir_btn.grid(row=0, column=1, padx=5, pady=5)
        
        clear_btn = ttk.Button(file_frame, text="Clear Selection", command=self._clear_selection)
        clear_btn.grid(row=0, column=2, padx=5, pady=5)
        
        # Selected files count
        self.files_label = ttk.Label(file_frame, text="No files selected")
        self.files_label.grid(row=0, column=3, padx=5, pady=5)
        
        # Preview frame
        preview_frame = ttk.LabelFrame(self.main_tab, text="Preview", padding=10)
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Canvas for preview
        self.preview_canvas = tk.Canvas(preview_frame, bg="light gray")
        self.preview_canvas.pack(fill=tk.BOTH, expand=True)
        
        # Set up canvas with a simple background
        self.preview_canvas.config(bg="#f0f0f0")
        
        # Add text when no image is selected
        self.preview_text = self.preview_canvas.create_text(
            200, 200, 
            text="Select an image using the buttons above\nto see a preview",
            fill="#666666", font=("Helvetica", 14)
        )
        
        # Control frame
        control_frame = ttk.Frame(self.main_tab, padding=10)
        control_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Profile selection
        ttk.Label(control_frame, text="Profile:").grid(row=0, column=0, padx=5, pady=5)
        
        self.profile_var = tk.StringVar()
        self.profile_dropdown = ttk.Combobox(control_frame, textvariable=self.profile_var)
        self.profile_dropdown.grid(row=0, column=1, padx=5, pady=5)
        self.profile_dropdown.bind("<<ComboboxSelected>>", self._update_preview)
        
        # Update profiles dropdown
        self._update_profile_dropdown()
        
        # Process with all profiles option
        self.use_all_profiles_var = tk.BooleanVar(value=False)
        use_all_profiles_check = ttk.Checkbutton(
            control_frame, 
            text="Process with all profiles", 
            variable=self.use_all_profiles_var
        )
        use_all_profiles_check.grid(row=0, column=2, padx=5, pady=5)
        
        # Process button
        self.process_btn = ttk.Button(control_frame, text="Process Images", command=self._process_images)
        self.process_btn.grid(row=0, column=3, padx=5, pady=5)
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(self.main_tab, variable=self.progress_var, maximum=100)
        self.progress_bar.pack(fill=tk.X, padx=15, pady=5)
        
        # Status label
        self.status_label = ttk.Label(self.main_tab, text="Ready")
        self.status_label.pack(padx=5, pady=5)
    
    def _setup_settings_tab(self):
        settings_frame = ttk.Frame(self.settings_tab, padding=10)
        settings_frame.pack(fill=tk.BOTH, expand=True)
        
        # Output directory
        ttk.Label(settings_frame, text="Output Directory:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.output_dir_var = tk.StringVar(value=self.settings.output_directory)
        output_entry = ttk.Entry(settings_frame, textvariable=self.output_dir_var, width=50)
        output_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        
        output_browse_btn = ttk.Button(settings_frame, text="Browse", command=self._browse_output_dir)
        output_browse_btn.grid(row=0, column=2, padx=5, pady=5)
        
        # Processed file option
        ttk.Label(settings_frame, text="After Processing:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        
        self.processed_option_var = tk.StringVar()
        options = {"Keep Original": "NONE", "Delete Original": "DELETE", "Move Original": "MOVE"}
        options_frame = ttk.Frame(settings_frame)
        options_frame.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        
        for i, (text, value) in enumerate(options.items()):
            rb = ttk.Radiobutton(
                options_frame, 
                text=text, 
                value=value, 
                variable=self.processed_option_var,
                command=self._option_changed
            )
            rb.grid(row=0, column=i, padx=5)
        
        # Set the initial value based on settings
        self.processed_option_var.set(self.settings.processed_file_option.name)
        
        # Processed directory (only visible when "Move" is selected)
        self.processed_dir_frame = ttk.Frame(settings_frame)
        self.processed_dir_frame.grid(row=2, column=0, columnspan=3, sticky=tk.W, padx=5, pady=5)
        
        ttk.Label(self.processed_dir_frame, text="Move to Directory:").grid(row=0, column=0, sticky=tk.W, padx=5)
        
        self.processed_dir_var = tk.StringVar()
        if self.settings.processed_directory:
            self.processed_dir_var.set(self.settings.processed_directory)
            
        processed_entry = ttk.Entry(self.processed_dir_frame, textvariable=self.processed_dir_var, width=50)
        processed_entry.grid(row=0, column=1, sticky=tk.W, padx=5)
        
        processed_browse_btn = ttk.Button(self.processed_dir_frame, text="Browse", command=self._browse_processed_dir)
        processed_browse_btn.grid(row=0, column=2, padx=5)
        
        # Update processed directory visibility
        self._update_processed_dir_visibility()
        
        # Save settings button
        save_btn = ttk.Button(settings_frame, text="Save Settings", command=self._save_ui_settings)
        save_btn.grid(row=3, column=1, pady=20)
    
    def _setup_profiles_tab(self):
        profiles_frame = ttk.Frame(self.profiles_tab, padding=10)
        profiles_frame.pack(fill=tk.BOTH, expand=True)
        
        # Profile list on the left
        list_frame = ttk.LabelFrame(profiles_frame, text="Profiles", padding=10)
        list_frame.grid(row=0, column=0, padx=5, pady=5, sticky=tk.NS)
        
        self.profile_listbox = tk.Listbox(list_frame, width=25, height=15)
        self.profile_listbox.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.profile_listbox.bind("<<ListboxSelect>>", self._select_profile)
        
        # Update profile list
        self._update_profile_list()
        
        # Buttons under the list
        btn_frame = ttk.Frame(list_frame)
        btn_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=5)
        
        add_btn = ttk.Button(btn_frame, text="Add", command=self._add_profile)
        add_btn.pack(side=tk.LEFT, padx=2)
        
        delete_btn = ttk.Button(btn_frame, text="Delete", command=self._delete_profile)
        delete_btn.pack(side=tk.RIGHT, padx=2)
        
        # Profile details on the right
        details_frame = ttk.LabelFrame(profiles_frame, text="Profile Details", padding=10)
        details_frame.grid(row=0, column=1, padx=5, pady=5, sticky=tk.NSEW)
        
        # Name
        ttk.Label(details_frame, text="Name:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.profile_name_var = tk.StringVar()
        name_entry = ttk.Entry(details_frame, textvariable=self.profile_name_var, width=30)
        name_entry.grid(row=0, column=1, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        # Border width
        ttk.Label(details_frame, text="Border Width:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.border_width_var = tk.StringVar()
        width_entry = ttk.Entry(details_frame, textvariable=self.border_width_var, width=10)
        width_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(details_frame, text="(e.g., 50px or 5%)").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        
        # Border color
        ttk.Label(details_frame, text="Border Color:").grid(row=2, column=0, sticky=tk.W, padx=5, pady=5)
        
        color_frame = ttk.Frame(details_frame)
        color_frame.grid(row=2, column=1, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        self.color_var = tk.StringVar(value="#FFFFFF")
        color_entry = ttk.Entry(color_frame, textvariable=self.color_var, width=10)
        color_entry.pack(side=tk.LEFT, padx=2)
        
        self.color_button = tk.Button(color_frame, width=3, bg=self.color_var.get(), command=self._pick_color)
        self.color_button.pack(side=tk.LEFT, padx=5)
        
        # Quality
        ttk.Label(details_frame, text="Quality:").grid(row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.quality_var = tk.IntVar(value=90)
        
        quality_frame = ttk.Frame(details_frame)
        quality_frame.grid(row=3, column=1, columnspan=2, sticky=tk.W, padx=5, pady=5)
        
        quality_slider = ttk.Scale(quality_frame, from_=1, to=100, orient=tk.HORIZONTAL, 
                                 variable=self.quality_var, length=200)
        quality_slider.pack(side=tk.LEFT)
        
        quality_label = ttk.Label(quality_frame, textvariable=self.quality_var)
        quality_label.pack(side=tk.LEFT, padx=5)
        
        # Resize options
        resize_frame = ttk.LabelFrame(details_frame, text="Resize (Optional)", padding=10)
        resize_frame.grid(row=4, column=0, columnspan=3, sticky=tk.EW, padx=5, pady=10)
        
        # Width
        ttk.Label(resize_frame, text="Width:").grid(row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.resize_width_var = tk.StringVar()
        width_entry = ttk.Entry(resize_frame, textvariable=self.resize_width_var, width=10)
        width_entry.grid(row=0, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(resize_frame, text="(e.g., 800px or 50%)").grid(row=0, column=2, sticky=tk.W, padx=5, pady=5)
        
        # Height
        ttk.Label(resize_frame, text="Height:").grid(row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.resize_height_var = tk.StringVar()
        height_entry = ttk.Entry(resize_frame, textvariable=self.resize_height_var, width=10)
        height_entry.grid(row=1, column=1, sticky=tk.W, padx=5, pady=5)
        ttk.Label(resize_frame, text="(e.g., 600px or 50%)").grid(row=1, column=2, sticky=tk.W, padx=5, pady=5)
        
        # Save button
        save_profile_btn = ttk.Button(details_frame, text="Save Profile", command=self._save_profile)
        save_profile_btn.grid(row=5, column=1, pady=10)
        
        # Make the profile details expand
        profiles_frame.columnconfigure(1, weight=1)
    
    def _create_menu(self):
        """Create the application menu."""
        self.menubar = tk.Menu(self.root)
        self.root.config(menu=self.menubar)
        
        # File menu
        file_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=file_menu)
        
        file_menu.add_command(label="Open Images...", command=self._browse_files)
        
        # Recent files submenu
        self.recent_menu = tk.Menu(file_menu, tearoff=0)
        file_menu.add_cascade(label="Recent Files", menu=self.recent_menu)
        
        # Update recent files menu
        self._update_recent_files_menu()
        
        file_menu.add_separator()
        file_menu.add_command(label="Save Settings", command=self._save_settings)
        file_menu.add_separator()
        file_menu.add_command(label="Exit", command=self.root.quit)
        
        # Help menu
        help_menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="Help", menu=help_menu)
        help_menu.add_command(label="About", command=self._show_about)
    
    def _update_recent_files_menu(self):
        """Update the recent files menu with current entries."""
        # Clear the menu
        self.recent_menu.delete(0, tk.END)
        
        if not self.settings.recent_files:
            self.recent_menu.add_command(label="(No recent files)", state=tk.DISABLED)
            return
        
        # Add recent files
        for file_path in self.settings.recent_files:
            if os.path.exists(file_path):
                # Use only the filename for display
                display_name = os.path.basename(file_path)
                self.recent_menu.add_command(
                    label=display_name,
                    command=lambda path=file_path: self._open_recent_file(path)
                )
        
        # Add clear option
        if self.settings.recent_files:
            self.recent_menu.add_separator()
            self.recent_menu.add_command(label="Clear Recent Files", command=self._clear_recent_files)
    
    def _open_recent_file(self, file_path):
        """Open a file from the recent files list."""
        if os.path.exists(file_path):
            self.selected_files = [file_path]
            self.files_label.config(text=f"{len(self.selected_files)} files selected")
            self._update_preview()
        else:
            # File doesn't exist anymore, remove from recent list
            self.settings.recent_files.remove(file_path)
            self._update_recent_files_menu()
            messagebox.showwarning("File Not Found", f"The file '{os.path.basename(file_path)}' could not be found.")
    
    def _clear_recent_files(self):
        """Clear the recent files list."""
        self.settings.recent_files = []
        self._update_recent_files_menu()
        self._save_settings()
    
    def _show_about(self):
        """Show the about dialog."""
        about_text = """Borderly

A Python application for adding borders to images.

Features:
- Add colored borders to images
- Multiple profiles for different border styles
- Batch processing
- Drag and drop support
- Resize images
"""
        messagebox.showinfo("About Borderly", about_text)
    
    def _browse_files(self):
        filetypes = [
            ("Image files", "*.jpg *.jpeg *.png *.tif *.tiff"),
            ("JPEG", "*.jpg *.jpeg"),
            ("PNG", "*.png"),
            ("TIFF", "*.tif *.tiff"),
            ("All files", "*.*")
        ]
        
        files = filedialog.askopenfilenames(
            title="Select images",
            filetypes=filetypes
        )
        
        if files:
            self.selected_files = list(files)
            self.files_label.config(text=f"{len(self.selected_files)} files selected")
            
            # Add to recent files
            for file_path in files:
                self.settings.add_recent_file(file_path)
            
            # Update the recent files menu
            self._update_recent_files_menu()
            
            # Update preview with first image
            if len(self.selected_files) > 0:
                self._update_preview()
    
    def _clear_selection(self):
        self.selected_files = []
        self.files_label.config(text="No files selected")
        
        # Clear preview
        self.preview_canvas.delete("all")
        self.preview_image = None
    
    def _update_preview(self, event=None):
        if not self.selected_files:
            return
        
        # Get the first selected file for preview
        file_path = self.selected_files[0]
        
        # Get the selected profile
        profile_name = self.profile_var.get()
        profile = next((p for p in self.profiles if p.name == profile_name), None)
        
        if not profile:
            self.preview_canvas.delete("all")
            self.preview_canvas.create_text(
                self.preview_canvas.winfo_width() // 2,
                self.preview_canvas.winfo_height() // 2,
                text="No profile selected",
                fill="black"
            )
            return
        
        try:
            # Create a temporary processor with preview settings
            temp_settings = Settings(
                input_directory="",
                output_directory=""
            )
            temp_processor = ImageProcessor(temp_settings)
            
            # Generate a temporary preview file
            temp_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "temp")
            os.makedirs(temp_dir, exist_ok=True)
            
            # Create a copy of the profile for preview
            preview_profile = Profile(
                name=profile.name,
                border_width=profile.border_width,
                border_color=profile.border_color,
                quality=profile.quality,
                resize_width=profile.resize_width,
                resize_height=profile.resize_height
            )
            
            # Process the image
            processed_path = temp_processor.process(file_path, preview_profile)
            
            if processed_path:
                # Load the processed image for preview
                img = Image.open(processed_path)
                
                # Scale the image to fit the canvas
                canvas_width = self.preview_canvas.winfo_width()
                canvas_height = self.preview_canvas.winfo_height()
                
                # Handle the case when the canvas hasn't been rendered yet
                if canvas_width <= 1:
                    canvas_width = 500
                if canvas_height <= 1:
                    canvas_height = 400
                
                # Calculate the scaling factor to fit the image in the canvas
                img_width, img_height = img.size
                scale = min(canvas_width / img_width, canvas_height / img_height)
                
                new_width = int(img_width * scale)
                new_height = int(img_height * scale)
                
                # Resize for display
                img = img.resize((new_width, new_height), Image.LANCZOS)
                
                # Convert to Tkinter PhotoImage
                photo = ImageTk.PhotoImage(img)
                
                # Update canvas
                self.preview_canvas.delete("all")
                self.preview_canvas.create_image(
                    canvas_width // 2,
                    canvas_height // 2,
                    image=photo
                )
                
                # Add a subtle border around the image to indicate it's the preview
                img_x1 = (canvas_width - new_width) // 2
                img_y1 = (canvas_height - new_height) // 2
                img_x2 = img_x1 + new_width
                img_y2 = img_y1 + new_height
                self.preview_canvas.create_rectangle(
                    img_x1 - 2, img_y1 - 2, img_x2 + 2, img_y2 + 2,
                    outline="#3498db", width=2, dash=None
                )
                
                # Keep a reference to prevent garbage collection
                self.preview_image = photo
                
                # Clean up temp files (optional)
                try:
                    os.remove(processed_path)
                except:
                    pass
        
        except Exception as e:
            self.preview_canvas.delete("all")
            self.preview_canvas.create_text(
                self.preview_canvas.winfo_width() // 2,
                self.preview_canvas.winfo_height() // 2,
                text=f"Error generating preview: {e}",
                fill="red"
            )
    
    def _process_images(self):
        if not self.selected_files:
            messagebox.showwarning("No files", "Please select images to process")
            return
        
        if not self.profiles:
            messagebox.showwarning("No profiles", "Please create at least one profile")
            return
        
        if self.processing:
            messagebox.showinfo("In progress", "Processing is already in progress")
            return
        
        # Update settings from UI
        self._save_ui_settings(silent=True)
        
        # Start processing in a separate thread
        self.processing = True
        self.progress_var.set(0)
        self.status_label.config(text="Processing...")
        self.process_btn.config(state=tk.DISABLED)
        
        # Clear existing results
        self.task_queue = queue.Queue()
        self.results = []
        
        # Check if we should use all profiles
        use_all_profiles = self.use_all_profiles_var.get()
        
        if use_all_profiles:
            # Use all profiles
            profiles_to_use = self.profiles
            total_tasks = len(self.selected_files) * len(profiles_to_use)
            
            for file_path in self.selected_files:
                for profile in profiles_to_use:
                    self.task_queue.put((file_path, profile))
        else:
            # Get the selected profile
            profile_name = self.profile_var.get()
            selected_profile = next((p for p in self.profiles if p.name == profile_name), None)
            
            if not selected_profile:
                messagebox.showerror("Error", "No profile selected")
                self.processing = False
                return
            
            # Prepare file-profile combinations with just the selected profile
            total_tasks = len(self.selected_files)
            for file_path in self.selected_files:
                self.task_queue.put((file_path, selected_profile))
        
        # Start worker threads
        num_workers = min(os.cpu_count() or 2, 4)  # Use up to 4 worker threads
        self.active_workers = num_workers
        
        def worker():
            while not self.task_queue.empty():
                try:
                    # Get task from queue
                    file_path, profile = self.task_queue.get(block=False)
                    
                    # Process image
                    result = self.image_processor.process(file_path, profile)
                    
                    # Handle result
                    if result:
                        with threading.Lock():
                            self.results.append(result)
                    
                    # Update progress
                    completed = total_tasks - self.task_queue.qsize()
                    self.root.after(0, lambda c=completed, t=total_tasks: self._update_progress(c, t))
                    
                    # Mark task as done
                    self.task_queue.task_done()
                except queue.Empty:
                    break
                except Exception as e:
                    print(f"Error in worker: {e}")
            
            # Report worker finished
            with threading.Lock():
                self.active_workers -= 1
                if self.active_workers == 0:
                    # All workers done, handle original files and complete
                    self._handle_originals()
                    self.root.after(0, lambda: self._processing_complete(self.results))
        
        # Start worker threads
        for _ in range(num_workers):
            threading.Thread(target=worker, daemon=True).start()
    
    def _update_progress(self, completed, total):
        """Update progress bar from main thread."""
        progress = (completed / total) * 100
        self.progress_var.set(progress)
        self.status_label.config(text=f"Processing: {completed}/{total} tasks completed")
        
    def _handle_originals(self):
        """Handle original files after processing (delete or move)."""
        # Create a set of processed files to avoid duplicates
        processed_files = set()
        
        for file_path in self.selected_files:
            if file_path in processed_files:
                continue
            
            processed_files.add(file_path)
            
            # Handle the original file according to settings
            try:
                if self.settings.processed_file_option == ProcessedFileOption.DELETE:
                    if os.path.exists(file_path):
                        os.remove(file_path)
                elif self.settings.processed_file_option == ProcessedFileOption.MOVE and self.settings.processed_directory:
                    if os.path.exists(file_path):
                        os.makedirs(self.settings.processed_directory, exist_ok=True)
                        dest = os.path.join(self.settings.processed_directory, os.path.basename(file_path))
                        shutil.move(file_path, dest)
            except Exception as e:
                print(f"Error handling original file {file_path}: {e}")
    
    def _processing_complete(self, results):
        self.processing = False
        self.progress_var.set(100)
        self.process_btn.config(state=tk.NORMAL)
        
        if results:
            self.status_label.config(text=f"Completed: {len(results)} files created")
            
            # Ask if user wants to open output folder
            if messagebox.askyesno("Complete", f"Processing complete. {len(results)} files created.\n\nOpen output folder?"):
                output_path = os.path.normpath(self.settings.output_directory)
                if sys.platform == 'win32':
                    os.startfile(output_path)
                elif sys.platform == 'darwin':  # macOS
                    os.system(f'open "{output_path}"')
                else:  # Linux
                    os.system(f'xdg-open "{output_path}"')
        else:
            self.status_label.config(text="Processing complete, but no files were created")
    
    def _processing_error(self, error_msg):
        self.processing = False
        self.process_btn.config(state=tk.NORMAL)
        self.status_label.config(text="Error during processing")
        messagebox.showerror("Processing Error", f"An error occurred:\n{error_msg}")
    
    def _browse_output_dir(self):
        directory = filedialog.askdirectory(title="Select Output Directory")
        if directory:
            self.output_dir_var.set(directory)
    
    def _browse_processed_dir(self):
        directory = filedialog.askdirectory(title="Select Directory for Processed Originals")
        if directory:
            self.processed_dir_var.set(directory)
    
    def _option_changed(self):
        self._update_processed_dir_visibility()
        
    def _browse_directory(self):
        """Browse for a directory and load all image files from it."""
        directory = filedialog.askdirectory(title="Select Directory with Images")
        if not directory:
            return
            
        # Find all image files in the directory
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.tif', '.tiff'}
        valid_files = []
        
        for file_name in os.listdir(directory):
            ext = os.path.splitext(file_name)[1].lower()
            if ext in allowed_extensions:
                file_path = os.path.join(directory, file_name)
                valid_files.append(file_path)
        
        if valid_files:
            self.selected_files = valid_files
            self.files_label.config(text=f"{len(self.selected_files)} files selected")
            
            # Add to recent files
            for file_path in valid_files:
                self.settings.add_recent_file(file_path)
            
            # Update the recent files menu
            self._update_recent_files_menu()
            
            # Update preview with first image
            if len(self.selected_files) > 0:
                self._update_preview()
        else:
            messagebox.showinfo("No Images", "No image files found in the selected directory.")
    
    def _update_processed_dir_visibility(self):
        if self.processed_option_var.get() == "MOVE":
            self.processed_dir_frame.grid()
        else:
            self.processed_dir_frame.grid_remove()
    
    def _save_ui_settings(self, silent=False):
        # Get values from UI
        output_dir = self.output_dir_var.get()
        processed_option = ProcessedFileOption[self.processed_option_var.get()]
        processed_dir = self.processed_dir_var.get() if processed_option == ProcessedFileOption.MOVE else None
        
        # Validate
        if not output_dir:
            if not silent:
                messagebox.showerror("Error", "Output directory is required")
            return False
        
        if processed_option == ProcessedFileOption.MOVE and not processed_dir:
            if not silent:
                messagebox.showerror("Error", "Process directory is required when 'Move' is selected")
            return False
        
        # Update settings
        self.settings.output_directory = output_dir
        self.settings.processed_file_option = processed_option
        self.settings.processed_directory = processed_dir
        
        # Update the processor
        self.image_processor = ImageProcessor(self.settings)
        
        # Save to file
        if not silent:
            self._save_settings()
        
        return True
    
    def _update_profile_list(self):
        self.profile_listbox.delete(0, tk.END)
        for profile in self.profiles:
            self.profile_listbox.insert(tk.END, profile.name)
        
        # Update dropdown too
        self._update_profile_dropdown()
    
    def _update_profile_dropdown(self):
        profile_names = [p.name for p in self.profiles]
        self.profile_dropdown['values'] = profile_names
        
        if profile_names:
            self.profile_dropdown.current(0)
    
    def _select_profile(self, event):
        # Get the index of the selected profile
        selection = self.profile_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        if index < 0 or index >= len(self.profiles):
            return
        
        # Update UI with selected profile
        profile = self.profiles[index]
        self.current_profile_index = index
        
        self.profile_name_var.set(profile.name)
        self.border_width_var.set(profile.border_width)
        self.color_var.set(profile.border_color)
        self.color_button.config(bg=profile.border_color)
        self.quality_var.set(profile.quality)
        self.resize_width_var.set(profile.resize_width or "")
        self.resize_height_var.set(profile.resize_height or "")
    
    def _add_profile(self):
        # Create a new profile
        new_name = f"Profile{len(self.profiles) + 1}"
        new_profile = Profile(
            name=new_name,
            border_width="50px",
            border_color="#FFFFFF",
            quality=90
        )
        
        self.profiles.append(new_profile)
        self._update_profile_list()
        
        # Select the new profile
        self.profile_listbox.selection_clear(0, tk.END)
        self.profile_listbox.selection_set(len(self.profiles) - 1)
        self._select_profile(None)
    
    def _delete_profile(self):
        # Get selected profile
        selection = self.profile_listbox.curselection()
        if not selection:
            return
        
        index = selection[0]
        if index < 0 or index >= len(self.profiles):
            return
        
        # Confirm deletion
        if messagebox.askyesno("Confirm", f"Delete profile '{self.profiles[index].name}'?"):
            del self.profiles[index]
            self._update_profile_list()
            
            # Select another profile if available
            if self.profiles:
                new_index = min(index, len(self.profiles) - 1)
                self.profile_listbox.selection_set(new_index)
                self._select_profile(None)
            else:
                # Clear UI if no profiles
                self.profile_name_var.set("")
                self.border_width_var.set("")
                self.color_var.set("#FFFFFF")
                self.color_button.config(bg="#FFFFFF")
                self.quality_var.set(90)
                self.resize_width_var.set("")
                self.resize_height_var.set("")
    
    def _save_profile(self):
        # Validate
        name = self.profile_name_var.get()
        border_width = self.border_width_var.get()
        color = self.color_var.get()
        quality = self.quality_var.get()
        resize_width = self.resize_width_var.get()
        resize_height = self.resize_height_var.get()
        
        if not name:
            messagebox.showerror("Error", "Profile name is required")
            return
        
        if not border_width:
            messagebox.showerror("Error", "Border width is required")
            return
        
        # Check for name conflicts
        if self.current_profile_index < 0 or self.current_profile_index >= len(self.profiles):
            # New profile
            if any(p.name == name for p in self.profiles):
                messagebox.showerror("Error", f"A profile with name '{name}' already exists")
                return
        else:
            # Existing profile being renamed
            current_name = self.profiles[self.current_profile_index].name
            if name != current_name and any(p.name == name for p in self.profiles):
                messagebox.showerror("Error", f"A profile with name '{name}' already exists")
                return
        
        # Update or create profile
        profile = Profile(
            name=name,
            border_width=border_width,
            border_color=color,
            quality=quality,
            resize_width=resize_width if resize_width else None,
            resize_height=resize_height if resize_height else None
        )
        
        if self.current_profile_index >= 0 and self.current_profile_index < len(self.profiles):
            # Update existing profile
            self.profiles[self.current_profile_index] = profile
        else:
            # Add new profile
            self.profiles.append(profile)
        
        self._update_profile_list()
        self._save_settings()  # Save to file
        
        # Update preview if profile being used
        if self.profile_var.get() == name:
            self._update_preview()
    
    def _pick_color(self):
        color = colorchooser.askcolor(initialcolor=self.color_var.get())[1]
        if color:
            self.color_var.set(color)
            self.color_button.config(bg=color)
    
    def _update_settings_ui(self):
        # Update settings tab UI with current settings
        self.output_dir_var.set(self.settings.output_directory)
        self.processed_option_var.set(self.settings.processed_file_option.name)
        
        if self.settings.processed_directory:
            self.processed_dir_var.set(self.settings.processed_directory)
        
        self._update_processed_dir_visibility()
    
    def _update_profiles_ui(self):
        # Update profiles list
        self._update_profile_list()
        
        # Select first profile if available
        if self.profiles:
            self.profile_listbox.selection_set(0)
            self._select_profile(None)


def main():
    root = tk.Tk()
    app = BorderlyApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()