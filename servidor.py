# -*- coding: utf-8 -*-
"""
Servidor local do Consulta de Estoque.

O que ele faz enquanto estiver aberto:
  1. Gera o app a partir das planilhas da pasta 'dados'
  2. Fica de olho na pasta. Se voce trocar, adicionar ou apagar um arquivo,
     ele gera tudo de novo sozinho e a pagina aberta recarrega
  3. Publica na sua rede, entao o celular no mesmo wi-fi abre pelo IP

Uso:  python servidor.py
Parar: Ctrl+C
"""

import os
import sys
import time
import socket
import threading
import webbrowser
import http.server
import socketserver

RAIZ = os.path.dirname(os.path.abspath(__file__))
PASTA_DADOS = os.path.join(RAIZ, "dados")
PASTA_SAIDA = os.path.join(RAIZ, "dist")
PORTA = int(os.environ.get("PORTA", "8080"))
INTERVALO = 2  # segundos entre cada checagem da pasta

sys.path.insert(0, RAIZ)
import build  # noqa: E402


def retrato():
    """Foto do estado da pasta: nome, tamanho e data de cada planilha."""
    itens = []
    for caminho in build.achar_planilhas():
        try:
            st = os.stat(caminho)
            itens.append((os.path.basename(caminho), st.st_size, int(st.st_mtime)))
        except OSError:
            pass
    return tuple(sorted(itens))


def gerar(motivo):
    print("\n[%s] %s" % (time.strftime("%H:%M:%S"), motivo))
    try:
        build.principal()
    except Exception as erro:
        print("  ERRO ao gerar: %s" % erro)
        print("  Confira se a planilha nao esta aberta no Excel e tente salvar de novo.")


def vigiar():
    anterior = retrato()
    while True:
        time.sleep(INTERVALO)
        atual = retrato()
        if atual != anterior:
            anterior = atual
            time.sleep(1)  # espera o arquivo terminar de ser copiado
            gerar("Planilhas mudaram, gerando o app de novo...")


def meu_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None


class Servidor(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PASTA_SAIDA, **kwargs)

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, formato, *args):
        pass  # nao polui o terminal


class ServidorTCP(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def principal():
    os.makedirs(PASTA_DADOS, exist_ok=True)
    gerar("Gerando o app pela primeira vez...")

    if not os.path.exists(os.path.join(PASTA_SAIDA, "index.html")):
        print("\nColoque as planilhas na pasta 'dados' e rode de novo.")
        return 1

    threading.Thread(target=vigiar, daemon=True).start()

    porta = PORTA
    servidor = None
    for tentativa in range(10):
        try:
            servidor = ServidorTCP(("0.0.0.0", porta), Servidor)
            break
        except OSError:
            porta += 1
    if servidor is None:
        print("Nao consegui abrir nenhuma porta entre %d e %d." % (PORTA, PORTA + 9))
        return 1

    ip = meu_ip()
    print("")
    print("=" * 58)
    print("  Consulta de Estoque no ar")
    print("")
    print("  Neste computador:  http://localhost:%d" % porta)
    if ip:
        print("  No celular:        http://%s:%d" % (ip, porta))
        print("                     (celular no mesmo wi-fi)")
    print("")
    print("  Troque as planilhas na pasta 'dados' e a pagina")
    print("  se atualiza sozinha. Ctrl+C para parar.")
    print("=" * 58)

    try:
        webbrowser.open("http://localhost:%d" % porta)
    except Exception:
        pass

    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        print("\nServidor parado.")
    finally:
        servidor.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(principal())
