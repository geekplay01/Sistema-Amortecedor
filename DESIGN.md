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
| `--pf-sky` | `#64C4E9` | igual | destaque, item atual do menu, gráficos |
| `--focus` | `#2F8FCB` | `#64C4E9` | anel de foco |
| `--ok` | `#0E9F6E` | `#34D399` | só «OK / atingido / recebido» |
| `--t-{blue,red,amber,emerald,violet}-*` | | | texto colorido legível sobre o fundo de cada tema |

**Significado fixo das cores** (não reutilize para outra coisa):
- vermelho = ruptura, erro, vencida, reprovada · laranja = risco, aviso, pendente, atalho «forte» · verde = OK, atingido, aprovado, recebido
- azul-marinho/`--b600` = selecionado, ação principal · azul-claro = destaque e séries de gráfico · cinza (`--mut`) = neutro, zerado, parado.
- Bolinha de sub status (`.psd-sd`): laranja = pendente, verde = finalizado/aprovado, vermelho = reprovado.

Selo/etiqueta: `PSDTW.badge(texto, tom)` com tons `blue · green · amber · red · violet · slate`. Fundo com `color-mix(... 12–15%, transparent)` do tom e texto no tom.

## 4. Tipografia

- **Barlow** (500/600/700, `static/fonts`, OFL) = `--fontd`: títulos, números grandes, rótulos em caixa-alta, cabeçalho de tabela.
- **Segoe UI** (sistema): texto corrido, tabelas, formulários.
- Escala: título da tela 28 px/700 · título de cartão 16 px/600 · número de KPI 30 px/700 (encolhe até 22 px em cartão estreito; nunca quebra no meio) · número de estágio 24 px/700 · texto 14 px ·
  tabela 14 px · rótulo (caixa-alta, `letter-spacing .08–.1em`) 11–12 px/600 · mínimo 11 px.
- Números sempre `font-variant-numeric: tabular-nums`; formatação `PSDTW.nf` (pt-BR), dinheiro `brl0`/`brl`, data `dmy` (dd/mm/aaaa).

## 5. Espaço, forma e densidade

- Grade de 4 px. Entre blocos da tela: 20 px (`gap-5`); dentro de cartão: 16–20 px.
- Densidade «compacta confortável»: linha de tabela 36 px; campo 40 px com texto 16 px; botão 40 px (32 px na versão pequena).
- Raios: KPI e cartão 16 px · menus/painéis 14 px · botão 10 px · pílula/busca/chip 999 px.
- Sombra só `--shadow` (discreta). Menu suspenso e diálogo têm sombra própria; nada de brilho, desfoque decorativo ou gradiente em componente.
- Ícones: `static/img/icones.svg` via `PSDTW.ico(nome, "sm"|""|"lg")` (18 px padrão, 16 px `sm`). Traço, sem preenchimento. Sem emoji como ícone
  (exceção histórica: ▲ ▼ das curtidas).

## 6. Componentes

Use o que existe antes de criar. Componente novo entra em `marca.css` com prefixo `psd-` e é descrito aqui.

### 6.1 Estrutura de toda tela (`templates/page.html`)
Menu lateral azul-marinho · barra do topo (título do app, sincronização, tema, usuário) · `h2.ptitle` + link «Regras da tela» (`.ptitle-regras`)
· faixa «vem de / alimenta» (`.relbar`) · conteúdo da tela em `#panel` (um arquivo por tela em `static/js/telas/`).

### 6.2 Números
- **KPI** `PSDTW.kpi(rótulo, valor, sub, tom, ícone)` → `.psd-kpi` com faixa inferior de 3 px no tom (`blue · green · red · amber · slate · sky`).
  Fileira de 4 (`grid-cols-2 lg:grid-cols-4`). Rótulo diz *o que* é; `sub` diz o recorte («itens em andamento · 337 códigos»).
- **Estágios** `.psd-est`: botões que filtram, número grande + linha de apoio; `soma` (agregado) e `fim` (fim do ciclo, faixa verde).
- **Seletor segmentado** `.psd-linha` (escolha excludente com contagem em pílula) e `.psd-seg` (dentro da barra de filtros).
- **Cartões de atalho do Dashboard** `.cards .card` (servidor, `app.CARDS`): zerado ganha `.zero` e recua.

### 6.3 Barra de filtros — padrão único
`PSDTW.pintarBarra(el, {busca, principais, mais, atalhos, etiquetas, acoes, aberto})` + `PSDTW.ligarBarra(el, handlers)`.
- Busca em pílula à esquerda · até **3 filtros principais** (`tipo: "lista"` com contagem por opção, ou `"seg"`) · «Mais filtros» para o resto ·
  ação à direita (`PSDTW.botao("Baixar Excel", {href, icone: "download"})`).
- **Atalhos** (chips com número) logo abaixo; `forte: true` (laranja) só para o atalho que pede ação (Ruptura, Pendente compras, Vencida).
- **Etiquetas** dos filtros ativos com × e «Limpar tudo».
- Estado em `PSDTW.filtros(tela, chaves)` (URL + lembrado). Contagem de cada opção = linhas da lista ao escolher (ignora o próprio filtro).

### 6.4 Listas e tabelas
`PSDTW.table(colunas, linhas, {h})`: cabeçalho fixo em Barlow caixa-alta, zebra, hover, altura máxima com rolagem interna (`max-h-[65vh]`).
Código do item é link (ficha ou detalhe). Texto longo: `truncate` com `title`. Paginação centralizada (‹ Página n de N ›). Linha de resumo acima da
tabela: `<b>N</b> item(ns) · k filtro(s) ativo(s)`.

### 6.4b Campos com sugestão e célula editável
- **Sugestões ao digitar**: use `<input list="id">` + `<datalist id="id">` e preencha o datalist; o `tw.js` troca a lista nativa (que segue a cor
  do Windows, não o tema) pela `.psd-sug` do app — ↑/↓ marcam, Enter usa a marcada, Esc fecha. Não desenhe lista de sugestão própria na tela.
- Campos de busca ficam sem o histórico do navegador (`autocomplete=off`, posto pelo `tw.js` ao focar).
- **Célula editável** (`.psd-ed` + lápis `.psd-ed-btn`, `PSDTW.editarCodigos`): Cobertura («Nosso código») e Brands («Código PERFECT»). Enter salva,
  Esc cancela, aviso com «Desfazer»; o que foi mudado no app ganha selo laranja («corrigido», «vinculado no app»). `.psd-ed.nw` não quebra linha.

### 6.5 Retorno e estados
- Carregando: `PSDTW.esqueleto(linhas, kpis)` no lugar do conteúdo (preferir a texto «Carregando…»); `carregando()` para blocos pequenos.
- Vazio: `PSDTW.empty(texto)` — frase curta com o que fazer.
- Aviso de estado: `PSDTW.notice(html, "blue"|"amber"|"red")`. Não usar para explicar regra (ver §2.3).
- Resultado de ação: `PSDTW.toast(msg, {tom})`; erro: `PSDTW.erro(e)`. Confirmação de exclusão: `PSDTW.confirmar({..., perigo: true})`.
- Botões: `.psd-btn` (`.prim` = ação principal, uma por bloco; `.perigo` = destrutiva). Componentes antigos usam `.btn` — mesmo visual.

### 6.6 Gráficos
`PSDCharts.{bars, line, hbars, donut, gauge, funnel}` (desenhados por `PSDTW.grafico`, Chart.js salvo no app). Cores **só** pelos tokens
`--chart-1..7` (azul da marca, azul-claro, laranja, vermelho, verde, violeta, cinza), que clareiam no escuro; cor da paleta clara passada pela tela é
traduzida para o tema. Grade `--chart-grid`, legenda `--chart-legend`, trilho do medidor `--chart-track`. Legenda com bolinha 8 × 8. Trocar o tema
repinta. Verde só para «atingido».

## 7. Movimento

- Entrada da tela 0,18 s (fade + 4 px); troca de tela por View Transition (o menu fica parado); toasts 0,2 s; hover 0,15 s.
- Nada de animação em número ou tabela. A única animação longa é a da tela inicial (13 s em ciclo, pausa fora da tela).
- `prefers-reduced-motion: reduce` desliga tudo (`marca.css`, fim do arquivo); a animação inicial fica parada, em pé.

## 8. Texto na interface

- Português, frases curtas, sem ponto final em rótulo e botão. Verbo no começo do botão: «Baixar Excel», «Editar meta», «Abrir lista».
- Aspas angulares «» para nomes de filtro, status e telas citados no texto.
- Status e sub status do servidor aparecem **como o servidor manda** (caixa-alta); rótulos do app em caixa normal (a caixa-alta dos rótulos vem do CSS).
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
- Cartões grandes para escolha simples (use seletor segmentado); mais de uma ação principal por bloco.
- Fonte abaixo de 11 px, emoji como ícone, gradiente/brilho decorativo.

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
