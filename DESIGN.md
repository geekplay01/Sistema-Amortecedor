# DESIGN.md — PERFECT Shock Data

Referência de design do app. **Toda mudança visual começa aqui**: siga o que está escrito; se a mudança pedir algo que não está aqui, decida, faça e
registre neste arquivo no mesmo commit. Tokens e componentes moram em `static/css/marca.css` (vale sobre `style.css` e `tw-fallback.css`) e em
`static/js/tw.js` (`window.PSDTW`). A tela `/guia-visual` mostra os componentes vivos.

## 1. Natureza do produto

- **Ferramenta de trabalho** (modo *Operate*): um usuário, um PC Windows, monitor de mesa. Sucesso = achar o número certo rápido e confiar nele.
  Leitura rápida, consistência entre telas e precisão valem mais que expressão. A marca aparece nos detalhes, não em enfeite.
- **Desktop primeiro** (1366–1920 px). O celular precisa funcionar sem rolagem lateral, mas não é o caso principal.
- A **tela inicial** (`home.html`) é a única vitrine: logo grande, animação do amortecedor (`_amortecedor.html` + `static/js/amortecedor.js`), busca rápida.
- Português do Brasil em tudo: interface, textos, nomes de classe novos quando fizer sentido, commits.

## 2. Princípios (ordem de prioridade)

1. **O número que a tela mostra é o número que abre ao clicar.** Contagem, atalho, estágio e cartão levam à lista com o mesmo total. Nunca mostre
   o mesmo conceito com dois números diferentes na mesma tela (ver §10).
2. **Uma pergunta por bloco.** Fileira de destaque (KPIs) → filtros → lista. Não repita no bloco seguinte o que o anterior já disse.
3. **A tela não explica regra.** Textos de «como calcula / o que entra» ficam em `regras_telas.py` (Configurações › Regras das telas); a tela leva só
   o link «Regras da tela» ao lado do título. Na tela ficam apenas avisos de estado (falta sincronizar, planilha não carregada) e instruções de envio de arquivo.
4. **Mesmo padrão em todas as telas**: barra de filtros única (§6.3), «Baixar Excel» com os filtros, filtros na URL.
5. **Os dois temas são de primeira classe**: toda cor vem de token; nada de cor fixa que só funciona no claro.
6. **Zero e vazio recuam**: valor zerado fica discreto; vazio tem mensagem curta que diz o que fazer.

## 3. Cor

Paleta do logo (as quatro faixas inclinadas): azul-marinho `#202D56` · vermelho `#E72B3B` · laranja `#F6A019` · azul-claro `#64C4E9`.

| Token | Claro | Escuro | Uso |
|---|---|---|---|
| `--bg` | `#F4F6FA` | `#0C111C` | fundo da página |
| `--card` | `#FFFFFF` | `#141A28` | cartões, tabelas, menus |
| `--bar` | `#FFFFFF` | `#0F1522` | barra do topo |
| `--line` | `#DCE2EC` | `#252E42` | bordas (1 px) |
| `--tx` | `#1B2238` | `#E8EBF2` | texto |
| `--mut` | `#5A6378` | `#9AA4B8` | texto secundário, rótulos (≈ 7:1 no escuro) |
| `--thead` / `--zebra` / `--hover` | `#EEF2F8` / `#F8FAFD` / `#EEF3FB` | `#192132` / `#161D2B` / `#1D2638` | tabela e hover |
| `--navy` | `#202D56` | `#16204A` | menu lateral (azul-marinho nos dois temas) |
| `--b500` / `--b600` / `--b700` | `#2F4A8C` / `#202D56` / `#162042` | `#6C8BE0` / `#3E5FC2` / `#3352AE` | ação principal, selecionado, foco de marca |
| `--cobalt` | = `--b500` | `#8FA9EE` | azul de **texto** dos estilos antigos (códigos `.pcx`, números dos cartões, links) |

**Tema escuro (etapa 22):** superfícies neutras e pouco saturadas, em degraus que clareiam com a elevação (página → barra → cartão → cabeçalho/hover →
menu suspenso); o azul-marinho fica só no menu lateral, que assim se separa da página. Azul usado como **texto** é claro (`--cobalt`, `--t-blue-*`,
≥ 7:1 sobre o cartão); azul usado como **fundo** com texto branco é o da marca (`--b600`, ≈ 5,8:1). Nunca use `--b500` como cor de texto no escuro.
| `--pf-sky` | `#64C4E9` | igual | destaque, item atual do menu (gráficos têm paleta própria, §6.6) |
| `--focus` | `#2F8FCB` | `#64C4E9` | anel de foco |
| `--ok` | `#0E9F6E` | `#34D399` | só «OK / atingido / recebido» |
| `--t-{blue,red,amber,emerald,violet}-*` | | | texto colorido legível sobre o fundo de cada tema |

**Significado fixo das cores** (não reutilize para outra coisa):
- vermelho = ruptura, erro, vencida, reprovada · laranja = risco, aviso, pendente, atalho «forte» · verde = OK, atingido, aprovado, recebido
  · **exceção (etapa 22): preço FOB destacado** (`.psd-fob-min`, `.psd-fobrd-c.on`) — o menor na ficha e na aba FOB; o do fornecedor do item em DES/R-D
  (o de comparação fica neutro, «em branco»)
- azul-marinho/`--b600` = selecionado, ação principal · azul-claro = destaque · cinza (`--mut`) = neutro, zerado, parado. Séries de gráfico: paleta
  própria `--chart-*` (§6.6).
- Bolinha de sub status (`.psd-sd`): laranja = pendente, verde = finalizado/aprovado, vermelho = reprovado.
- **Faixa inclinada do logo (etapa 23 · Q7)** — `--inc` (paralelogramo) em azul-claro `--pf-sky`: o **único** destaque de marca dentro das telas. Marca só
  o que está selecionado: estágio (`.psd-est`), item atual do menu (`.nav-item.is-cur`), opção do seletor de linha (`.psd-linha`) e do segmentado (`.psd-seg`)
  e o passo atual da bancada de validação (`.psd-passos`, etapa 24). Não usar como enfeite em outro lugar.
- **Desenho técnico (etapa 24)**: `--papel` (branco nos dois temas) — desenho é preto sobre branco e não se inverte no escuro. `--cota` (= vermelho da marca)
  só para a **marca de cota** do F-008: quadrado de borda vermelha com o número da linha (`.psd-mk` no desenho, `.psd-num` na tabela); cheio quando em foco.

Selo/etiqueta: `PSDTW.badge(texto, tom)` com tons `blue · green · amber · red · violet · slate`. Fundo com `color-mix(... 12–15%, transparent)` do tom e texto no tom.

## 4. Tipografia

- **Barlow** (500/600/700, `static/fonts`, OFL) = `--fontd`: títulos, números grandes, rótulos, cabeçalho de tabela.
- **Segoe UI** (sistema): texto corrido, tabelas, formulários.
- Escala: título da tela 28 px/700 · título de cartão 16 px/600 · número de KPI 30 px/700 (encolhe até 22 px em cartão estreito; nunca quebra no meio) · número de estágio 24 px/700 · texto 14 px ·
  tabela 14 px · rótulo 13 px/600 Barlow **em caixa normal** (`.psd-rot`; etapa 23 · Q2 — nada de caixa-alta espaçada) · mínimo 11 px.
- Números sempre `font-variant-numeric: tabular-nums`; formatação `PSDTW.nf` (pt-BR), dinheiro `brl0`/`brl`, data `dmy` (dd/mm/aaaa).

## 5. Espaço, forma e densidade

- Grade de 4 px. Entre blocos da tela: 20 px (`gap-5`); dentro de cartão: 16–20 px.
- Densidade «compacta confortável»: linha de tabela 36 px; campo 40 px com texto 16 px; botão 40 px (32 px na versão pequena).
- Raios: cartão 16 px · faixa de números, estágios e lista de atalhos 12 px · menus/painéis 14 px · botão 10 px · pílula/busca/chip 999 px.
- Sombra só `--shadow` (discreta). Menu suspenso e diálogo têm sombra própria; nada de brilho, desfoque decorativo ou gradiente em componente
  (etapa 23 · Q6: a barra de prazo é laranja lisa e o avatar do escuro é `--b600`; só a tela inicial tem fundo em degradê, por ser a vitrine).
- Hover muda o fundo ou a borda; nada «pula» (`translateY`) ao passar o mouse.
- Ícones: `static/img/icones.svg` via `PSDTW.ico(nome, "sm"|""|"lg")` (18 px padrão, 16 px `sm`). Traço, sem preenchimento. Sem emoji como ícone
  (exceção histórica: ▲ ▼ das curtidas).

## 6. Componentes

Use o que existe antes de criar. Componente novo entra em `marca.css` com prefixo `psd-` e é descrito aqui.

### 6.1 Estrutura de toda tela (`templates/page.html`)
Menu lateral azul-marinho · barra do topo (título do app, sincronização, tema, usuário, **«Fechar o sistema»** — ícone `power`, último à direita,
confirmação com `perigo`; etapa 24, o app roda sem a janela do cmd) · `h2.ptitle` + link «Regras da tela» (`.ptitle-regras`)
· faixa «vem de / alimenta» (`.relbar`) · conteúdo da tela em `#panel` (um arquivo por tela em `static/js/telas/`).

### 6.2 Números
- **KPI** `PSDTW.kpi(rótulo, valor, sub, tom, ícone)` → `.psd-kpi`. **Etapa 23 · Q4:** KPIs vizinhos formam **uma faixa só** (o contêiner que só tem
  KPIs vira uma superfície com divisórias finas — `marca.css`, sem classe extra na tela); sem linha colorida embaixo. O tom só muda a cor do número
  quando é alerta: `red` (ruptura/erro) e `amber` (risco); `blue · green · slate · sky` ficam neutros. Fileira de 4 (`grid-cols-2 lg:grid-cols-4`).
  Rótulo diz *o que* é; `sub` diz o recorte — cada « · » do `sub` vira uma linha (uma informação por linha).
- **Estágios** `.psd-est`: uma faixa de botões que filtram (número grande + linha de apoio); o escolhido leva a faixa inclinada (§3); `fim` (fim do
  ciclo) com o número em verde. No DES/R-D os estágios **são** a fileira de números (não há KPI repetindo o estágio). A linha de apoio mostra os
  códigos só quando diferem dos itens.
- **Seletor segmentado** `.psd-linha` (escolha excludente com contagem em pílula) e `.psd-seg` (dentro da barra de filtros).
- **Atalhos do Dashboard** `.cards.psd-atl` (servidor, `app.CARDS`): **lista em duas colunas** (número, nome, descrição curta), primeiro o que pede
  ação, depois os cadastros; zerado ganha `.zero`, recua e vai para o fim (`app.js`).

### 6.3 Barra de filtros — padrão único
`PSDTW.pintarBarra(el, {busca, principais, mais, atalhos, etiquetas, acoes, aberto})` + `PSDTW.ligarBarra(el, handlers)`.
- Busca em pílula à esquerda · até **3 filtros principais** (`tipo: "lista"` com contagem por opção, ou `"seg"`) · «Mais filtros» para o resto ·
  ação à direita (`PSDTW.botao("Baixar Excel", {href, icone: "download"})`).
- **Atalhos** (chips com número) logo abaixo; `forte: true` (laranja) só para o atalho que pede ação (Ruptura, Pendente compras, Vencida).
- **Etiquetas** dos filtros ativos com × e «Limpar tudo».
- Estado em `PSDTW.filtros(tela, chaves)` (URL + lembrado). Contagem de cada opção = linhas da lista ao escolher (ignora o próprio filtro).

### 6.4 Listas e tabelas
`PSDTW.table(colunas, linhas, {h})`: cabeçalho fixo em Barlow 13 px, caixa normal, zebra, hover, altura máxima com rolagem interna (`max-h-[65vh]`).
Código do item é link (ficha ou detalhe). Texto longo: `truncate` com `title`. Paginação centralizada (‹ Página n de N ›). Linha de resumo acima da
tabela: `<b>N</b> item(ns), k filtro(s) ativo(s)`.
- **Item identificado (etapa 24 · Q7, Anomalias):** onde a linha traz um código PERFECT, vêm junto a descrição e a aplicação (coluna «Aplicação» em
  texto pequeno, `min-w-[12rem] max-w-[24rem]`, quebra linha). Linha com vários códigos (Concorrentes repetidos, Cross corrigido) lista cada código com a
  sua descrição e aplicação embaixo; a coluna de referências quebra linha (`max-w-[16rem]`) para a tabela caber.

### 6.4b Campos com sugestão e célula editável
- **Sugestões ao digitar**: use `<input list="id">` + `<datalist id="id">` e preencha o datalist; o `tw.js` troca a lista nativa (que segue a cor
  do Windows, não o tema) pela `.psd-sug` do app — ↑/↓ marcam, Enter usa a marcada, Esc fecha. Não desenhe lista de sugestão própria na tela.
- Campos de busca ficam sem o histórico do navegador (`autocomplete=off`, posto pelo `tw.js` ao focar).
- **Busca rápida da tela inicial** (`#quick-results`, `app.js`): mesmo visual da `.psd-sug` (fundo do cartão, cores do tema, ↑/↓/Enter/Esc), selos
  como no Brands (Catálogo azul, DESENVOLVIMENTO violeta, REDESENVOLVIMENTO verde); só a resposta da última busca é desenhada (etapa 23).
- **Célula editável** (`.psd-ed` + lápis `.psd-ed-btn`, `PSDTW.editarCodigos`): Cobertura («Nosso código») e Brands («Código PERFECT»). Enter salva,
  Esc cancela, aviso com «Desfazer»; o que foi mudado no app ganha selo laranja («corrigido», «vinculado no app»). `.psd-ed.nw` não quebra linha.

### 6.4c Bancada de validação (etapa 24, `telas/validacao.js`)
Um cartão (`.psd-banc`): cabeçalho com o código, a descrição e os dados do par (fornecedor, código, família, tipo) em `dl.psd-par`; faixa de **passos** numerados
(`.psd-passos`, sequência real: «1 · Desenhos» … «4 · Revisão e aprovação»; o atual leva a faixa inclinada, o concluído tem a linha de apoio em verde); corpo do passo.
- **Desenhos lado a lado** em papel (`.psd-papel`); envio por área tracejada (`.psd-drop`, clique ou arrastar). Máscara: arrastar seleciona (`.psd-sel`),
  Delete apaga, Ctrl+Z desfaz.
- **Medidas**: tabela editável (`.psd-vtab`, campos discretos que ganham borda no foco) ao lado dos dois desenhos empilhados (fixos ao rolar). O número da
  linha liga tabela e desenhos: passar o mouse acende a linha e as duas cotas; as marcas se arrastam. Ap em selo A (verde) / R (vermelho) (`.psd-ap`).
- **Digitação no desenho** (padrão, sem API): a linha em digitação fica marcada (faixa `.psd-vmarca` acima da tabela, linha `.armada`, desenho com borda `--cota`);
  o clique na cota abre o campo no ponto (`.psd-vpop`, cartão pequeno com sombra de menu; abre acima quando não cabe embaixo). Enter grava e passa para a próxima.
- **Só marcar** (padrão) | **Marcar e digitar** (`.psd-seg` na faixa de marcação): no primeiro, cada clique põe o número e passa para a próxima linha;
  Ctrl+Z tira o último; duplo clique num número abre o campo. O nome da cota é um campo na própria tabela (maiúsculas, vai para o F-008).
- **Sobrepor** (`.psd-vsob`, tela inteira): PERFECT em vermelho `--sob-p`, fornecedor em azul `--sob-f`, coincidência escura `--sob-e` (cores do desenho,
  iguais nos dois temas), legenda no topo; arrastar move e a roda muda o tamanho do desenho do fornecedor.
- **Item com mola** no passo 2: chave liga/desliga `.psd-switch` (rótulo em negrito + linha de apoio).
- **Avisos da bancada** (`.psd-vaviso`, faixa azul discreta com ícone, texto e uma ação à direita): «copiado do outro lado» (com «Espelhar posições») e «dá para reaproveitar posições».
  Valor já preenchido pelo app (PERFECT do catálogo ou de validação anterior) fica em itálico azul (`input.pre`) até ser mexido. O par aparece no cabeçalho
  («Lado: LE, par AMD0138 (LD)», link). No passo 4, a decisão do outro lado fica em destaque (Reprovar cheio em vermelho quando o par foi reprovado).
- **Tabela como planilha**: Enter/↓ desce na coluna, Shift+Enter/↑ sobe, colar uma coluna do Excel preenche para baixo.
- **Damping**: Enter vai para o valor ao lado (no fim, a linha de baixo), Shift+Enter volta, colar vários números preenche a linha.
- **Zoom**: roda do mouse sobre o ponto, botões «+ − Ajustar» e «Tela cheia» no título do desenho (`.psd-zctl`); os números mantêm o tamanho (`--z`).
  **Rodinha apertada** (botão do meio) arrasta o desenho, em qualquer modo; o clique esquerdo continua marcando (etapa 24 · Q3).
- **Recorte do damping** (passo 4, `.psd-vrecs`, grade de um quadro por desenho com «só a tabela» / «desenho inteiro» ao lado do nome): arrastar seleciona
  sobre a tabela de damping e «Manter só a seleção» (ícone `crop`) guarda o retângulo (`.psd-recorte`: borda vermelha da marca, o resto escurecido); só esse
  pedaço vai para a aba DampingForce do F-008. «Desenho inteiro» desfaz.
- **Revisões** (Q5): concluída, a bancada oferece «Nova revisão (Rev.0n)» no lugar de duplicar; a faixa `.psd-vrevs` lista as revisões da validação (a atual
  marcada) e a lista da tela Validação mostra uma linha por validação (a revisão mais nova) com a contagem de revisões. Excluir (Q4): lixeira `.psd-vx` ao
  lado da revisão, em qualquer situação, com confirmação `perigo`.
  Em tela cheia o bloco vai para o `<body>` (fora do recorte do cartão) e Esc volta (Esc fecha antes o campo aberto).
- **Revisão**: tabela de damping, faixa de três números (A, R em vermelho quando houver, conferidas em laranja enquanto faltar), duas ações (Aprovar = principal;
  Reprovar = contorno vermelho, não preenchido) e os arquivos do F-008. Concluída, a bancada fica só leitura.
- Abaixo de 1100 px as colunas viram uma.

### 6.5 Retorno e estados
- Carregando: `PSDTW.esqueleto(linhas, kpis)` no lugar do conteúdo (preferir a texto «Carregando…»); `carregando()` para blocos pequenos.
- Vazio: `PSDTW.empty(texto)` — frase curta com o que fazer.
- Aviso de estado: `PSDTW.notice(html, "blue"|"amber"|"red")`. Não usar para explicar regra (ver §2.3).
- Resultado de ação: `PSDTW.toast(msg, {tom})`; erro: `PSDTW.erro(e)`. Confirmação de exclusão: `PSDTW.confirmar({..., perigo: true})`.
- Botões: `.psd-btn` (`.prim` = ação principal, uma por bloco; `.perigo` = destrutiva). Componentes antigos usam `.btn` — mesmo visual.
- **Envio de planilha (etapa 24 · Q8):** todo módulo que recebe planilha usa a área tracejada de Desenhos em versão compacta —
  `PSDTW.zonaPlanilha({id, titulo, dica, multiplo, aceita})` (`.psd-drop.psd-drop-p`, ícone `file-spreadsheet` em cobalto) + `PSDTW.ligarPlanilha(alvo,
  {aceita, multiplo, receber})`: clique, Enter/Espaço, arrastar e soltar (`.sobre` enquanto passa por cima) e **Ctrl+V** de arquivo copiado no Explorer
  (vale enquanto a área está na tela). Extensão fora de `aceita` → aviso «Arquivo não aceito». Em Atualização de dados, FOB, Vendas (BI), Damping e
  Importação de Excel. Não desenhe `<input type=file>` solto.

### 6.6 Gráficos (etapa 24 · Q9, skill `dataviz`; maquete aprovada em 26/11/2026)
`PSDCharts.{bars, line, hbars, donut, gauge, funnel}` e `PSDTW.grafico(el, cfg)` (Chart.js salvo no app). Os padrões abaixo vêm de `PSDTW.grafico`;
a tela só passa dados, rótulos e, quando precisa, a cor por token. **A forma vem antes da cor.**

**Paleta** (validada pelo script da skill: faixa de claridade, croma mínimo, separação para daltonismo, contraste ≥ 3:1, nos dois temas — o escuro
tem degraus próprios sobre o cartão `#141A28`, não uma inversão):

| Ordem | Token | Claro | Escuro |
|---|---|---|---|
| 1 azul | `--chart-1` | `#3A57A3` | `#6F8EE6` |
| 2 laranja | `--chart-2` | `#D27800` | `#CC7E12` |
| 3 azul-claro | `--chart-3` | `#2E9FD0` | `#2493C6` |
| 4 vermelho | `--chart-4` | `#D62E3D` | `#E8505C` |
| 5 violeta | `--chart-5` | `#7B5CE0` | `#9479EE` |
| 6 verde | `--chart-6` | `#0E9F6E` | `#1FAE7E` |
| cinza de fundo (não é série) | `--chart-7` | `#A3AEC2` | `#4A5468` |
| degrau claro do azul (escala) | `--chart-1s` | `#93A3CC` | `#465A90` |
| trilho do medidor | `--chart-trilho` | `#DCE4F5` | `#26324F` |

- **Ordem fixa, nunca ciclada.** A 1ª série é azul, a 2ª laranja… Vermelho e verde só a partir da 4ª. Passou de 6 séries: junte em «Outros» ou divida o gráfico.
- **A cor segue a coisa, não a posição:** DES = azul, R-D = laranja (Dashboard e Metas); fornecedor = a cor do selo dele na tabela (ZS azul, E-WIN verde,
  XGM violeta, VERIFICAR cinza — trio validado). Filtrar não repinta.
- **Cinza = o resto:** ano anterior ao lado do atual (Garantia), «Sem dado», as barras não escolhidas quando uma está em destaque (laranja).
- **Escala ordenada** (curva A > B > C, Cobertura): um azul em degraus (`--chart-1`, `--chart-1s`, `--chart-7`) com legenda em HTML (`PSDTW.legenda`), nunca
  cores de identidade.
- **Status não é série:** verde = atingido/OK, vermelho = crítico. Gráfico de estado (OK, risco, ruptura…) usa as cores de status, com o nome na legenda.
- Cor pedida pela tela: token (`"--chart-2"` ou `"var(--chart-2)"`). Hex antigo ainda cai no slot equivalente (`ANTIGAS` em `tw.js`), mas não use em código novo.

**Marcas e eixos:**
- Barra ≤ **24 px**, ponta arredondada de **4 px** e base reta; duas séries lado a lado (ano atual × anterior) com 12 px cada.
- Pilha: **vão de 2 px** na cor do cartão entre os blocos (borda de cima), só o bloco do topo arredondado. Nunca contorno em volta da marca.
- Linha de **2 px**, interpolação monótona (não passa do valor nem fura o zero), sem área embaixo com 2 séries ou mais (uma série pode lavar a 10 %);
  só o **último ponto** tem bolinha (8 px, anel de 2 px na cor do cartão).
- Grade fina e sólida **só no eixo dos valores**, sem linha de eixo; até 5 marcas com número curto (`PSDTW.curto`: 950 · 12,5 mil · 2,3 mi).
  Barras deitadas (ranking) mostram todos os nomes.
- **Um eixo só.** Dois eixos Y inventam uma relação entre as escalas: o Pareto mostra o acumulado como a divisória «80% em N defeitos» (plugin
  `psdDivisa`) e o % de cada um na dica.

**Texto:**
- Legenda **só com 2 séries ou mais**, alinhada à esquerda, bolinha 8 × 8; uma série não tem legenda (o título do cartão diz o que é).
- **Rótulo seletivo** (`psdRotulos`): linha = o valor no fim de cada série; barras de uma série = o maior e o último mês. Rótulos que se tocariam: fica
  um, o resto vai para a dica. O texto nunca sai do quadro e nunca usa a cor da série (`--tx`).
- Dica ao passar o mouse em tudo; linhas e barras agrupadas mostram todas as séries do mês, com a linha vertical do cursor (`psdCursor`) nas linhas.

**Formas que substituem a rosca e a meia-rosca:**
- **Parte de um todo** → barra segmentada alta (`PSDTW.segmentos(el, [{l, v, cor}])`, `.psd-segbar`): 28 px, 2 px entre as partes, cantos de 4 px, a fatia
  escrita dentro em branco ou quase-preto (o que contrastar mais) **só se couber**; a que não cabe vai para a legenda ao lado do nome. Legenda na ordem
  dos blocos. Embaixo, a tabela com os números (Vendas por classe). `PSDCharts.donut` já desenha assim.
- **Meta** → medidor reto (`PSDTW.medidor({value, target, title, subtitle})`, `.psd-med`): número grande, «de N (x%)» e o trilho; preenche em azul e em
  verde (`--ok`) só quando bate a meta. `PSDCharts.gauge` já desenha assim.

Trocar o tema repinta: as cores dos eixos são lidas do token a cada desenho e o cache de opções do Chart.js é limpo. Gráfico leva `aria-label` (`titulo`);
barra segmentada e medidor têm nome acessível com todos os valores.

## 7. Movimento

- Entrada da tela 0,18 s (fade + 4 px); troca de tela por View Transition (o menu fica parado); toasts 0,2 s; hover 0,15 s.
- Botão de tema (etapa 23): o ícone que entra gira e cresce em 0,35 s (sol gira, lua balança); as cores da página trocam na hora.
- Ação demorada (ler os desenhos com o Claude, gerar o F-008): o botão troca o texto e mostra o ícone girando (`.psd-gira`) até terminar.
- **Chaves de escolha (etapa 24)**: em toda `.psd-seg` e `.psd-linha` o destaque **desliza** até a opção escolhida em 0,2 s (`.psd-ind`, posto pelo
  `tw.js`; a posição anterior fica guardada pelo `id`/`aria-label` da chave, então desliza também quando a tela redesenha a chave). Vale para todos os
  módulos, sem código na tela. Troca de aba dentro da mesma tela (Itens | Validar itens) não recarrega a página. Chave liga/desliga (`.psd-switch`):
  a bolinha corre em 0,2 s.
- Nada de animação em número ou tabela. A única animação longa é a da tela inicial (13 s em ciclo, pausa fora da tela).
- `prefers-reduced-motion: reduce` desliga tudo (`marca.css`, fim do arquivo); a animação inicial fica parada, em pé.

## 8. Texto na interface

- Português, frases curtas, sem ponto final em rótulo e botão. Verbo no começo do botão: «Baixar Excel», «Editar meta», «Abrir lista».
- **Sem «·» emendando informações** (etapa 23 · Q3): uma informação por linha ou vírgula numa lista («1.870.034 peças, até 01/11/2026»); título com
  recorte usa «em», «de» ou dois-pontos («Vendas em 12 meses», «Funil de DESENVOLVIMENTO»). O «·» só fica na numeração de etapas («1 · Em produção»)
  e no título da aba do navegador.
- Aspas angulares «» para nomes de filtro, status e telas citados no texto.
- Status e sub status do servidor aparecem **como o servidor manda** (caixa-alta) na lista, nas etiquetas e nos filtros; rótulos do app em caixa
  normal. Exceção: o nome do estágio no botão da faixa de estágios vai em caixa normal com siglas («Finalizando CIT»).
- Unidades explícitas: «itens» = linhas do servidor, «códigos» = códigos distintos, «peças», «meses», «d» (dias).
- Erro diz o que aconteceu e o que fazer; nunca mostrar exceção crua sem contexto.

## 9. Acessibilidade e tamanho de tela

- Foco visível (`:focus-visible`, 2 px `--focus`). Alvo de clique ≥ 32 px (40 px em controles principais).
- Contraste: texto ≥ 4,5:1 nos dois temas; não usar opacidade para apagar texto (exceção: `.zero`, que é decorativo e mantém o número legível).
- Ícone sem texto leva `aria-label`; ícone decorativo `aria-hidden`. Gráfico com `aria-label` (`titulo`).
- Sem rolagem lateral na página até 375 px. Tabela larga rola dentro do próprio contêiner.
- Ao usar classe Tailwind nova, rodar `tools/tw_fallback.py` (o app funciona sem internet).

## 10. Não fazer

- Mostrar o mesmo número com valores diferentes na mesma tela (aconteceu no Dashboard: 337 × 864).
- Explicar regra de cálculo na tela (vai para `regras_telas.py`).
- Barra de filtros própria de uma tela, ou «Exportar CSV» em vez de «Baixar Excel».
- Cor fixa (hex) em componente novo; verde para qualquer coisa que não seja «OK».
- Gráfico com dois eixos Y, rosca/pizza, meia-rosca de meta, número em todo ponto, legenda de uma série só, barra grossa (> 24 px) ou cor de série
  escolhida pela posição (§6.6).
- Cartões grandes para escolha simples (use seletor segmentado); mais de uma ação principal por bloco.
- Fonte abaixo de 11 px, emoji como ícone, gradiente/brilho decorativo.
- Sinais de design genérico (etapa 23, skill `frontend-design`): caixas iguais para tudo, rótulo em CAIXA ALTA espaçada, informações emendadas com «·»,
  número repetido em dois blocos, cartão que «pula» no hover, enfeite de marca fora do que está selecionado.

## 11. Pendências de design conhecidas

- **Vendas** ainda usa barra própria (Ano/Mês, busca e classe abaixo do gráfico, «Exportar CSV»): migrar para §6.3 quando o usuário pedir
  (maquete aprovada como referência em DECISOES_ETAPA21.md; adiada em 23/11/2026).
- **Estoque**: 11 colunas; «Cobertura» só aparece rolando em telas < ~1600 px.
- **Celular**: a faixa «vem de / alimenta» ocupa meia tela antes do conteúdo.
- `style.css` ainda carrega estilos antigos (`.btn`, `.dlg`, `.cards`, `.tbl`); `marca.css` os alinha à marca. Ao mexer num deles, prefira migrar
  para o componente `psd-` equivalente.

## 12. Como mudar o design

1. Leia a seção deste arquivo que cobre o que vai mudar.
2. Use token e componente existentes; cor nova só como token em `:root` **e** `[data-theme="dark"]`.
3. Confira a tela renderizada nos dois temas (e em 375 px se mexer em layout).
4. Se a decisão é nova ou muda uma regra daqui, atualize este arquivo no mesmo commit.
