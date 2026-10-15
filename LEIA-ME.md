# Consulta de Estoque

App para consultar o estoque pelo computador e pelo celular: onde o produto
está, quanto tem, quanto está empenhado e o que falta acertar no endereçamento.

Ele monta tudo a partir das duas exportações do sistema:

| Exportação | Serve para |
|---|---|
| **Saldo físico** (SB2) | descrição, saldo, empenho, custo, última saída |
| **Saldo por endereço** (SBF) | o endereço físico do produto (A03-B04, por exemplo) |
| **Produtos a endereçar** (SDA) | o que entrou por nota e ainda espera endereço — opcional |
| **Movimentações internas** (SD3) | o que saiu, de qual endereço, para o inventário rotativo — opcional |
| **Indicadores de produto** (SBZ) | se o produto controla endereço, por filial — opcional |

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

## As cinco abas

- **Produtos** — busca por código ou descrição, com várias palavras
  (`filtro fleetguard`). Abrindo o item: saldo, empenho, disponível, todos os
  endereços, saldo por armazém, última saída, custo e valor em estoque.
  Cada produto com saldo tem uma caixa de seleção à esquerda: marque os que
  quer e toque em **Separar** para mandar todos de uma vez para a lista de
  separação. A seleção continua valendo se você fizer outra busca, então dá
  para juntar produtos de buscas diferentes. **Selecionar todos** marca todos
  os produtos da busca atual — inclusive os que não couberam na tela. Produto
  que já está na lista de separação não é somado de novo.
- **Endereços** — o caminho inverso. Escolhe a rua e vê o que está guardado lá.

Na aba Produtos, cada produto mostra o campo **Contr. Endereço** da SBZ, com o
mesmo valor da tabela: **Sim** ou **Nao**. Uma fileira de botões filtra por ele:
**Todos**, **Sim**, **Nao** e **Fora da SBZ** (produto que não tem registro na
SBZ), cada um com a quantidade ao lado.
- **Pendentes** — o que chegou por nota e ainda não tem endereço, agrupado
  por nota fiscal, da mais antiga para a mais nova. Notas com mais de 7 dias
  aparecem em laranja. Quando o produto já tem estoque guardado em algum
  lugar, o cartão mostra esse endereço como sugestão de onde guardar. Busca
  por código, descrição ou número da nota, e imprime com uma coluna em branco
  para anotar onde foi guardado.
- **Inventário** — tem dois modos, escolhidos no topo da aba, e uma linha de
  **Filiais** onde dá para marcar **uma ou várias** filiais. Nesta aba, os botões
  de filial do topo do app somem, para não ter dois controles; ao voltar para as
  outras abas eles reaparecem como estavam.
  - **Rotativo · o que saiu**: conta o que saiu, pela SD3, no endereço de onde
    saiu. Filtra por dia e por tipo de produto.
  - **Completo · 100%**: todo o saldo das filiais marcadas, para o inventário
    geral. Com mais de uma filial, os endereços de mesmo nome continuam
    separados (o R01 de uma filial é outra prateleira que o R01 da outra), e
    a folha ganha a coluna Filial. Uma linha por endereço com saldo, mais uma linha para o
    saldo **sem endereço** e para a **diferença** quando o saldo do armazém é
    maior que a soma dos endereços — assim nada fica sem ser contado. Material
    com **saldo negativo** no sistema também entra, marcado em vermelho. Os
    itens de custo do Protheus (códigos "MO…": mão de obra, depreciação, GGF)
    ficam de fora, porque não são material físico.
    Ordena por **endereço** (o percurso no galpão), **código**, **descrição** ou
    **armazém**, filtra por armazém, e a busca serve para contar uma rua só
    (digite "A03"). A tela mostra todas as linhas, desenhando conforme você rola; a impressão
    também sai com todas, com coluna "Contado" e linhas de assinatura. Dá para imprimir também um
    endereço só, pelo ícone no cabeçalho dele.
  Nos dois modos, a opção "Contagem cega" tira o saldo do sistema da folha.
- **Separação** — monta a lista de material a separar, ordenada por endereço,
  e imprime. Fica salva no aparelho que montou a lista.

---

## Instalar no celular e usar sem internet

O consultor pode ser **instalado** como um app, com ícone próprio — a etiqueta
amarela de prateleira — e funciona **sem internet**, com a última base que
abriu no aparelho.

- **Android e computador (Chrome ou Edge):** no fim da lista de produtos
  aparece o botão **Instalar o consultor neste aparelho**. Também dá pelo menu
  do navegador, em "Instalar app".
- **iPhone:** no Safari, toque em Compartilhar e depois em "Adicionar à Tela de
  Início". O app mostra essa dica no fim da lista.

Sem internet, aparece um aviso no topo dizendo de quando é a base que está na
tela. Busca, Endereços, Pendentes, Inventário e Separação funcionam
normalmente.

Com internet, o app busca sempre a versão nova primeiro, então ele **não fica
preso numa base velha**: quando você publica planilhas novas, a versão nova
chega sozinha.

**Onde funciona:** pelo site do GitHub (endereço https) e, no computador do
servidor, pelo `http://localhost:8080`. **Não** funciona pelo endereço com IP
da rede local (`http://192.168...`): os navegadores só permitem app offline
em endereço seguro. No celular, use o site do GitHub para instalar.

Os arquivos que fazem isso — `sw.js`, `manifest.webmanifest` e os
`icone-*.png` — são gerados pelo build junto com o `index.html`. Não precisa
copiar nem editar, e eles não vão para o repositório.

### Velocidade

O app abre mais rápido porque desenha primeiro o que você vê: os ~40 mil
produtos sem saldo são montados em segundo plano depois que a lista aparece, e
as listas longas são desenhadas conforme você rola.

---

## Os arquivos

```
dados/            as planilhas exportadas do sistema  ← você mexe aqui
template.html     a aparência e o funcionamento do app
build.py          lê as planilhas e gera o app
servidor.py       vigia a pasta, regera, publica na rede e envia ao GitHub
iniciar.bat       liga tudo aqui no computador
publicar.bat      gera o app e manda para o GitHub em um clique (dá para
                  fazer o mesmo pelo painel do VS Code)
verificar.bat     diz por que o GitHub não está gerando o app
verificar.py      o diagnóstico que o verificar.bat roda
requirements.txt  as bibliotecas do Python que o projeto usa
index.html        o app pronto (gerado, não edite)
versao.txt        gerado, é o sinal de "recarregue a página"
sw.js             gerado, guarda o app no aparelho para funcionar sem internet
manifest.webmanifest, icone-*.png
                  gerados, nome e ícones do app instalado
.github/          a receita que o GitHub usa para gerar o app sozinho
.vscode/          os atalhos do VS Code (Iniciar, Gerar, Instalar bibliotecas)
.gitignore        o que nunca vai para o GitHub (app gerado, chaves)
.gitattributes    mantém as quebras de linha certas entre Windows e GitHub
```

---

## Subir para o GitHub e o app se atualizar sozinho

O GitHub recebe as **planilhas**, não o app pronto. Ele mesmo lê a pasta
`dados`, gera o app e publica o site. Assim qualquer aparelho, em qualquer
lugar, vê a versão nova — sem precisar de Python na máquina de quem atualiza.

### Ligando, uma vez só

1. Instale o Git: <https://git-scm.com/download/win>, opções padrão. Feche e
   abra o VS Code depois.
2. No VS Code, abra o painel **Controle do Código-Fonte** (o ícone de três
   bolinhas ligadas, na barra da esquerda, ou `Ctrl+Shift+G`).
3. Clique em **Publicar no GitHub**. Ele pede o login pelo navegador e
   pergunta o nome do repositório e se é **privado ou público** — leia o aviso
   sobre isso mais abaixo antes de responder.
4. No site do repositório: **Settings > Pages > Source: GitHub Actions**.

O endereço do site aparece nessa mesma tela, no formato
`https://SEUUSUARIO.github.io/NOME-DO-REPOSITORIO/`.

### No dia a dia, pelo VS Code

1. Salve as planilhas novas **por cima** das antigas, na pasta `dados`.
2. No painel Controle do Código-Fonte, os arquivos trocados aparecem na lista.
3. Escreva uma frase curta na caixa de cima (ex.: "estoque de 16/09") e clique
   em **Confirmar**.

Só isso. O envio para o GitHub acontece junto com a confirmação — isso está
configurado no `.vscode/settings.json`. Em uns dois minutos o site está
atualizado e as páginas abertas recarregam sozinhas.

**Se o arquivo novo tiver nome diferente do antigo**, apague o antigo pelo
Explorador do VS Code (botão direito, Excluir). Senão os dois ficam na pasta e
sobem juntos. O build percebe e descarta as linhas repetidas, mas o certo é
apagar. O arquivo apagado aparece no painel com um `D` do lado, e some do
GitHub quando você confirma.

**Para acompanhar**, a aba **Actions** do repositório mostra cada geração.
Verde deu certo, vermelho deu erro — clicando você vê onde parou.

O `publicar.bat` faz o mesmo sem abrir o VS Code: confere as planilhas, gera o
app, e envia ao GitHub com um clique.

### Conferindo se atualizou

No canto de cima do app tem a data da base e uma marca curta, tipo
`base de 16/09/2026 · v4395d`. Essa marca muda só quando os dados mudam.
Compare entre os aparelhos: iguais, mesma versão. O GitHub Pages guarda o
arquivo em cache por até uns 10 minutos.

### Antes de escolher Public

Agora as **planilhas** vão para o GitHub, não só o app. Elas trazem a base
completa: 45 mil produtos, saldos, custos unitários e valores. Em repositório
público, qualquer pessoa na internet baixa esses arquivos direto.

- **Private** é o certo para este caso. O Actions gera o app normalmente. Só
  que o GitHub Pages em repositório privado exige plano pago — confirme no
  site do GitHub, que os planos mudam.
- **Public** só se a sua empresa disser que não há problema. Se for por esse
  caminho, tire ao menos os custos: no topo do `build.py`, deixe
  `INCLUIR_CUSTOS = False`. Isso limpa o app, mas **não** limpa as planilhas,
  que continuam inteiras no repositório.

### Sobre o tamanho do repositório

Um `.xlsx` já é um arquivo compactado, então o Git não consegue guardar só a
diferença entre duas versões. Medindo com a sua base, cada exportação nova
custa cerca de **4 a 5 MB** de histórico. Atualizando toda semana, dá uns
250 MB por ano; todo dia, passa de 1 GB. Funciona, mas em algum momento vale
limpar o histórico. Quando chegar lá, me peça o procedimento.

---

## Deixar tudo automático

Com o `iniciar.bat` aberto, você não precisa clicar em mais nada. Ele fica
observando a pasta `dados` e, quando uma planilha muda:

1. gera o app aqui no computador, e as páginas abertas recarregam sozinhas;
2. manda as planilhas novas para o GitHub;
3. o GitHub gera o app e atualiza o site, em uns dois minutos.

Ou seja: salvar a exportação por cima da antiga é a única coisa que você faz.

No terminal você acompanha cada passo:

```
[14:32:07] Mudanca detectada, gerando o app de novo...
App gerado: index.html  (2.7 MB)
  Enviando para o GitHub...
  OK - planilhas enviadas. O GitHub vai publicar em uns 2 minutos.
```

### Antes de contar com isso

O envio automático **nunca pergunta senha**. Então o login do GitHub já precisa
estar guardado: publique uma vez pelo VS Code ou pelo `publicar.bat`. Enquanto
isso não acontecer, o terminal avisa em vez de travar esperando.

Se você salvar a planilha três vezes seguidas, vira um envio só. Ele espera os
arquivos ficarem parados alguns segundos antes de agir.

Se nada mudou de verdade, ele não envia. Abrir e fechar a planilha sem alterar
nada não gera versão nova.

Se der erro — login vencido, sem internet, alguém enviou antes — ele escreve o
motivo no terminal e continua vigiando. O servidor não cai, e na próxima
alteração tenta de novo.

### Para desligar o envio automático

No topo do `servidor.py`:

```
ENVIAR_PARA_O_GITHUB = False
```

Aí ele volta a só gerar o app aqui, sem mandar nada para lugar nenhum.

### E a janela precisa ficar aberta?

Sim. É o `iniciar.bat` que vigia a pasta. Pode deixar minimizado no canto.
Se você quiser isso rodando sem janela nenhuma, iniciando junto com o Windows,
me peça que eu preparo.

---

## Subi para o GitHub e o app não mudou

Duplo clique em **`verificar.bat`**. Ele olha o repositório e aponta o que
falta. Se do lado de cá estiver tudo certo, ele diz o que conferir no site do
GitHub, na ordem.

As causas, da mais comum para a menos:

**O `index.html` ficou versionado de antes.** Nas versões anteriores deste
projeto o app ia junto para o GitHub. Agora quem gera é o GitHub, então ele
não deve mais subir — mas colocar no `.gitignore` não desfaz o que já estava
lá dentro. Resultado: o repositório continua carregando um `index.html` velho
e o site mostra ele. O `verificar.bat` detecta e corrige, tirando o arquivo do
repositório sem apagar da sua pasta.

**A pasta `.github` não foi copiada.** Ela começa com ponto e o Windows a
esconde. Quando se arrastam os arquivos de uma pasta para outra, ela fica para
trás — e sem ela o GitHub não tem a receita, então nada acontece. Mesma coisa
com o `.gitignore` e o `.vscode`.

**O Pages está na fonte errada.** Em *Settings > Pages > Source* tem que estar
**GitHub Actions**. Se estiver em *Deploy from a branch*, o site serve os
arquivos crus do repositório, e como o `index.html` não vai mais para lá, você
vê a versão antiga ou um erro 404.

**O branch tem outro nome.** A receita roda em `main` e `master`. Em qualquer
outro nome ela não dispara.

**O repositório é privado sem plano pago.** O Actions gera o app normalmente,
mas a publicação falha. Aparece vermelho na aba Actions.

### A aba Actions responde quase tudo

No seu repositório, aba **Actions**. Cada envio vira uma linha ali.

- **Nenhuma linha** — a receita não chegou ao GitHub, ou o branch é outro.
- **Bolinha amarela** — está rodando, espere os dois minutos.
- **Bolinha verde** — gerou e publicou. Se o site ainda mostra o antigo, é
  cache: recarregue segurando Ctrl. Pode levar uns 10 minutos.
- **Bolinha vermelha** — clique nela e depois no passo vermelho. A mensagem
  de erro é a mesma que apareceria aqui no seu computador.

---

## Perguntas rápidas

**Precisa de internet?** Não. A única coisa que vem da internet é a fonte do
texto; sem conexão o app usa a fonte do sistema e funciona igual.

**Dá para mandar o app para alguém?** Sim. O `index.html` é um arquivo só, com
os dados dentro. Mande por e-mail ou copie para a área de trabalho e a pessoa
abre com duplo clique, sem instalar nada. Só não se atualiza sozinho.

**Por que o `index.html` não vai para o GitHub?** Porque lá ele é gerado a
partir das planilhas. Mandar os dois seria guardar a mesma informação duas
vezes e engordar o repositório à toa.

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
`Quantidade`. A lista de produtos a endereçar precisa ter `Filial`, `Produto`,
`Armazem`, `Qtd Original`, `Saldo` e `Documento`. A relação de movimentações
internas (SD3) precisa ter `Filial`, `Produto`, `TP Movimento`, `Quantidade` e
`Endereco`. Para o filtro por tipo funcionar, a exportação precisa trazer o
tipo do produto preenchido (`Tipo Produto` ou `Tipo`). Movimentos estornados
ficam de fora sozinhos. A SBZ precisa ter `Filial`, `Codigo` e `Contr.Endere`.

**Sobre o "controla endereço".** O indicador vem da SBZ, que é por filial. Ele
aparece na lista de produtos e na ficha do produto (bloco "Onde está"). Na
lista ele muda um aviso: um
produto com saldo e sem endereço só fica em laranja se ele controla endereço.
Diesel, bauxita e outros produtos a granel com Contr. Endereço = Nao
aparecem com a etiqueta "Contr. Endereço: Nao", sem alarme — para eles, ficar
sem endereço é o normal. Produto que não está na SBZ aparece como "fora
da SBZ" e continua com o aviso, porque nesse caso o indicador mora no
cadastro de produtos (SB1), que não está na base.

**Para o inventário rotativo fazer sentido**, exporte o saldo por endereço
*depois* das movimentações do dia. O número "Sistema" da folha vem dele: se o
saldo por endereço for de antes das saídas, ele não reflete o que saiu e a
contagem vai dar diferença em tudo.

---

## Dois detalhes desta base

**Filiais com cadastro diferente.** O código `010100001` é ETANOL COMUM na
020102 e CAMINHÃO MERCEDES na 100106. Por isso cada filial é tratada separada,
nunca somada pelo código.

**Filial 100102.** Ela aparece no saldo por endereço mas não veio em nenhum
arquivo de saldo físico. Esses itens mostram só o endereçamento, e o app avisa
isso na tela do produto. Se exportar o saldo físico dela, o aviso some sozinho.
