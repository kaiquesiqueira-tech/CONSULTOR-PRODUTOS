# -*- coding: utf-8 -*-
"""
Servidor local do Consulta de Estoque.

O que ele faz enquanto estiver aberto:
  1. Gera o app a partir das planilhas da pasta 'dados'
  2. Fica de olho na pasta. Se voce trocar, adicionar ou apagar um arquivo,
     ele gera tudo de novo sozinho e a pagina aberta recarrega
  3. Publica na sua rede, entao o celular no mesmo wi-fi abre pelo IP
     (so os arquivos do app; as planilhas nao ficam acessiveis)
  4. Se ENVIAR_PARA_O_GITHUB estiver ligado, manda as planilhas novas
     para o GitHub, que gera e publica o app sozinho

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
import subprocess
import urllib.parse
import re
import json
import shutil

RAIZ = os.path.dirname(os.path.abspath(__file__))
PASTA_DADOS = os.path.join(RAIZ, "dados")
PASTA_SAIDA = RAIZ   # o app e gerado na propria pasta do projeto
# ---------------------------------------------------------------------
#  ENVIAR_PARA_O_GITHUB
#    True  = ao detectar planilha nova, alem de gerar o app aqui, manda
#            para o GitHub sozinho. O GitHub gera e publica o site.
#    False = so gera aqui no computador.
#
#  Para funcionar, o repositorio precisa ja estar ligado e o login do
#  GitHub ja feito uma vez (pelo VS Code ou pelo publicar.bat). Este
#  envio automatico nunca pergunta senha.
# ---------------------------------------------------------------------
ENVIAR_PARA_O_GITHUB = True

PORTA = int(os.environ.get("PORTA", "8080"))
INTERVALO = 2  # segundos entre cada checagem da pasta

sys.path.insert(0, RAIZ)
import build  # noqa: E402


def vigiados():
    """Tudo que, ao mudar, obriga a gerar o app de novo."""
    caminhos = list(build.achar_planilhas())
    modelo = os.path.join(RAIZ, "template.html")
    if os.path.exists(modelo):
        caminhos.append(modelo)
    return caminhos


def retrato():
    """Foto do estado dos arquivos: nome, tamanho e data de cada um."""
    itens = []
    for caminho in vigiados():
        try:
            st = os.stat(caminho)
            itens.append((os.path.basename(caminho), st.st_size, int(st.st_mtime)))
        except OSError:
            pass
    return tuple(sorted(itens))


def _git(*args, **kwargs):
    ambiente = dict(os.environ)
    ambiente["GIT_TERMINAL_PROMPT"] = "0"   # falha rapido em vez de travar pedindo senha
    ambiente["GCM_INTERACTIVE"] = "never"
    return subprocess.run(["git"] + list(args), cwd=RAIZ, capture_output=True,
                          text=True, env=ambiente, timeout=kwargs.get("timeout", 120))


def _recado(texto):
    for linha in (texto or "").splitlines():
        if linha.strip():
            return linha.strip()
    return ""


def enviar_para_o_github():
    """Manda as planilhas novas. Devolve (enviou, recado). Nunca levanta erro."""
    try:
        if not os.path.isdir(os.path.join(RAIZ, ".git")):
            return False, "esta pasta nao esta ligada a nenhum repositorio."
        if _git("remote", "get-url", "origin").returncode != 0:
            return False, "nenhum repositorio do GitHub configurado."
        if _git("config", "user.name").returncode != 0:
            return False, "falta configurar seu nome no Git."

        if _git("add", "-A").returncode != 0:
            return False, "nao consegui preparar os arquivos."
        _git("reset", "-q", "--", "gemini_chave.txt", "jarvis_chave.txt")   # chaves nunca sobem
        if _git("diff", "--cached", "--quiet").returncode == 0:
            return False, "nada novo para enviar."

        recado = "Planilhas de " + time.strftime("%d/%m/%Y %H:%M")
        r = _git("commit", "-m", recado)
        if r.returncode != 0:
            return False, _recado(r.stderr or r.stdout)

        r = _git("push", "origin", "HEAD", timeout=300)
        if r.returncode != 0:
            saida = (r.stderr or "") + (r.stdout or "")
            if "Authentication" in saida or "could not read" in saida.lower():
                return False, ("o GitHub recusou o acesso. Envie uma vez pelo VS Code "
                               "para o login ficar guardado.")
            return False, _recado(saida)

        return True, "planilhas enviadas. O GitHub vai publicar em uns 2 minutos."
    except subprocess.TimeoutExpired:
        return False, "o envio demorou demais. Tenta de novo na proxima alteracao."
    except Exception as erro:
        return False, "falha inesperada: %s" % erro


def gerar(motivo, enviar=False):
    print("\n[%s] %s" % (time.strftime("%H:%M:%S"), motivo))
    try:
        build.principal()
    except Exception as erro:
        print("  ERRO ao gerar: %s" % erro)
        print("  Confira se a planilha nao esta aberta no Excel e tente salvar de novo.")
        return

    if enviar and ENVIAR_PARA_O_GITHUB:
        print("  Enviando para o GitHub...")
        foi, recado = enviar_para_o_github()
        print("  %s %s" % ("OK -" if foi else "   -", recado))


def vigiar():
    anterior = retrato()
    while True:
        time.sleep(INTERVALO)
        atual = retrato()
        if atual == anterior:
            continue
        # espera parar de mudar: evita gerar no meio de uma copia de arquivo
        estavel = 0
        while estavel < 2:
            time.sleep(INTERVALO)
            novo = retrato()
            estavel = estavel + 1 if novo == atual else 0
            atual = novo
        anterior = atual
        gerar("Mudanca detectada, gerando o app de novo...", enviar=True)


def meu_ip():
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None


# ---------------------------------------------------------------------
#  ATUALIZAR A BASE PELO APP
#  O app manda as planilhas para ca. Elas esperam em dados/_recebidos ate
#  voce confirmar no app. Ao confirmar, as antigas do mesmo tipo e filiais
#  vao para dados/_substituidos/<data-hora> (nada e apagado) e as novas
#  entram em dados. A vigia percebe, monta o app e envia ao GitHub.
# ---------------------------------------------------------------------
PASTA_RECEBIDOS = os.path.join(PASTA_DADOS, "_recebidos")
PASTA_SUBSTITUIDOS = os.path.join(PASTA_DADOS, "_substituidos")
TAMANHO_MAXIMO = 80 * 1024 * 1024
TRAVA_ENVIO = threading.Lock()


def _lote_valido(lote):
    return bool(re.fullmatch(r"[A-Za-z0-9]{6,40}", lote or ""))


def _nome_valido(nome):
    nome = os.path.basename((nome or "").replace("\\", "/")).strip()
    if not nome or nome.startswith(("~$", ".")) or not nome.lower().endswith((".xlsx", ".xlsm", ".xls")):
        return ""
    return nome


def atuais_na_pasta():
    """Tipo e filiais das planilhas que estao hoje em dados (do ultimo build; le na hora o que for novo)."""
    conhecidos = {a["n"]: a for a in build.ARQUIVOS_LIDOS}
    return [conhecidos.get(os.path.basename(c)) or build.analisar_planilha(c) for c in build.achar_planilhas()]


def conferir_lote(lote):
    pasta = os.path.join(PASTA_RECEBIDOS, lote)
    novos, recusados = [], []
    for nome in sorted(os.listdir(pasta)) if os.path.isdir(pasta) else []:
        info = build.analisar_planilha(os.path.join(pasta, nome))
        (novos if info["t"] else recusados).append(info)
    plano = build.plano_de_troca(novos, atuais_na_pasta())
    plano["recusados"] = recusados
    return plano


def aplicar_lote(lote):
    plano = conferir_lote(lote)        # confere de novo: nao confia no que o app mandou
    if not plano["entram"]:
        return {"ok": False, "erro": "Nenhuma planilha reconhecida para entrar."}
    copia = os.path.join(PASTA_SUBSTITUIDOS, time.strftime("%Y-%m-%d_%H-%M-%S"))
    sairam = []
    for item in plano["saem"]:
        origem = os.path.join(PASTA_DADOS, item["n"])
        if os.path.exists(origem):
            os.makedirs(copia, exist_ok=True)
            shutil.move(origem, os.path.join(copia, item["n"]))
            sairam.append(item["n"])
    for item in plano["entram"]:
        destino = os.path.join(PASTA_DADOS, item["n"])
        if os.path.exists(destino):
            os.makedirs(copia, exist_ok=True)
            shutil.move(destino, os.path.join(copia, item["n"]))
        shutil.move(os.path.join(PASTA_RECEBIDOS, lote, item["n"]), destino)
        os.utime(destino, None)        # a mais nova fica por ultimo na leitura
    shutil.rmtree(os.path.join(PASTA_RECEBIDOS, lote), ignore_errors=True)
    print("\n[%s] Planilhas recebidas pelo app: %s" % (time.strftime("%H:%M:%S"),
                                                      ", ".join(i["n"] for i in plano["entram"])))
    if sairam:
        print("  Substituidas (guardadas em %s): %s" % (os.path.relpath(copia, RAIZ), ", ".join(sairam)))
    return {"ok": True, "entraram": [i["n"] for i in plano["entram"]], "sairam": sairam,
            "copia": os.path.relpath(copia, RAIZ) if sairam else "", "avisos": plano["avisos"],
            "recusados": [i["n"] for i in plano["recusados"]],
            "github": ENVIAR_PARA_O_GITHUB and os.path.isdir(os.path.join(RAIZ, ".git"))}


def limpar_recebidos_velhos():
    """Envios que ninguem confirmou ha mais de um dia."""
    if not os.path.isdir(PASTA_RECEBIDOS):
        return
    for nome in os.listdir(PASTA_RECEBIDOS):
        caminho = os.path.join(PASTA_RECEBIDOS, nome)
        try:
            if time.time() - os.path.getmtime(caminho) > 86400:
                shutil.rmtree(caminho, ignore_errors=True)
        except OSError:
            pass


class Servidor(http.server.SimpleHTTPRequestHandler):
    extensions_map = dict(http.server.SimpleHTTPRequestHandler.extensions_map,
                          **{".webmanifest": "application/manifest+json", ".js": "text/javascript"})
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PASTA_SAIDA, **kwargs)

    def _liberado(self):
        """Quando o app e gerado na propria pasta do projeto, so os arquivos
        do site sao servidos. Sem isso qualquer um na rede baixaria as
        planilhas e os arquivos do projeto."""
        if PASTA_SAIDA != RAIZ:
            return True
        alvo = urllib.parse.unquote(self.path.split("?")[0].split("#")[0]).strip("/")
        if alvo in ("", "index.html"):
            return True
        return alvo in build.ARQUIVOS_DO_SITE

    def _json(self, status, obj):
        corpo = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(corpo)))
        self.end_headers()
        self.wfile.write(corpo)

    def do_POST(self):
        u = urllib.parse.urlparse(self.path)
        rota = u.path.strip("/")
        q = urllib.parse.parse_qs(u.query)
        lote = (q.get("lote") or [""])[0]
        if rota not in ("base/receber", "base/conferir", "base/aplicar"):
            self.send_error(404, "Nao disponivel")
            return
        if not _lote_valido(lote):
            self._json(400, {"ok": False, "erro": "Envio invalido."})
            return
        try:
            if rota == "base/receber":
                nome = _nome_valido((q.get("nome") or [""])[0])
                tamanho = int(self.headers.get("Content-Length") or 0)
                if not nome:
                    self.close_connection = True
                    self._json(400, {"ok": False, "erro": "So planilhas do Excel (.xlsx, .xls, .xlsm)."})
                    return
                if tamanho <= 0 or tamanho > TAMANHO_MAXIMO:
                    self.close_connection = True
                    self._json(413, {"ok": False, "erro": "Arquivo vazio ou maior que 80 MB."})
                    return
                pasta = os.path.join(PASTA_RECEBIDOS, lote)
                os.makedirs(pasta, exist_ok=True)
                falta = tamanho
                with open(os.path.join(pasta, nome), "wb") as f:
                    while falta > 0:
                        pedaco = self.rfile.read(min(1 << 20, falta))
                        if not pedaco:
                            break
                        f.write(pedaco)
                        falta -= len(pedaco)
                self._json(200, {"ok": falta == 0, "nome": nome})
            elif rota == "base/conferir":
                with TRAVA_ENVIO:
                    self._json(200, dict(conferir_lote(lote), ok=True))
            else:
                with TRAVA_ENVIO:
                    self._json(200, aplicar_lote(lote))
        except Exception as erro:
            self._json(500, {"ok": False, "erro": "O servidor nao conseguiu processar: %s" % erro})

    def do_GET(self):
        if urllib.parse.urlparse(self.path).path.strip("/") == "base/status":
            self._json(200, {"ok": True, "arquivos": atuais_na_pasta(),
                             "github": ENVIAR_PARA_O_GITHUB and os.path.isdir(os.path.join(RAIZ, ".git"))})
            return
        if not self._liberado():
            self.send_error(404, "Nao disponivel")
            return
        super().do_GET()

    def do_HEAD(self):
        if not self._liberado():
            self.send_error(404, "Nao disponivel")
            return
        super().do_HEAD()

    def end_headers(self):
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def log_message(self, formato, *args):
        pass  # nao polui o terminal


class ServidorTCP(socketserver.ThreadingTCPServer):
    allow_reuse_address = True
    daemon_threads = True


def principal():
    build.desligar_selecao_no_console()
    os.makedirs(PASTA_DADOS, exist_ok=True)
    limpar_recebidos_velhos()
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

    if ENVIAR_PARA_O_GITHUB:
        print("")
        if os.path.isdir(os.path.join(RAIZ, ".git")):
            print("  Envio automatico para o GitHub: LIGADO")
        else:
            print("  Envio automatico: ligado, mas esta pasta ainda nao esta")
            print("  ligada a um repositorio. Publique uma vez pelo VS Code.")
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
