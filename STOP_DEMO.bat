@echo off
setlocal
for %%I in ("%~dp0.") do set "PROJECT_ROOT=%%~fI"
cd /d "%PROJECT_ROOT%"
powershell -NoProfile -ExecutionPolicy Bypass -File "%PROJECT_ROOT%\scripts\stop_demo_one_click.ps1" -ProjectRoot "%PROJECT_ROOT%"
pause
