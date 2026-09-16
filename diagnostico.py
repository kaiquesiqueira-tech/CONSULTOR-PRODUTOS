# -*- coding: utf-8 -*-
"""
Diagnostico: mostra o estado real de tudo, para achar por que o app
nao esta mostrando o que voce espera.

Uso:  python diagnostico.py
"""

import os
import re
import sys
import json
import datetime
import subprocess

RAIZ = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, RAIZ)


def titulo(texto):
    print("")
    print(texto)
    print("-" * 62)


def quando(caminho):
    try:
        return datetime.datetime.fromtimestamp(os.path.getmtime(caminho)).strftime("%d/%m/%Y %H:%M")
    except OSError:
        return "?"


def tamanho(caminho):
    try:
        n = os.path.getsize(caminho)
        return "%.1f MB" % (n / 1e6) if n > 1e6 else "%d KB" % (n // 1024)
    except OSError:
        return "?"


def ler_base(caminho):
    """Puxa so os campos de identificacao de dentro do app gerado."""
    try:
        with open(caminho, encoding="utf-8") as f:
            html = f.read()
        bloco = re.search(r'<script type="application/json" id="dados">(.*?)</script>', html, re.S)
        if not bloco:
            return None
        d = json.loads(bloco.group(1))
        itens = sum(1 for a in d.get("ativos", []) for r in a["r"] if r[1] > 0)
        return {
            "marca": d.get("marca", "?"),
            "gerado": d.get("gerado", "?"),
            "filiais": ", ".join(d.get("filiais", [])),
            "itens": itens,
            "custos": "nao" if d.get("semCustos") else "sim",
        }
    except Exception as erro:
        return {"erro": str(erro)}


def git(*args):
    try:
        return subprocess.run(["git"] + list(args), cwd=RAIZ, capture_output=True,
                              text=True, timeout=30)
    except Exception:
        return None


def principal():
    print("")
    print("=" * 62)
    print("  DIAGNOSTICO - Consulta de Estoque")
    print("  %s" % datetime.datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
    print("=" * 62)
    problemas = []

    # ---------------- planilhas ----------------
    titulo("1. Planilhas na pasta 'dados'")
    try:
        import build
        arquivos = build.achar_planilhas()
    except Exception as erro:
        arquivos = []
        problemas.append("Nao consegui ler a pasta 'dados': %s" % erro)

    if not arquivos:
        print("  NENHUMA planilha encontrada.")
        problemas.append("A pasta 'dados' esta vazia. E dali que o app tira tudo.")
    else:
        tipos = {}
        for caminho in arquivos:
            try:
                tipo, df, erro = build.ler_planilha(caminho)
            except Exception as e:
                tipo, df, erro = None, None, str(e)
            rotulo = {"SB2": "saldo fisico", "SBF": "por endereco"}.get(tipo, "IGNORADO")
            tipos.setdefault(rotulo, []).append(os.path.basename(caminho))
            print("  %-34s %-13s %8s  %s" % (
                os.path.basename(caminho)[:34], rotulo, tamanho(caminho), quando(caminho)))
            if tipo is None:
                print("      motivo: %s" % erro)
                problemas.append("O arquivo '%s' nao foi reconhecido: %s"
                                 % (os.path.basename(caminho), erro))
        if len(tipos.get("saldo fisico", [])) > 2:
            problemas.append("Ha %d arquivos de saldo fisico. Se forem exportacoes da mesma\n"
                             "  filial, apague as antigas." % len(tipos["saldo fisico"]))
        if "por endereco" not in tipos:
            problemas.append("Nenhum saldo por endereco na pasta. Sem ele o app nao mostra "
                             "onde o produto esta.")

    # ---------------- app gerado ----------------
    titulo("2. App gerado")
    try:
        saida = build.pasta_saida()
    except Exception:
        saida = RAIZ
    gerado = os.path.join(saida, "index.html")
    rotulo = "index.html (na pasta do projeto)" if saida == RAIZ else \
             os.path.basename(saida) + "/index.html"
    if not os.path.exists(gerado):
        print("  %s NAO EXISTE." % rotulo)
        problemas.append("O app nunca foi gerado. Rode o iniciar.bat ou 'python build.py'.")
    else:
        print("  %s   %s   gerado em %s" % (rotulo, tamanho(gerado), quando(gerado)))
        info = ler_base(gerado)
        if info and "erro" not in info:
            print("  marca da versao ... %s" % info["marca"])
            print("  data da base ...... %s" % info["gerado"])
            print("  filiais ........... %s" % info["filiais"])
            print("  itens com saldo ... %d" % info["itens"])
            print("  custos na base .... %s" % info["custos"])
        else:
            problemas.append("Nao consegui ler os dados de dentro do app gerado.")

        # o app esta mais velho que as planilhas?
        if arquivos:
            mais_nova = max(os.path.getmtime(a) for a in arquivos)
            if mais_nova > os.path.getmtime(gerado) + 5:
                problemas.append("As planilhas sao MAIS NOVAS que o app gerado. Ou seja: voce\n"
                                 "  trocou os arquivos mas o app nao foi gerado depois disso.\n"
                                 "  Rode o iniciar.bat, ou clique em publicar.bat, ou ligue o vigia.")

    # ---------------- pasta antiga ----------------
    for nome in ("dist", "docs", "site", "publico"):
        antiga = os.path.join(RAIZ, nome)
        alvo = os.path.join(antiga, "index.html")
        if antiga != saida and os.path.isfile(alvo):
            titulo("3. Sobra de versao antiga")
            info = ler_base(alvo)
            print("  %s/index.html existe, de %s, marca %s"
                  % (nome, quando(alvo), (info or {}).get("marca", "?")))
            problemas.append("Sobrou uma pasta '%s' com um app antigo dentro. Se algum\n"
                             "  atalho, link ou o GitHub Pages apontar para ela, voce ve dados\n"
                             "  velhos. Pode apagar a pasta '%s'." % (nome, nome))

    # ---------------- configuracao ----------------
    titulo("4. Configuracao")
    try:
        import publicacao
        print("  publicar_automatico ... %s" % publicacao.config("publicar_automatico", "nao"))
        print("  incluir_custos ........ %s" % publicacao.config("incluir_custos", "sim"))
        print("  pasta_do_site ......... %s" % publicacao.config("pasta_do_site", "raiz"))
    except Exception as erro:
        print("  nao consegui ler o config.txt: %s" % erro)

    # ---------------- github ----------------
    titulo("5. GitHub")
    if not os.path.isdir(os.path.join(RAIZ, ".git")):
        print("  Este projeto nao esta ligado a nenhum repositorio.")
    else:
        r = git("remote", "get-url", "origin")
        print("  repositorio ....... %s" % (r.stdout.strip() if r and r.returncode == 0 else "nenhum"))
        r = git("log", "-1", "--format=%cd | %s", "--date=format:%d/%m/%Y %H:%M")
        if r and r.returncode == 0 and r.stdout.strip():
            print("  ultimo commit ..... %s" % r.stdout.strip())
        r = git("status", "--porcelain")
        if r and r.returncode == 0:
            pendentes = [l for l in r.stdout.splitlines() if l.strip()]
            if pendentes:
                print("  NAO enviado ....... %d arquivo(s) alterados aqui" % len(pendentes))
                for linha in pendentes[:6]:
                    print("                      %s" % linha.strip())
                problemas.append("Ha alteracoes que ainda nao foram para o GitHub.\n"
                                 "  Rode o publicar.bat.")
            else:
                print("  pendencias ........ nenhuma, tudo enviado")
        r = git("log", "origin/main..HEAD", "--oneline")
        if r and r.returncode == 0 and r.stdout.strip():
            n = len(r.stdout.strip().splitlines())
            print("  commits presos ..... %d ainda nao subiram" % n)
            problemas.append("%d versao(oes) registradas aqui mas nao enviadas ao GitHub." % n)

    # ---------------- vigia ----------------
    titulo("6. Vigia (publicacao automatica)")
    log = os.path.join(RAIZ, "vigia.log")
    if not os.path.exists(log):
        print("  Nunca rodou (nao ha vigia.log).")
    else:
        print("  ultima anotacao em %s. Ultimas linhas:" % quando(log))
        try:
            with open(log, encoding="utf-8", errors="replace") as f:
                for linha in f.readlines()[-8:]:
                    print("    %s" % linha.rstrip())
        except OSError:
            pass

    # ---------------- resumo ----------------
    print("")
    print("=" * 62)
    if problemas:
        print("  O QUE PRECISA DE ATENCAO")
        print("=" * 62)
        for i, p in enumerate(problemas, 1):
            print("")
            print("  %d. %s" % (i, p))
    else:
        print("  Nada fora do lugar.")
        print("=" * 62)
        print("")
        print("  Se mesmo assim o app mostra dados velhos, e cache do navegador.")
        print("  Compare a marca da versao mostrada aqui com a que aparece no")
        print("  canto de cima do app. Se forem diferentes, recarregue a pagina")
        print("  segurando Ctrl e clicando no botao de recarregar.")
    print("")
    return 0


if __name__ == "__main__":
    sys.exit(principal())
