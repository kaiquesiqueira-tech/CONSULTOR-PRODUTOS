@echo off
chcp 65001 >nul
title Consulta de Estoque
cd /d "%~dp0"

where py >nul 2>&1
if %errorlevel%==0 (set PY=py -3) else (set PY=python)

%PY% -c "import pandas, openpyxl" >nul 2>&1
if errorlevel 1 (
  echo.
  echo Instalando as bibliotecas necessarias. Isso so acontece na primeira vez...
  echo.
  %PY% -m pip install -r requirements.txt
)

%PY% servidor.py
echo.
pause
