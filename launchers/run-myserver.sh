#!/usr/bin/env bash

cd /home/jetson/Projects/BiblionOCR || exit 1

/usr/bin/python3 ViewController/0-MainUI/MyServer.py "$@"
status=$?

echo
echo "MyServer exited with status $status"
echo "Press Enter to close"
read -r

exit $status