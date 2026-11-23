@echo off
cd /d "%~dp0"
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0build_windows.ps1" %*
if errorlevel 1 echo Build fehlgeschlagen. Bitte BUILD_ANLEITUNG.md lesen.
pause
