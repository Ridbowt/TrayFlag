@echo off
echo === STARTING FULL BUILD PROCESS ===
echo.

echo --- Step 1: Building Rust components ---
call build_rust.bat
if %errorlevel% neq 0 (
    echo.
    echo FATAL ERROR: Rust build failed. Halting process.
    pause
    exit /b 1
)

echo.
echo --- Step 2: Building Python components ---
call build_python.bat
if %errorlevel% neq 0 (
    echo.
    echo FATAL ERROR: Python build failed.
    pause
    exit /b 1
)

echo.
echo === ALL BUILDS COMPLETED SUCCESSFULLY! ===
pause