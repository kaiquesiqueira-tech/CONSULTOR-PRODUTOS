#!/usr/bin/env bash
# Versao do publicar.bat para Linux e Mac
set -e
cd "$(dirname "$0")"

command -v git >/dev/null || { echo "Git nao instalado."; exit 1; }

echo "[1 de 4] Gerando o app..."
python3 build.py

if [ ! -d .git ]; then
  echo
  echo "Primeira vez. Crie um repositorio VAZIO no GitHub e cole o endereco."
  read -r -p "Endereco do repositorio (.git): " REPO
  [ -z "$REPO" ] && { echo "Cancelado."; exit 1; }
  git init -q && git branch -M main && git remote add origin "$REPO"
fi

git add -A
if git diff --cached --quiet; then
  echo "Nada mudou desde o ultimo envio."
  exit 0
fi

read -r -p "Descricao da mudanca (Enter para usar a data): " MSG
[ -z "$MSG" ] && MSG="Atualizacao de $(date '+%d/%m/%Y %H:%M')"

git commit -qm "$MSG"
git push -u origin main
echo "Enviado."
