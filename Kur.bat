@echo off
chcp 65001 >nul
cd /d "%~dp0"
echo === ULTRON kurulum ===
where python >nul 2>&1 || (echo Python bulunamadi. https://python.org adresinden 3.10+ kur. & pause & exit /b 1)
if not exist venv python -m venv venv
call venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt || (echo Paket kurulumu basarisiz. & pause & exit /b 1)
if not exist .env copy .env.example .env >nul
python tools\setup_models.py
echo.
echo Kurulum bitti. .env dosyasina OPENROUTER_API_KEY yaz (online mod icin), sonra Baslat_Ultron.bat calistir.
pause
