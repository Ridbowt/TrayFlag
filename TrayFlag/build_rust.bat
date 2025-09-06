@echo off
chcp 65001 > nul

echo --- Building Rust utility (ip_lookup.exe) ---

echo Adding Cargo to PATH for this session...
rem Use %USERPROFILE% so that the path is universal for any user
set "PATH=%PATH%;%USERPROFILE%\.cargo\bin"

rem 1. Go to the folder with the Rust project
pushd rust_ip_lookup_cli

rem 2. Build the project in release mode
echo Compiling...
cargo build --release

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Rust compilation failed.
    popd
    pause
    exit /b 1
)

rem 3. Return to the root project folder
popd

echo Copying executable to 'src' folder...

rem 4. Copy the result from the target/release folder to the src folder of the Python project,
rem    simultaneously renaming it to ip_lookup.exe
copy /Y rust_ip_lookup_cli\target\release\rust_ip_lookup_cli.exe src\ip_lookup.exe

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to copy Rust executable.
    pause
    exit /b 1
)

echo.
echo --- Rust build successful! ---
echo ip_lookup.exe has been updated in the 'src' folder.
pause