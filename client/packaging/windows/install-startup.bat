@echo off
setlocal

set "CLIENT_DIR=%~dp0..\.."
set "EXE_PATH=%CLIENT_DIR%\dist\WhatsMeal.exe"
set "STARTUP_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup"
set "SHORTCUT_PATH=%STARTUP_DIR%\WhatsMeal.lnk"

if not exist "%EXE_PATH%" (
  echo WhatsMeal.exe was not found.
  echo Build it first with:
  echo   packaging\windows\build.bat
  exit /b 1
)

powershell -NoProfile -ExecutionPolicy Bypass -Command ^
  "$shell = New-Object -ComObject WScript.Shell; " ^
  "$shortcut = $shell.CreateShortcut('%SHORTCUT_PATH%'); " ^
  "$shortcut.TargetPath = '%EXE_PATH%'; " ^
  "$shortcut.WorkingDirectory = '%CLIENT_DIR%\dist'; " ^
  "$shortcut.Description = 'Start WhatsMeal when Windows signs in'; " ^
  "$shortcut.Save()"

if errorlevel 1 goto :error

echo Startup shortcut installed:
echo   %SHORTCUT_PATH%
exit /b 0

:error
echo Failed to install startup shortcut.
exit /b 1
