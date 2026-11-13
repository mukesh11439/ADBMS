@echo off
cd /d "%~dp0"
set DB_TYPE=sqlite

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m streamlit run app.py
) else (
    python -m streamlit run app.py
)

if errorlevel 1 (
    echo.
    echo App could not start. Make sure Python and project dependencies are installed.
    pause
)
