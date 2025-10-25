@echo off
setlocal
title WoW Arena Notify - Ultra Fast Build
color 0A

echo ============================================
echo     ⚡ WoW Arena Notify - Ultra Fast Build
echo ============================================
echo.

REM === CONFIG ===
set MAIN_FILE=main.py
set APP_NAME=WoW_Arena_Notify
set ICON_FILE=icon.ico
set CACHE_DIR=%~dp0\.pyinstaller_cache

if not exist "%CACHE_DIR%" mkdir "%CACHE_DIR%"
set PYI_CACHE_DIR=%CACHE_DIR%

set MODE=%1
if "%MODE%"=="" set MODE=fast

echo Build mode: %MODE%
echo.

REM === CLEAN MODE ===
if /I "%MODE%"=="clean" (
    color 0E
    echo 🧹 Performing full clean...
    rmdir /s /q build 2>nul
    rmdir /s /q dist 2>nul
    del /q "%APP_NAME%.spec" 2>nul
    echo ✅ Clean complete.
    echo.
)

REM === Verify assets ===
if not exist "%ICON_FILE%" (
    color 0C
    echo ❌ Missing icon file: "%ICON_FILE%"
    pause
    exit /b 1
)
if not exist "ui\styles.qss" (
    color 0C
    echo ❌ Missing UI style file: "ui\styles.qss"
    pause
    exit /b 1
)
echo ✅ Assets verified.
echo.

REM === PyInstaller Flags ===
set FLAGS=--noconfirm --noupx --onefile --windowed ^
 --hidden-import=PySide6.QtCore ^
 --hidden-import=PySide6.QtGui ^
 --hidden-import=PySide6.QtWidgets ^
 --hidden-import=win32crypt ^
 --hidden-import=win32api ^
 --hidden-import=win32con ^
 --hidden-import=win32security ^
 --add-data "ui\styles.qss;ui" ^
 --add-data "icon.ico;." ^
 --add-data ".env;." ^
 --workpath "%CACHE_DIR%\build_main" ^
 --distpath "dist" ^
 --name "%APP_NAME%" ^
 --icon "%ICON_FILE%"

if /I "%MODE%"=="clean" (
    set FLAGS=%FLAGS% --clean
)

REM === Start build ===
color 0B
echo 🏗  Building %APP_NAME%.exe ...
echo.

pyinstaller %FLAGS% "%MAIN_FILE%"

if errorlevel 1 (
    color 0C
    echo ❌ Build failed!
    pause
    exit /b 1
)

color 0A
echo ✅ Build complete!
echo.
echo ============================================
echo Executable: dist\%APP_NAME%.exe
echo Cache dir : %CACHE_DIR%
echo Mode      : %MODE%
echo ============================================
echo.
pause
endlocal
