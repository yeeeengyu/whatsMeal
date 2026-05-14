@echo off
setlocal

cd /d "%~dp0\..\.."

if not exist .venv (
  py -3.11 -m venv .venv
)

call .venv\Scripts\activate.bat
echo [1/4] Updating pip...
python -m pip install --upgrade pip
if errorlevel 1 goto :error

echo [2/4] Installing dependencies...
pip install --prefer-binary -r requirements.txt
if errorlevel 1 goto :error

echo [3/4] Cleaning old build output...
if exist build rmdir /S /Q build
if exist dist rmdir /S /Q dist

echo [4/4] Building single exe. This can take a few minutes...
pyinstaller --noconfirm --clean packaging\windows\WhatsMealOneFile.spec
if errorlevel 1 goto :error

echo.
echo Build complete: dist\WhatsMeal.exe
exit /b 0

:error
echo.
echo Build failed. Read the error above.
exit /b 1
