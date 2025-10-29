@echo off
setlocal enabledelayedexpansion

:: ===== WoW Arena Notify — Project Tree (Windows .bat using PowerShell) =====
set OUTPUT=project_tree.txt

echo Generuje liste plikow (bez smieci) -> %OUTPUT%
echo.

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$ErrorActionPreference='Stop';" ^
  "$root = Get-Location;" ^
  "$excludeDirRegex = '(^|\\|/)(\.git|build|\.gradle|\.idea|__pycache__|\.venv|venv|node_modules|out|dist|tmp|temp)(\\|/|$)';" ^
  "$excludeExt = @('.iml','.class','.log','.db','.sqlite','.sqlite3','.png','.jpg','.jpeg','.gif','.ico','.webp','.mp3','.wav','.mp4','.zip','.tar','.gz','.exe','.dll','.so','.pyc','.pyo','Thumbs.db','.DS_Store');" ^
  "$files = Get-ChildItem -Recurse -File | Where-Object { $_.FullName -notmatch $excludeDirRegex -and ($excludeExt -notcontains $_.Extension.ToLower()) -and ($excludeExt -notcontains $_.Name) };" ^
  "$rel = $files | ForEach-Object { $_.FullName.Substring($root.Path.Length + 1) } | Sort-Object;" ^
  "$rel | Set-Content -Encoding UTF8 '%OUTPUT%';" ^
  "Write-Host ('Zapisano ' + $rel.Count + ' plikow do %OUTPUT%');"

if exist "%OUTPUT%" (
  echo.
  echo ✅ Gotowe: %OUTPUT%
) else (
  echo.
  echo ❌ Nie udalo sie utworzyc %OUTPUT%. Uruchom to okno jako Administrator lub sprawdz uprawnienia do folderu.
)

echo.
pause
