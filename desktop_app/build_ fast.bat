@echo off
setlocal
title WoW Arena Notify - Ultra Fast Build
color 0A

::
:: ✅ ULTRA FAST BUILD — inkrementalny
:: - ⚡ najszybszy build (bez clean)
:: - NIE przebudowuje bibliotek ani plików assets
:: - ✅ idealny przy zmianach w kodzie .py
:: - ❌ jeśli zmieniłeś PNG/QSS/icons → użyj build_dev.bat
::

set MAIN_FILE=main.py
set APP_NAME=WoW_Arena_Notify
set ICON_FILE=icon.ico
set CACHE_DIR=%~dp0\.pyinstaller_cache

if not exist "%CACHE_DIR%" mkdir "%CACHE_DIR%"
set PYI_CACHE_DIR=%CACHE_DIR%

echo 🏗  Building FAST: %APP_NAME%.exe ...
echo.

pyinstaller ^
 --noconfirm ^
 --noupx ^
 --onefile ^
 --windowed ^
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
 --workpath "%CACHE_DIR%\build_fast" ^
 --distpath "dist" ^
 "%MAIN_FILE%"

echo.
echo ✅ FAST build complete → dist\%APP_NAME%.exe
echo.
pause
endlocal
