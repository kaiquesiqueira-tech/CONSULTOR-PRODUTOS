@echo off
chcp 65001 >nul
title Verificar o envio para o GitHub
cd /d "%~dp0"
where py >nul 2>&1
if %errorlevel%==0 (py -3 verificar.py) else (python verificar.py)
echo.
pause
