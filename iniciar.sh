#!/usr/bin/env bash
cd "$(dirname "$0")" || exit 1
python3 -c "import pandas, openpyxl" 2>/dev/null || {
  echo "Instalando as bibliotecas necessarias..."
  python3 -m pip install -r requirements.txt
}
python3 servidor.py
