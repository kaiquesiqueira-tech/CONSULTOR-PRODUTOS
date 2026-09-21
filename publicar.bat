@echo off
setlocal
pushd "%~dp0"

echo.
echo  == CONSULTA DE ESTOQUE ==
echo  Pasta: %CD%
echo.

where py >nul 2>&1
if %errorlevel%==0 (set PY=py -3) else (set PY=python)

rem ---------------- conferindo as planilhas ----------------
if not exist "dados" goto sempasta

dir /b "dados\~$*.xls*" >nul 2>&1
if not errorlevel 1 goto excelaberto

dir /b "dados\*.xls*" >nul 2>&1
if errorlevel 1 goto semplanilha

for /f "delims=" %%s in ('dir /b "dados\*.xls*"') do echo  [ok] dados\%%s

rem ---------------- gerando ----------------
echo.
echo  Gerando a base...
echo.
%PY% build.py
if errorlevel 1 goto erro

rem ---------------- conferindo o repositorio ----------------
where git >nul 2>&1
if errorlevel 1 goto semgit
if not exist ".git" goto semrepo
git remote get-url origin >nul 2>&1
if errorlevel 1 goto semrepo

rem ---------------- enviando ----------------
echo.
echo  Enviando para o GitHub...
git add -A
git diff --cached --quiet
if not errorlevel 1 goto semmudanca

git commit -m "atualiza base"
if errorlevel 1 goto erro
git push -u origin HEAD
if errorlevel 1 goto erropush

set "REPO="
for /f "delims=" %%u in ('git remote get-url origin 2^>nul') do set "REPO=%%u"
set "REPO=%REPO:.git=%"

echo.
echo  Publicado. O GitHub esta gerando o app agora, leva uns 2 minutos.
echo  Os aparelhos com o consultor aberto trocam de base sozinhos.
if defined REPO echo  Acompanhe em: %REPO%/actions
goto fim

:sempasta
echo  [x] nao existe a pasta "dados" aqui.
echo.
echo  Crie a pasta "dados" e salve nela as exportacoes do Protheus.
goto fim

:semplanilha
echo  [x] a pasta "dados" esta vazia.
echo.
echo  Salve nela as duas exportacoes do Protheus:
echo    - SALDO FISICO       com Produto, Nome Cientif, Saldo Atual
echo    - SALDO POR ENDERECO com Produto, Endereco, Quantidade
echo.
echo  O nome do arquivo nao importa: o programa descobre pelas colunas.
goto fim

:excelaberto
echo  [x] tem planilha aberta no Excel.
echo.
echo  O Excel segura o arquivo e a leitura falha. Feche a planilha
echo  e clique aqui de novo.
goto fim

:semgit
echo.
echo  [x] o Git nao esta instalado neste computador.
echo.
echo  Baixe em https://git-scm.com/download/win e instale com as
echo  opcoes padrao. A base foi gerada, so o envio ficou pendente.
goto fim

:semrepo
echo.
echo  [x] esta pasta ainda nao esta ligada a um repositorio do GitHub.
echo.
echo  Faca isso uma vez pelo VS Code: painel Controle do Codigo-Fonte,
echo  botao "Publicar no GitHub". Depois este arquivo passa a funcionar.
echo  A base ja foi gerada e esta no index.html.
goto fim

:semmudanca
echo.
echo  A base gerada e igual a que ja esta publicada. Nada a enviar.
goto fim

:erropush
echo.
echo  O envio falhou. Verifique a conexao e se voce esta logado no GitHub.
echo  Se alguem enviou algo antes de voce, rode:  git pull --rebase
goto fim

:erro
echo.
echo  Algo deu errado no passo acima. Leia a mensagem e tente de novo.

:fim
echo.
popd
pause
