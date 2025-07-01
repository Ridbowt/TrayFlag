@echo off
chcp 65001 > nul
echo [1/4] Cleaning up...
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist

echo [2/4] Compiling Core App (in 'bin')...
python -m nuitka --standalone --output-dir=build\core --output-filename=TrayFlag_core.exe --remove-output --windows-disable-console --enable-plugin=pyqt6 --include-data-dir=assets=assets --include-package=soundfile,sounddevice,win32com src/TrayFlag_core.py
if %errorlevel% neq 0 (echo ERROR: Core compilation failed. & pause & exit /b 1)

echo [3/4] Compiling Launcher (in root)...
python -m nuitka --onefile --output-dir=build\launcher --output-filename=TrayFlag.exe --remove-output --windows-disable-console --windows-icon-from-ico=assets/icons/logo.ico run_trayflag.py
if %errorlevel% neq 0 (echo ERROR: Launcher compilation failed. & pause & exit /b 1)

echo [4/4] Organizing final 'dist' folder...
python organize_build.py

echo. & echo Build successful! Find the result in the 'dist' folder. & pause