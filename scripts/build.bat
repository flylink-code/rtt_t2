@echo off
setlocal

set "ROOT_DIR=%~dp0.."

echo Starting to package the application...
pyinstaller "%ROOT_DIR%\rtt_t2.spec"
echo Packaging complete!
pause

endlocal
