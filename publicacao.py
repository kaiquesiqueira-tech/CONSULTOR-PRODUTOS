# -*- coding: utf-8 -*-
"""
Envio automatico para o GitHub, sem ninguem clicar em nada.

Usado pelo servidor.py e pelo vigia.py. Nunca pergunta nada: se faltar
alguma coisa (login, repositorio), ele avisa e segue a vida, tentando de
novo na proxima alteracao.
"""

import os
import datetime
import subprocess

RAIZ = os.path.dirname(os.path.abspath(__file__))
CONFIG = os.path.join(RAIZ, "config.txt")

PADRAO = """# Configuracao da Consulta de Estoque
#
# publicar_automatico
#   sim = toda vez que as planilhas ou o app mudarem, envia para o GitHub
#         sozinho, sem perguntar nada
#   nao = nao envia nada (use o publicar.bat quando quiser)
#
# Antes de ligar, rode o publicar.bat UMA vez e faca o login do GitHub.
# Sem isso o envio automatico nao tem como entrar na sua conta.

# incluir_custos
#   sim = o app mostra custo unitario e valor em estoque
#   nao = o app sai sem nenhum custo e sem nenhum valor. Use isso se o
#         repositorio do GitHub for PUBLICO, para nao expor os precos
#         da empresa na internet.

publicar_automatico = nao
incluir_custos = sim
"""


def _garantir_config():
    if not os.path.exists(CONFIG):
        with open(CONFIG, "w", encoding="utf-8") as f:
            f.write(PADRAO)


def config(chave, padrao=""):
    _garantir_config()
    try:
        with open(CONFIG, encoding="utf-8") as f:
            for linha in f:
                linha = linha.split("#")[0].strip()
                if "=" in linha:
                    k, v = linha.split("=", 1)
                    if k.strip().lower() == chave:
                        return v.strip()
    except OSError:
        pass
    return padrao


def ligado():
    return config("publicar_automatico", "nao").lower() in ("sim", "s", "yes", "1", "true")


def definir(chave, valor):
    _garantir_config()
    with open(CONFIG, encoding="utf-8") as f:
        linhas = f.readlines()
    achou = False
    for i, linha in enumerate(linhas):
        if linha.split("#")[0].strip().lower().startswith(chave + " ") or \
           linha.split("#")[0].strip().lower().startswith(chave + "="):
            linhas[i] = "%s = %s\n" % (chave, valor)
            achou = True
            break
    if not achou:
        linhas.append("%s = %s\n" % (chave, valor))
    with open(CONFIG, "w", encoding="utf-8") as f:
        f.writelines(linhas)


def _git(*args, **kwargs):
    ambiente = dict(os.environ)
    ambiente["GIT_TERMINAL_PROMPT"] = "0"   # nunca trava esperando senha
    ambiente["GCM_INTERACTIVE"] = "never"
    return subprocess.run(
        ["git"] + list(args), cwd=RAIZ, capture_output=True, text=True,
        env=ambiente, timeout=kwargs.get("timeout", 120),
    )


def _primeira_linha(texto):
    for linha in (texto or "").splitlines():
        if linha.strip():
            return linha.strip()
    return ""


def publicar(mensagem=None):
    """Envia o estado atual da pasta. Devolve (enviou, recado)."""
    try:
        if _git("--version").returncode != 0:
            return False, "Git nao encontrado neste computador."
    except (OSError, subprocess.SubprocessError):
        return False, "Git nao encontrado neste computador."

    if not os.path.isdir(os.path.join(RAIZ, ".git")):
        return False, "Este projeto ainda nao foi ligado ao GitHub. Rode o publicar.bat uma vez."

    if _git("remote", "get-url", "origin").returncode != 0:
        return False, "Nenhum repositorio configurado. Rode o publicar.bat uma vez."

    if _git("config", "user.name").returncode != 0:
        return False, "Falta configurar seu nome no Git. Rode o publicar.bat uma vez."

    try:
        if _git("add", "-A").returncode != 0:
            return False, "Nao consegui preparar os arquivos."

        if _git("diff", "--cached", "--quiet").returncode == 0:
            return False, "Nada mudou, nada a enviar."

        if mensagem is None:
            mensagem = "Atualizacao automatica de " + datetime.datetime.now().strftime("%d/%m/%Y %H:%M")

        r = _git("commit", "-m", mensagem)
        if r.returncode != 0:
            return False, "Nao consegui registrar a versao: " + _primeira_linha(r.stderr or r.stdout)

        r = _git("push", "origin", "HEAD", timeout=300)
        if r.returncode != 0:
            erro = _primeira_linha(r.stderr or r.stdout)
            if "Authentication" in (r.stderr or "") or "could not read" in (r.stderr or "").lower():
                erro = "o GitHub recusou o acesso. Rode o publicar.bat uma vez e faca o login."
            return False, "Versao registrada aqui, mas o envio falhou: " + erro

        return True, "Enviado para o GitHub."

    except subprocess.TimeoutExpired:
        return False, "O envio demorou demais e foi interrompido. Tenta de novo na proxima alteracao."
    except (OSError, subprocess.SubprocessError) as erro:
        return False, "Falha inesperada no envio: %s" % erro
