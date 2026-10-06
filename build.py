# -*- coding: utf-8 -*-
"""
Gera o app de consulta de estoque a partir das planilhas da pasta 'dados'.

Coloque na pasta 'dados' os arquivos exportados do sistema:
  - SALDO FISICO (tabela SB2)        -> pode ser mais de um arquivo
  - SALDO POR ENDERECO (tabela SBF)  -> pode ser mais de um arquivo

O tipo de cada arquivo e descoberto automaticamente pelas colunas,
entao o nome do arquivo nao importa.

Uso:  python build.py                 -> gera o index.html aqui na pasta
      python build.py --saida site    -> gera dentro da pasta 'site'

O segundo jeito e o que o GitHub usa para montar o app sozinho.
"""

import os
import re
import sys
import glob
import json
import hashlib
import datetime

try:
    import pandas as pd
    import numpy as np
except ImportError:
    print("Faltam bibliotecas. Rode:  pip install -r requirements.txt")
    sys.exit(1)

# O leitor 'calamine' e cerca de 4x mais rapido. Se nao estiver instalado,
# o pandas usa o openpyxl normalmente.
try:
    import python_calamine  # noqa: F401
    LEITOR = "calamine"
except ImportError:
    LEITOR = None


def ler_excel(caminho, **extras):
    if LEITOR:
        try:
            return pd.read_excel(caminho, engine=LEITOR, **extras)
        except Exception:
            pass
    return pd.read_excel(caminho, **extras)


AVISOS = []

RAIZ = os.path.dirname(os.path.abspath(__file__))
PASTA_DADOS = os.path.join(RAIZ, "dados")
# ---------------------------------------------------------------------
#  UNICA COISA QUE VOCE PODE QUERER MUDAR AQUI
#
#  INCLUIR_CUSTOS
#     True  = o app mostra custo unitario e valor em estoque
#     False = o app sai sem nenhum custo e sem nenhum valor
# ---------------------------------------------------------------------
INCLUIR_CUSTOS = True

# ---------------------------------------------------------------------
#  GEMINI (opcional) - pesquisa na internet para "para que serve" e
#  "onde e aplicado". A chave vem da variavel GEMINI_API_KEY (e assim
#  que o GitHub passa o segredo) ou do arquivo gemini_chave.txt aqui na
#  pasta, que nunca vai para o GitHub. Sem chave, o Jarvis responde so
#  com a base.
#
#  GEMINI_MODELOS: tentados nessa ordem; o primeiro que existir e usado.
# ---------------------------------------------------------------------
GEMINI_MODELOS = ["gemini-flash-latest", "gemini-2.5-flash", "gemini-2.0-flash"]


def chave_gemini():
    chave = os.environ.get("GEMINI_API_KEY", "").strip()
    if chave:
        return chave
    try:
        with open(os.path.join(RAIZ, "gemini_chave.txt"), encoding="utf-8-sig") as f:
            for linha in f:
                linha = linha.strip()
                if linha and not linha.startswith("#"):
                    return linha
    except OSError:
        pass
    return ""

# arquivos que o build cria. O servidor so entrega estes, para ninguem
# na rede baixar as planilhas ou os scripts pelo navegador.
ARQUIVOS_DO_SITE = ("index.html", "versao.txt")

PASTAS_ANTIGAS = ("dist", "docs", "app", "publico")
EPOCA = datetime.date(2000, 1, 1)


# --------------------------------------------------------------------------
# leitura das planilhas
# --------------------------------------------------------------------------
def achar_planilhas():
    # nao usa glob: no servidor do GitHub (Linux) ele diferencia .xlsx de .XLSX
    if not os.path.isdir(PASTA_DADOS):
        return []
    arquivos = [os.path.join(PASTA_DADOS, n) for n in os.listdir(PASTA_DADOS)
                if n.lower().endswith((".xlsx", ".xlsm", ".xls")) and not n.startswith("~$")]
    return sorted(arquivos, key=lambda a: (os.path.getmtime(a), a))


def ler_planilha(caminho):
    """Descobre em que linha esta o cabecalho e qual e o tipo do arquivo."""
    try:
        topo = ler_excel(caminho, header=None, nrows=15, dtype=object)
    except Exception as erro:
        return None, None, "nao foi possivel abrir (%s)" % erro

    linha_cab = None
    for i in range(len(topo)):
        valores = [str(v).strip() for v in topo.iloc[i].tolist() if not pd.isna(v)]
        if "Filial" in valores and ("Produto" in valores or "Codigo" in valores):
            linha_cab = i
            break
    if linha_cab is None:
        return None, None, "nao achei o cabecalho (linha com 'Filial' e 'Produto')"

    df = ler_excel(caminho, header=linha_cab)
    df.columns = [str(c).strip() for c in df.columns]
    colunas = set(df.columns)

    if {"Endereco", "Prioridade", "Quantidade"} <= colunas:
        return "SBF", df, None
    if {"Saldo Atual", "Nome Cientif"} <= colunas:
        return "SB2", df, None
    if {"Qtd Original", "Saldo", "Documento"} <= colunas:
        return "SDA", df, None
    if {"Contr.Endere", "Codigo"} <= colunas:
        return "SBZ", df.rename(columns={"Codigo": "Produto"}), None
    if {"TP Movimento", "Endereco", "Quantidade"} <= colunas:
        return "SD3", df, None
    if {"TP Movimento", "Qtd. Saida"} <= colunas:
        return "SD3R", df, None
    return None, None, "colunas nao reconhecidas"


# --------------------------------------------------------------------------
# conversoes
# --------------------------------------------------------------------------
def chave(valor, largura):
    if pd.isna(valor):
        return ""
    if isinstance(valor, float) and float(valor).is_integer():
        valor = int(valor)
    return str(valor).strip().zfill(largura)


def numero(valor):
    """Converte para numero aceitando o formato brasileiro.

    O Protheus as vezes exporta quantidade como texto ('7,9', '1.234,50').
    Sem isso, float() falha nesses casos e o valor viraria zero calado."""
    if valor is None:
        return 0.0
    if isinstance(valor, (int, float, np.integer, np.floating)):
        f = float(valor)
        return 0.0 if np.isnan(f) else round(f, 3)
    texto = str(valor).strip().replace("\u00a0", "")
    if not texto or texto.lower() == "nan":
        return 0.0
    if "," in texto:                                   # 1.234,50 -> 1234.50
        texto = texto.replace(".", "").replace(",", ".")
    elif re.fullmatch(r"-?\d{1,3}(\.\d{3})+", texto):  # 1.234 -> 1234
        texto = texto.replace(".", "")
    try:
        return round(float(texto), 3)
    except ValueError:
        return 0.0


def dia(valor):
    if pd.isna(valor):
        return 0
    try:
        d = pd.to_datetime(valor).date()
    except Exception:
        return 0
    if d.year < 2000 or d.year > 2100:
        return 0
    return (d - EPOCA).days


def coluna(df, nome):
    """Devolve a coluna se existir; senao, uma coluna de zeros."""
    if nome in df.columns:
        return df[nome]
    return pd.Series([0] * len(df), index=df.index)


# --------------------------------------------------------------------------
# montagem da base
# --------------------------------------------------------------------------
def montar(sb2, sbf, sda=None, sd3=None, sbz=None):
    for df in (sb2, sbf, sda, sd3, sbz):
        if df is None or df.empty:
            continue
        df["F"] = df["Filial"].apply(lambda v: chave(v, 6))
        df["P"] = df["Produto"].apply(lambda v: chave(v, 9))
        df["A"] = df["Armazem"].apply(lambda v: chave(v, 2)) if "Armazem" in df.columns else ""

    if sb2 is not None and not sb2.empty:
        sb2 = sb2[sb2["P"] != ""]
        repetidas = sb2.duplicated(subset=["F", "P", "A"], keep="last").sum()
        if repetidas:
            sb2 = sb2[~sb2.duplicated(subset=["F", "P", "A"], keep="last")]
            AVISOS.append(
                "%d linhas repetidas no saldo fisico foram descartadas. Isso acontece\n"
                "  quando ha exportacoes sobrepostas na pasta 'dados'. Valeu a do arquivo\n"
                "  mais recente. Apague as antigas para nao correr risco." % repetidas)

    if sbf is not None and not sbf.empty:
        sbf = sbf[sbf["P"] != ""]
        chave_sbf = [c for c in ["F", "P", "A", "Endereco", "Lote", "Sub-Lote", "Num de Serie"]
                     if c in sbf.columns]
        repetidas = sbf.duplicated(subset=chave_sbf, keep="last").sum()
        if repetidas:
            sbf = sbf[~sbf.duplicated(subset=chave_sbf, keep="last")]
            AVISOS.append(
                "%d linhas repetidas no saldo por endereco foram descartadas.\n"
                "  Apague as exportacoes antigas da pasta 'dados'." % repetidas)

    # enderecos agrupados por filial + produto + armazem
    mapa_end = {}
    if sbf is not None and not sbf.empty:
        for _, r in sbf.iterrows():
            k = (r["F"], r["P"], r["A"])
            e = "" if pd.isna(r["Endereco"]) else str(r["Endereco"]).strip()
            if e in ("", "nan", "0"):
                e = "SEM ENDERECO"
            atual = mapa_end.setdefault(k, {}).setdefault(e, [0.0, 0.0, 0])
            atual[0] += numero(r["Quantidade"])
            atual[1] += numero(r.get("Empenho", 0))
            atual[2] = max(atual[2], dia(r["Dt Invent"]) if "Dt Invent" in sbf.columns else 0)

    filiais = set()
    if sb2 is not None and not sb2.empty:
        filiais |= set(sb2["F"])
    if sbf is not None and not sbf.empty:
        filiais |= set(sbf["F"])
    if sda is not None and not sda.empty:
        filiais |= set(sda["F"])
    if sd3 is not None and not sd3.empty:
        filiais |= set(sd3["F"])
    filiais = sorted(f for f in filiais if f)
    idx_filial = {f: i for i, f in enumerate(filiais)}

    textos, idx_texto = [], {}

    def ref(texto):
        if texto not in idx_texto:
            idx_texto[texto] = len(textos)
            textos.append(texto)
        return idx_texto[texto]

    itens = {}

    if sb2 is not None and not sb2.empty:
        for _, r in sb2.iterrows():
            k = (r["F"], r["P"])
            desc = "" if pd.isna(r["Nome Cientif"]) else str(r["Nome Cientif"]).strip()
            it = itens.setdefault(k, {"f": idx_filial[r["F"]], "c": r["P"], "d": "", "r": []})
            if len(desc) > len(it["d"]):
                it["d"] = desc
            ends = mapa_end.pop((r["F"], r["P"], r["A"]), {})
            it["r"].append([
                r["A"],
                numero(r["Saldo Atual"]),
                numero(r.get("Empenho", 0)),
                numero(r.get("C Unitario", 0)),
                numero(r.get("Qtd.Prevista", 0)),
                numero(r.get("Qtd.a Endere", 0)),
                dia(r.get("DT.Ult.Saida")),
                dia(r.get("Dt Movimento")),
                dia(r.get("Dt.Invent.")),
                [[e, round(v[0], 3), round(v[1], 3)] for e, v in sorted(ends.items())],
            ])

    # enderecos de produtos que nao aparecem no saldo fisico
    for (f, p, a), ends in mapa_end.items():
        it = itens.setdefault((f, p), {"f": idx_filial[f], "c": p, "d": "", "r": []})
        it["r"].append([a, 0, 0, 0, 0, 0, 0, 0, 0,
                        [[e, round(v[0], 3), round(v[1], 3)] for e, v in sorted(ends.items())]])

    # SBZ: indicador por filial. 1 = controla endereco, 0 = nao controla.
    # Produto fora da SBZ fica sem a chave: o indicador dele mora no SB1.
    controla = {}
    if sbz is not None and not sbz.empty:
        for _, r in sbz[sbz["P"] != ""].iterrows():
            v = "" if pd.isna(r.get("Contr.Endere")) else str(r.get("Contr.Endere")).strip().lower()
            if v in ("sim", "s"):
                controla[(r["F"], r["P"])] = 1
            elif v in ("nao", "não", "n"):
                controla[(r["F"], r["P"])] = 0
    for (f, p), it in itens.items():
        if (f, p) in controla:
            it["e"] = controla[(f, p)]

    ativos, zerados = [], []
    for it in itens.values():
        linhas = [r for r in it["r"] if r[1] or r[2] or r[4] or r[5] or r[9]]
        if linhas:
            it["r"] = linhas
            it["d"] = ref(it["d"])
            ativos.append(it)
        else:
            ultima = max([r[6] for r in it["r"]] + [0]) or max([r[7] for r in it["r"]] + [0])
            z = [it["f"], it["c"], ref(it["d"]), ultima]
            if "e" in it:
                z.append(it["e"])
            zerados.append(z)

    # descricao vem so da coluna "Nome Cientif" do saldo fisico. Se ela vier vazia
    # em boa parte das linhas, a exportacao saiu com problema: avisa em vez de publicar calado.
    com_saldo = [a for a in ativos if sum(r[1] for r in a["r"]) > 0]
    sem_desc = [a for a in com_saldo if not textos[a["d"]].strip()]
    if com_saldo and len(sem_desc) > max(20, 0.05 * len(com_saldo)):
        exemplo = ", ".join(a["c"] for a in sem_desc[:3])
        AVISOS.append(
            "%d de %d produtos com saldo vieram SEM DESCRICAO na planilha de saldo\n"
            "  fisico (coluna 'Nome Cientif'). Exemplos: %s.\n"
            "  Abra a planilha e confira essa coluna antes de publicar: se ela veio\n"
            "  vazia ou com descricao trocada, exporte de novo." % (len(sem_desc), len(com_saldo), exemplo))

    ativos.sort(key=lambda x: (x["f"], x["c"]))
    zerados.sort(key=lambda x: (x[0], x[1]))

    fil_sb2 = set(sb2["F"]) if (sb2 is not None and not sb2.empty) else set()
    sem_sb2 = [f for f in filiais if f not in fil_sb2]

    if not INCLUIR_CUSTOS:
        for it in ativos:
            for r in it["r"]:
                r[3] = 0.0

    pendentes = []
    if sda is not None and not sda.empty:
        sda = sda[sda["P"] != ""].copy()
        sda["_doc"] = sda["Documento"].apply(lambda v: chave(v, 9))
        sda["_saldo"] = sda["Saldo"].apply(numero)
        sda["_ori"] = sda["Qtd Original"].apply(numero)
        sda["_dia"] = sda["Data"].apply(dia) if "Data" in sda.columns else 0

        # a mesma linha repetida por inteiro e colagem duplicada, nao duas linhas da nota
        chave_sda = ["F", "P", "A", "_doc", "_saldo", "_ori", "_dia"]
        repetidas = sda.duplicated(subset=chave_sda, keep="first").sum()
        if repetidas:
            sda = sda[~sda.duplicated(subset=chave_sda, keep="first")]
            AVISOS.append(
                "%d linhas repetidas por inteiro nos pendentes foram descartadas.\n"
                "  Parece a mesma lista colada duas vezes. Confira a exportacao." % repetidas)

        for _, r in sda.iterrows():
            if r["_saldo"] <= 0:
                continue
            desc = "" if pd.isna(r.get("Descricao")) else str(r.get("Descricao")).strip()
            if not desc:
                it = itens.get((r["F"], r["P"]))
                if it is not None and isinstance(it.get("d"), str):
                    desc = it["d"]
            origem = "" if pd.isna(r.get("Origem Mov")) else str(r.get("Origem Mov")).strip()
            pendentes.append([idx_filial[r["F"]], r["P"], ref(desc), r["A"],
                              r["_saldo"], r["_ori"], r["_doc"], r["_dia"], origem])
        pendentes.sort(key=lambda x: (x[7] or 99999, x[6], x[1]))

    def desc_do_item(f, p):
        it = itens.get((f, p))
        if not it:
            return ""
        d = it.get("d")
        return textos[d] if isinstance(d, int) else (d or "")

    def texto(r, *nomes):
        for n in nomes:
            if n in r.index and not pd.isna(r[n]):
                v = str(r[n]).strip()
                if v and v.lower() != "nan":
                    return v
        return ""

    movimentos = []
    if sd3 is not None and not sd3.empty:
        sd3 = sd3[sd3["P"] != ""]
        estornadas = 0
        for _, r in sd3.iterrows():
            if texto(r, "Estornado").lower() in ("sim", "s"):
                estornadas += 1
                continue
            qtd = numero(r.get("Qtd. Saida")) if "Qtd. Saida" in r.index else 0
            if not qtd:
                qtd = numero(r.get("Quantidade"))
            if not qtd:
                continue
            tm = texto(r, "TP Movimento")
            if tm.endswith(".0"):
                tm = tm[:-2]
            desc = texto(r, "Descr. Prod", "Descricao", "Descrição") or desc_do_item(r["F"], r["P"])
            tipo = texto(r, "Tipo Produto", "Tp. Produto", "Tipo Prod", "Tp Produto")
            if not tipo:
                bruto = texto(r, "Tipo")
                if bruto and len(bruto) <= 3 and bruto.isalpha():   # so aceita se parecer codigo de tipo
                    tipo = bruto.upper()
            arm = r["A"] if isinstance(r["A"], str) else ""
            movimentos.append([
                idx_filial[r["F"]], r["P"], ref(desc), qtd, tm,
                texto(r, "Centro Custo"), texto(r, "Documento"), dia(r.get("DT Emissao")),
                arm, texto(r, "Endereco"), tipo, texto(r, "Unidade"), texto(r, "Desc Clas Vl"),
            ])
        if estornadas:
            AVISOS.append("%d movimentacao(oes) estornada(s) ficaram de fora do inventario." % estornadas)
        movimentos.sort(key=lambda x: (-x[7], x[0], x[1]))

    base = {
        "v": 1,
        "gerado": datetime.date.today().isoformat(),
        "filiais": filiais,
        "semSB2": sem_sb2,
        "semCustos": not INCLUIR_CUSTOS,
        "descs": textos,
        "ativos": ativos,
        "zerados": zerados,
        "pendentes": pendentes,
        "movimentos": movimentos,
    }
    # marca curta que muda so quando os dados mudam: serve para conferir
    # se dois aparelhos estao vendo a mesma versao
    bruto = json.dumps(base, ensure_ascii=False, sort_keys=True).encode("utf-8")
    base["marca"] = hashlib.sha1(bruto).hexdigest()[:5]
    return base





# --------------------------------------------------------------------------
def principal(saida=None):
    arquivos = achar_planilhas()
    if not arquivos:
        print("Nenhuma planilha em 'dados'.")
        if not os.path.isdir(PASTA_DADOS):
            print("A pasta 'dados' nem existe aqui.")
        else:
            outros = sorted(os.listdir(PASTA_DADOS))
            print("A pasta 'dados' tem: %s" % (", ".join(outros) if outros else "nada"))
        if os.environ.get("GITHUB_ACTIONS"):
            print("")
            print("Isto esta rodando no GitHub: as planilhas precisam estar no repositorio,")
            print("nao so no seu computador. Confira se o .gitignore nao esta bloqueando")
            print("a pasta dados e envie de novo pelo publicar.bat.")
        else:
            print("Coloque ali o SALDO FISICO e o SALDO POR ENDERECO em .xlsx e rode de novo.")
        return 1

    del AVISOS[:]
    partes_sb2, partes_sbf, partes_sda, partes_sd3, partes_sd3r, partes_sbz = [], [], [], [], [], []
    print("Lendo planilhas de 'dados':")
    for caminho in arquivos:
        nome = os.path.basename(caminho)
        tipo, df, erro = ler_planilha(caminho)
        quando = datetime.datetime.fromtimestamp(os.path.getmtime(caminho)).strftime("%d/%m/%Y %H:%M")
        if tipo == "SB2":
            partes_sb2.append(df)
            print("  [saldo fisico]   %-34s %6d linhas   %s" % (nome[:34], len(df), quando))
        elif tipo == "SBF":
            partes_sbf.append(df)
            print("  [por endereco]   %-34s %6d linhas   %s" % (nome[:34], len(df), quando))
        elif tipo == "SDA":
            partes_sda.append(df)
            print("  [a enderecar]    %-34s %6d linhas   %s" % (nome[:34], len(df), quando))
        elif tipo == "SD3":
            partes_sd3.append(df)
            print("  [movimentos]     %-34s %6d linhas   %s" % (nome[:34], len(df), quando))
        elif tipo == "SBZ":
            partes_sbz.append(df)
            print("  [indicadores]     %-33s %6d linhas   %s" % (nome[:33], len(df), quando))
        elif tipo == "SD3R":
            partes_sd3r.append((nome, df, quando))
        else:
            print("  [ignorado]       %-34s %s" % (nome[:34], erro))

    if not partes_sb2 and not partes_sbf:
        print("\nNenhum arquivo reconhecido. Exporte de novo o SALDO FISICO e o SALDO POR ENDERECO.")
        return 1
    if not partes_sb2:
        print("\nAviso: nenhum saldo fisico encontrado. O app vai mostrar so o enderecamento.")
    if not partes_sbf:
        print("\nAviso: nenhum saldo por endereco encontrado. Os itens vao aparecer sem endereco.")

    sb2 = pd.concat(partes_sb2, ignore_index=True) if partes_sb2 else None
    sbf = pd.concat(partes_sbf, ignore_index=True) if partes_sbf else None
    sda = pd.concat(partes_sda, ignore_index=True) if partes_sda else None
    for nome, df, quando in partes_sd3r:
        if partes_sd3:
            print("  [ignorado]       %-34s a SD3 com endereco substitui" % nome[:34])
        else:
            partes_sd3.append(df)
            print("  [movimentos]     %-34s %6d linhas   %s  (sem endereco)" % (nome[:34], len(df), quando))
    sd3 = pd.concat(partes_sd3, ignore_index=True) if partes_sd3 else None

    sbz = pd.concat(partes_sbz, ignore_index=True) if partes_sbz else None

    base = montar(sb2, sbf, sda, sd3, sbz)

    modelo = os.path.join(RAIZ, "template.html")
    if not os.path.exists(modelo):
        print("\nNao achei o 'template.html'.")
        return 1
    html = open(modelo, encoding="utf-8").read()
    marca_app = hashlib.sha1(html.encode("utf-8")).hexdigest()[:5]
    quando_modelo = datetime.datetime.fromtimestamp(
        os.path.getmtime(modelo)).strftime("%d/%m/%Y %H:%M")
    base["appv"] = marca_app
    if chave_gemini():
        base["gemini"] = {"chave": chave_gemini(), "modelos": GEMINI_MODELOS}

    dados = json.dumps(base, ensure_ascii=False, separators=(",", ":"))
    dados = dados.replace("</", "<\\u002f")  # seguranca ao embutir no HTML

    saida = RAIZ if not saida else os.path.join(RAIZ, saida)
    os.makedirs(saida, exist_ok=True)
    destino = os.path.join(saida, "index.html")
    with open(destino, "w", encoding="utf-8") as f:
        f.write(html.replace("__DADOS__", dados))

    carimbo = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(os.path.join(saida, "versao.txt"), "w", encoding="utf-8") as f:
        f.write(carimbo)

    com_saldo = sum(1 for a in base["ativos"] for r in a["r"] if r[1] > 0)
    com_end = sum(len(r[9]) for a in base["ativos"] for r in a["r"])
    tamanho = os.path.getsize(destino) / 1e6

    print("")
    onde = "index.html" if saida == RAIZ else os.path.relpath(destino, RAIZ).replace("\\", "/")
    print("App gerado: %s  (%.1f MB)" % (onde, tamanho))
    print("  filiais ............ %s" % ", ".join(base["filiais"]))
    print("  itens com saldo .... %d" % com_saldo)
    print("  linhas de endereco . %d" % com_end)
    print("  produtos no total .. %d" % (len(base["ativos"]) + len(base["zerados"])))
    if base["pendentes"]:
        notas = len(set((p[0], p[6]) for p in base["pendentes"]))
        print("  a enderecar ........ %d linhas em %d notas" % (len(base["pendentes"]), notas))
    if base["movimentos"]:
        dias = sorted(set(m[7] for m in base["movimentos"] if m[7]))
        quando_mov = ", ".join((EPOCA + datetime.timedelta(days=d)).strftime("%d/%m") for d in dias)
        prods = len(set((m[0], m[1]) for m in base["movimentos"]))
        print("  movimentos ......... %d linhas, %d produtos (%s)" % (len(base["movimentos"]), prods, quando_mov))
        tipos = sorted(set(m[10] for m in base["movimentos"] if m[10]))
        print("  tipos de produto ... %s" % (", ".join(tipos) if tipos else
              "nenhum (a coluna de tipo veio vazia na exportacao)"))
    if partes_sbz:
        sim = sum(1 for a in base["ativos"] if a.get("e") == 1)
        nao = sum(1 for a in base["ativos"] if a.get("e") == 0)
        sem = sum(1 for a in base["ativos"] if "e" not in a)
        print("  controla endereco .. %d sim, %d nao, %d sem indicador (itens ativos)" % (sim, nao, sem))
    print("  marca dos dados .... %s" % base["marca"])
    print("  Gemini ............. %s" % ("ligado" if base.get("gemini") else
                                         "desligado (sem gemini_chave.txt nem GEMINI_API_KEY)"))
    print("  marca do app ....... %s   (template.html de %s)" % (marca_app, quando_modelo))
    if base.get("semCustos"):
        print("  custos ............. FORA da base (INCLUIR_CUSTOS = False no build.py)")
    if base["semSB2"]:
        print("  sem saldo fisico ... filial %s (so tem enderecamento)" % ", ".join(base["semSB2"]))

    for aviso in AVISOS:
        print("")
        print("  ATENCAO: %s" % aviso)

    for nome in PASTAS_ANTIGAS:
        antiga = os.path.join(RAIZ, nome)
        if antiga != saida and os.path.isfile(os.path.join(antiga, "index.html")):
            print("")
            print("  ATENCAO: sobrou uma pasta '%s' com um app antigo dentro." % nome)
            print("  O app agora e gerado no index.html, aqui na pasta do projeto.")
            print("  Se algum atalho ou link apontar para '%s', vai mostrar dados velhos." % nome)
            print("  Pode apagar a pasta '%s' sem medo." % nome)
    return 0


if __name__ == "__main__":
    destino = None
    argumentos = sys.argv[1:]
    if "--saida" in argumentos:
        posicao = argumentos.index("--saida")
        if posicao + 1 < len(argumentos):
            destino = argumentos[posicao + 1]
        else:
            print("Faltou dizer a pasta depois de --saida")
            sys.exit(1)
    sys.exit(principal(destino))
