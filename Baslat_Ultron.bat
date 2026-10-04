@echo off
echo ULTRON baslatiliyor...
taskkill /f /im pythonw.exe >nul 2>&1
taskkill /f /im python.exe >nul 2>&1
timeout /t 2 /nobreak >nul
start "" "D:\ultron\venv\Scripts\pythonw.exe" "D:\ultron\ultron_daemon.py" > "D:\ultron\daemon_out.log" 2> "D:\ultron\daemon_err.log"
echo ULTRON arka plan motoru baslatildi!
timeout /t 2 /nobreak >nul
