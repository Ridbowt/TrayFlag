rem "F:\Scripts\Python\TrayFlag\build_python.bat"

@echo off
chcp 65001 > nul

echo --- Building Python application (TrayFlag.exe) ---

echo Cleaning up old build folders...
if exist "TrayFlag" rmdir /s /q TrayFlag
if exist "build" rmdir /s /q build

echo.
echo Compiling with Nuitka...

python -m nuitka ^
    --standalone ^
    --output-filename=TrayFlag.exe ^
    --output-dir=TrayFlag ^
    --remove-output ^
    --windows-console-mode=disable ^
    --windows-product-name="TrayFlag" ^
    --windows-file-description="TrayFlag" ^
    --windows-company-name="Ridbowt" ^
    --windows-file-version=1.0.0.0 ^
    --windows-product-version=1.0.0.0 ^
    --enable-plugin=pyside6 ^
    --windows-icon-from-ico=assets/icons/logo.ico ^
    --include-data-dir=assets=assets ^
    --include-data-file=getip\getip_ipify-org.exe=getip\getip_ipify-org.exe ^
    --include-data-file=getip\getip_myip-com.exe=getip\getip_myip-com.exe ^
    --include-data-file=getip\getip_ipinfo-io.exe=getip\getip_ipinfo-io.exe ^
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