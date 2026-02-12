@echo off
setlocal

cd /d %~dp0

where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python not found in PATH. Please install Python 3.10+ and check "Add Python to PATH".
  exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
  echo [INFO] Creating virtual environment .venv ...
  python -m venv .venv || exit /b 1
)

call ".venv\Scripts\activate.bat"

python -m pip install --upgrade pip
pip install -r requirements.txt || exit /b 1

echo [INFO] Starting Streamlit GUI at http://localhost:8501 ...
python -m streamlit run src\enzyme_miner\gui\app.py

endlocal
