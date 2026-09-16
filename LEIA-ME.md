# Consulta de Estoque

App para consultar o estoque pelo computador e pelo celular: onde o produto está,
quanto tem, quanto está empenhado e o que falta acertar no endereçamento.

Ele monta tudo a partir das duas exportações do sistema:

| Exportação | Serve para |
|---|---|
| **Saldo físico** (SB2) | descrição, saldo, empenho, custo, última saída |
| **Saldo por endereço** (SBF) | o endereço físico de cada produto (A03-B04, por exemplo) |

As duas se ligam por **Filial + Produto + Armazém**.

---

## Primeira vez (uma vez só)

**1. Instale o Python**
Baixe em <https://www.python.org/downloads/>. Na tela de instalação,
marque **"Add Python to PATH"** antes de clicar em Install.

**2. Abra a pasta no VS Code**
`Arquivo > Abrir Pasta` e escolha esta pasta.

**3. Instale as bibliotecas**
No VS Code: `Ctrl+Shift+P` → *Tasks: Run Task* → **Instalar as bibliotecas**.
Ou pelo terminal: `pip install -r requirements.txt`

---

## Usando no dia a dia

**1. Coloque as planilhas na pasta `dados`**
Exporte do sistema e salve os `.xlsx` ali. Pode ser mais de um arquivo de cada
tipo (um por filial, por exemplo). O nome não importa — o programa descobre o
tipo pelas colunas.

**2. Ligue o app**
Duplo clique em **`iniciar.bat`** (Windows) ou, no VS Code, `Ctrl+Shift+B`.

O terminal mostra:

```
  Consulta de Estoque no ar

  Neste computador:  http://localhost:8080
  No celular:        http://192.168.0.15:8080
```

**3. No celular**
Com o celular no mesmo wi-fi, digite o segundo endereço no navegador.
Vale salvar na tela de início do telefone: no Chrome, `⋮ > Adicionar à tela
inicial`; no iPhone, botão de compartilhar `> Adicionar à Tela de Início`.
Fica com ícone, igual a um aplicativo.

**4. Para atualizar os dados**
Exporte de novo e salve por cima dos arquivos da pasta `dados`.
Em poucos segundos o app se regenera e as páginas abertas recarregam sozinhas.
Não precisa parar nem reiniciar nada.

Para desligar: `Ctrl+C` no terminal, ou feche a janela.

---

## O que tem em cada aba

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

## Arquivos do projeto

```
dados/              as planilhas exportadas do sistema  ← você mexe aqui
app/template.html   a aparência e o funcionamento do app
dist/index.html     o app pronto (gerado, não edite)
build.py            lê as planilhas e monta o app
servidor.py         vigia a pasta, regera e publica na rede
iniciar.bat         atalho para ligar tudo no Windows
```

---

## Perguntas rápidas

**Precisa de internet?**
Não. Tudo roda na sua máquina. A única coisa que vem da internet é a fonte do
texto; sem conexão o app usa a fonte do sistema e funciona igual.

**Dá para mandar o app pronto para alguém?**
Sim. O `dist/index.html` é um arquivo só, com os dados dentro. Mande por e-mail
ou WhatsApp e a pessoa abre com duplo clique — sem instalar nada. Só não se
atualiza sozinho: quando os dados mudarem, mande o arquivo novo.

**Quero mudar a porta 8080**
No terminal: `set PORTA=9000` (Windows) ou `export PORTA=9000` e ligue de novo.

**O celular não abre o endereço**
Os dois têm que estar no mesmo wi-fi. Se ainda assim não abrir, é o firewall do
Windows: na primeira execução ele pergunta se libera o Python na rede —
responda que sim, para redes privadas.

**Mudei a planilha e nada aconteceu**
O arquivo precisa estar salvo e fechado. O Excel segura o arquivo enquanto está
aberto. Veja também se caiu na pasta `dados` mesmo.

**Aparece "colunas não reconhecidas"**
A exportação veio sem as colunas esperadas. O saldo físico precisa ter
`Filial`, `Produto`, `Armazem`, `Nome Cientif` e `Saldo Atual`. O saldo por
endereço precisa ter `Filial`, `Produto`, `Armazem`, `Endereco`, `Prioridade`
e `Quantidade`.

---

## Dois detalhes desta base

**Filiais com cadastro diferente.** O código `010100001` é ETANOL COMUM na
020102 e CAMINHÃO MERCEDES na 100106. Por isso cada filial é tratada separada,
nunca somada pelo código.

**Filial 100102.** Ela aparece no saldo por endereço mas não veio em nenhum
arquivo de saldo físico. Esses itens mostram só o endereçamento, e o app avisa
isso na tela do produto. Se exportar o saldo físico dela e jogar na pasta
`dados`, o aviso some sozinho.
