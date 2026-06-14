@echo off
setlocal
set "PROJECT_ROOT=%~dp0"
cd /d "%PROJECT_ROOT%"
powershell -NoProfile -ExecutionPolicy Bypass -File "%PROJECT_ROOT%scripts\stop_demo_one_click.ps1" -ProjectRoot "%PROJECT_ROOT%"
pause
