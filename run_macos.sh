#!/bin/bash

# Script for macOS with enhanced drag and drop handling using Homebrew

# Check if Homebrew is installed
if ! command -v brew &> /dev/null; then
    echo "Homebrew is not installed. Installing Homebrew..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
fi

# Install Python if not already installed
if ! command -v python3 &> /dev/null; then
    echo "Installing Python using Homebrew..."
    brew install python
fi

# Install Pillow using Homebrew
echo "Installing dependencies using Homebrew..."
brew install pillow || true

# Install Tkinter (should already be included with Python)
# For newer Python versions, we might need to install it separately
brew install python-tk || true

# Create AppleScript handler for enhanced drag and drop
SCRIPT_DIR="$HOME/Library/Application Scripts/Borderly"
mkdir -p "$SCRIPT_DIR"

cat > "$SCRIPT_DIR/open_with_borderly.scpt" << EOF
on open theFiles
    set filePaths to ""
    repeat with aFile in theFiles
        set filePaths to filePaths & (POSIX path of aFile) & " "
    end repeat
    
    -- Find the script directory
    set scriptPath to path to me
    set scriptFolder to container of scriptPath as text
    
    -- Run the application with the files
    do shell script "cd " & quoted form of POSIX path of scriptFolder & " && ./run.sh " & filePaths
end open
EOF

# Make the script executable
chmod +x "$SCRIPT_DIR/open_with_borderly.scpt"

# Run the application
echo "Starting Borderly GUI..."
python3 borderly_gui.py "$@" || {
    echo "Error running Borderly. Please check the error message above."
    echo "If you're having issues with tkinter, try installing it with: brew install python-tk"
    exit 1
}