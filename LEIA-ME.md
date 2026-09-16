# Consulta de Estoque

App para consultar o estoque pelo computador e pelo celular: onde o produto
está, quanto tem, quanto está empenhado e o que falta acertar no endereçamento.

Ele monta tudo a partir das duas exportações do sistema:

| Exportação | Serve para |
|---|---|
| **Saldo físico** (SB2) | descrição, saldo, empenho, custo, última saída |
| **Saldo por endereço** (SBF) | o endereço físico do produto (A03-B04, por exemplo) |

As duas se ligam por **Filial + Produto + Armazém**.

---

## Primeira vez

1. Instale o Python: <https://www.python.org/downloads/>.
   Marque **"Add Python to PATH"** na tela da instalação.
2. Abra esta pasta no VS Code (`Arquivo > Abrir Pasta`).
3. Instale as bibliotecas: `Ctrl+Shift+P` → *Tasks: Run Task* →
   **Instalar as bibliotecas**. Ou no terminal: `pip install -r requirements.txt`

---

## Dia a dia

**1. Coloque as planilhas na pasta `dados`.**
Pode ser mais de um arquivo de cada tipo, um por filial. O nome não importa —
o programa descobre o tipo pelas colunas.

**2. Ligue o app.**
Duplo clique em **`iniciar.bat`**, ou `Ctrl+Shift+B` no VS Code.

O terminal mostra os dois endereços:

```
  Neste computador:  http://localhost:8080
  No celular:        http://192.168.0.15:8080
```

**3. No celular.** Mesmo wi-fi, digite o segundo endereço. Vale salvar na tela
de início: no Chrome `⋮ > Adicionar à tela inicial`, no iPhone o botão de
compartilhar `> Adicionar à Tela de Início`.

**4. Para atualizar.** Salve as planilhas novas por cima das antigas na pasta
`dados`. Em alguns segundos o app se regenera e as páginas abertas recarregam
sozinhas. Editar o `template.html` tem o mesmo efeito.

Para desligar: `Ctrl+C` no terminal, ou feche a janela.

---

## As quatro abas

- **Produtos** — busca por código ou descrição, com várias palavras
  (`filtro fleetguard`). Abrindo o item: saldo, empenho, disponível, todos os
  endereços, saldo por armazém, última saída, custo e valor em estoque.
- **Endereços** — o caminho inverso. Escolhe a rua e vê o que está guardado lá.
- **Separação** — monta a lista de material a separar, ordenada por endereço,
  e imprime. Fica salva no aparelho que montou a lista.
- **Conferência** — itens com saldo e sem endereço, divergências entre a soma
  dos endereços e o saldo físico, itens a endereçar, sem saída há mais de um
  ano e com pedido a receber.

---

## Os arquivos

```
dados/            as planilhas exportadas do sistema  ← você mexe aqui
template.html     a aparência e o funcionamento do app
build.py          lê as planilhas e gera o app
servidor.py       vigia a pasta, regera e publica na rede
iniciar.bat       liga tudo
index.html        o app pronto (gerado, não edite)
versao.txt        gerado, é o sinal de "recarregue a página"
```

---

## Perguntas rápidas

**Precisa de internet?** Não. A única coisa que vem da internet é a fonte do
texto; sem conexão o app usa a fonte do sistema e funciona igual.

**Dá para mandar o app para alguém?** Sim. O `index.html` é um arquivo só, com
os dados dentro. Mande por e-mail ou copie para a área de trabalho e a pessoa
abre com duplo clique, sem instalar nada. Só não se atualiza sozinho.

**Quero esconder os custos.** No topo do `build.py`, troque para
`INCLUIR_CUSTOS = False` e gere de novo. Os custos e valores saem da base
inteira, não só da tela.

**As planilhas ficam expostas na rede?** Não. O servidor entrega só o
`index.html` e o `versao.txt`. Quem tentar abrir `/dados/...` ou `/build.py`
no navegador recebe erro.

**Trocou a planilha e nada mudou?** O arquivo precisa estar salvo e fechado —
o Excel segura o arquivo enquanto está aberto. No canto de cima do app tem uma
marca de versão (`base de 16/09/2026 · v4395d`) que muda quando os dados
mudam; se ela não mudou, o app não foi regerado.

**Sobrou exportação antiga na pasta?** Se você acrescentou os arquivos novos
sem apagar os velhos, os dois entram. O build percebe, descarta as linhas
repetidas mantendo as do arquivo mais recente e avisa na tela. Mas o certo é
apagar as antigas.

**Aparece "colunas não reconhecidas".** O saldo físico precisa ter `Filial`,
`Produto`, `Armazem`, `Nome Cientif` e `Saldo Atual`. O saldo por endereço
precisa ter `Filial`, `Produto`, `Armazem`, `Endereco`, `Prioridade` e
`Quantidade`.

---

## Dois detalhes desta base

**Filiais com cadastro diferente.** O código `010100001` é ETANOL COMUM na
020102 e CAMINHÃO MERCEDES na 100106. Por isso cada filial é tratada separada,
nunca somada pelo código.

**Filial 100102.** Ela aparece no saldo por endereço mas não veio em nenhum
arquivo de saldo físico. Esses itens mostram só o endereçamento, e o app avisa
isso na tela do produto. Se exportar o saldo físico dela, o aviso some sozinho.
