@echo off
echo Building to exe
pyinstaller gui.py --hidden-import autoit --hidden-import selenium --name pywsp --icon icon.ico
echo Finished.
pause