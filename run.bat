@echo off
setlocal
cd /d "%~dp0"
title GenTrust AI
echo.
echo  ==========================================
echo    GenTrust AI - starting up
echo  ==========================================
echo.

set "PY="
python --version >nul 2>nul && set "PY=python"
if not defined PY ( py -3 --version >nul 2>nul && set "PY=py -3" )
if not defined PY (
  echo  Python was not found. Install Python 3.10+ from https://www.python.org/downloads/
  echo  and tick "Add Python to PATH" during setup, then run this file again.
  pause
  exit /b 1
)

if not exist "venv\Scripts\python.exe" (
  echo  Creating virtual environment ^(first run only^)...
  %PY% -m venv venv
  if errorlevel 1 ( echo  Could not create the virtual environment. & pause & exit /b 1 )
)

if not exist ".env" (
  copy ".env.example" ".env" >nul
  echo  Created a .env file. Opening it now: paste your Groq API key, save, then close Notepad.
  notepad ".env"
)

echo  Installing / checking dependencies...
"venv\Scripts\python.exe" -m pip install --disable-pip-version-check -q -r requirements.txt
if errorlevel 1 ( echo  Dependency installation failed. Check your internet connection. & pause & exit /b 1 )

echo.
echo  Launching GenTrust AI - your browser will open shortly.
echo  Close this window to stop the app.
echo.
"venv\Scripts\python.exe" -m streamlit run app.py
pause
