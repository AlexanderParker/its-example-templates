#!/bin/bash
echo "Setting up ITS Example Templates project..."
python -m venv venv
source venv/bin/activate
pip install -e .
echo "Setup complete! Run: source venv/bin/activate"