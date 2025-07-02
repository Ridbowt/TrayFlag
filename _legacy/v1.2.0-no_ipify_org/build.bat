@echo off
chcp 65001 > nul

echo [1/2] Cleaning up...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build

echo [2/2] Compiling with Nuitka (single folder mode)...

rem Результат будет в dist\TrayFlag.dist
python -m nuitka --standalone --output-dir=dist --remove-output --windows-disable-console --enable-plugin=pyqt6 --windows-icon-from-ico=assets/icons/logo.ico --include-data-dir=assets=assets --include-package=soundfile,sounddevice,win32com src/TrayFlag.py

if %errorlevel% neq 0 (
    echo ERROR: Nuitka compilation failed.
    pause
    exit /b 1
)

echo.
echo Build successful!
echo The result is in the 'dist\TrayFlag.dist' folder.
pause