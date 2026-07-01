# Jetson Desktop Launchers That Preserve Tracebacks

Use this note when a desktop launcher starts a Biblion module in a terminal, but the terminal disappears as soon as Python crashes.

For interactive terminal commands in this note, assume the shell already opens in your home directory, so `cd Projects/BiblionOCR` is sufficient.
Absolute paths are still used in `.desktop` entries and wrapper-script locations because those should not depend on the caller's starting directory.

## Problem

The current launcher pattern runs Python directly from the desktop entry:

```ini
Exec=/usr/bin/python3 /home/jetson/Projects/BiblionOCR/ViewController/0-MainUI/MyExplorer.py %f
Terminal=true
```

That opens a terminal, but the terminal is still tied to the Python process. If the app exits on an exception, the terminal window can close before you finish reading the traceback.

## Recommended Standard

For each module:

1. Launch a small shell wrapper script from the `.desktop` file.
2. Let the wrapper run the Python file.
3. Print the exit status.
4. Wait for Enter before closing.

This is the cleanest pattern to standardize across all Biblion modules.

## MyServer Example

Canonical example files are now included in this repo:

- `launchers/run-myserver.sh`
- `My Server.desktop`

Create this wrapper script on the Jetson:

Path:

```text
/home/jetson/Projects/BiblionOCR/launchers/run-myserver.sh
```

Contents:

```bash
#!/usr/bin/env bash

cd /home/jetson/Projects/BiblionOCR || exit 1

/usr/bin/python3 ViewController/0-MainUI/MyServer.py "$@"
status=$?

echo
echo "MyServer exited with status $status"
echo "Press Enter to close"
read -r

exit $status
```

Make it executable:

```bash
chmod +x /home/jetson/Projects/BiblionOCR/launchers/run-myserver.sh
```

Then use this desktop entry for MyServer:

```ini
[Desktop Entry]
Type=Application
Name=My Server
Comment=Launch My Server
Version=1.0
Exec=/home/jetson/Projects/BiblionOCR/launchers/run-myserver.sh %f
TryExec=/home/jetson/Projects/BiblionOCR/launchers/run-myserver.sh
Icon=/home/jetson/Projects/BiblionOCR/ViewController/0-MainUI/Icons/BiblionBoxer2.png
Path=/home/jetson/Projects/BiblionOCR
Terminal=true
Categories=Utility;
Name[en_US]=My Server
```

## Why This Works

- The `.desktop` file launches a shell script instead of Python directly.
- The shell script stays alive after Python exits.
- The traceback remains visible until you press Enter.
- The same pattern works for normal exits and crash exits.

## How To Replicate This For Other Modules

Use the same wrapper pattern and change only the Python file name and display name.

Examples:

- `MyExplorer.py` -> `run-myexplorer.sh`
- `MyBoxer.py` -> `run-myboxer.sh`
- `MyGrounder.py` -> `run-mygrounder.sh`
- `MyPixler.py` -> `run-mypixler.sh`

Template wrapper:

```bash
#!/usr/bin/env bash

cd /home/jetson/Projects/BiblionOCR || exit 1

/usr/bin/python3 ViewController/0-MainUI/MODULE_FILE.py "$@"
status=$?

echo
echo "MODULE_FILE.py exited with status $status"
echo "Press Enter to close"
read -r

exit $status
```

Template desktop entry:

```ini
[Desktop Entry]
Type=Application
Name=MODULE NAME
Comment=Launch MODULE NAME
Version=1.0
Exec=/home/jetson/Projects/BiblionOCR/launchers/WRAPPER_SCRIPT.sh %f
TryExec=/home/jetson/Projects/BiblionOCR/launchers/WRAPPER_SCRIPT.sh
Icon=/home/jetson/Projects/BiblionOCR/ViewController/0-MainUI/Icons/BiblionBoxer2.png
Path=/home/jetson/Projects/BiblionOCR
Terminal=true
Categories=Utility;
Name[en_US]=MODULE NAME
```

## Optional Logging Version

If you also want a log file for each run, use this wrapper body instead:

```bash
#!/usr/bin/env bash

cd /home/jetson/Projects/BiblionOCR || exit 1

log_dir=/home/jetson/Projects/BiblionOCR/logs
mkdir -p "$log_dir"
log_file="$log_dir/myserver.log"

/usr/bin/python3 ViewController/0-MainUI/MyServer.py "$@" 2>&1 | tee "$log_file"
status=${PIPESTATUS[0]}

echo
echo "MyServer exited with status $status"
echo "Log saved to $log_file"
echo "Press Enter to close"
read -r

exit $status
```

## Practical Rule

If a module is launched from the desktop and you care about the traceback, do not point the `.desktop` file straight at Python.
Point it at a wrapper script that pauses before exit.