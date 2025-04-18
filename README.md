# Borderly GUI

A Python reimplementation of the Borderly image processing application with a graphical user interface that allows drag-and-drop functionality and interactive controls.

## Features

- User-friendly interface for image processing
- Drag-and-drop functionality for easy image processing
- Interactive controls with sliders and color pickers
- Live preview of image processing results
- Multiple profile support for different border and resize settings
- Options for handling original files (keep, delete, or move)
- Progress tracking for batch processing
- Settings persistence between sessions
- Recent files menu for quick access to previously processed images
- Multithreaded processing for improved performance

## Requirements

- Python 3.7+
- Pillow (Python Imaging Library)
- Tkinter (usually comes with Python)

## Installation

### Quick Install (Recommended)

Use our automated installation script for a simple setup:

1. Clone or download this repository
2. Make the installation script executable:
   ```bash
   chmod +x install.sh
   ```
3. Run the installation script:
   ```bash
   ./install.sh
   ```
   This will:
   - Set proper permissions on all scripts
   - Detect your OS (macOS, Linux, etc.)
   - Let you choose installation method on macOS (Homebrew or pip)
   - Install all dependencies and run the application

### Manual Installation Options

#### Option 1: Using pip (cross-platform)

1. Clone or download this repository
2. Make the script executable:
   ```bash
   chmod +x run.sh
   ```
3. Run the script to install dependencies and start the app:
   ```bash
   ./run.sh
   ```

#### Option 2: Using Homebrew (macOS only)

1. Clone or download this repository
2. Make the script executable:
   ```bash
   chmod +x run_brew.sh
   ```
3. Run the Homebrew installation script:
   ```bash
   ./run_brew.sh
   ```
   This will automatically:
   - Install Homebrew if not already installed
   - Install Python using Homebrew if needed
   - Install Pillow and Tkinter using Homebrew
   - Run the application

## Usage

Run the application using the provided scripts:

On macOS:
```bash
# First make scripts executable
chmod +x run.sh run_brew.sh run_macos.sh

# Using pip with virtual environment
./run.sh

# Using Homebrew (recommended)
./run_brew.sh

# For enhanced drag-and-drop support with Homebrew
./run_macos.sh
```

On Windows:
```bash
run.bat
```

You can also run the application directly:
```bash
python borderly_gui.py
```

### Drag and Drop

You can drag and drop image files directly onto the application:

1. Start the application
2. Select files from your file explorer/finder
3. Drag them onto the application window's canvas area
4. Files will be automatically loaded for processing

### Main Features

1. **Processing Images**
   - Select files using the "Select Files" button
   - Choose a profile from the dropdown
   - See a live preview of how the selected profile will affect the image
   - Click "Process Images" to apply the selected profile to all images
   - Progress bar will show processing status

2. **Configure Settings**
   - Set the output directory for processed images
   - Choose what to do with original files:
     - Keep in the original location
     - Delete after processing
     - Move to a specified directory

3. **Manage Profiles**
   - Create multiple profiles with different settings
   - Each profile can specify:
     - Border width (fixed pixels or percentage)
     - Border color (with color picker)
     - Output quality (for JPEG images)
     - Optional resizing (width/height in pixels or percentage)
   - Preview results before processing

## Profiles

Each profile defines how images will be processed:

- **Name**: Used to identify the profile and as a subfolder name
- **Border Width**: Thickness in pixels or as a percentage (e.g., "50px" or "5%")
- **Border Color**: Color for the border (with visual color picker)
- **Quality**: JPEG quality setting (1-100)
- **Resize Width/Height**: Optional resizing of images before adding borders

## Comparison to the Original C# Version

This Python GUI implementation provides the same core functionality as the original C# version but adds:

1. Graphical user interface for easier interaction
2. Drag-and-drop support for images
3. Live preview of processing results
4. Interactive sliders for quality settings
5. Visual color picker for border colors
6. Progress tracking during batch processing
7. Multithreaded processing for better performance