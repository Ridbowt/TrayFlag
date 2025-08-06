@echo off
chcp 65001 > nul

echo [1/3] Cleaning up...
if exist "TrayFlag" rmdir /s /q TrayFlag
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist

echo [2/3] Compiling Python executable with Nuitka...

python -m nuitka --standalone --output-filename=TrayFlag.exe --output-dir=TrayFlag --remove-output --windows-console-mode=disable --enable-plugin=pyqt6 --windows-icon-from-ico=assets/icons/logo.ico --include-data-dir=assets=assets --include-package=soundfile,sounddevice,win32com,win32api,win32con,pycaw src/main.py

if %errorlevel% neq 0 (
    echo ERROR: Nuitka compilation failed.
    pause
    exit /b 1
)

echo [3/3] Compiling Go executable (ip_lookup.exe) and moving it...
go build -ldflags="-H windowsgui" -o src\ip_lookup.exe src\ip_lookup.go

if %errorlevel% neq 0 (
    echo ERROR: Go compilation failed.
    pause
    exit /b 1
)

echo Moving ip_lookup.exe to the distribution folder...
move /Y src\ip_lookup.exe TrayFlag\ip_lookup.exe

if %errorlevel% neq 0 (
    echo ERROR: Failed to move ip_lookup.exe.
    pause
    exit /b 1
)

echo.
echo Build successful!
echo The result is in the 'TrayFlag' folder.
pause