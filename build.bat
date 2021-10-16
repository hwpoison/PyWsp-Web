@echo off
echo Building to exe
pyinstaller gui.py --hidden-import autoit --hidden-import selenium --name pywsp
echo Finished.
pause