@echo off
setlocal

cd /d "%~dp0.." || exit /b 1

if exist "C:\Program Files\Python311\python.exe" (
    "C:\Program Files\Python311\python.exe" "ViewController\2-TrainTesseract\MyReader.py" %*
) else (
    py -3 "ViewController\2-TrainTesseract\MyReader.py" %*
)

set "STATUS=%ERRORLEVEL%"
echo.
echo MyReader exited with status %STATUS%
set /p DUMMY=Press Enter to close: 
exit /b %STATUS%