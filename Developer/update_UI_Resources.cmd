@echo off
setlocal

if exist "%~dp0..\.venv\Scripts\python.exe" (
  "%~dp0..\.venv\Scripts\python.exe" "%~dp0update_ui_resources.py" %*
) else (
  where py >nul 2>nul
  if errorlevel 1 (
    python "%~dp0update_ui_resources.py" %*
  ) else (
    py -3 "%~dp0update_ui_resources.py" %*
  )
)
set exit_code=%errorlevel%
endlocal & exit /b %exit_code%
