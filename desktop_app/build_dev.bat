@echo off
setlocal
title WoW Arena Notify - Dev Build
color 0B

set MAIN_FILE=main.py
set APP_NAME=WoW_Arena_Notify
set ICON_FILE=icon.ico
set CACHE_DIR=%~dp0\.pyinstaller_cache

if not exist "%CACHE_DIR%" mkdir "%CACHE_DIR%"
set PYI_CACHE_DIR=%CACHE_DIR%

echo 🧽 Cleaning old dist...
rmdir /s /q dist 2>nul
echo.

echo 🏗 Building DEV build: %APP_NAME%.exe ...
pyinstaller ^
 --noconfirm ^
 --noupx ^
 --onefile ^
 --windowed ^
 --name "%APP_NAME%" ^
 --icon "%ICON_FILE%" ^
 --add-data "ui\styles.qss;ui" ^
 --add-data "icon.ico;." ^
 --add-data ".env;." ^
 --hidden-import=PySide6.QtCore ^
 --hidden-import=PySide6.QtGui ^
 --hidden-import=PySide6.QtWidgets ^
 --hidden-import=win32crypt ^
 --hidden-import=win32api ^
 --hidden-import=win32con ^
 --hidden-import=win32security ^
 --workpath "%CACHE_DIR%\build_dev" ^
 --distpath "dist" ^
 "%MAIN_FILE%"

if errorlevel 1 (
    color 0C
    echo ❌ Build failed!
    pause
    exit /b 1
)

echo.
echo ✅ Build complete! Output: dist\%APP_NAME%.exe
echo.
pause
endlocal
