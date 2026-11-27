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
Menu lateral azul-marinho · barra do topo (título do app, sincronização, tema, configurações) · `h2.ptitle` + link «Regras da tela» (`.ptitle-regras`)
· conteúdo da tela em `#panel` (um arquivo por tela em `static/js/telas/`).
- **Menu lateral (update 8, maquete aprovada):** alfinete `.psd-pin` no topo, ao lado do logo. Fixado (padrão) = como sempre; desfixado (`html.psd-mini`,
  lembrado no navegador em `psd-menu-fixo`, aplicado no `base.html` antes de desenhar) = faixa de 64 px só com os ícones, que abre por cima da tela (sombra,
  sem empurrar o conteúdo) ao passar o mouse ou ao chegar pelo teclado (`#psd-side.abre`) e fecha ao sair; Esc fecha. Na faixa, os títulos dos grupos viram
  uma linha fina e os contadores viram um ponto laranja. O ícone anima só ele (0,32 s): fixar = o alfinete desce e fica em pé; desfixar = sobe e fica
  inclinado 40°. Só no computador (≥ 768 px); no celular continua o ☰. **Saíram** as bolinhas e a linha vertical dos grupos 1 a 4 (a numeração já dá a
  ordem) e a faixa «vem de / alimenta» (`.relbar`) de todas as telas.
- **Ícone da aba (update 5, ajustado em 26/11/2026 a pedido do usuário):** um só em todas as páginas e no login — o logo `static/img/ShockAbsorberData.ico`
  (P colorido com o amortecedor), servido em `/favicon.ico` e ligado só por ele (`base.html`, `login.html`). O `favicon.svg` fica no projeto, mas não é
  ligado: antes os dois se alternavam de uma tela para outra. Para trocar o ícone, troque esse arquivo e suba o `?v=` do link.
- **«Fechar o sistema» (update 5):** saiu da barra do topo (era fácil clicar sem querer). Fica em Configurações › **Sistema**, a primeira seção e a que
  abre: faixa com «Aberto desde», «Endereço» e «Mensagens do sistema» (`.psd-sis`) e o botão de contorno vermelho `.psd-btn-sair` (destrutivo, mas não
  a ação principal), com a confirmação `perigo` de sempre (`app.js`, `#psd-fechar`).

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
- **Sub status do servidor (DES/R-D, update 5):** um bloco `.psd-subfs` com **uma faixa por grupo** (`.psd-subf`: nome do grupo à esquerda, em Barlow
  cinza) e chips `.psd-subc` (bolinha da cor do sub status, valor, número de itens em pílula; os códigos vão na dica). O escolhido fica cheio em
  `--b600`. Zerados recolhidos em «+n sem itens» (`.psd-subz`, por grupo); escolhido zerado continua à mostra. Abaixo de 640 px o nome vai para cima.
  **Faixa «Inmetro» (update 8):** em vez do texto do servidor, sempre as três situações do item, em caixa normal (rótulos do app): «Em aprovação» (bolinha
  laranja), «Com nº Inmetro» (verde), «Fora do certificado» (cinza, `.psd-sd.mu`); filtro `sub=inmetro:@APROVACAO|@COM_NUM|@FORA`.
- **Selo Inmetro** `.psd-inm` (update 8): pílula pequena — cinza = nº do certificado («Inmetro 002533/2018»), âmbar `.am` = «Inmetro em aprovação, nº»,
  verde `.ok` = «Com nº Inmetro» (ficha). Na lista do DES/R-D é uma coluna própria («Inmetro»); fora do certificado mostra «–». Divergência numa célula:
  linha de apoio âmbar `.psd-dv` («certificado: Semi-estrutural», «catálogo: Ø 12,4 mm»).
- **Abas dentro de uma tela** (Redesenvolvimento: Itens | Validar itens; Produtos e códigos: Catálogo | Inmetro, update 8; Monitoramento de IPI: Itens | Anomalias | Próximos cadastros, update 9): seletor `.psd-seg` com
  `role="tablist"` acima do conteúdo; a aba fica na URL (`?aba=`), a troca não recarrega a página.
- **Cartões de família (aba Inmetro, update 8)** `.psd-ifam`: botão que filtra a lista (nome, «447 de 448 com certificado», barrinha nos dois / num só /
  sem — `--chart-1`, `--chart-3`, laranja — e os números do certificado de cada fornecedor); escolhido com borda `--b600`.
- **Gráfico que filtra (update 5, Metas):** clicar numa barra filtra a lista da mesma tela (mês e tipo da barra), põe as etiquetas com × no cartão da
  lista e rola até ela; clicar de novo na mesma barra tira o filtro. O cartão do gráfico diz «clique numa barra para ver …» à direita do título.

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
- **Excluir cota (update 5):** ✕ (`.psd-vx`) em toda linha da tabela de medidas, inclusive as da família; o aviso traz «Desfazer» (8 s). No desenho, clicar
  num número o seleciona (`.psd-mk.sel`: cheio em vermelho com anel de foco) e Delete o tira; o botão direito abre um menu pequeno (`.psd-vctx`, mesmo
  visual do `.psd-menu`) com «Tirar o número n deste desenho». Arrastar continua movendo o número; Esc desfaz a seleção; Ctrl+Z devolve.
- **Lista «Validar itens» (update 5):** atalhos «Todos em andamento» / «Pendentes de validação» (forte); o outro lado de um pendente leva o selo azul
  «par de AMD…». Validação concluída cujo par ainda não tem validação mostra o aviso `.psd-vaviso` com «Preparar o par (AMD… LE)».
  Em tela cheia o bloco vai para o `<body>` (fora do recorte do cartão) e Esc volta (Esc fecha antes o campo aberto).
- **Revisão**: tabela de damping, faixa de três números (A, R em vermelho quando houver, conferidas em laranja enquanto faltar), duas ações (Aprovar = principal;
  Reprovar = contorno vermelho, não preenchido) e os arquivos do F-008. Concluída, a bancada fica só leitura.
- Abaixo de 1100 px as colunas viram uma.

### 6.4d Monitoramento de IPI (update 9, `telas/ipi.js`; maquete aprovada em 27/11/2026)
- **Faixa do fluxo** `.psd-fluxo`: os 4 números são o caminho do item, da esquerda para a direita (Pendente controladoria → Pendente precificação →
  Enviados para aprovação → IPI aprovado); cada um é um botão que filtra a lista (o escolhido ganha a linha azul-clara embaixo). Os aprovadores ficam dentro
  de «Enviados» (`.psd-pes`), com a bolinha `.psd-dot`: amarela = aguardando, verde = aprovou, cinza = nada enviado.
- **Uma ação principal**: «Enviar para aprovação» (com o número de itens) no topo, à direita; «Baixar Excel» é secundário. O e-mail **não** aparece na tela:
  o botão baixa a planilha e abre o Gmail numa nova aba. Envio preparado = faixa `.psd-envio` (azul-claro) com «Confirmar envio» / «Cancelar».
- **Resposta** `.psd-resp`: a resposta da Mariana como chegou; verde com o trecho da aprovação marcado (`mark`) quando o corpo aprova; neutra quando não.
- **Selo de IPI** `.psd-ipi`: 10,4 em azul (`--chart-1`, leve e passeio), 2,6 em roxo (`--chart-5`, utilitário e pesado), contorno laranja (`.dv`) quando o
  IPI do servidor diverge da sugestão. A regra que gerou a sugestão vai embaixo, em texto pequeno.
- **Anomalias** em aba própria: cartões `.psd-anc` (3 colunas), um por tipo, com o número em laranja (cinza se zero) e a lista de códigos.
- **Tela do aprovador** (`templates/aprovacao_ipi.html` + `static/js/aprovacao_ipi.js`, perfil «Aprovador IPI»; repaginada com `/frontend-design`, maquete
  aprovada em 27/11/2026): **abre escura** e o botão de tema do topo troca como no sistema (mesma onda e mesma escolha gravada; tema claro com os mesmos
  tokens `--ap-*` clareados); no topo também «Baixar planilha» (os itens de agora no modelo IPI.xlsx, com a situação). Título sem envio: «47 itens
  pendentes de aprovação de IPI». em azul-petróleo profundo próprio (`body.psd-aprov`: fundo `#071820`, superfície `#0C2430`; 10,4% em
  azul-céu `#64C4E9`, 2,6% em lilás `#A890F2`, aguardando em laranja, aprovado em verde), sem menu, ícone do PERFECT Shock Data no topo
  (`static/img/shock-data-128.png`). A página conta uma coisa: **qual alíquota vai em cada item**. Ordem: a frase do momento (`.ap-frase`, muda com a
  situação: finalizando o CIT · aguardam sua aprovação · aprovados), o caminho em 3 passos numerados (`.ap-cam`, é uma sequência: preparada → enviada →
  aprovada; atual em laranja, feitos em verde), a resposta aprovada (`.ap-resp`), as pessoas com a bolinha, a busca e os filtros (Todos, Aguardando,
  Aprovados) e o **elemento memorável**: as duas alíquotas como as duas colunas (`.ap-pista`), com o número grande (64 px) no cabeçalho, o total à
  direita e a faixa de proporção acima. Os mesmos dados do Monitoramento de IPI; só leitura. Próximos cadastros recolhidos (`details`).### 6.5 Retorno e estados
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

**«Painel de instrumento» (update 6, maquete aprovada em 26/11/2026; skill `frontend-design`):** o elemento memorável dos gráficos é o **visor** — o número
reage ao cursor como um mostrador de ensaio. Vale para todo gráfico de barras ou linhas desenhado num contêiner (`PSDTW.grafico`; `cfg.visor = false` desliga).
- **Visor** `.psd-vis`, acima do quadro (`.psd-ch-q`): o rótulo lido em chip (`.m`, Barlow) e a leitura. **Uma série:** número grande (`.n`, Barlow 26 px) +
  o nome da série; com `visor.anoAnterior: 12`, a variação sobre o mesmo mês do ano anterior (`.d`, verde «▲ +x%» / laranja «▼ x%»); `visor.parcial` marca o
  mês em andamento (sem variação). **Pilha:** total grande + cada parte. **Várias séries:** cada uma com a bolinha da cor e o valor (`.k`) — **o visor é a
  legenda**, por isso a legenda do Chart.js e a caixinha da dica saem. Se a tela já define as dicas (`tooltip.callbacks.title/label/afterLabel`), o visor usa
  esses textos (nada se perde: Pareto, Garantia em R$, participação no ranking, aplicações da Cobertura).
- **Leitura sem cursor:** `visor.padrao` (a tela escolhe: 1º defeito do Pareto, último mês fechado de Vendas); senão o último ponto com dado em todas as
  séries e com algum valor (Garantia: dez/26 só tem o ano anterior → nov; Pedidos: «depois» zerado → o último mês com chegada); no ranking deitado, o 1º.
  Um formato de número por leitura (passou de 100 mil, tudo em «mil/mi»).
- **Ponteiro** (`psdPonteiro`, índice em `chart.$at`): barras = faixa de fundo `--chart-banda` na categoria e as **outras barras apagadas a 32%**; linhas = linha
  vertical do cursor e a bolinha (8 px, anel de 2 px da cor do cartão) só no ponto lido. O rótulo lido fica **destacado no eixo** (chip `--tx` com texto `--card`;
  no ranking deitado, à esquerda). Sair do gráfico volta a leitura ao padrão.
- **Linha única:** degradê leve embaixo (16% → 0, a cor da série). Rótulos diretos (`psdRotulos`) e legenda continuam só nos gráficos sem visor.
- Gráfico desenhado direto num `<canvas>` (sem contêiner) fica no modo anterior: legenda com 2+ séries, rótulo seletivo e dica.

**Formas que substituem a rosca e a meia-rosca:**
- **Parte de um todo** → barra segmentada alta (`PSDTW.segmentos(el, [{l, v, cor}])`, `.psd-segbar`): 28 px, 2 px entre as partes, cantos de 4 px, a fatia
  escrita dentro em branco ou quase-preto (o que contrastar mais) **só se couber**; a que não cabe vai para a legenda ao lado do nome. Legenda na ordem
  dos blocos. Embaixo, a tabela com os números (Vendas por classe). `PSDCharts.donut` já desenha assim.
- **Meta** → **anel de progresso** (update 5, maquete aprovada em 26/11/2026; substituiu o medidor reto): `PSDTW.anel({value, target, title, subtitle, year})`,
  `.psd-anel`. Anel de 9 px no trilho `--chart-trilho`, o % no centro em Barlow, preenchido em `--chart-1` e em `--ok` só quando bate a meta. Um
  **tracinho** no anel marca o ritmo de hoje (meta × parte do ano já passada; ano encerrado = 1, ano futuro = 0). Ao lado: título, «n de meta», a linha
  do ritmo («ritmo de hoje: 113», «meta atingida em 2026», «ano encerrado») e o selo da distância `.psd-anel-d` — laranja «▼ n abaixo do ritmo»,
  verde «▲ n acima do ritmo / da meta». Dashboard: um anel embaixo do outro; Metas: um por cartão. `PSDCharts.gauge` já desenha assim.
  (`PSDTW.medidor` continua disponível para barras de progresso simples.)
  **Update 7 (maquete aprovada em 26/11/2026), anel mais rico e dinâmico:** com `serie` (o realizado de cada mês) e `inicio`, embaixo do anel vem uma
  faixa `.ms` com uma barrinha por mês (altura proporcional, cor do anel; meses que ainda não chegaram = trilho, desligados). **Mouse ou teclado num
  mês rebobina o anel** até o acumulado daquele mês (o traço anda em 0,45 s; o centro diz «até jul»); o tracinho e a projeção somem enquanto se lê
  um mês; sair volta ao ano. **Projeção** (só no ano corrente): arco tracejado do realizado até o fim do ano no ritmo atual (realizado ÷ parte do ano
  que passou). Tracejado só para projeção. A interação é delegada no documento (`tw.js`).
  **Texto (update 7b, maquete aprovada): sem negrito no meio do texto** — o número pesa pelo tamanho e pela fonte, as palavras ficam em cinza. Linha do
  número: «52» (Barlow 500, 28 px) + «de 125» (13 px, letra normal, cinza) + o selo. Embaixo, **indicadores curtos** `.st` (rótulo 11,5 px cinza em cima, número em
  Barlow 500, 17 px, embaixo): «Ritmo de hoje 113» (ou «Atingida em 2026») e «Fecha o ano com 58 no ritmo atual». Lendo um mês, os mesmos indicadores
  mostram o mês: chip «jul/26» (como o do visor) + «No mês 60», «Acumulado 89», «Ideal até aqui 88»; o selo some enquanto isso. No centro, o % em
  Barlow 500, 20 px, e «da meta» em letra normal, 10 px, cinza. Rosca: no centro, o número em Barlow 500 e o nome (letra normal) e o % (Barlow 500)
  menores e cinza; na tabela, os números em Barlow 500, alinhados.
  **Peso dos gráficos (update 7c): nada acima de 500 dentro de um gráfico.** Números em Barlow 500 (visor, anel, rosca, medidor, selos, quadrinhos
  `.psd-stn` de Metas, números das barras do funil, rótulos e chip do eixo e título da dica no canvas); palavras em letra normal (400), incluindo as
  letras dos meses do anel. Número citado numa frase abaixo do gráfico: `font-medium`, nunca `<b>` puro. O título do cartão (h3) não é texto do gráfico
  e segue a regra dos títulos. Atenção: a classe global `.num` (style.css) põe peso 800; contêiner de gráfico que usa `.num` fixa o próprio peso.
- **Mapa do Brasil por estado (update 8: Vendas; Garantia desde a etapa 18):** contornos do IBGE (`brasil_uf.js`), 5 tons em quintis misturados ao fundo
  do cartão — **vendas em azul `--chart-1`** (não é alerta), garantia em vermelho (índice de garantia é alerta) —, «sem venda» em `--thead`; sigla em Barlow
  500 (branca nos dois tons mais escuros). Vendas: seletor Peças | R$ (`.psd-seg sm`) no título, visor acima do mapa (período e total, ou o estado
  escolhido e sua parte do total), legenda dos tons embaixo; à direita as regiões (barra + maior estado, `.psd-vreg`) ou, com um estado escolhido (clique
  ou Enter; clicar de novo solta), os 10 códigos mais vendidos ali (`.psd-uftop`: código, descrição, barrinha, peças, R$, % do estado) e «Baixar Excel de
  UF» com todos os códigos do estado. Segue o ano, o mês e as linhas da tela.
- **Exceção à regra da rosca — Sistema no Dashboard (update 5, pedido do usuário):** `PSDTW.rosca(partes, {rotulo, acoes})`, `.psd-rosca`. Rosca **fina**
  (12 px, 2 px de vão entre as fatias), o total no centro e, ao lado, nome, quantidade e % de cada parte — os números se leem sem passar o mouse, o que
  tira o defeito da rosca (comparar fatias pelo ângulo). Só para parte de um todo com 2 ou 3 partes de tamanhos bem diferentes; «Sem dado» em cinza.
  Nas outras telas continua a barra segmentada. **Update 7, dinâmica:** mouse ou teclado numa fatia ou na linha dela → a fatia engrossa (12 → 18 px), as
  outras e as outras linhas se apagam e o centro troca o total pela parte («142, FORCE OIL, 15,5%»); a linha é o link (`href` da parte: Produtos
  filtrado pelo sistema, com «abrir» ao passar) e a fatia também abre. Sem foco, o centro volta ao total. Os botões «Ver …» embaixo saíram.

Trocar o tema repinta **na hora, sem animação** (`update("none")` — a onda fotografa a tela logo depois): as cores dos eixos são lidas do token a cada
desenho e o cache de opções do Chart.js é limpo. Gráfico leva `aria-label` (`titulo`); barra segmentada, anel e rosca têm nome acessível com todos os valores.

## 7. Movimento

- Entrada da tela 0,18 s (fade + 4 px); troca de tela por View Transition (o menu fica parado); toasts 0,2 s; hover 0,15 s.
- Botão de tema (etapa 23): o ícone que entra gira e cresce em 0,35 s (sol gira, lua balança).
- **Onda da troca de tema (update 6):** o tema novo entra num **círculo que nasce do centro do botão clicado** (topo ou Claro/Escuro de Configurações ›
  Aparência) e cobre a tela em 0,6 s, `cubic-bezier(.2,.8,.2,1)`. View Transitions (`psdTheme.set(t, origem)` em `app.js`): o navegador fotografa a tela
  antes e depois e só o recorte `clip-path: circle()` da foto nova cresce — nada é recalculado por quadro. Durante a onda, `html.psd-onda` tira o nome de
  transição do menu e da barra do topo (senão escapariam do círculo) e desliga o esmaecer da troca de página. Sem o recurso no navegador, com «reduzir
  movimento» ou numa onda já em curso, a troca é instantânea. Os gráficos repintam dentro da troca, sem animação.
- **Entrada dos gráficos (update 6):** só na **1ª vez que o gráfico aparece na tela** (por página e título): barras sobem da base em 0,48 s (`easeOutCubic`),
  a linha se desenha da esquerda para a direita em 0,65 s (`psdRevela`), o anel e a rosca varrem do zero em 0,7 s. Filtro, troca de tema e redesenho não
  reanimam. Os números nunca se mexem.
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
- Gráfico com dois eixos Y, rosca/pizza (exceção: Sistema no Dashboard, §6.6), meia-rosca de meta, número em todo ponto, legenda de uma série só,
  barra grossa (> 24 px) ou cor de série escolhida pela posição (§6.6).
- Cartões grandes para escolha simples (use seletor segmentado); mais de uma ação principal por bloco.
- Fonte abaixo de 11 px, emoji como ícone, gradiente/brilho decorativo.
- Sinais de design genérico (etapa 23, skill `frontend-design`): caixas iguais para tudo, rótulo em CAIXA ALTA espaçada, informações emendadas com «·»,
  número repetido em dois blocos, cartão que «pula» no hover, enfeite de marca fora do que está selecionado.

## 11. Pendências de design conhecidas

- **Vendas** ainda usa barra própria (Ano/Mês, busca e classe abaixo do gráfico, «Exportar CSV»): migrar para §6.3 quando o usuário pedir
  (maquete aprovada como referência em DECISOES_ETAPA21.md; adiada em 23/11/2026).
- **Estoque**: 11 colunas; «Cobertura» só aparece rolando em telas < ~1600 px.
- `style.css` ainda carrega estilos antigos (`.btn`, `.dlg`, `.cards`, `.tbl`); `marca.css` os alinha à marca. Ao mexer num deles, prefira migrar
  para o componente `psd-` equivalente.

## 12. Como mudar o design

1. Leia a seção deste arquivo que cobre o que vai mudar.
2. Use token e componente existentes; cor nova só como token em `:root` **e** `[data-theme="dark"]`.
3. Confira a tela renderizada nos dois temas (e em 375 px se mexer em layout).
4. Se a decisão é nova ou muda uma regra daqui, atualize este arquivo no mesmo commit.
