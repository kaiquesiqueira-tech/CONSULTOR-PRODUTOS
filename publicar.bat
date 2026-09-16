@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title Publicar no GitHub
cd /d "%~dp0"

echo.
echo ==========================================
echo    Consulta de Estoque - publicar
echo ==========================================
echo.

rem ================= checagens =================
where git >nul 2>&1
if errorlevel 1 goto SEM_GIT

where py >nul 2>&1
if %errorlevel%==0 (set "PY=py -3") else (set "PY=python")

rem ================= 1. gerar =================
echo [1 de 4] Gerando o app a partir das planilhas...
echo.
%PY% build.py
if errorlevel 1 goto FALHOU_BUILD

rem ================= 2. repositorio =================
echo.
echo [2 de 4] Conferindo o repositorio...
if exist ".git" goto TEM_PASTA_GIT

echo.
echo   Primeira vez neste computador.
echo.
echo   Crie um repositorio VAZIO no GitHub antes de continuar:
echo     1. Entre em github.com e clique em New repository
echo     2. De um nome, por exemplo: consulta-estoque
echo     3. Escolha Private. Leia o LEIA-ME antes de escolher Public,
echo        porque a base leva saldos e custos da empresa
echo     4. Nao marque nada na parte de Initialize this repository
echo     5. Copie o endereco que termina em .git
echo.
set "REPO="
set /p "REPO=Cole aqui o endereco do repositorio: "
if "!REPO!"=="" goto CANCELADO
git init -q
git branch -M main
git remote add origin "!REPO!"
echo   Repositorio ligado.

:TEM_PASTA_GIT
git remote get-url origin >nul 2>&1
if not errorlevel 1 goto TEM_REMOTO
set "REPO="
set /p "REPO=Endereco do repositorio: "
if "!REPO!"=="" goto CANCELADO
git remote add origin "!REPO!"

:TEM_REMOTO
git config user.name >nul 2>&1
if not errorlevel 1 goto TEM_IDENTIDADE
echo.
echo   Falta dizer quem esta enviando. Isso so e perguntado uma vez.
set "GNOME="
set "GMAIL="
set /p "GNOME=Seu nome: "
set /p "GMAIL=Seu e-mail do GitHub: "
git config user.name "!GNOME!"
git config user.email "!GMAIL!"

:TEM_IDENTIDADE

rem ================= 3. registrar a versao =================
echo.
echo [3 de 4] Vendo o que mudou...
git add -A
git diff --cached --quiet
if not errorlevel 1 goto NADA_MUDOU

git diff --cached --name-only
echo.
set "MSG="
set /p "MSG=Descreva a mudanca, ou de Enter para usar a data: "
if "!MSG!"=="" set "MSG=Atualizacao de %date% %time%"

git commit -q -m "!MSG!"
if errorlevel 1 goto FALHOU_COMMIT

rem ================= 4. enviar =================
echo.
echo [4 de 4] Enviando para o GitHub...
echo Na primeira vez abre uma janela pedindo para voce entrar na sua conta.
echo.
git push -u origin main
if errorlevel 1 goto FALHOU_PUSH

echo.
echo ==========================================
echo    Enviado com sucesso.
echo ==========================================
echo.
git remote get-url origin
echo.
pause
exit /b 0

rem ================= saidas =================
:SEM_GIT
echo O Git nao esta instalado neste computador.
echo.
echo Baixe em https://git-scm.com/download/win e instale com as opcoes
echo padrao. Depois abra este arquivo de novo.
echo.
pause
exit /b 1

:FALHOU_BUILD
echo.
echo Nao consegui gerar o app. O erro esta na mensagem acima.
echo Na maioria das vezes e uma planilha aberta no Excel ou fora do padrao.
echo.
pause
exit /b 1

:NADA_MUDOU
echo.
echo Nada mudou desde o ultimo envio. Nao ha o que publicar.
echo.
pause
exit /b 0

:FALHOU_COMMIT
echo.
echo Nao consegui registrar a versao. Veja a mensagem acima.
echo.
pause
exit /b 1

:FALHOU_PUSH
echo.
echo ==========================================
echo    O envio falhou.
echo ==========================================
echo.
echo As causas mais comuns:
echo.
echo  - A janela de login foi fechada sem entrar na conta.
echo    Clique neste arquivo de novo e faca o login.
echo.
echo  - O endereco do repositorio esta errado. Para trocar, abra o
echo    terminal nesta pasta e rode:
echo      git remote set-url origin ENDERECO_CERTO
echo.
echo  - Alguem enviou algo antes de voce. Nesse caso rode:
echo      git pull --rebase
echo    e clique neste arquivo de novo.
echo.
pause
exit /b 1

:CANCELADO
echo.
echo Cancelado. Nada foi enviado.
echo.
pause
exit /b 1
