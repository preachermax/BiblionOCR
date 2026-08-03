@echo off
setlocal

cd /d "%~dp0.." || exit /b 1

if exist "C:\Program Files\Python311\python.exe" (
    "C:\Program Files\Python311\python.exe" "ViewController\2-TrainTesseract\MyTrainer.py" %*
) else (
    py -3 "ViewController\2-TrainTesseract\MyTrainer.py" %*
)

set "STATUS=%ERRORLEVEL%"
echo.
echo MyTrainer exited with status %STATUS%
set /p DUMMY=Press Enter to close: 
exit /b %STATUS%