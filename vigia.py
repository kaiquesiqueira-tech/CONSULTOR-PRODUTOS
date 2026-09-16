# -*- coding: utf-8 -*-
"""
Vigia em segundo plano.

Fica observando as planilhas da pasta 'dados' e os arquivos da pasta 'app'.
Quando alguma coisa muda, gera o app e envia para o GitHub sozinho.

Nao abre janela nem servidor. Serve para deixar rodando junto com o
Windows: o area-de-trabalho.bat instala isso para voce.

Tudo que acontece fica anotado em vigia.log, dentro da pasta do projeto.

Para rodar na mao e acompanhar:  python vigia.py
"""

import os
import sys
import time
import datetime

RAIZ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, RAIZ)

import build         # noqa: E402
import publicacao    # noqa: E402
import servidor      # noqa: E402  (reaproveita a funcao que fotografa a pasta)

LOG = os.path.join(RAIZ, "vigia.log")
INTERVALO = 3
LIMITE_LOG = 400 * 1024   # 400 KB


def anotar(texto):
    linha = "[%s] %s" % (datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"), texto)
    print(linha)
    try:
        if os.path.exists(LOG) and os.path.getsize(LOG) > LIMITE_LOG:
            with open(LOG, encoding="utf-8", errors="replace") as f:
                fim = f.readlines()[-200:]
            with open(LOG, "w", encoding="utf-8") as f:
                f.writelines(fim)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(linha + "\n")
    except OSError:
        pass


def gerar_e_publicar():
    try:
        codigo = build.principal()
    except Exception as erro:
        anotar("ERRO ao gerar o app: %s" % erro)
        return
    if codigo:
        anotar("O app nao foi gerado. Confira as planilhas da pasta 'dados'.")
        return
    anotar("App gerado.")

    if not publicacao.ligado():
        anotar("Publicacao automatica desligada no config.txt. Nada enviado.")
        return

    enviou, recado = publicacao.publicar()
    anotar(("Enviado: " if enviou else "Nao enviado: ") + recado)


def principal():
    anotar("Vigia iniciado. Observando 'dados' e 'app'.")
    if not publicacao.ligado():
        anotar("Aviso: publicacao automatica esta DESLIGADA no config.txt.")

    anterior = servidor.retrato()
    while True:
        try:
            time.sleep(INTERVALO)
            atual = servidor.retrato()
            if atual == anterior:
                continue

            estavel = 0
            while estavel < 2:
                time.sleep(INTERVALO)
                novo = servidor.retrato()
                estavel = estavel + 1 if novo == atual else 0
                atual = novo

            anterior = atual
            anotar("Mudanca detectada.")
            gerar_e_publicar()

        except KeyboardInterrupt:
            anotar("Vigia encerrado.")
            return 0
        except Exception as erro:
            anotar("Erro inesperado, continuando: %s" % erro)
            time.sleep(10)


if __name__ == "__main__":
    sys.exit(principal())
