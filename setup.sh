#!/bin/bash

echo "Setting up ITS Example Templates project..."

# Check if virtual environment already exists
if [ ! -f "venv/bin/activate" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment"
        echo "Make sure Python 3 is installed"
        exit 1
    fi
    echo "Virtual environment created successfully"
else
    echo "Virtual environment already exists, skipping creation"
fi

echo "Activating virtual environment..."
source venv/bin/activate
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to activate virtual environment"
    exit 1
fi

echo "Installing project dependencies..."
pip install -e .
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi

echo
echo "====================================================="
echo "Setup complete!"
echo
echo "To use the project:"
echo "  1. Activate environment: source venv/bin/activate"
echo "  2. Run compiler: python compile_all_templates.py"
echo "====================================================="