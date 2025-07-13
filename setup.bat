@echo off
echo Setting up ITS Example Templates project...
python -m venv venv
call venv\Scripts\activate
pip install -e .
echo Setup complete! Run: venv\Scripts\activate