@echo off
echo ================================================
echo Testing GUI Installer (without building EXE)
echo ================================================
echo.
echo This will launch the installer GUI directly from Python.
echo Use this for testing before building the final EXE.
echo.
pause

call .venv\Scripts\activate
python installer_gui.py

pause
