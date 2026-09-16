@echo off
chcp 65001 >nul
title Diagnostico
cd /d "%~dp0"
where py >nul 2>&1
if %errorlevel%==0 (py -3 diagnostico.py) else (python diagnostico.py)
echo.
pause
