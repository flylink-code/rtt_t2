@echo off
setlocal

set "ROOT_DIR=%~dp0.."
set "PYINSTALLER=%ROOT_DIR%\.venv\Scripts\pyinstaller.exe"
set "PYTHON=%ROOT_DIR%\.venv\Scripts\python.exe"

if not exist "%PYTHON%" (
    echo [ERROR] Virtual environment not found. Run:
    echo   python -m venv .venv
    echo   .venv\Scripts\pip install -r requirements.txt -r requirements-dev.txt
    exit /b 1
)

if not exist "%PYINSTALLER%" (
    echo [INFO] Installing pyinstaller into .venv ...
    "%ROOT_DIR%\.venv\Scripts\pip.exe" install -r "%ROOT_DIR%\requirements-dev.txt"
)

set PYQTGRAPH_QT_LIB=PySide6
echo Starting to package the application...
"%PYINSTALLER%" "%ROOT_DIR%\rtt_t2.spec" --noconfirm
if errorlevel 1 (
    echo Packaging failed.
    exit /b 1
)

echo Packaging complete: %ROOT_DIR%\dist\rtt_t2\
endlocal
