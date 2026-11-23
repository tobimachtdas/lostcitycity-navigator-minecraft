@echo off
cd /d "%~dp0"
call mvn -B clean package
if errorlevel 1 (echo BUILD FEHLGESCHLAGEN & pause & exit /b 1)
echo Fertig: target\LostCityNavigator-0.9.2.jar
pause
