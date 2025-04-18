#!/bin/bash

# Script for macOS/Unix with Homebrew instead of pip

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

# Install dependencies using Homebrew
echo "Installing dependencies using Homebrew..."
brew install pillow || true
brew install python-tk || true

# Run the application
echo "Starting Borderly GUI..."
python3 borderly_gui.py "$@" || {
    echo "Error running Borderly. Please check the error message above."
    echo "If you're having issues with tkinter, try installing it with: brew install python-tk"
    exit 1
}