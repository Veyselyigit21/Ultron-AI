@echo off
cd /d "%~dp0"
set "LNK=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\ULTRON.lnk"
powershell -NoProfile -Command "$s=(New-Object -ComObject WScript.Shell).CreateShortcut('%LNK%'); $s.TargetPath='%~dp0venv\Scripts\pythonw.exe'; $s.Arguments='main_gui.py --hidden'; $s.WorkingDirectory='%~dp0'; $s.Save()"
echo ULTRON Windows ile birlikte arka planda baslayacak. Kaldirmak icin: %LNK%
pause
