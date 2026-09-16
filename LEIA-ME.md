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
Exporte de novo e salve por cima dos arquivos da pasta `dados`. Mexer no
`app/template.html` tem o mesmo efeito.
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
docs/index.html     o app pronto (gerado, não edite)
build.py            lê as planilhas e monta o app
servidor.py         vigia a pasta, regera e publica na rede
iniciar.bat         atalho para ligar tudo no Windows
publicar.bat        gera o app e envia para o GitHub num clique
area-de-trabalho.bat  poe o app na sua area de trabalho
automatico.bat      liga e desliga a publicacao sozinha
vigia.py            fica de olho nas pastas e publica sem janela
config.txt          suas preferencias (gerado no primeiro uso)
vigia.log           o que o vigia fez (gerado no primeiro uso)
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

## Colocar na área de trabalho

Duplo clique em **`area-de-trabalho.bat`** e escolha uma das opções.

### Opção 1 — atalho do app

Cria um ícone chamado **Consulta de Estoque** na sua área de trabalho.
Clicou, ele liga o servidor e abre o navegador já na tela certa. Os dados são
sempre os das planilhas que estão na pasta `dados` naquele momento, e o celular
continua funcionando pelo IP.

Precisa do Python instalado e a pasta do projeto tem que continuar onde está —
o atalho aponta para ela.

### Opção 2 — cópia solta

Copia o app para a área de trabalho como **Consulta de Estoque.html**, um
arquivo único de uns 2,6 MB. Duplo clique e abre, sem Python, sem servidor e
sem internet.

Em compensação ele é uma fotografia: guarda os dados do momento em que foi
gerado. Quando os dados mudarem, rode o `area-de-trabalho.bat` de novo para
substituir a cópia. É a melhor opção para levar num notebook, mandar por
e-mail ou deixar numa máquina que não tem nada instalado.

### Opção 3 — instalar como aplicativo de verdade

Essa é a mais confortável para o dia a dia. Com o app aberto pelo servidor
(`http://localhost:8080`):

- **Chrome**: ícone de instalar na barra de endereço, ou menu `⋮ > Transmitir,
  salvar e compartilhar > Instalar página como app`
- **Edge**: menu `... > Aplicativos > Instalar este site como um aplicativo`

Ele vira uma janela própria, com o ícone da etiqueta amarela, sem barra de
navegação, e aparece no menu Iniciar e na barra de tarefas. Você pode arrastar
para a área de trabalho de lá.

Instalado assim ele também **abre sem rede**: se o servidor estiver desligado
ou o wi-fi cair, ele mostra a última versão que carregou. Quando o servidor
volta, os dados se atualizam sozinhos.

No celular é o mesmo caminho: abra pelo IP e use `Adicionar à tela de início`.

### Qual usar

| Situação | Melhor opção |
|---|---|
| Uso diário no seu computador | Instalar como aplicativo |
| Computador sem Python instalado | Cópia solta |
| Levar para outro lugar, mandar para alguém | Cópia solta |
| Quer o ícone mas prefere abrir no navegador | Atalho do app |

---

## Enviar para o GitHub

O `publicar.bat` faz tudo num clique: gera o app com as planilhas de agora,
registra a versão e envia para o GitHub.

### Antes de tudo: privado ou público?

Essa escolha importa mais que o resto. O `dist/index.html` carrega os saldos,
os custos unitários e o valor em estoque de cada item — na base de hoje, R$ 72
milhões em estoque.

- **Private** — só você e quem você convidar enxergam. É o recomendado.
- **Public** — qualquer pessoa na internet vê tudo. Só escolha isso se a sua
  empresa não se importar em expor esses números.

As planilhas da pasta `dados` **não** são enviadas em nenhum dos dois casos.
Isso está no `.gitignore`, e dá para mudar se você quiser.

### Primeira vez

1. Instale o Git: <https://git-scm.com/download/win>, opções padrão.
2. No GitHub, clique em **New repository**, dê um nome, escolha **Private** e
   **não marque nada** em "Initialize this repository". Copie o endereço que
   termina em `.git`.
3. Duplo clique em **`publicar.bat`** e cole o endereço quando ele pedir.
4. Vai abrir uma janela do navegador pedindo o login da sua conta do GitHub.
   Entre por ali. Isso acontece uma vez só — o Windows guarda o acesso.

### Nos próximos dias

Mexeu no app ou trocou as planilhas? Duplo clique em `publicar.bat`.
Ele mostra o que mudou, pergunta uma descrição (pode dar Enter e ele usa a
data) e envia. Se nada tiver mudado, ele avisa e não faz nada.

### Abrir o app pela internet

Veja a seção "Abrir de qualquer lugar, fora da rede da empresa" mais abaixo.

### Sobre o tamanho do repositório

Cada versão enviada guarda o `docs/index.html` inteiro, uns 700 KB depois de
compactado. Enviando todo dia, o repositório cresce perto de 250 MB por ano —
funciona, mas em algum momento vale limpar. Se chegar lá, me avise que eu
passo o procedimento.

---

## Abrir de qualquer lugar, fora da rede da empresa

Enviar para o GitHub **não** coloca nada no ar. Para virar um endereço que
qualquer celular abre, de qualquer lugar, é preciso ligar o GitHub Pages.

### Ligando o Pages

No repositório: **Settings > Pages**. Duas formas, escolha uma:

- **Deploy from a branch** → branch `main`, pasta `/docs`. É por isso que a
  saída do projeto se chama `docs`: o Pages só aceita a raiz ou essa pasta.
- **GitHub Actions** → usa o workflow que já está em `.github/workflows/`.

Em um ou dois minutos o endereço aparece na própria tela de Pages, no formato
`https://SEUUSUARIO.github.io/NOME-DO-REPOSITORIO/`.

### Conferindo se sincronizou

No canto de cima do app tem a data da base e uma marca curta, tipo
`base de 16/09/2026 · v88b9a`. Essa marca muda só quando os dados mudam de
verdade.

Abra o app no computador e no celular e compare as duas marcas. Iguais,
estão na mesma versão. Diferentes, o aparelho de trás está com uma cópia
velha: puxe a tela para baixo para recarregar, ou espere alguns minutos,
porque o GitHub guarda o arquivo em cache por até 10 minutos.

### O preço de deixar público

Repositório público quer dizer que **qualquer pessoa na internet** baixa o
que você enviou, mesmo sem o Pages ligado. O app carrega saldo, endereço,
custo unitário e valor em estoque de cada item.

Você tem três caminhos:

**1. Deixar o repositório privado.** O app fica completo, o GitHub serve de
backup e histórico, e o acesso continua pelo servidor local na rede da
empresa. Pages em repositório privado exige plano pago — confirme no site do
GitHub, que os planos mudam.

**2. Público, mas sem preço.** No `automatico.bat`, opção **[8] > [2]**, ou
no `config.txt`:

```
incluir_custos = nao
```

Os custos e valores saem da base inteira, não só da tela — nem abrindo o
código-fonte alguém acha. Ficam o produto, o endereço e a quantidade. Continua
sendo informação da empresa, mas sem expor preço de compra.

**3. Público com tudo.** Só se a sua empresa disser que não há problema.

Se você já enviou a versão com custos para um repositório público, mudar a
configuração agora não apaga o que já foi. O histórico do Git guarda todas as
versões anteriores. Nesse caso o caminho é apagar o repositório no GitHub e
criar outro, ou me pedir o procedimento para limpar o histórico.

---

## Publicar sozinho, sem clicar em nada

O `publicar.bat` continua existindo para quando você quiser enviar na hora.
Mas dá para o envio acontecer sozinho: você salva a planilha ou mexe no app, e
alguns segundos depois já está no GitHub.

Quem faz isso é o **vigia**. Ele observa a pasta `dados` e a pasta `app`.
Quando algo muda, ele espera os arquivos pararem de mexer, gera o app e envia.

### Ligando

**1. Faça um envio manual primeiro.** Rode o `publicar.bat` uma vez e faça o
login do GitHub. É obrigatório: o envio automático nunca pergunta senha, então
o acesso já precisa estar guardado no Windows.

**2. Abra o `automatico.bat`** e escolha:

- **[1] Ligar a publicação automática** — grava a preferência no `config.txt`
- **[5] Fazer o vigia subir junto com o Windows** — a partir daí ele liga
  sozinho toda vez que você entra no computador, sem janela nenhuma

Pronto. Não tem mais clique nenhum no dia a dia.

### Vendo o que ele andou fazendo

Como ele roda escondido, tudo fica anotado no `vigia.log`. A opção **[7]** do
menu mostra as últimas linhas:

```
[16/09/2026 17:25:53] Mudanca detectada.
[16/09/2026 17:26:00] App gerado.
[16/09/2026 17:26:00] Enviado: Enviado para o GitHub.
```

O mesmo menu mostra, no topo, se o vigia está rodando agora e se está
instalado no início do Windows.

### Detalhes que importam

**Salvou três vezes seguidas?** Vira um envio só. Ele espera os arquivos
ficarem parados por uns segundos antes de agir, então não enche o repositório
de versões repetidas.

**Nada mudou de verdade?** Ele não envia. Abrir e fechar a planilha sem
alterar nada não gera commit.

**Deu erro?** Ele anota no log e continua vigiando. Se o login do GitHub
expirar, o log avisa e basta rodar o `publicar.bat` uma vez de novo.

**O servidor também publica.** Se você deixa o `iniciar.bat` aberto, ele faz o
mesmo assim que a publicação automática está ligada — não precisa dos dois
rodando ao mesmo tempo.

**Para desligar:** opção [2] para parar de publicar, ou [6] para tirar o vigia
do início do Windows.

---

## Dois detalhes desta base

**Filiais com cadastro diferente.** O código `010100001` é ETANOL COMUM na
020102 e CAMINHÃO MERCEDES na 100106. Por isso cada filial é tratada separada,
nunca somada pelo código.

**Filial 100102.** Ela aparece no saldo por endereço mas não veio em nenhum
arquivo de saldo físico. Esses itens mostram só o endereçamento, e o app avisa
isso na tela do produto. Se exportar o saldo físico dela e jogar na pasta
`dados`, o aviso some sozinho.
