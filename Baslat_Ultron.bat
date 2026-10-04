@echo off
cd /d "%~dp0"
if not exist venv\Scripts\pythonw.exe ( echo Once Kur.bat calistir. & pause & exit /b 1 )
REM Tek ornek korumasi uygulama icinde; baska python islemlerini oldurmez.
start "" venv\Scripts\pythonw.exe main_gui.py --hidden
