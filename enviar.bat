@echo off
setlocal enabledelayedexpansion
chcp 65001 >nul
title Enviar para o GitHub
cd /d "%~dp0"

echo.
echo ==========================================
echo    Enviar as planilhas para o GitHub
echo ==========================================
echo.
echo  O app nao e enviado daqui. Voce manda as planilhas,
echo  e o proprio GitHub gera o app e atualiza o site.
echo.

where git >nul 2>&1
if errorlevel 1 goto SEM_GIT

if exist ".git" goto TEM_GIT

echo  Primeira vez neste computador.
echo.
echo  Crie um repositorio VAZIO no GitHub:
echo    github.com  -  New repository  -  sem marcar nada em Initialize
echo.
echo  Sobre a visibilidade: as planilhas vao junto, com custos e saldos.
echo  Em repositorio Public qualquer pessoa baixa tudo. Leia o LEIA-ME.
echo.
set "REPO="
set /p "REPO=Cole o endereco do repositorio: "
if "!REPO!"=="" goto CANCELADO
git init -q
git branch -M main
git remote add origin "!REPO!"

:TEM_GIT
git remote get-url origin >nul 2>&1
if not errorlevel 1 goto TEM_REMOTO
set "REPO="
set /p "REPO=Endereco do repositorio: "
if "!REPO!"=="" goto CANCELADO
git remote add origin "!REPO!"

:TEM_REMOTO
git config user.name >nul 2>&1
if not errorlevel 1 goto TEM_NOME
echo.
echo  Isso e perguntado uma vez so.
set "GNOME="
set "GMAIL="
set /p "GNOME=Seu nome: "
set /p "GMAIL=Seu e-mail do GitHub: "
git config user.name "!GNOME!"
git config user.email "!GMAIL!"

:TEM_NOME
echo.
echo  Vendo o que mudou...
git add -A
git diff --cached --quiet
if not errorlevel 1 goto NADA

echo.
git diff --cached --name-only
echo.
set "MSG="
set /p "MSG=Descreva o envio, ou de Enter para usar a data: "
if "!MSG!"=="" set "MSG=Planilhas de %date%"

git commit -q -m "!MSG!"
if errorlevel 1 goto FALHOU

echo.
echo  Enviando... na primeira vez abre uma janela pedindo seu login.
echo.
git push -u origin main
if errorlevel 1 goto FALHOU_PUSH

echo.
echo ==========================================
echo    Enviado.
echo ==========================================
echo.
echo  Agora o GitHub esta gerando o app. Leva uns 2 minutos.
echo  Acompanhe na aba Actions do seu repositorio.
echo.
pause
exit /b 0

:SEM_GIT
echo  O Git nao esta instalado. Baixe em https://git-scm.com/download/win
echo.
pause
exit /b 1

:NADA
echo.
echo  Nada mudou desde o ultimo envio.
echo.
pause
exit /b 0

:FALHOU
echo.
echo  Nao consegui registrar a versao. Veja a mensagem acima.
echo.
pause
exit /b 1

:FALHOU_PUSH
echo.
echo  O envio falhou. Causas comuns:
echo    - a janela de login foi fechada sem entrar
echo    - o endereco do repositorio esta errado
echo      corrija com:  git remote set-url origin ENDERECO_CERTO
echo    - alguem enviou antes de voce
echo      rode:  git pull --rebase   e tente de novo
echo.
pause
exit /b 1

:CANCELADO
echo.
echo  Cancelado.
echo.
pause
exit /b 1
