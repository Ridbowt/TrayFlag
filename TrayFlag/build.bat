@echo off
chcp 65001 > nul

echo [1/3] Cleaning up...
if exist "TrayFlag" rmdir /s /q TrayFlag
if exist "build" rmdir /s /q build

echo [2/3] Compiling Python executable with Nuitka...

rem Nuitka создаст папку 'TrayFlag\main.dist'
python -m nuitka --standalone --output-filename=TrayFlag.exe --output-dir=TrayFlag --remove-output --windows-console-mode=disable --enable-plugin=pyqt6 --windows-icon-from-ico=assets/icons/logo.ico --include-data-dir=assets=assets --include-package=soundfile,sounddevice,win32com,win32api,win32con,pycaw src/main.py

if %errorlevel% neq 0 (
    echo ERROR: Nuitka compilation failed.
    pause
    exit /b 1
)

echo [3/3] Compiling Go executable and moving it...
go build -ldflags="-s -w -H windowsgui" -o src\ip_lookup.exe src\ip_lookup.go

if %errorlevel% neq 0 (
    echo ERROR: Go compilation failed.
    pause
    exit /b 1
)

echo Moving ip_lookup.exe to the distribution folder...
rem Перемещаем Go-утилиту в папку .dist, созданную Nuitka
move /Y src\ip_lookup.exe TrayFlag\main.dist\ip_lookup.exe

if %errorlevel% neq 0 (
    echo ERROR: Failed to move ip_lookup.exe.
    pause
    exit /b 1
)

echo.
echo Build successful!
echo The result is in the 'TrayFlag\main.dist' folder.
pause