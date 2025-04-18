#!/bin/bash
# Installation script for Borderly

echo "=== Borderly Installation Script ==="
echo "This script will set up Borderly with all necessary permissions and dependencies."

# Step 1: Make all scripts executable
echo "Setting executable permissions on scripts..."
chmod +x run.sh run_brew.sh run_macos.sh

# Step 2: Check for platform
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "macOS detected."
    echo "Do you want to install using Homebrew (recommended) or pip?"
    echo "1. Homebrew (recommended)"
    echo "2. pip with virtual environment"
    read -p "Enter choice [1-2]: " choice
    
    if [ "$choice" == "1" ]; then
        echo "Installing with Homebrew..."
        ./run_brew.sh
        echo "Installation complete! You can now run Borderly using ./run_brew.sh"
    else
        echo "Installing with pip..."
        ./run.sh
        echo "Installation complete! You can now run Borderly using ./run.sh"
    fi
else
    # For Linux or other Unix-like systems
    echo "Linux/Unix system detected."
    ./run.sh
    echo "Installation complete! You can now run Borderly using ./run.sh"
fi

echo "Borderly has been installed successfully!"
echo "Enjoy using Borderly!"