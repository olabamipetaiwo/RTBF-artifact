@echo off
rem Kick-the-tires check: no accounts, no browser, about one minute.
rem Runs the tests, then the offline stages on the example files in a temporary
rem folder, so nothing in data\ or results\ is touched.
rem Usage: scripts\quick_check.bat   (after setup.bat)
cd /d "%~dp0\.."
if not exist .venv\Scripts\python.exe (echo Run setup.bat first. & exit /b 1)
set "TMPDIR=%TEMP%\didr_quick_check_%RANDOM%"
mkdir "%TMPDIR%"
set "DIDR_WORKBOOK=%TMPDIR%\test_cases.xlsx"
set "DIDR_STATE_DIR=%TMPDIR%\state"
set "DIDR_RESULTS_DIR=%TMPDIR%\results"
echo == 1/2 Tests
.venv\Scripts\python -m pytest tests -q -p no:cacheprovider || exit /b 1
echo.
echo == 2/2 Offline stages on examples\design.csv
.venv\Scripts\python scripts\pipeline.py init --design examples\design.csv || exit /b 1
.venv\Scripts\python scripts\pipeline.py generate || exit /b 1
.venv\Scripts\python scripts\pipeline.py sample-requests --requests examples\example_requests.csv --target 10 --floor 2 || exit /b 1
.venv\Scripts\python scripts\pipeline.py status || exit /b 1
rmdir /s /q "%TMPDIR%"
echo.
echo Quick check passed.
