@echo off
setlocal
chcp 65001 >nul
title Publicacao automatica
cd /d "%~dp0"

:MENU
cls
echo.
echo ==========================================
echo    Publicacao automatica no GitHub
echo ==========================================
echo.
powershell -NoProfile -ExecutionPolicy Bypass -File "app\vigia-controle.ps1" -Acao estado
call :MOSTRAR_CONFIG
call :MOSTRAR_CUSTOS
echo.
echo  Como funciona: ele fica de olho na pasta dados e na pasta app.
echo  Quando algo muda, gera o app e envia para o GitHub sozinho.
echo.
echo  [1] Ligar a publicacao automatica
echo  [2] Desligar a publicacao automatica
echo.
echo  [3] Iniciar o vigia agora, em segundo plano
echo  [4] Parar o vigia
echo.
echo  [5] Fazer o vigia subir junto com o Windows
echo  [6] Tirar do inicio do Windows
echo.
echo  [7] Ver as ultimas linhas do log
echo  [8] Mostrar ou esconder custos e valores na base
echo  [9] Sair
echo.

set "OP="
set /p "OP=Digite o numero e tecle Enter: "

if "%OP%"=="1" goto LIGAR
if "%OP%"=="2" goto DESLIGAR
if "%OP%"=="3" goto INICIAR
if "%OP%"=="4" goto PARAR
if "%OP%"=="5" goto INSTALAR
if "%OP%"=="6" goto REMOVER
if "%OP%"=="7" goto LOG
if "%OP%"=="8" goto CUSTOS
goto FIM

:LIGAR
echo.
echo ATENCAO: antes de ligar, rode o publicar.bat UMA vez e faca o login
echo do GitHub. Sem isso o envio automatico nao consegue entrar na conta.
echo.
set "OK="
set /p "OK=Ja fez esse primeiro envio? (s/n): "
if /i not "%OK%"=="s" goto VOLTA
call :PY -c "import publicacao; publicacao.definir('publicar_automatico','sim'); print('  Publicacao automatica LIGADA.')"
goto VOLTA

:DESLIGAR
call :PY -c "import publicacao; publicacao.definir('publicar_automatico','nao'); print('  Publicacao automatica DESLIGADA.')"
goto VOLTA

:INICIAR
powershell -NoProfile -ExecutionPolicy Bypass -File "app\vigia-controle.ps1" -Acao iniciar
goto VOLTA

:PARAR
powershell -NoProfile -ExecutionPolicy Bypass -File "app\vigia-controle.ps1" -Acao parar
goto VOLTA

:INSTALAR
powershell -NoProfile -ExecutionPolicy Bypass -File "app\vigia-controle.ps1" -Acao instalar
powershell -NoProfile -ExecutionPolicy Bypass -File "app\vigia-controle.ps1" -Acao iniciar
goto VOLTA

:REMOVER
powershell -NoProfile -ExecutionPolicy Bypass -File "app\vigia-controle.ps1" -Acao remover
powershell -NoProfile -ExecutionPolicy Bypass -File "app\vigia-controle.ps1" -Acao parar
goto VOLTA

:CUSTOS
echo.
echo  Se o repositorio do GitHub for PUBLICO, qualquer pessoa na internet
echo  baixa o app com tudo que estiver dentro dele, inclusive custo
echo  unitario e valor em estoque de cada item.
echo.
echo  [1] Deixar os custos na base  (use so com repositorio privado)
echo  [2] Tirar os custos da base   (seguro para repositorio publico)
echo.
set "CC="
set /p "CC=Escolha: "
if "%CC%"=="1" call :PY -c "import publicacao; publicacao.definir('incluir_custos','sim'); print('  Custos incluidos. Gere o app de novo.')"
if "%CC%"=="2" call :PY -c "import publicacao; publicacao.definir('incluir_custos','nao'); print('  Custos removidos. Gere o app de novo.')"
echo.
echo  Gerando o app com a nova preferencia...
call :PY build.py
goto VOLTA

:LOG
echo.
if not exist "vigia.log" echo  Ainda nao ha log. O vigia nunca rodou.
if exist "vigia.log" powershell -NoProfile -Command "Get-Content vigia.log -Tail 20"
goto VOLTA

:MOSTRAR_CONFIG
if not exist "config.txt" (
  echo   Publicacao automatica: desligada
  exit /b 0
)
findstr /i /c:"publicar_automatico = sim" config.txt >nul 2>&1
if errorlevel 1 (echo   Publicacao automatica: desligada) else (echo   Publicacao automatica: LIGADA)
exit /b 0

:MOSTRAR_CUSTOS
if not exist "config.txt" (echo   Custos na base: incluidos & exit /b 0)
findstr /i /c:"incluir_custos = nao" config.txt >nul 2>&1
if errorlevel 1 (echo   Custos na base: incluidos) else (echo   Custos na base: REMOVIDOS)
exit /b 0

:PY
where py >nul 2>&1
if %errorlevel%==0 (py -3 %*) else (python %*)
exit /b 0

:VOLTA
echo.
pause
goto MENU

:FIM
exit /b 0
