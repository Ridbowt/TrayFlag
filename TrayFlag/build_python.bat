@echo off
chcp 65001 > nul

echo --- Building Python application (TrayFlag.exe) ---

echo Cleaning up old build folders...
if exist "TrayFlag" rmdir /s /q TrayFlag
if exist "build" rmdir /s /q build

echo.
echo Compiling with Nuitka...

rem Проверяем, что ip_lookup.exe на месте
if not exist "src\ip_lookup.exe" (
    echo.
    echo ERROR: ip_lookup.exe not found in 'src' folder.
    echo Please run build_rust.bat first to compile it.
    pause
    exit /b 1
)

python -m nuitka --standalone --output-filename=TrayFlag.exe --output-dir=TrayFlag --remove-output --windows-console-mode=disable --enable-plugin=pyside6 --windows-icon-from-ico=assets/icons/logo.ico --include-data-dir=assets=assets --include-package=soundfile,sounddevice,win32com,win32api,win32con,pycaw --include-data-file=src/ip_lookup.exe=ip_lookup.exe src/main.py

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