@echo off
setlocal ENABLEDELAYEDEXPANSION

set OUTPUT=project_tree.txt

echo Generuje liste plikow (bez smieci) -> %OUTPUT%
echo.

powershell -NoProfile -ExecutionPolicy Bypass ^
  "$ErrorActionPreference = 'Stop';" ^
  "$root = Get-Location;" ^
  "$excludeDirs = @('.git','.idea','.vscode','build','dist','.gradle','__pycache__','node_modules','.pyinstaller_cache','tmp','temp','caches','release','debug');" ^
  "$excludeExt = @('.iml','.class','.log','.db','.sqlite','.sqlite3','.zip','.gz','.tar','.apk','.aab','.exe','.dll','.so','.pyc','.pyo','.pyd','.pkg','.toc','.html','.spec','.enc');" ^
  "$excludeNames = @('google-services.json','firebase.json','.env','.firebaserc');" ^
  "$files = Get-ChildItem -Recurse -File | Where-Object {" ^
  "    $relative = $_.FullName.Substring($root.Path.Length + 1);" ^
  "" ^
  "    foreach ($dir in $excludeDirs) {" ^
  "        if ($relative.ToLower().Contains('\'+$dir.ToLower()+'\')) { return $false }" ^
  "    }" ^
  "" ^
  "    if ($excludeExt -contains $_.Extension.ToLower()) { return $false }" ^
  "    if ($excludeNames -contains $_.Name.ToLower()) { return $false }" ^
  "" ^
  "    return $true" ^
  "};" ^
  "$rel = $files | ForEach-Object { $_.FullName.Substring($root.Path.Length + 1) } | Sort-Object;" ^
  "$rel | Set-Content -Encoding UTF8 '%OUTPUT%';" ^
  "Write-Host \"Zapisano $($rel.Count) plikow do %OUTPUT%\""

echo.
echo ✅ Gotowe: %OUTPUT%
echo.
pause
