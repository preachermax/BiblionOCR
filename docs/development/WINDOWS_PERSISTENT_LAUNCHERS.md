# Windows Launchers That Preserve Tracebacks

Use this note when a Windows shortcut starts a Biblion module in a terminal, but the terminal disappears as soon as Python crashes.

## Problem

If a Windows shortcut points straight at Python, the console window usually closes as soon as the process exits. That means an exception traceback can vanish before you finish reading it.

## Recommended Standard

For each module:

1. Launch a small `.cmd` wrapper from the shortcut.
2. Let the wrapper change into the repo root.
3. Run the Python file.
4. Print the exit status.
5. Wait for Enter before closing.

This is the closest Windows equivalent to the Jetson `.desktop` plus shell-wrapper pattern.

## Canonical Wrapper Set

Standard Windows wrappers now exist in `launchers/` for these canonical runnable modules:

- `run-myboxer.cmd`
- `run-myexplorer.cmd`
- `run-myglypher.cmd`
- `run-mygrounder.cmd`
- `run-mylauncher.cmd`
- `run-mylexer.cmd`
- `run-mypixler.cmd`
- `run-myreader.cmd`
- `run-myresolver.cmd`
- `run-myscanner.cmd`
- `run-myserver.cmd`
- `run-mysliders.cmd`
- `run-mytrainer.cmd`
- `run-myversifier.cmd`
- `run-mywriter.cmd`

These correspond to the main `My*.py` entry points in `ViewController/0-MainUI`.
Generated `*UI.py` files and obvious backup variants such as `copy`, `Old`, and one-off experiment files are intentionally not wrapped.
`MyScannerWin.py` is also intentionally excluded from the repo-supported wrapper set because the module was removed from version control and should stay absent unless there is an explicit decision to restore it.

## MyServer Example

Canonical example file now included in this repo:

- `launchers/run-myserver.cmd`

Wrapper contents:

```cmd
@echo off
setlocal

cd /d "%~dp0.." || exit /b 1

if exist "C:\Program Files\Python311\python.exe" (
    "C:\Program Files\Python311\python.exe" "ViewController\0-MainUI\MyServer.py" %*
) else (
    py -3 "ViewController\0-MainUI\MyServer.py" %*
)

set "STATUS=%ERRORLEVEL%"
echo.
echo MyServer exited with status %STATUS%
set /p DUMMY=Press Enter to close: 
exit /b %STATUS%
```

## How To Create The Shortcut

Create a normal Windows shortcut whose target launches `cmd.exe` and tells it to run the wrapper.

Target:

```text
C:\Windows\System32\cmd.exe /k "C:\Users\Max\Projects\BiblionOCR\launchers\run-myserver.cmd"
```

Start in:

```text
C:\Users\Max\Projects\BiblionOCR
```

Notes:

- `/k` keeps the console open after the wrapper exits.
- The wrapper already pauses before exit, so `/k` is optional. If you prefer the wrapper to control everything, use `/c` instead.
- Point the shortcut to the wrapper, not directly to `python.exe`.

## Why This Works

- The shortcut launches `cmd.exe`, not Python directly.
- The wrapper stays in control after Python exits.
- The traceback remains visible until you press Enter.
- The same pattern works for both clean exits and crash exits.

## How To Replicate This For Other Modules

Use the same wrapper pattern and change only the Python file name and display name.

Examples:

- `MyExplorer.py` -> `run-myexplorer.cmd`
- `MyBoxer.py` -> `run-myboxer.cmd`
- `MyGrounder.py` -> `run-mygrounder.cmd`
- `MyPixler.py` -> `run-mypixler.cmd`

Template wrapper:

```cmd
@echo off
setlocal

cd /d "%~dp0.." || exit /b 1

if exist "C:\Program Files\Python311\python.exe" (
    "C:\Program Files\Python311\python.exe" "ViewController\0-MainUI\MODULE_FILE.py" %*
) else (
    py -3 "ViewController\0-MainUI\MODULE_FILE.py" %*
)

set "STATUS=%ERRORLEVEL%"
echo.
echo MODULE_FILE.py exited with status %STATUS%
set /p DUMMY=Press Enter to close: 
exit /b %STATUS%
```

Template shortcut target:

```text
C:\Windows\System32\cmd.exe /c "C:\Users\Max\Projects\BiblionOCR\launchers\WRAPPER_SCRIPT.cmd"
```

## Optional Logging Version

If you also want a log file for each run, use this wrapper body instead:

```cmd
@echo off
setlocal

cd /d "%~dp0.." || exit /b 1

set "LOG_DIR=%CD%\logs"
if not exist "%LOG_DIR%" mkdir "%LOG_DIR%"
set "LOG_FILE=%LOG_DIR%\myserver.log"

if exist "C:\Program Files\Python311\python.exe" (
    "C:\Program Files\Python311\python.exe" "ViewController\0-MainUI\MyServer.py" %* 1>>"%LOG_FILE%" 2>&1
) else (
    py -3 "ViewController\0-MainUI\MyServer.py" %* 1>>"%LOG_FILE%" 2>&1
)

set "STATUS=%ERRORLEVEL%"
type "%LOG_FILE%"
echo.
echo MyServer exited with status %STATUS%
echo Log saved to %LOG_FILE%
set /p DUMMY=Press Enter to close: 
exit /b %STATUS%
```

## Practical Rule

If a module is launched from a Windows shortcut and you care about the traceback, do not point the shortcut straight at Python.
Point it at a wrapper script that pauses before exit.

## PowerShell Alternative

You can do the same thing with a `.ps1` wrapper, but `.cmd` is usually simpler on Windows because it avoids PowerShell execution-policy friction for double-click launchers.