@echo off
rem Creates the virtual environment in .venv and installs everything DIDR needs.
rem Usage: setup.bat        (then: .venv\Scripts\activate)
cd /d "%~dp0"
python -c "import sys; sys.exit(sys.version_info < (3, 11))" || (echo DIDR needs Python 3.11 or later. & exit /b 1)
python -m venv .venv || exit /b 1
.venv\Scripts\python -m pip install --upgrade pip --quiet
.venv\Scripts\python -m pip install -r requirements.txt --quiet || exit /b 1
.venv\Scripts\python -c "import nltk; nltk.download('wordnet', quiet=True)"
echo.
echo Done. Activate the environment with:  .venv\Scripts\activate
