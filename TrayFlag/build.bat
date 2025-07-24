@echo off
chcp 65001 > nul

echo [1/3] Cleaning up...
if exist "dist" rmdir /s /q dist
if exist "build" rmdir /s /q build

echo [2/3] Compiling Python executable with Nuitka...

rem Результат будет в dist\TrayFlag.dist
python -m nuitka --standalone --output-dir=dist --remove-output --windows-disable-console --enable-plugin=pyqt6 --windows-icon-from-ico=assets/icons/logo.ico --include-data-dir=assets=assets --include-package=soundfile,sounddevice,win32com src/TrayFlag.py

if %errorlevel% neq 0 (
    echo ERROR: Nuitka compilation failed.
    pause
    exit /b 1
)

echo [3/3] Compiling Go executable (ip_lookup.exe) and moving it...
rem Исходный файл Go находится в src/ip_lookup.go
rem Компилируем Go-файл как GUI-приложение, чтобы не появлялась консоль
go build -ldflags="-H windowsgui" -o src\ip_lookup.exe src\ip_lookup.go

if %errorlevel% neq 0 (
    echo ERROR: Go compilation failed.
    pause
    exit /b 1
)

echo Moving ip_lookup.exe to the distribution folder...
move /Y src\ip_lookup.exe dist\TrayFlag.dist\ip_lookup.exe

if %errorlevel% neq 0 (
    echo ERROR: Failed to move ip_lookup.exe.
    pause
    exit /b 1
)

echo.
echo Build successful!
echo The result is in the 'dist\TrayFlag.dist' folder.
pause
