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
import base64
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
#  APP INSTALAVEL E OFFLINE
#  O build gera, junto com o index.html, os arquivos que deixam o
#  consultor ser instalado no celular e funcionar sem internet:
#    sw.js                 guarda o app no aparelho
#    manifest.webmanifest  nome, cores e icones do app instalado
#    icone-*.png           os icones (desenhados uma vez e guardados aqui)
# ---------------------------------------------------------------------
ICONES = {
    "icone-512.png": (
        "iVBORw0KGgoAAAANSUhEUgAAAgAAAAIACAYAAAD0eNT6AAArRUlEQVR42u3de5Cdd33f8c/3+zx7drU37Uq2hey1wJIsY0UO"
        "xoZyMe2GNA1NSSAkEcMAodMOwTBgJkMzmWkGmjRQ2lJKO1yaGEgzZSCQuC7EgSQwIUEMBpyADbEjW7Ikx7JsIdnSSru67OU8"
        "v2//eM7ZPVoka3e1qz2X92tGvqyk1dFvzz7fz+/7+z2/x4SlMEkujVr5v7sKSTH/F23cuLF3oq+vLzubbnJlPVK8PMxyKYZN"
        "uqX+O8LiBpMN1D6HMbwA2lRIslBMWNie+tU0pPslG7OIqmTfTiomizX+4MDp06cPHz585vzX4NGsdv0NSel812BcvJBhYVwa"
        "9dqbrZj/k/0bt12RZ7FdoZvd4rkhu0mRtspsUGbrJcnM5r4FGt6rEbxvAXRY8TE7txTZvOthxDFFjMt8nykeTGGPy/SDamG7"
        "Tx3e+8x5PmVWTsp2pVogAAFgOWb5587wN27c2DuV9e+Qxcsj9AKZfkKhbWa+VrNv6pAiVL6XZyt8usDYO8MNoMOkeZ2BeddD"
        "KzNC+Y96KFBEOinTXoX+wUw/VNi3u4tTD83rFNQ6BHQHCABLK/rVxp9Y99zrb1QRLw3Tzyv0IjPbJPNaoa+n1kjlDzW+a41x"
        "BoBFi7kf9UmUuWRuVu8YmBRJEXFQpu9Z6MvK7LvHH3/04XM/1WhOGCAAXIhLO026q7G1nw1v2vKSCHudJY3KdIu5Z2UIrVf8"
        "KBqKvTOeAHBZgkFqCAWZzKy+pBApFQrdH65dZvHFsYP779M5y7Y7M+muEMsEHV2w6kW7MRFmw5tueElE8ToLvdrMbpRZLX8m"
        "lQXfGn8vAGD11a7jIckyMy+v0hGKiIfD9BWz7ItjB/c0hoHz1QACQPv/nXd642x/3aat25V8Zyheb6btZdEPxews3+qze2b4"
        "AND8HYIol2MtMzObu6Zrt8n+RJ7uOn5w3+55XYGOCwKdVNDqRbws/Fu3dg9Nxass/F1S/LR5ltXWkhqLPrN8AGj57kBjGHBF"
        "KgrJ/josffxEt31V+/ZN1X5tptklBgJA2xX+vquu29Bd6Xp7KL3B3J8/r71Pax8A2jsMROMyQaT0iMm/MDU98/unjz52pJOC"
        "QDsHgHMK//DI5h2m/N2heI25b6jN9ustHzbwAUDnqBd3MzMvuwLpiMnuCVU/OnbowEOdEASsTf9O3lj4Zdl7FPEm86wS5Z16"
        "zPYBAHNdAfPMyuWBaZl9TlF8ZF4QaLs9AtZmf5cLFH6vREqSoipZxmwfAPDjXYEoJMvNXZFS2weBdimEWb3w923YfFUl9/fK"
        "7HZzqxf+xp38AAA8WxAoNw26K1JMK+LO6Wr6wOkjB47OrzkEgNV9/SYpafv2ytD4zO0mvdfcrqLwAwCWMQgcDekDJwa77tTu"
        "3dMqO87Ryt2AVi6MuaSqJA1fs+3nzONDMt/RsMZP4QcALE8QqO0RUKSHItlvjj259y/m1yICwMqrb9xL66+94epQ8d8lf4MU"
        "Cgo/AGAFg4CZZ7XG8xdM2b879sSepxrrUiv9hbIWnPUXkmJo5Po7pPgjc39J1Pr9bPADAKzchNlqRwdHmPtNEfGrPYPrpybH"
        "j99X1iDlrRQCrIVep0sqrrj6um0pyz8q81c1tPsz3psAgMvYECgalgW+6kX13c889dhetdCdAq1QOGcHc3jk+jeE+91mdlOk"
        "otqQyAAAuJzz0nITYKTC3Lcl8zeuGVx/cHL8+IMNtaupQ0CTB4DRXHq8WL/+hoE1V6z7hLl/UIre2qw/F+1+AMAqpgDVHi4g"
        "sz5z/5U1g+tGeruu/MbZs8cmazUsNfGLb9rX5ZKKtRu33OKZf9rcX1g+wIFjewEATSckJfMsi5QeSEV668nD++9XEy8JNGMH"
        "YHY35fDIlrda5p83t+eWLX9m/QCAJp64Rqqa+zXm9sY1g8NPT46Pfb9hUttUIaDZAkA9KeVDI1v/l3v+H6XU3dDyBwCgmXNA"
        "bUlAPeb5a7oHhjdOjh//S5V3sDXVvoBmmk1nkorBkZF1udbcI/fbaPkDAFrU7JKAUrq3qrOvGT906Lia6BjhJtlBP5pLKtaP"
        "XPfizNZ8V263RarW0xLFHwDQcq0ASVmkaiG32zJb8931I9e9uCz+o3mzvMAmKP67qsMbN9+mLPszMxuOmF3vBwCg1ZsBVbMs"
        "j4gxFcUvjB0+cG+99q3mq1rlPQC14n/Nll9Tlt0lUx/r/QCANmsGuJQKmfXK/S1rBoZ/NDnxwPdW+zbBVQwAc8XfPPukIkxz"
        "x/kCANBmIUBJkptnr+kZGHpqtUPAKhXbc4t/+RCf2dskAABoyxRQ/iuSefba1Q4BqxAAzlv82ekPAOiUEGDNEAIucwCg+AMA"
        "CAHNEAIuYwCg+AMA0Cwh4HIV31wSxR8AgHOVBwaZZ5GKt409uf9T9Zq50n/wZdh0N0rxBwDgwhNxj0iFefbJ4Wu2/FpZ/Ff+"
        "sKCVLsKZpGL46i0vs8zvjYjQbNsDAAA0dALCzCyKdNvYU/u/oxU+NnglOwDl2f7Xbn6RZf7lmHsAAsUfAIDzTMhDCsv8y4PX"
        "bn6R5h4g1FIdAJekwZGRoUw93zPz62qtfw75AQDgwgozzyLSY4UmXzR+6NCJ2seXfWPgSnQA6i3+yNT9lbL4FxR/AAAuLoso"
        "CjO/LlP3V8qmwMosna9EUc4lFUMjW+50z18bkXiwDwAAC59HuxRV83xT98DQxsnxsXtqtXVZuwDLHQBySdW1I5v/TeZdvxup"
        "qNY+BgAAFs4VUXXPX1wZWHtwanzs/uUOAbasL1ZKQ9dc95Pm+bcV0SNu9wMAYKlCUpLZZKTqy088+djf12vtchXt5QoStmHD"
        "hj5X9lmT9Ynb/QAAuOTaarI+V/bZDRs2LGttXa4AkEkqpvP+jynLboooquLJfgAAXHKdjiiqyrKbpvP+j2kZbw3MlulzFMNX"
        "b3m95fl/ilRl0x8AAMvXCHBFqlqW39rTN/Tw5MTYg7XaG5faXrjUDkIMXrt1cy772witlYJ1fwAAlldIlsx0sqr4J+NP7DtQ"
        "q7VL3g9wqW368n7/0J0yW1cLIxR/AACWuQ1QZgBbl4Xu1Nz5AEuWXeLvLYZGtrzTPX9XpMQtfwAArBxXRNU829o9MPTM5PjY"
        "fbqEpQBb8ouQom/D5isrXdkjktZKwa5/AABWVkgWkk5OzxTPP33kwNNa4lLAEpcAdpqk6M794+Y+LKVLbkUAAICFTNxTmPtw"
        "d+4fLwPBTlviJ1q0TFKx7tqtPyv5V3nIDwAAl11h5pmUXnX8iX1f0xIeHbzYDoBJCo0qj9BHYxk2IQAAgMVP4EOKCH1Uo8q1"
        "hHq82Jl7JikNFVve4Z6/RZESs38AAC5/AJAimWdXdh8fOjo5Pva3WuSGQFvcHyat3bRpyIvKfrkNKbjtDwCAVRIyk1KcSNn0"
        "lpMHD56Y/fgCLGYJwCWFF5X3W5YNKyJR/AEAWMUuQESyLBv2ovL+WuH3hf/mRRT/gaufty33rocaTvsjAAAAsJpdgNopgdU0"
        "s2PiqX/cqwXeFrjQpGCSIvf8t8w9V9n7p/gDALDaXQBFmHuee/5bWsRmwIX8osbZ/w+l6GL2DwBA03UBZqpp5gUL7QIspAPQ"
        "OPvvZvYPAEBTdgG6F9MFuNgvcEmxfuNzb0hZ5QfM/gEAaO4ugBfTNx87/Piei3UBLtYBMEmRPP+N2uyfnf8AADRnFyCZe3fy"
        "/DcW0gWwi/1c/8Zt67uy9LBk63ncLwAAzdwFMElxbKbwG08d3nusoTuwqA5AJikqWXqneXaFlJj9AwDQ1F2AlMyzKypZemet"
        "8F/wtF5/ltl/oZGRNRHxlogUklH8AQBo7gxgESki4i0aGVmj8gFBtpgA4JJiOCqvNM821079cwYWAICm5opI5tnm4ai8Us9y"
        "OuCFinr5G8zfw1gCANCKzQB/T31Cf96fvkAoSIMjW7Zm8oelyMTaPwAArSQkKwqlG8cP7d9Xr+0X6wC4JGWhN9eO/S0YRwAA"
        "Wqr+F+aeZ6E3X6jeny8AFNq+vSLZm6I89I+1fwAAWop5rYa/qazpKi4WADJJMXBy+hYz26xIbP4DAKD1uCIlM9s8cHL6Fp3n"
        "lsB5xX3UJKlL+mW5e+3kPwAA0HIiyd27pF9urPGzPYL5PQNt3941PD79oMy2cfsfAAAtK8nMFbF3bLByk3bvnlHDHQGNxb3W"
        "/p95oZltpfgDANDSyjMBzLYOnJx5oeYtAzQU+Hr7P3bKaP8DAND6IsncuxQ7G2v9vACwq5DkIf2Uyp2D3PsPAEBLM1OEQvqp"
        "subvKuYHAJcUA1dft1VmO6K8dyBj4AAAaGlZRITMdgxcfd1WNRwNXAsAoy5JXZ69wty7a0/+AwAALS8lc+/u8uwVjTW/FgB2"
        "hSRF6DVlOKD7DwBAezBJUavxczXfaz9TbNiwoS8sbo0UDcEAAAC0OI8UCotbN2zY0KfaI4LrAUBnu3q3u3yjajsAGS8AANql"
        "BRDh8o1nu3q31z/muvXWTJLysJfJPePhPwAAtJso5J7lYS+TJN16a+bq7y/X/81fyAABANDGMaBe6/v7w7VrV5KUSfEC8fQ/"
        "AADakHlZ4+MFkjLt2pVcUurfuG04QlvL2/9Z/wcAoN0SQEQoQlv7N24blpTK+/9VvcE9668d/0sAAACgzQKAFMk96+9S9Qap"
        "drtfZHazzIzz/wEAaFeRZGaR2c1zAUB+PQMDAEAHxIBazXdJskjbaycA0v4HAKAtmUlRq/mSr1+/fsDEBkAAANo9AUSETNq6"
        "fv36AZ8cHOyV2XD9JxkfAADaMwDUGgHDk4ODvd4z7dtlNqjgCGAAANo6AJSPBh7smfbtnjLvFQ//AQCgU3jKvNeV4mVW7v3j"
        "FkAAANpbMjMpxcuc2T8AAJ3XBfCQ1jMOAAB0jpDWu0W8WNwCCABAJzBFyCJe7JIVjAcAAB2VAwoXm/8AAOg0KQ/FjYpaWwAA"
        "ALT11D8iFIob3cwG6h9kXAAAaO8AIElmNuBSbf4PAAA6RTgzfwAAOq8TwCFAAAB0IAIAAAAEAAAAQAAAAAAEAAAAQAAAAAAE"
        "AAAAQAAAAAAEAAAAQAAAAAAEAAAAQAAAAAAEAAAAQAAAAAAEAAAAQAAAAAAEAAAAQAAAAAAEAAAACAAAAIAAAAAACAAAAIAA"
        "AAAACAAAAIAAAAAACAAAAIAAAAAACAAAAIAAAAAACAAAAIAAAAAACAAAAIAAAAAACAAAAIAAAAAACAAAABAAAAAAAQAAABAA"
        "AAAAAQAAABAAAAAAAQAAABAAAAAAAQAAABAAAAAAAQAAABAAAAAAAQAAABAAAADA0uQMwfIxa4JEZ3wdALSvFFIE40AAWO2C"
        "X/tHhJRS+cZcTSFpapoEAKA9haTuPNTVJeVZ+YEiMS4EgFUo/NWifPNVcqlvjdTXHVqtDBBRfkNsvrpQ5iRkAO3HXXrsR64n"
        "nzEdO2nKM2mwr7zYJYIAAWDFi3+t8EdIw/2hkStDVw2FertDlUyrEgDqr2mwN/Tf3jGt3t6kKJpjSQIAlm36b9LYKdPBo64f"
        "POq6+5td+tr3cplJA72hasEwEQBWsNBOz5SF9sZNSVevD3VlZRcgJWmmqLUH4vK/rmqSZqrSqbOSyVQlAABoQ2u6pJuel/SC"
        "bYXe8rMz+voDud7/mW598+8zrRssL750QAkAy1/8q9K1V4Zu3lKop1IW3KmZsuibGgquXf7XVv/z3Ws/ggAAoP0UIZ2ZktJZ"
        "k5v0My+q6p/uKPShP67oP3+uW92VkLMMuiDcBriI4r/5OUkvfX6hPCs7AY3FFwBwGa7HKu92yrNysjMxUXY83/e2KX303ZM6"
        "O8UVmQCwnMV/Rrr2itCtW5NmirLdz+waAFZflpX/Pvm06a2/NK0PvW1Sx8fLDYIgAFxS8S8KabBXunlLoWoq20oUfwBormt1"
        "nksTx0137JzWm35mRmMTNhsOQABYkhTSjZvKNX9m/gDQpCGgfs0upN9647T615R3BXDJJgAsSbUob/W7en1oukrxB4Bmlrl0"
        "+oxp+5ZCb/jpGY2fpgtAAFhKmrTy9r6RK8pb/cSOUgBoiWt3KqRf/RdV9XRxUiABYAkiyhP+rhpOqrZI69+MZwEAoAswNWl6"
        "wZZC259X6OyUcV0kACxOStKaitTb3RpHTJqV5xKcnWKpAkBnqxZSX2/o+ZsSy7cEgMUX0xRSb0/Z/m/2AyUiytQ7fsZ0ZKy8"
        "/YUVCwCdKiQpk27clFRwKioBoFOCC290ACgVzIQIAACADpwUMQQEAAAAQAAAAIAAwBAAAEAAAAAABAAAAEAAAAAABAAAAEAA"
        "AAAABAAAAEAAAAAABAAAAEAAAAAABAAAAEAAAAAABAAAAEAAAAAABAAAAEAAAAAABAAAAEAAAACAAAAAAAgAAACAAAAAAAgA"
        "AACAAAAAAAgAAACAAAAAAAgAAACAAAAAAAgAAACAAAAAAAgAAACAAAAAAAgAAACAAAAAAAgAAACAAAAAAAEAAAAQAAAAAAEA"
        "AAAQAAAAAAEAAAAQAAAAAAEAAAAQAAAAwGrLGQJcLhG1H5JM5b8BPLv694qZ5MZ4gACAFlMkqZJL3d1cwYClSIV0dqqMzca3"
        "EQgAaBUD/aZnjifd9w8zSqm8gAUtAODiHQCTikK6ctj1E1tyzVRDMzOSs4ALAgCaWUjq6pL+8Etn9Ym7z+rIMwWtf2Cx30ch"
        "9VRMt93cpY/8+oCGBlyTU0EIAAEAzakopIEB0//+0lm9539MaN1aV+8aepfAolN0bSPAV741rRMT4/rD3x5UX4+pKFgOAAEA"
        "TThjqXRJTx9P+r27z2h40FXJy70AAJYQAiRtXG/65gPT+vxfTupdb+zV+MlQnjE8WBoaSFgRKcoNf7sPVPWjY0mVLoo/cKmq"
        "hdTXY/ruQzOKGe4KAAEATd4JYLMfwPcUCAAAAIAAAAAACAAAAIAAAAAACAAAAIAAAAAACAAAAIAAAAAACAAAAIAAAAAAAQAA"
        "ABAAAAAAAQAAABAAAAAAAQAAABAAAAAAAQAAABAAAAAAAQAAABAAAAAAAQAAABAAAAAAAQAAOpYxBCAAoNmlYAyA5S7+Bd9X"
        "IACgmUVIvT2mLGMsgOUq/iGpr8ckL/8bWKqcIcBKyFw6Oxn6yetzbbs210MHqlo3aJqpMjbAkoq/SebS2anQq15akXkZsgEC"
        "AJpOSlJPj+m/3DGgf/07J3X0eFJ/r0nBzAVYbPEvitDJ06G3/1KvXvtT3Tp9KpTTXQMBAM3Ia12AW7fn+qP3r9WHP3dauw9U"
        "lYJNTMCiwnRIQ/2ZfvGV3Xrnr/RqpkqEBgEATS5zaeJUaMeWXJ/5nbU6cjwpYm4tE8DFZ/8pSQO9pv4B0+lTMftxgACApg8B"
        "ZybLi9bQgDH7BxYhVNv5n6SJ8WBTLQgAaC1eu9+kyiZAYImtAFH8QQBAC1/DmP4DQHNMzBgCAAAIAAAAgAAAAAAIAAAAgAAA"
        "AAAIAAAAgAAAAAAIAAAAgAAAAAAIAAAAgAAAAAAIAAAAgAAAAAAIAAAAgAAAAAAIAAAAgAAAAAAIAAAAdKScIcDlkpKUgnFo"
        "29mESc6UAiAAAHURUkjq7zWpS+X/oL2YpBnp9NmQrPxfAAQAdHjxzzKpp2L69t/P6L6HZpSCAtFWX+Pa7P8lO7r00h1dmpwJ"
        "RZKMLzJAAEBnF/+z09Jv/M9xffEbU5qphoLy33bcQmamf/sLa/T+d/RrcjoUIugBBAB0pBRSX4/pP/3BKX3mzyd1zZVOSWhb"
        "ppD0e//vjHoqpv/wtj5NnA5l7AkACADovNl/T0V67FChu/9mUhvWuYpUfhxtGgFMWj/o+vzXzupXX92jkatc0zMsBQDNinyO"
        "FZv9d3WZHnuy0PjpkDvFvxNCX55JE2dCjz1ZqKvLuOsDIACgY99gvMM6KwTwdQcIAAAAgAAAAAAIAAAAgAAAAAAIAAAAgAAA"
        "AAAIAAAAgAAAAAAIAAAAgAAAAAAIAAAAgAAAAAABAAAAEAAAAAABAAAAEAAAAAABAAAAEAAAAAABAJ3LjDHg6w6AAICOUy2k"
        "YBg6StS+7gAIAOjEGaCkopCuGnb1dJmCFNAZxT+kni7TVcOuoijfBwCaU84QYEWSpUtnp0Lbt+R6xc1d+vK3prVxvWmmmAsI"
        "aJ8ZvyR1ZdLhY6Gff0VF27fkOjsZcqYYAAEAndkFqFZDH/71AY1NjOubD0yrr4duQFt+rU06PRn6Zy+s6MO/PqBqNQh5AAEA"
        "nVwUZmak4QHX//ntQX32Lyd130MzSolNYm3VAYiy4/OSHV1687/s0UCfa3KK2T9AAEBHc5cmp0Nrekx3vLFXd1TLgiETuwPb"
        "IuWVX0ez8moyeSY0OU3xBwgAgCS3ckPgxMlg5t8BnQDnawwQAIDZiaJJWcY4AEDTTM4YAgAACAAAAIAAAAAACAAAAIAAAAAA"
        "CAAAAIAAAAAACAAAAIAAAAAACAAAAIAAAAAACAAAAIAAAAAACAAAAIAAAAAACAAAAIAAAAAACAAAABAAAAAAAQAAABAAAAAA"
        "AQAAABAAAAAAAQAAABAAAAAAAQAAABAAAAAAAQAAABAAAAAAAQAAABAAAAAAAQAAABAAAAAAAQAAABAAAAAgAAAAAAIAAAAg"
        "AAAAAAIAAAAgAAAAAAIAAAAgAAAAcNkFQ0AA6Jg3e5Q/AABSZozBs8kZgvMXUjfpzKRppij/u5mZSUWSBntDG9aFilR+zHjz"
        "A2ij6fxC5zcmSYX08EFXljExIgAskrs0OS2dnZIGeqWUmj+0dOVSJQ/NzJQhIBEAALRJ8Tcz+QJ71nkmnTljeuSgq5KzFEAA"
        "WMKseroqnThlGuoPFUXzzqgjytdWLaQ9/zil3u5o+sACAAudzRchDfSarhvpvui1LYW0plt6+HHX/qdc3RWuhwSAJb7xDj3j"
        "2nRV0TKvuShC1WooEXkBtEsASFKxwJZmSlJWCf3pvblOnDJdsTZULRhHAsAiZ9VduXTkhOnoSdOGodBMtfnX1etr/3T/AbRL"
        "AFjoNS1C6q5IR552ffrPu9S/plwOxflxF8ACPPy4z26sAwA0p2ohdfeG/uvnKzp41NVTYQMgAeASugB5Jj09btpzyNXdJVrr"
        "ANCEpmektetCd3+9S5/4UkXD/bT+CQDLEAIqufTIE659T7nWVLjfHgCa6Ro9U5WG1of+9sFMd3ysR90VLtAEgGWUufTAftcj"
        "T7i68rIzQBAAgNWRomz557m0djj0f/+qS7/43l6dPC26tQvEJsBFhoAfHHAdnzDdeG3S2v5Q1N6EKxkEFvK5U9R3ykpFwZsf"
        "QHuo3wVQLeautblLvd2SV0I/etr1oU916xNfqqi7EurtFhv/CAAro7tLOvSM6Udjma69MmnTVaGhvlBXvnInBuZZXHQLbEpS"
        "b3do3UBoTYXbAAG0VwBY2xfqHwppRjp1xrT7cdeX7s31B3/epYNHXcP95UWP4r+IsR0e2UqpWOyg2dy6U+blEbwDvdLAmlBo"
        "+W7Bi1rX4XnPSbNLDs/6a016zrqq3Dj5CkD7BID6tbBvjWv3Qdeeg+UhPydOmfrXhHoqYsMfAWB1gkCRypb7Si0DFKn2HVD/"
        "Trjgd0n57AL2JQBoRylJWVYeed5TKfdiFYlr3lKxBHApM/Tamy53rejJO6aFfv7gACAAbdsKMM1tvq5vAgQBYHWDgLSiPfeV"
        "/vwAgM7DbYAAABAAAAAAAQAAABAAAAAAAQAAABAAAAAAAQAAABAAAAAAAQAAABAAAAAAAQAAABAAAAAAAQAAABAAAAAAAQAA"
        "ABAAAAAAAQAAABAAAAAgAAAAAAIAAAAgAAAAAAIAAAAgAAAAAAIAAAAgAAAAAAIAAAAgAAAAAAIAAAAgAAAAAAIAAAAgAAAA"
        "AAIAAAAgAAAAAAIAAAAgAAAAQAAAAAAEAAAAQAAAAAAEAAAAQAAAAAAEAAAAQAAAAAAEAAAAQAAAAAAEAAAAQAAAAAAEAAAA"
        "QAAAAAAEAAAAsIgAEAwDAAAdJVySMQ4AAHQU84iYqKcBxgMAgPae+UtSREy4yR42MwIAAAAdEADMTCZ72MVGQAAAOo27FBnj"
        "AABARzUCMg+zvxNLAAAAdETll5nC7O/cpGOMBwAAncOkYy4pMRQAAHSU5HL7TkRIbAYEAKDdeURIbt9xL9IZugAAAHTQ7L9I"
        "Z3yyknYrYlzlYQBsBAQAoD2FzEwR45OVtNt7xsfPKGJs9icBAEB7BgBJihjrGR8/48eOHZsIaR+nAQIA0N4BwMwU0r5jx45N"
        "ePkR310+EygIAAAAtGf9D8lqNb+289+UHmVgAABof/WaXwaAIn6giJCMWwEBAGjP0u+KCCviB7MBYEb5npSKU7UAwDIAAADt"
        "JSTzlIpTM8r31AOAnzq8d8yMjYAAALRrADAzmWnfqcN7xyS5a3TUJRWS/bB8KFBwKBAAAO1V/1NZ4+2HkgqNjrrr1CmTJIv0"
        "AAMEAED7mq31p06Z6/vfLySpavEdpVRIljFEAAC0VenPlFJRtfiOJOn73y9mN/2tmTmzOykdljgSGACANhKSWVI6vGbmzO76"
        "x+oBIDty5MhpC/u+uUk8HAgAgHaRzE0W9v0jR46clpTVA4Ck0XIfgOme2omADBcAAO3SAJDVavxcza8FgF1JkmZS8a1IaUpy"
        "DgQCAKAtuEdKUzOp+FZjza8X+iTJJp56bJ8iHrLyQICCQQMAoKUVVj4C+KGJpx7bp7LNf04AkDSaSUomfaO2D5B1AAAAWlqE"
        "zGTSN8rCPzp7p19DANgVkjQju0uREs8FAACg1ZkrUpqR3dVY6+cFABWSbGJt1wMRsU9mLu4GAACgVSWZeUTsm1jb9YDK9n9x"
        "vgAgaTTT7t3TFrqnrP8cCwwAQGuKZOay0D3avXu6sf1/ngBQXwbQ3UosAwAA0LrMlVKake5urPEXCAD1ZYDK/RFxQOYsAwAA"
        "0HqSzD0iDkysrdyvee3/8wUAScrKVkF8zng6IAAALShSrYZ/rqzp+rHn/Ph5U4OkwvTZSKnKw4EAAGg1lkVK1cL02cbavpAA"
        "4OOH9h+QYpeVDwfgUCAAAFpDUdbu2FXWcvlCA4BUPyko0kcYRwAAWlBZw1OtpmuhASBJsjGb/ptIxQHOBAAAoCWU9/6n4sCY"
        "Tf+NGo7+XWgACEmZDh06a2afqbUSOBoYAIDmnvaHmZuZfUaHDp1V7dG/iwkAUu2WwOnCPxGpeKb2hEBCAAAATVr9yyf/Fc9M"
        "F/4JnefWv4UGgJDkpw7vfUYRf2ruJgWbAQEAaM76X5i7KeJPTx3e+0ytxsdSAkA9BJin6ocjpanayYB0AQAAaLrZv3mkNOWp"
        "+uHa7P9Z6/XFAkCS5McOP/6IFH9snjkHAwEA0HT1P9Vq9B+XNVsX3by/kLP+Q5JVU/WDtS7ARVMFAAC4rLN/i5Smqqn6wYXM"
        "/hcaAJIkn3jqH/fQBQAAoHln/2Wt1oJu3V/o0/4auwBVugAAADTV7L+6mNn/YgLAXBcg4s4yaXAwEAAAq6yc/UfcuZjZv3SB"
        "4wGf7deu3bRpyIvKfrkN1c4GMsYfAIBVmP2bSSlOpGx6y8mDB0/MdQWWrwNQ/4R+8uDBsbB4X+0hQXQBAABYrdm/uYXF+04e"
        "PDimi9z3fykBQLWC7ye27L8zUrFH5iwFAACwCsVf5h6p2HNiy/47tYjW/1IDQEgy7VLVTO+2RWw2AAAAyyZMMjO9W7tU1RLq"
        "sS/hDy2kndnxJ/Z9TSndZZ5lHBEMAMBlq/2FeZYppbuOP7Hva9LOTM9y5v+FLHUDn0uKvg2br6x0ZY9IWluGETYEAgCwktVf"
        "spB0cnqmeP7pIwee1rM88ne5OwCq/UF++siBo6H0PnP3paQPAACwKIW5eyi97/SRA0e1hLX/S+0A1GWSiuGRrX9l7v88Uipq"
        "HwMAAMtf/LNI6etjh/b9TL0GL/WT+SW+mJBkhel2RRyv5Qk2BQIAsLxCMinieGG6XcuwCf9SA0CS5ONP7NsfRXqHubMhEACA"
        "5a//5ey/SO8Yf2Lffl1C679uOdr1ISmfnBh7sKd/6LmW5bcqUlUy5wsGAMAll9mqeZ5HUf3Dsaf2f1BSrmXYd7dcRbqQlFWq"
        "p+5QUTxoluXigCAAAC5VMstyFcWDleqpO3SJ6/4rEQBCUhw5cuR0UvHmUJyuf4yvHQAAS6+toTidVLz5yJEjy1pbs2V+ofnk"
        "xInD3YNDh93z1ymiWMaQAQBAJynMszxF9e0nn3zsq1qm1v9KBACpbPvnU+Nj93cPDF3tnr9YEVVCAAAAi1I1z/KUqp88eejA"
        "+2vFv7qcf8BKnNxntYKfhke2fNsse2lEUUjG+QAAAFxUFGZZFlF8d+zQ/pdrbsf/si6rr8TMvL4+YYWmXh2RHjPLlm3TAgAA"
        "baxW/NNjhaZerbn7/Zd9T91KteaTJBs/dOh4Yen1UhyX2ZLOKgYAoEOkslbG8cLS68cPHTquJZ7zvxAr/fCe8qjgq7e8zDK/"
        "NyKi9mfy0CAAAOaEpDAziyLdNvbU/u9oGW/5u5wdgLpCGs3Hntr/nUjpdjNfkXUMAABavPgnM/dI6fay+I8u647/1egA1OWS"
        "qsPXbPk18+yTEal+eyCdAAAAxd88i1S8bezJ/Z/SCuz4X40OQF1VGs3Hntz/qUjF28w8oxMAAKD4zy/+o5el+EuX9dG9jydp"
        "NJ+ceOB7PQNDT5lnr5UiiT0BAACKf63476perhdwme/NJwQAACj+q138VyEAEAIAABT/1S7+qxQALhgC6gNDCAAAtKMkycrd"
        "/qtb/FcxAPx4CJD7v5JZJkUhGc8OAAC008S/kHkms0IpvX21i7+aY7ZdDsDwxs23Kcv+zMyGI4qqZDlvGABAGxT/qlmWR8SY"
        "iuIXxg4fuHe1i7/UFE/p21XeInj4wL2u6qtC8ah5lpedAAAAWnvmb57loXjUVX1VsxT/JukAzMokFYMjI+tyrblH7rdFKjgw"
        "CADQkpVfUjLPMqV0b1VnX1M7279pHo7XbIW1PjD50MjWj7tnt0cUUgSPEwYAtMysX2aZWaaUijtPHNr3LpWH+zTVk3GbrahG"
        "bcafJsePf7lnYOhJmb/S3HsUqcrmQABAkxf/armMrQlF8a4Th/b/bmNta6ZX2qytdasNVrF245ZbPPNPm/sLWRIAADRr5Vet"
        "5R8pPZCK9NaTh/ffX5toN+XR997EA1lIo/nJw/vv97M+qkifNs+y2rOS2SAIAGiWklXIzMyzTJE+7Wd9tCz+s0/0a8rn3rTC"
        "THp2zWR45Po3yPRxM1sfqajW9gXQDQAArNJktbbLP+KYQu8aO/ToF+bXrmYuri0wwDJJ2eT48Qf7+9d+Kcy3mWfbyo9zcBAA"
        "YDVm/e7mmSviq1lR/ZXjT+7f1VBXU7P/DVpt9jz7mMShkevvMOm95nZVpFQfaIIAAGAlJUkyd48UR0P6wIlDj35sfo1qBVkL"
        "DrxLssnx4/f1rb3yj6R0jZnfZDbbDeChQgCAZZ/yS5HMPDNzk9IX3LJfGju09+ua25zeUvvTWrlQziat4Wu2/Zx5fEjmOyKS"
        "FKm+LEAQAABccuFXWfilSA9Fst8ce3LvX7TirL+VOwDzuwEmyScnjj16duQ5f9A9WTxt0q3mPqAIOgIAgEsr/LLaOr+ORsS/"
        "HxvsetvkgUf2aG7JObXqX7BdCuPsbsu+DZuvquT+Xpndbm6VSEkNGwUJAgCAhRT+zNwVKaYVced0NX3g9JEDR+fXnFbWTgVx"
        "9vAgSRoe2bxDlr1HEW8y93oQ4NZBAMCFCn8hWV4W/jQts88pio+MHTrwUEPhb8pDfTo9ACwgCGSVhj0C9V8HAOhcSYqor/FH"
        "Ktq+8LdzAKg7Z1fm8MjmHab83aF4jblvUCRFRP0LyvIAAHTUbL/cR2ZmLnNFSkdMdk+o+tF5hb/+a9tyttzuzgkCfVddt6G7"
        "0vX2UHqDuT9fIdVyAF0BAOiE2b6s3NFvUqT0iMm/MDU98/unjz52pBMKfycFgPMGAW3d2j00Fa+y8HdJ8dO1M5wVEdGwaZAw"
        "AACtX/TLTX1mVs72i0Kyvw5LHz/RbV/Vvn1TnVT4OzEANPydd7p01+wOznWbtm5X8p2heL2ZtstMipgfBridEACaX6hxJ7+Z"
        "zV3TtdtkfyJPdx0/uG/33G/ZmUl3td0aPwHg2f/u9ecz17/o2fCmG14SUbzOQq82sxvLN845ywSNvxcA0BSzfEXt0TGz7f3a"
        "RO7hMH3FLPvi2ME992nu9r3z1YCOK4KQXNppjV2BMgxseUmEvc6SRmW6xdwzSSobA/XugNSwd4DxBICVn+HX1vIlyTKZmVl5"
        "+Y2UCoXuD9cus/ji2MH9jUW/PtvvmDY/AWDRXYFRk3adc7Tjuudef6OKeGmYfl6hF5nZpnJlIGodglDZcorUEAoafwAAFlfo"
        "6+38erF3ydzM5pqx5d6tgzJ9z0JfVmbfPf74ow+f+6lGc2lXdPJsnwCw9DBQNL5pNm7c2DuV9e+Qxcsj9AKZfkKhbWa+VmZz"
        "791yzUlzb95zEqed24EAgI6S5hX7edfD2qS+8TT3CEWkkzLtVegfzPRDhX27uzj10OHDh8+ce30dzSj6BIDl4tKo195QP3YE"
        "ZP/GbVfkWWxX6Ga3eG7IblKkrTIblNn62tu54a0+936M4L0JoMOKj9m5pcjmXQ8jjiliXOb7TPFgCntcph9UC9t96vDeZ87z"
        "KbPahC2J9j4B4PJ0B6T5HYLGTsFEX19fdjbd5Mp6pHh5mOVSDJt0S/13hMUNJhuofQ6+JgDaVUiyUExY2J761TSk+yUbs4iq"
        "ZN9OKiaLNf7gwOnTp+fN7OfN8CVm+Uv3/wH9L9kfpgLykQAAAABJRU5ErkJggg=="
    ),
    "icone-192.png": (
        "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"
    ),
    "icone-mascara-512.png": (
        "iVBORw0KGgoAAAANSUhEUgAAAgAAAAIACAYAAAD0eNT6AAAQqElEQVR42u3dX6xlV0HH8d/ae59778y9M7e3M60wrQHapiht"
        "BIvSkGgQxUSjPpBGTUQS4wvKEyEaEiMRNDE+GBT74p+oxCiJwQixPoiEghYVIUItBGgKQqT8GfpnmLl37p9zzt7Lh3Nnpkin"
        "M53OMOfe+XySmWaSNrdZ++y1vmvtfdqydvNtNQDANaUxBAAgAAAAAQAACAAAQAAAAAIAABAAAIAAAAAEAAAgAAAAAQAACAAA"
        "QAAAAAIAABAAAIAAAAAEAAAgAABAAAAAAgAAEAAAgAAAAAQAACAAAAABAAAIAABAAAAAAgAAEAAAgAAAAAQAACAAAAABAAAI"
        "AABAAACAAAAABAAAIAAAAAEAAAgAAEAAAAACAAAQAACAAAAABAAAIAAAAAEAAAgAAEAAAAACAAAQAACAAAAAAQAACAAAQAAA"
        "AAIAABAAAIAAAAAEAAAgAAAAAQAACAAAQAAAAAIAABAAAIAAAAAEAAAgAAAAAQAAAgAAEAAAgAAAAAQAACAAAAABAAAIAABA"
        "AAAAAgAAEAAAgAAAAAQAACAAAAABAAAIAABAAAAAAgAABIAhAAABAAAIAABAAAAAAgAAEAAAgAAAAAQAACAAAAABAAAIAABA"
        "AAAAAgAAEAAAgAAAAAQAACAAAAABAAACAAAQAACAAAAABAAAIAAAAAEAAAgAAEAAAAACAAAQAACAAAAABAAAIAAAAAEAAAgA"
        "AEAAAAACAAAEAAAgAAAAAQAACAAAQAAAAAIAABAAAIAAAAAEAAAgAAAAAQAACAAAQAAAAAIAABAAAIAAAAAEAAAIAABAAAAA"
        "AgAAEAAAgAAAAAQAACAAAAABAAAIAABAAAAAAgAAEAAAgAAAAAQAACAAAAABAAAIAAAQAACAAAAABAAAIAAAAAEAAAgAAEAA"
        "AAACAACYD50h4HzK2d8ALqxWYyAAuGIL8TB8535uX93QwMVpSjLqklKSoX5n5yoEwL5d+Kf97GYqJVkcJU2TpF7ZH1xrstDV"
        "jEZX+GcBe3vXv7v474xLHjtZMu1nIXDoQE0pSS8EBADPcg3eXfhrTVaXa56/VnNktWZlqaZrd3fmV+h4vi3Jqc2Se141zWt/"
        "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"
        "/O6FvPPvFjKeJoeXa3rP/QUAF4iA3S34F7/e5NHHk5uODrnp+lkILIxmLw3WS1j8U5O1lZpR98z/fFOSrZ3khutqrltJFkbx"
        "NUDgaeerrs1sZ9+XHH+y5OFH23zowTbv/uAoX/x6k7WVmoNLsfjPobJ2822exszrxSnnnqM1TbI4SlaW6iwALvFm/a61mgOL"
        "NUN95mP+Wku6tqZra84cOAB8yzyx+9dRV7KxmTzylTaPn0q2xyWHDtQsLeyeOhoqAcClh0AyO2YbnuP7ALP/CUe5qFu71nL2"
        "iM+HBHja+SmzeaktyeJCzaidbVjOPLJkfnkEsBcqu54Lge45vra50CUpF3FX1tnfZ+cPXOxpQK2zGBgc9wsArlwMPJeb9KK3"
        "8+odYN/yNUAAEAAAgAAAAAQAACAAAAABAAAIAABAAAAAAgAAEAAAgAAAAAQAACAAAAABAAAIAABAAAAAAgAAEAAAIAAAAAEA"
        "AAgAAEAAAAACAAAQAACAAAAABAAAIAAAAAEAAAgAAEAAAAACAAAQAACAAAAABAAAIAAAQAAAAAIAABAAAIAAAAAEAAAgAAAA"
        "AQAACAAAQAAAAAIAABAAAIAAAAAEAAAgAAAAAQAACAAAQAAAgAAAAAQAACAAAAABAAAIAABAAAAAAgAAEAAAgAAAAAQAACAA"
        "AAABAAAIAABAAAAAAgAAEAAAgAAAAAEAAAgAAEAAAAACAAAQAACAAAAABAAAIAAAAAEAAAgAAEAAAAACAAAQAACAAAAABAAA"
        "IAAAAAEAAAgAABAAAIAAAAAEAAAgAAAAAQAACAAAQAAAAAIAABAAAIAAAAAEAAAgAAAAAQAACAAAQAAAAAIAABAAACAAAAAB"
        "AAAIAABAAAAAAgAAEAAAgAAAAAQAACAAAAABAAAIAABAAAAAAgAAEAAAgAAAAAQAACAAAEAAAAACAAAQAACAAAAABAAAIAAA"
        "AAEAAAgAAEAAAAACAAAQAACAAAAABAAAIAAAAAEAAAgAAEAAAIAAAAAEAAAgAAAAAQAACAAAQAAAAAIAABAAAIAAAAAEAAAg"
        "AAAAAQAACAAAQAAAAAIAABAAAIAAAAABAAAIAABAAAAAAgAAEAAAgAAAAAQAACAAAIA58X8sKbm1JBrH5gAAAABJRU5ErkJg"
        "gg=="
    ),
    "icone-180.png": (
        "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"
        "jT4Pw25ByTcAAAAASUVORK5CYII="
    ),
}

MANIFESTO = {
    "name": "Consulta de Estoque",
    "short_name": "Estoque",
    "description": "Saldo, endereço e inventário do almoxarifado",
    "lang": "pt-BR",
    "start_url": "./",
    "scope": "./",
    "display": "standalone",
    "background_color": "#111C24",
    "theme_color": "#111C24",
    "icons": [
        {"src": "icone-192.png", "sizes": "192x192", "type": "image/png", "purpose": "any"},
        {"src": "icone-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any"},
        {"src": "icone-mascara-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
    ],
}

SERVICE_WORKER = """/* Gerado pelo build.py. Guarda o consultor no aparelho para funcionar sem internet.
   Com internet: busca sempre a versao nova primeiro (e guarda a copia).
   Sem internet, ou com a rede muito lenta: entrega a copia guardada. */
const VERSAO = 'estoque-__VERSAO__';
const FONTES = 'estoque-fontes';
const PAGINA = new URL('index.html', self.registration.scope).href;
const ESSENCIAIS = ['index.html', 'manifest.webmanifest', 'icone-192.png', 'icone-512.png',
                    'icone-mascara-512.png', 'icone-180.png'];

self.addEventListener('install', (e) => {
  e.waitUntil(caches.open(VERSAO).then((c) => c.addAll(ESSENCIAIS)).then(() => self.skipWaiting()));
});

self.addEventListener('activate', (e) => {
  e.waitUntil(caches.keys()
    .then((nomes) => Promise.all(nomes
      .filter((n) => n.startsWith('estoque-') && n !== VERSAO && n !== FONTES)
      .map((n) => caches.delete(n))))
    .then(() => self.clients.claim()));
});

self.addEventListener('fetch', (e) => {
  const req = e.request;
  if (req.method !== 'GET') return;
  const u = new URL(req.url);
  if (u.hostname === 'fonts.googleapis.com' || u.hostname === 'fonts.gstatic.com') {
    e.respondWith(guardadoPrimeiro(req, FONTES));
    return;
  }
  if (u.origin !== self.location.origin) return;        // outros sites: sempre direto na rede
  if (u.pathname.endsWith('/versao.txt')) return;        // aviso de versao nova: sempre da rede
  if (u.pathname.indexOf('/base/') >= 0) return;         // envio de planilhas: sempre direto ao servidor
  if (req.mode === 'navigate') { e.respondWith(paginaRedePrimeiro(req)); return; }
  e.respondWith(guardadoPrimeiro(req, VERSAO));
});

async function paginaRedePrimeiro(req) {
  const cache = await caches.open(VERSAO);
  const daRede = fetch(req).then((resp) => {
    if (resp && resp.ok) cache.put(PAGINA, resp.clone());
    return resp;
  });
  daRede.catch(() => {});
  try {
    // rede muito lenta: depois de 4 segundos mostra a copia guardada (e a rede atualiza a copia quando chegar)
    return await Promise.race([daRede, new Promise((_, nao) => setTimeout(() => nao(new Error('lenta')), 4000))]);
  } catch (erro) {
    const guardada = await cache.match(PAGINA);
    return guardada || daRede;
  }
}

async function guardadoPrimeiro(req, nome) {
  const cache = await caches.open(nome);
  const achou = await cache.match(req);
  if (achou) return achou;
  const resp = await fetch(req);
  if (resp && (resp.ok || resp.type === 'opaque')) cache.put(req, resp.clone());
  return resp;
}
"""


def gravar_app_instalavel(saida, versao):
    """Grava o service worker, o manifesto e os icones junto do index.html."""
    with open(os.path.join(saida, "sw.js"), "w", encoding="utf-8") as f:
        f.write(SERVICE_WORKER.replace("__VERSAO__", versao))
    with open(os.path.join(saida, "manifest.webmanifest"), "w", encoding="utf-8") as f:
        json.dump(MANIFESTO, f, ensure_ascii=False, indent=2)
    for nome, partes in ICONES.items():
        with open(os.path.join(saida, nome), "wb") as f:
            f.write(base64.b64decode("".join(partes)))

# arquivos que o build cria. O servidor so entrega estes, para ninguem
# na rede baixar as planilhas ou os scripts pelo navegador.
ARQUIVOS_DO_SITE = ("index.html", "versao.txt", "sw.js", "manifest.webmanifest",
                    "icone-192.png", "icone-512.png", "icone-mascara-512.png", "icone-180.png")

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
# atualizar a base pelo app: o que cada planilha e, e o que ela substitui
# --------------------------------------------------------------------------
TIPOS = {"SB2": "Saldo fisico", "SBF": "Saldo por endereco", "SDA": "A enderecar",
         "SD3": "Movimentacoes (SD3)", "SD3R": "Relacao de movimentacoes", "SBZ": "Indicadores (SBZ)"}
ARQUIVOS_LIDOS = []   # o que o ultimo build leu: [{"n": nome, "t": tipo, "f": [filiais]}]


def filiais_da_planilha(df):
    if df is None or "Filial" not in df.columns:
        return []
    # celula vazia vira "" ou "000000": nenhuma das duas e filial
    return sorted(set(c for c in (chave(v, 6) for v in df["Filial"]) if c and c.strip("0")))


def analisar_planilha(caminho):
    """Tipo e filiais de uma planilha, sem montar nada. Usado para conferir um envio."""
    tipo, df, erro = ler_planilha(caminho)
    return {"n": os.path.basename(caminho), "t": tipo, "f": filiais_da_planilha(df) if tipo else [], "erro": erro}


def mesma_familia(novo, atual):
    return novo == atual or (novo == "SD3" and atual == "SD3R")


def plano_de_troca(novos, atuais):
    """Cada planilha nova substitui as atuais do mesmo tipo cujas filiais ela cobre
    inteiras, e a que tiver o mesmo nome. A mesma regra existe no app (atualizar
    pelo GitHub): se mudar aqui, mude la tambem."""
    saem, avisos, vistos = [], [], set()
    for novo in novos:
        fn = set(novo["f"])
        for atual in atuais:
            if atual["n"] in vistos:
                continue
            fa = set(atual.get("f") or [])
            if atual["n"] == novo["n"]:
                saem.append(dict(atual, por=novo["n"], motivo="mesmo nome"))
                vistos.add(atual["n"])
            elif atual.get("t") and mesma_familia(novo["t"], atual["t"]) and fa <= fn:
                saem.append(dict(atual, por=novo["n"], motivo="mesmo tipo e filiais"))
                vistos.add(atual["n"])
            elif atual.get("t") and mesma_familia(novo["t"], atual["t"]) and fa & fn:
                avisos.append("%s cobre so parte das filiais de %s (%s): a antiga fica. Para trocar de vez, "
                              "exporte todas essas filiais juntas." % (novo["n"], atual["n"], ", ".join(sorted(fa - fn))))
    return {"entram": novos, "saem": saem, "avisos": avisos}


def repositorio():
    """Repositorio e ramo do GitHub, para o app saber para onde mandar as planilhas."""
    nome = os.environ.get("GITHUB_REPOSITORY", "")
    ramo = os.environ.get("GITHUB_REF_NAME", "")
    if not nome:
        try:
            import subprocess
            url = subprocess.run(["git", "remote", "get-url", "origin"], cwd=RAIZ, capture_output=True,
                                 text=True, timeout=5).stdout.strip()
            m = re.search(r"github\.com[:/]+([^/]+/[^/]+?)(?:\.git)?/?$", url)
            if m:
                nome = m.group(1)
                ramo = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], cwd=RAIZ, capture_output=True,
                                      text=True, timeout=5).stdout.strip()
        except Exception:
            pass
    if not nome:
        return None
    return {"nome": nome, "ramo": ramo or "main"}


# --------------------------------------------------------------------------
# conversoes
# --------------------------------------------------------------------------
def desligar_selecao_no_console():
    """No Windows, o "Modo de Edicao Rapida" do Prompt de Comando pausa o programa
    quando alguem clica dentro da janela, ate apertar uma tecla. Desliga so nesta
    janela. Em qualquer outro lugar (Linux, GitHub, VS Code) nao faz nada."""
    if os.name != "nt":
        return
    try:
        import ctypes
        k = ctypes.windll.kernel32
        k.GetStdHandle.restype = ctypes.c_void_p          # no Windows 64 bits o identificador e um ponteiro
        h = ctypes.c_void_p(k.GetStdHandle(-10))
        modo = ctypes.c_uint()
        if k.GetConsoleMode(h, ctypes.byref(modo)):
            k.SetConsoleMode(h, (modo.value | 0x80) & ~0x40)
    except Exception:
        pass


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
    lidos = []
    partes_sb2, partes_sbf, partes_sda, partes_sd3, partes_sd3r, partes_sbz = [], [], [], [], [], []
    print("Lendo planilhas de 'dados':")
    for caminho in arquivos:
        nome = os.path.basename(caminho)
        tipo, df, erro = ler_planilha(caminho)
        if tipo:
            lidos.append({"n": nome, "t": tipo, "f": filiais_da_planilha(df)})
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
    base["arquivos"] = lidos
    base["repo"] = repositorio()
    ARQUIVOS_LIDOS[:] = lidos

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
    gravar_app_instalavel(saida, "%s-%s" % (base["marca"], base.get("appv", "")))

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
