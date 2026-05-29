@echo off
setlocal

set "SHORTCUT_PATH=%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\WhatsMeal.lnk"

if exist "%SHORTCUT_PATH%" (
  del "%SHORTCUT_PATH%"
  echo Startup shortcut removed:
  echo   %SHORTCUT_PATH%
) else (
  echo Startup shortcut was not installed.
)
