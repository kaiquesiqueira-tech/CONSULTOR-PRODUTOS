@echo off
setlocal
chcp 65001 >nul
title Colocar na area de trabalho
cd /d "%~dp0"

echo.
echo ==========================================
echo    Colocar na area de trabalho
echo ==========================================
echo.
echo  [1] Atalho do app
echo      Um icone que liga o app e abre o navegador.
echo      Os dados sao sempre os das planilhas de agora.
echo      Precisa do Python instalado.
echo.
echo  [2] Copia solta do app
echo      Um arquivo unico que abre com duplo clique, sem Python
echo      e sem internet. Guarda os dados do momento em que foi
echo      gerado. Bom para levar em notebook ou mandar por e-mail.
echo.
echo  [3] Os dois
echo.
echo  [4] Sair
echo.

set "OPCAO="
set /p "OPCAO=Digite o numero e tecle Enter: "

if "%OPCAO%"=="1" goto ATALHO
if "%OPCAO%"=="2" goto COPIA
if "%OPCAO%"=="3" goto AMBOS
goto FIM

:COPIA
call :GERAR
powershell -NoProfile -ExecutionPolicy Bypass -File "app\atalho.ps1" -Modo copia
goto PRONTO

:AMBOS
call :GERAR
powershell -NoProfile -ExecutionPolicy Bypass -File "app\atalho.ps1" -Modo ambos
goto PRONTO

:ATALHO
powershell -NoProfile -ExecutionPolicy Bypass -File "app\atalho.ps1" -Modo atalho
goto PRONTO

:GERAR
echo.
echo Gerando o app com as planilhas de agora...
where py >nul 2>&1
if %errorlevel%==0 (py -3 build.py) else (python build.py)
exit /b 0

:PRONTO
echo.
echo Pronto. Veja na sua area de trabalho.
echo.
pause
exit /b 0

:FIM
echo.
exit /b 0
