# -*- coding: utf-8 -*-
"""
Verifica por que o GitHub nao esta gerando o app.

Olha o repositorio local e aponta o que falta. Nao muda nada sem
perguntar antes.

Uso:  python verificar.py
"""

import os
import sys
import subprocess

RAIZ = os.path.dirname(os.path.abspath(__file__))
WORKFLOW = ".github/workflows/publicar.yml"


def git(*args):
    try:
        # quotepath=false para nomes com acento aparecerem certos
        return subprocess.run(["git", "-c", "core.quotepath=false"] + list(args),
                              cwd=RAIZ, capture_output=True, text=True, timeout=30)
    except Exception:
        return None


def ok(texto):
    print("  [ok]    %s" % texto)


def erro(texto):
    print("  [ERRO]  %s" % texto)


def principal():
    print("")
    print("=" * 64)
    print("  Por que o GitHub nao esta gerando o app")
    print("=" * 64)
    print("")

    problemas = []

    # 1. git existe?
    r = git("--version")
    if r is None or r.returncode != 0:
        erro("O Git nao esta instalado.")
        print("\n  Baixe em https://git-scm.com/download/win e rode de novo.\n")
        return 1

    if not os.path.isdir(os.path.join(RAIZ, ".git")):
        erro("Esta pasta nao e um repositorio.")
        print("\n  No VS Code: painel Controle do Codigo-Fonte > Publicar no GitHub.\n")
        return 1
    ok("Esta pasta e um repositorio Git.")

    # 2. remoto
    r = git("remote", "get-url", "origin")
    if r.returncode != 0:
        erro("Nenhum repositorio do GitHub ligado a esta pasta.")
        problemas.append("Ligue o repositorio pelo VS Code, em Publicar no GitHub.")
    else:
        ok("Ligado a: %s" % r.stdout.strip())

    # 3. branch
    r = git("rev-parse", "--abbrev-ref", "HEAD")
    branch = r.stdout.strip() if r and r.returncode == 0 else "?"
    if branch in ("main", "master"):
        ok("Branch atual: %s" % branch)
    else:
        erro("Branch atual: %s" % branch)
        problemas.append("A receita do GitHub so roda nos branches 'main' e 'master'.\n"
                         "     Voce esta em '%s', por isso nada acontece.\n"
                         "     Renomeie com:  git branch -M main" % branch)

    # 4. workflow no disco e dentro do repositorio
    if not os.path.isfile(os.path.join(RAIZ, WORKFLOW)):
        erro("O arquivo %s nao existe nesta pasta." % WORKFLOW)
        problemas.append("A pasta '.github' comeca com ponto e fica escondida no Windows.\n"
                         "     Ao copiar os arquivos, ela costuma ficar para tras.\n"
                         "     Copie a pasta '.github' do zip para ca.")
    else:
        r = git("ls-files", "--error-unmatch", WORKFLOW)
        if r.returncode == 0:
            ok("A receita do GitHub esta no repositorio.")
        else:
            erro("A receita existe aqui, mas nunca foi enviada.")
            problemas.append("Confirme e envie o arquivo %s.\n"
                             "     Ele deve aparecer no painel do VS Code." % WORKFLOW)

    # 5. planilhas versionadas
    r = git("ls-files", "dados/")
    planilhas = [l for l in (r.stdout or "").splitlines() if l.lower().endswith((".xlsx", ".xls"))]
    if planilhas:
        ok("%d planilha(s) no repositorio:" % len(planilhas))
        for p in planilhas:
            print("            %s" % p)
    else:
        erro("Nenhuma planilha no repositorio.")
        problemas.append("As planilhas estao na pasta 'dados' mas nunca foram enviadas.\n"
                         "     Sem elas o GitHub nao tem o que ler.")

    # 6. index.html nao pode estar versionado
    r = git("ls-files", "--error-unmatch", "index.html")
    index_versionado = r is not None and r.returncode == 0
    if index_versionado:
        erro("O 'index.html' ainda esta sendo versionado.")
        problemas.append("ESTE E O CULPADO MAIS COMUM.\n"
                         "     O app agora e gerado pelo GitHub, entao o index.html nao deve\n"
                         "     ir junto. Como ele foi enviado numa versao anterior, o Git\n"
                         "     continua carregando o arquivo velho e o site mostra ele.\n"
                         "     A correcao esta no fim deste relatorio.")
    else:
        ok("O 'index.html' nao e versionado, correto.")

    # 7. pendencias
    r = git("status", "--porcelain")
    pendentes = [l for l in (r.stdout or "").splitlines() if l.strip()]
    if pendentes:
        erro("%d arquivo(s) alterados que ainda nao foram enviados:" % len(pendentes))
        for l in pendentes[:8]:
            print("            %s" % l.strip())
        problemas.append("Confirme essas mudancas no painel do VS Code.")
    else:
        ok("Nada pendente aqui.")

    r = git("log", "origin/%s..HEAD" % branch, "--oneline")
    if r and r.returncode == 0 and r.stdout.strip():
        n = len(r.stdout.strip().splitlines())
        erro("%d versao(oes) confirmadas mas nao enviadas." % n)
        problemas.append("Clique em Sincronizar no VS Code, ou rode:  git push")

    # ---------------- resumo ----------------
    print("")
    print("=" * 64)
    if not problemas:
        print("  Do lado de ca esta tudo certo.")
        print("=" * 64)
        print("")
        print("  Entao o problema esta na configuracao do site. Confira, nesta ordem:")
        print("")
        print("  1. Aba ACTIONS do seu repositorio no GitHub.")
        print("     Sem nenhuma execucao listada = a receita nao chegou la.")
        print("     Bolinha vermelha = clique nela e leia onde parou.")
        print("")
        print("  2. Settings > Pages > Source.")
        print("     Tem que estar em 'GitHub Actions'.")
        print("     Se estiver em 'Deploy from a branch', o site serve os arquivos")
        print("     crus do repositorio e nunca vai mostrar o app gerado.")
        print("")
        print("  3. Se o repositorio for privado, o GitHub Pages exige plano pago.")
        print("     Nesse caso o Actions gera o app mas a publicacao falha.")
    else:
        print("  O QUE PRECISA SER RESOLVIDO")
        print("=" * 64)
        for i, p in enumerate(problemas, 1):
            print("")
            print("  %d. %s" % (i, p))

    if index_versionado:
        print("")
        print("=" * 64)
        print("  CORRECAO DO index.html")
        print("=" * 64)
        print("")
        print("  Isso tira o arquivo do repositorio SEM apagar ele do seu computador.")
        resposta = input("  Fazer isso agora? (s/n): ").strip().lower()
        if resposta == "s":
            for arquivo in ("index.html", "versao.txt"):
                git("rm", "--cached", "-q", arquivo)
            print("")
            print("  Feito. Agora confirme e envie pelo painel do VS Code.")
            print("  Os dois arquivos vao aparecer como apagados (D) - e o esperado:")
            print("  eles saem do GitHub e continuam aqui na sua pasta.")
        else:
            print("")
            print("  Para fazer depois, rode nesta pasta:")
            print("    git rm --cached index.html versao.txt")
    print("")
    return 0


if __name__ == "__main__":
    sys.exit(principal())
