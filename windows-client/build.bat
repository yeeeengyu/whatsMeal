@echo off
setlocal

cd /d "%~dp0"

if not exist .venv (
  where py >nul 2>nul
  if errorlevel 1 (
    python -m venv .venv
  ) else (
    py -3 -m venv .venv
  )
  if errorlevel 1 goto :error
)

call .venv\Scripts\activate.bat
if errorlevel 1 goto :error

echo [1/4] Updating pip...
python -m pip install --upgrade pip
if errorlevel 1 goto :error

echo [2/4] Installing dependencies...
python -m pip install --prefer-binary -r requirements.txt
if errorlevel 1 goto :error

tasklist /FI "IMAGENAME eq WhatsMeal.exe" | find /I "WhatsMeal.exe" >nul
if not errorlevel 1 (
  echo WhatsMeal.exe is currently running. Close it from the tray or Task Manager, then run this script again.
  goto :error
)

echo [3/4] Cleaning old build output...
if exist build rmdir /S /Q build
if exist dist rmdir /S /Q dist

echo [4/4] Building single exe. This can take a few minutes...
python -m PyInstaller --noconfirm --clean WhatsMealOneFile.spec
if errorlevel 1 goto :error

echo.
echo Build complete: dist\WhatsMeal.exe
exit /b 0

:error
echo.
echo Build failed. Read the error above.
exit /b 1
