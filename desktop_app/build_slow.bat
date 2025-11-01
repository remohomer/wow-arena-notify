@echo off
setlocal
title WoW Arena Notify - Dev Clean Build
color 0E

::
:: 🧹 FULL CLEAN DEV BUILD
:: - czyści build + dist
:: - odbudowuje wszystkie dependency + assets
:: - wolniejszy (kilka sekund)
:: ✅ używaj przy zmianach w QSS/PNG/icon
::

set MAIN_FILE=main.py
set APP_NAME=WoW_Arena_Notify
set ICON_FILE=icon.ico
set CACHE_DIR=%~dp0\.pyinstaller_cache

echo 🧽 Cleaning old build artifacts...
rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
del /q "%APP_NAME%.spec" 2>nul
echo.

echo 🏗 DEV CLEAN build: %APP_NAME%.exe ...
echo.

pyinstaller ^
 --noconfirm ^
 --noupx ^
 --onefile ^
 --windowed ^
 --clean ^
 --name "%APP_NAME%" ^
 --icon "%ICON_FILE%" ^
 --add-data "ui/styles.qss;ui" ^
 --add-data "icon.ico;." ^
 --add-data ".env;." ^
 --add-data "assets/portal_icon.png;assets" ^
 --add-data "assets/gong.wav;assets" ^
 --hidden-import=PySide6.QtCore ^
 --hidden-import=PySide6.QtGui ^
 --hidden-import=PySide6.QtWidgets ^
 --hidden-import=win32crypt ^
 --hidden-import=win32api ^
 --hidden-import=win32con ^
 --hidden-import=win32security ^
 --hidden-import=pyperclip ^
 --exclude-module PyQt5 ^
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
echo ✅ DEV CLEAN build complete → dist\%APP_NAME%.exe
echo.
pause
endlocal
