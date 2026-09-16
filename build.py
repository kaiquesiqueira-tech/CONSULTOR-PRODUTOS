# -*- coding: utf-8 -*-
"""
Gera o app de consulta de estoque a partir das planilhas da pasta 'dados'.

Coloque na pasta 'dados' os arquivos exportados do sistema:
  - SALDO FISICO (tabela SB2)        -> pode ser mais de um arquivo
  - SALDO POR ENDERECO (tabela SBF)  -> pode ser mais de um arquivo

O tipo de cada arquivo e descoberto automaticamente pelas colunas,
entao o nome do arquivo nao importa.

Uso:  python build.py
Saida: dist/index.html  (arquivo unico, funciona sozinho)
"""

import os
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
PASTA_APP = os.path.join(RAIZ, "app")
# nomes dos arquivos que o build cria. Usados tambem pelo servidor, para
# nao servir mais nada quando a saida e a propria pasta do projeto.
ARQUIVOS_DO_SITE = ("index.html", "versao.txt", ".nojekyll", "manifest.webmanifest",
                    "sw.js", "icone-192.png", "icone-512.png")

PASTAS_ANTIGAS = ("dist", "docs", "site", "publico")


def pasta_saida():
    """Onde o app e gravado. Vem do config.txt, campo pasta_do_site."""
    try:
        sys.path.insert(0, RAIZ)
        import publicacao
        valor = publicacao.config("pasta_do_site", "raiz").strip()
    except Exception:
        valor = "raiz"
    if valor.lower() in ("raiz", "principal", ".", "", "root"):
        return RAIZ
    return os.path.join(RAIZ, valor)
EPOCA = datetime.date(2000, 1, 1)


# --------------------------------------------------------------------------
# leitura das planilhas
# --------------------------------------------------------------------------
def achar_planilhas():
    arquivos = []
    for ext in ("*.xlsx", "*.xlsm", "*.xls"):
        arquivos += glob.glob(os.path.join(PASTA_DADOS, ext))
    arquivos = [a for a in arquivos if not os.path.basename(a).startswith("~$")]
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
        if "Filial" in valores and "Produto" in valores:
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
    try:
        f = float(valor)
        return 0.0 if np.isnan(f) else round(f, 3)
    except Exception:
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
def montar(sb2, sbf):
    for df in (sb2, sbf):
        if df is None or df.empty:
            continue
        df["F"] = df["Filial"].apply(lambda v: chave(v, 6))
        df["P"] = df["Produto"].apply(lambda v: chave(v, 9))
        df["A"] = df["Armazem"].apply(lambda v: chave(v, 2))

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

    ativos, zerados = [], []
    for it in itens.values():
        linhas = [r for r in it["r"] if r[1] or r[2] or r[4] or r[5] or r[9]]
        if linhas:
            it["r"] = linhas
            it["d"] = ref(it["d"])
            ativos.append(it)
        else:
            ultima = max([r[6] for r in it["r"]] + [0]) or max([r[7] for r in it["r"]] + [0])
            zerados.append([it["f"], it["c"], ref(it["d"]), ultima])

    ativos.sort(key=lambda x: (x["f"], x["c"]))
    zerados.sort(key=lambda x: (x[0], x[1]))

    fil_sb2 = set(sb2["F"]) if (sb2 is not None and not sb2.empty) else set()
    sem_sb2 = [f for f in filiais if f not in fil_sb2]

    if not incluir_custos():
        for it in ativos:
            for r in it["r"]:
                r[3] = 0.0

    base = {
        "v": 1,
        "gerado": datetime.date.today().isoformat(),
        "filiais": filiais,
        "semSB2": sem_sb2,
        "semCustos": not incluir_custos(),
        "descs": textos,
        "ativos": ativos,
        "zerados": zerados,
    }
    # marca curta que muda so quando os dados mudam: serve para conferir
    # se dois aparelhos estao vendo a mesma versao
    bruto = json.dumps(base, ensure_ascii=False, sort_keys=True).encode("utf-8")
    base["marca"] = hashlib.sha1(bruto).hexdigest()[:5]
    return base


def incluir_custos():
    """Le a preferencia do config.txt. Sem o arquivo, inclui os custos."""
    try:
        sys.path.insert(0, RAIZ)
        import publicacao
        return publicacao.config("incluir_custos", "sim").lower() not in ("nao", "n", "no", "0", "false")
    except Exception:
        return True


# --------------------------------------------------------------------------
def principal():
    arquivos = achar_planilhas()
    if not arquivos:
        print("Nenhuma planilha em 'dados'.")
        print("Coloque ali o SALDO FISICO e o SALDO POR ENDERECO em .xlsx e rode de novo.")
        return 1

    del AVISOS[:]
    partes_sb2, partes_sbf = [], []
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

    base = montar(sb2, sbf)

    modelo = os.path.join(PASTA_APP, "template.html")
    if not os.path.exists(modelo):
        print("\nNao achei 'app/template.html'.")
        return 1
    html = open(modelo, encoding="utf-8").read()

    dados = json.dumps(base, ensure_ascii=False, separators=(",", ":"))
    dados = dados.replace("</", "<\\u002f")  # seguranca ao embutir no HTML

    saida = pasta_saida()
    os.makedirs(saida, exist_ok=True)
    destino = os.path.join(saida, "index.html")
    with open(destino, "w", encoding="utf-8") as f:
        f.write(html.replace("__DADOS__", dados))

    # arquivos de apoio para instalar o app (icone, manifesto, modo sem rede)
    import shutil
    for apoio in ("manifest.webmanifest", "sw.js", "icone-192.png", "icone-512.png"):
        origem = os.path.join(PASTA_APP, apoio)
        if os.path.exists(origem):
            shutil.copyfile(origem, os.path.join(saida, apoio))

    # o GitHub Pages ignora arquivos que comecam com _ sem este arquivo
    open(os.path.join(saida, ".nojekyll"), "w").close()

    carimbo = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with open(os.path.join(saida, "versao.txt"), "w", encoding="utf-8") as f:
        f.write(carimbo)

    com_saldo = sum(1 for a in base["ativos"] for r in a["r"] if r[1] > 0)
    com_end = sum(len(r[9]) for a in base["ativos"] for r in a["r"])
    tamanho = os.path.getsize(destino) / 1e6

    print("")
    onde = "index.html (na pasta do projeto)" if saida == RAIZ else \
           os.path.basename(saida) + "/index.html"
    print("App gerado: %s  (%.1f MB)" % (onde, tamanho))
    print("  filiais ............ %s" % ", ".join(base["filiais"]))
    print("  itens com saldo .... %d" % com_saldo)
    print("  linhas de endereco . %d" % com_end)
    print("  produtos no total .. %d" % (len(base["ativos"]) + len(base["zerados"])))
    print("  marca da versao .... %s" % base["marca"])
    if base.get("semCustos"):
        print("  custos ............. FORA da base (config.txt: incluir_custos = nao)")
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
            print("  O app agora e gerado em %s." % ("index.html, aqui na pasta do projeto"
                                                     if saida == RAIZ else nome))
            print("  Se algum atalho ou link apontar para '%s', vai mostrar dados velhos." % nome)
            print("  Pode apagar a pasta '%s' sem medo." % nome)
    return 0


if __name__ == "__main__":
    sys.exit(principal())
