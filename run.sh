#!/usr/bin/env bash
cd "$(dirname "$0")" || exit 1

echo
echo " =========================================="
echo "   GenTrust AI - starting up"
echo " =========================================="
echo

PY=$(command -v python3 || command -v python)
if [ -z "$PY" ]; then
  echo " Python 3.10+ was not found. Install it from https://www.python.org/downloads/"
  exit 1
fi

if [ ! -d venv ]; then
  echo " Creating virtual environment (first run only)..."
  "$PY" -m venv venv || { echo " Could not create the virtual environment."; exit 1; }
fi

if [ ! -f .env ]; then
  cp .env.example .env
  echo " Created a .env file. Open it, paste your Groq API key, save, then re-run this script."
  echo " (Or paste the key into the app's sidebar.)"
fi

echo " Installing / checking dependencies..."
venv/bin/python -m pip install --disable-pip-version-check -q -r requirements.txt || exit 1

echo
echo " Launching GenTrust AI at http://localhost:8501"
venv/bin/python -m streamlit run app.py
