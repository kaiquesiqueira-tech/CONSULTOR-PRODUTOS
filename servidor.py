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
import urllib.request
import urllib.error
import json

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
#  GitHub ja feito uma vez (pelo VS Code ou pelo enviar.bat). Este
#  envio automatico nunca pergunta senha.
# ---------------------------------------------------------------------
ENVIAR_PARA_O_GITHUB = True

# ---------------------------------------------------------------------
#  JARVIS - assistente com IA
#
#  A chave da API fica SO neste computador, no arquivo jarvis_chave.txt
#  (ou na variavel de ambiente ANTHROPIC_API_KEY). Ela nunca vai para o
#  navegador nem para o GitHub: o servidor faz a ponte com a IA.
#
#  MODELO_JARVIS: o modelo usado. Troque aqui se quiser outro.
# ---------------------------------------------------------------------
MODELO_JARVIS = "claude-sonnet-5"
ARQUIVO_CHAVE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "jarvis_chave.txt")
URL_API = os.environ.get("JARVIS_URL_API", "https://api.anthropic.com/v1/messages")

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
        _git("reset", "-q", "--", "jarvis_chave.txt")   # a chave do Jarvis nunca sobe
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


def chave_jarvis():
    chave = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if chave:
        return chave
    try:
        with open(ARQUIVO_CHAVE, encoding="utf-8-sig") as f:
            for linha in f:
                linha = linha.strip()
                if linha and not linha.startswith("#"):
                    return linha
    except OSError:
        pass
    return ""


def _traduzir_erro(status, mensagem):
    if status == 401:
        return "A chave do Jarvis foi recusada. Confira o arquivo jarvis_chave.txt."
    if status == 403:
        return "A chave nao tem permissao para usar a API."
    if status == 404 and "model" in mensagem.lower():
        return "Modelo nao encontrado (%s). Troque MODELO_JARVIS no servidor.py." % MODELO_JARVIS
    if status == 429:
        return "Limite de uso da API atingido. Espere um pouco e tente de novo."
    if status in (500, 529) or "overloaded" in mensagem.lower():
        return "A API esta sobrecarregada agora. Tente de novo em instantes."
    if status == 400 and ("credit" in mensagem.lower() or "billing" in mensagem.lower()):
        return "A conta da API esta sem credito."
    return "A API respondeu com erro %s: %s" % (status, mensagem)


def perguntar_ao_claude(corpo):
    """Recebe system, messages e tools do navegador e repassa para a API.
    O navegador nao escolhe modelo, limite nem endereco: so a conversa."""
    chave = chave_jarvis()
    if not chave:
        return 503, {"erro": "O Jarvis esta sem chave. Crie o arquivo jarvis_chave.txt na pasta "
                             "do projeto, com a chave da API na primeira linha, e ligue o servidor de novo."}
    mensagens = corpo.get("messages")
    if not isinstance(mensagens, list) or not mensagens:
        return 400, {"erro": "Conversa vazia."}
    pedido = {
        "model": MODELO_JARVIS,
        "max_tokens": 1500,
        "system": str(corpo.get("system", ""))[:30000],
        "messages": mensagens,
    }
    if isinstance(corpo.get("tools"), list):
        pedido["tools"] = corpo["tools"]
    req = urllib.request.Request(
        URL_API, data=json.dumps(pedido).encode("utf-8"), method="POST",
        headers={"content-type": "application/json", "x-api-key": chave,
                 "anthropic-version": "2023-06-01"})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return 200, json.loads(r.read().decode("utf-8"))
    except urllib.error.HTTPError as erro:
        try:
            detalhe = json.loads(erro.read().decode("utf-8"))
            mensagem = (detalhe.get("error") or {}).get("message") or str(erro)
        except Exception:
            mensagem = str(erro)
        return erro.code, {"erro": _traduzir_erro(erro.code, mensagem)}
    except Exception as erro:
        return 502, {"erro": "Nao consegui falar com a API. Confira a internet deste computador. (%s)" % erro}


class Servidor(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=PASTA_SAIDA, **kwargs)

    def _liberado(self):
        """Quando o app e gerado na propria pasta do projeto, so os arquivos
        do site sao servidos. Sem isso qualquer um na rede baixaria as
        planilhas e o config.txt."""
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
        alvo = urllib.parse.unquote(self.path.split("?")[0]).strip("/")
        if alvo != "jarvis":
            self.send_error(404, "Nao disponivel")
            return
        try:
            tamanho = int(self.headers.get("Content-Length") or 0)
        except ValueError:
            tamanho = 0
        if tamanho <= 0 or tamanho > 3000000:
            self._json(413, {"erro": "Conversa grande demais. Comece uma nova conversa."})
            return
        try:
            corpo = json.loads(self.rfile.read(tamanho).decode("utf-8"))
        except Exception:
            self._json(400, {"erro": "Pedido invalido."})
            return
        status, resposta = perguntar_ao_claude(corpo)
        self._json(status, resposta)

    def do_GET(self):
        if urllib.parse.unquote(self.path.split("?")[0]).strip("/") == "jarvis/status":
            ok = bool(chave_jarvis())
            self._json(200, {"ok": ok, "modelo": MODELO_JARVIS,
                             "motivo": "" if ok else "sem chave"})
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
    print("")
    print("  Jarvis: %s" % ("ligado (%s)" % MODELO_JARVIS if chave_jarvis()
                             else "sem chave - crie o arquivo jarvis_chave.txt"))
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
