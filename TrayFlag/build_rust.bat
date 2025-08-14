@echo off
chcp 65001 > nul

echo --- Building Rust utility (ip_lookup.exe) ---

echo Adding Cargo to PATH for this session...
rem Используем %USERPROFILE% чтобы путь был универсальным для любого пользователя
set "PATH=%PATH%;%USERPROFILE%\.cargo\bin"

rem 1. Переходим в папку с Rust-проектом
pushd rust_ip_lookup_cli

rem 2. Собираем проект в релизном режиме
echo Compiling...
cargo build --release

if %errorlevel% neq 0 (
    echo.
    echo ERROR: Rust compilation failed.
    popd
    pause
    exit /b 1
)

rem 3. Возвращаемся в корневую папку проекта
popd

echo Copying executable to 'src' folder...

rem 4. Копируем результат из папки target/release в папку src Python-проекта,
rem    одновременно переименовывая его в ip_lookup.exe
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