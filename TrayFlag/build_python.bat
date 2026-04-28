rem "F:\Scripts\Python\TrayFlag\build_python.bat"

@echo off
chcp 65001 > nul

echo --- Building Python application (TrayFlag.exe) ---

echo Cleaning up old build folders...
if exist "TrayFlag" rmdir /s /q TrayFlag
if exist "build" rmdir /s /q build

echo.
echo Compiling with Nuitka...

rem --- УДАЛЕНА ПРОВЕРКА НА ip_lookup.exe ---

python -m nuitka ^
    --standalone ^
    --output-filename=TrayFlag.exe ^
    --output-dir=TrayFlag ^
    --remove-output ^
    --windows-console-mode=disable ^
    --enable-plugin=pyside6 ^
    --windows-icon-from-ico=assets/icons/logo.ico ^
    --include-data-dir=assets=assets ^
    --include-data-dir=getip=getip ^
    --include-package=soundfile,sounddevice,win32com,win32api,win32con,pycaw ^
    --include-data-file=updater.ps1=updater.ps1 ^
    src/main.py

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Nuitka compilation failed.
    pause
    exit /b 1
)

echo.
echo --- Python build successful! ---
echo The final application is in the 'TrayFlag' folder.
pause