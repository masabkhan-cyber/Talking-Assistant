@echo off
echo Installing Python package dependencies...
echo This may take a few minutes. 
echo.
echo Installing local project from setup.py...
python -m pip install .
python -m pip install -r requirements.txt
echo.
echo Installation complete! You can close this window.
pause