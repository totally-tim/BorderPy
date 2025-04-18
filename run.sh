#!/bin/bash

# Create a virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate the virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run the application
echo "Starting Borderly GUI..."
python borderly_gui.py || {
    echo "Error running Borderly. Please check the error message above."
    echo "If using a virtual environment, make sure all dependencies are properly installed."
    echo "Try running: pip install -r requirements.txt"
    # Deactivate even if there was an error
    deactivate
    exit 1
}

# Deactivate the virtual environment when done
deactivate
