@echo off
setlocal

REM Backward-compatible wrapper. Canonical script lives in Developer\.
call Developer\update_UI_Resources.cmd %*
exit /b %errorlevel%
