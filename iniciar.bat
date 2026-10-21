@echo off
chcp 65001 >nul
title Consulta de Estoque
cd /d "%~dp0"

where py >nul 2>&1
if %errorlevel%==0 (set PY=py -3) else (set PY=python)
rem Desliga o "Modo de Edicao Rapida" so nesta janela: com ele ligado, um clique
rem dentro dela pausa tudo ate apertar uma tecla, e parece que travou.
%PY% -c "import ctypes as c;k=c.windll.kernel32;k.GetStdHandle.restype=c.c_void_p;h=c.c_void_p(k.GetStdHandle(-10));m=c.c_uint();k.GetConsoleMode(h,c.byref(m)) and k.SetConsoleMode(h,(m.value|0x80)&~0x40)" >nul 2>&1

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
