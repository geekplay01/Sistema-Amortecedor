# Etapa 22 — Brands com vínculo manual, FOB completo, sugestões no tema e modo escuro reformulado (24/11/2026)

Pedido: (1) Brands: como na Cobertura de concorrentes, incluir manualmente o item PERFECT relativo; (2) FOB: o AMD0637 não puxava o preço da XGM e
da ZS; (3) ao pesquisar no modo claro as opções ficavam no modo escuro; (4) reformular o modo escuro para ficar mais bonito e agradável (ui-ux-pro-max).

## Fatos levantados

- **FOB** (planilha «FOB (1).xlsx» de 24/11): o AMD0637 está em duas linhas — `Codigo 1BP36349AA → PartNumber AMD0637` (só E-WIN 8,35) e
  `Codigo AMD0637` com **PartNumber vazio** (E-WIN 8,35 · ZS 8,50 · XGM 8,29). O app (a) descartava linha sem PartNumber e (b) num PartNumber repetido
  ficava só com a linha mais barata. Na planilha: 76 linhas são o próprio AMD sem PartNumber, 116 itens perdiam algum fornecedor; itens com FOB 841 → 914.
- **Opções escuras no modo claro**: as listas da barra de filtros e os menus do app já seguiam o tema. O que fica escuro é a lista **do navegador**
  — sugestões de `<datalist>` (códigos PERFECT na Comparação, Cobertura, Amostras, Damping, Brands) e o histórico dos campos de busca —, que o
  Chrome/Edge desenham com a cor do Windows, não da página.
- **Escuro**: o `--cobalt` dos estilos antigos apontava para `--b500` (#4D69B8) e era usado como TEXTO (códigos `.pcx`, números dos cartões do
  Dashboard, links) → ≈ 3,4:1 sobre o cartão, abaixo dos 4,5:1. Fundo, cartão e menu eram todos azul saturado e pouco se separavam.
- O ui-ux-pro-max deste PC só tem o SKILL.md (sem o script de busca nem as referências): valeram as regras de prioridade da própria skill
  (contraste 4,5:1, tokens semânticos, elevação no escuro por superfícies mais claras, nada de cor fixa).

## Decisões

| # | Tema | Decisão |
|---|---|---|
| 1 | Brands | Lápis na célula «Código PERFECT» (itens que não são PERFECT) grava o conjunto completo de códigos (`brands.vincular`, tabela `brand_links`, `POST /api/brands/vinculo` e `/desfazer`). Vale sobre a base, selo «vinculado no app», «Desfazer» no aviso. Mesma validação da Cobertura (AMD do catálogo ou de DES/R-D). Os vínculos **não** entram em Anomalias › Cross corrigido (lá só correções do CrossCatalogo). |
| 2 | Editor comum | `PSDTW.editarCodigos` (tw.js) passou a servir a Cobertura e Brands (antes o editor morava na Cobertura). |
| 3 | FOB | Chave = PartNumber; vazio e Codigo AMD… → o Codigo. Repetidos juntam fornecedores (menor de cada), FOB = menor de todos, «Melhor Preço» da linha mais barata, códigos da planilha listados. Precisa **reenviar a tabela FOB** no app para valer no banco. |
| 4 | Sugestões | Todo `<input list>` mostra `.psd-sug` (lista do app, cores do tema, ↑/↓/Enter/Esc), lendo o próprio datalist: as telas não mudaram. Campos de busca com `autocomplete=off`. |
| 5 | Escuro | Superfícies neutras em degraus (`--bg #0C111C` → `--card #141A28` → `--thead #192132` → `--hover #1D2638`), linha `#252E42`, menu azul-marinho `#16204A`; azul de texto claro (`--cobalt #8FA9EE`, ≈ 7:1), botão `--b600 #3E5FC2` com branco (≈ 5,8:1). DESIGN.md §3. |
| 6 | KPI | Número encolhe até 22 px em cartão estreito em vez de quebrar no meio («R$ 25.467.64 / 8» em Vendas, que já acontecia). |

## Segunda rodada (grill, 24/11/2026) — FOB conferido em todos os itens e FOB em DES/R-D

Comparação da 1ª reimportação no banco real (backup × atual): 914 itens (eram 841), 73 novos (72 do catálogo), 117 ganharam fornecedor, nenhum sumiu nem subiu.
Problema achado: em 6 itens o FOB baixou para a XGM enquanto o «Melhor preço» continuava ZS/E-WIN (a planilha deixa a XGM fora do «Mínimo» nesses itens).
Novo dado: o servidor traz `FOB_FINAL` em quase todas as aplicações de DES/R-D (394 de 428 códigos nos status escolhidos), e a planilha quase nunca tem o preço do
fornecedor do R-D (237 de 240 em FINALIZANDO CIT).

| # | Pergunta | Decisão |
|---|---|---|
| Q1 | Qual número vale como FOB | O **menor valor** entre os fornecedores; o «Melhor preço» é o fornecedor dono dele (em verde), mesmo que a planilha indique outro |
| Q3 | 9 linhas 1BP sem PartNumber | Entram pelo item PERFECT relativo do Brands, se for um só e sem linha própria |
| Q4 | Selo «cotação antiga» | Não |
| Q6 | Aba FOB | Menor preço de cada linha em verde; «Melhor preço» = fornecedor do menor valor |
| Q7 | Origem/data quando o fornecedor muda | Em branco |
| Q8 | Empate | «ZS / XGM», os dois em verde |
| Q9 | Só «Mínimo» (13 itens) | A ficha mostra o «Mínimo» com o fornecedor da planilha |
| Q10 | Verde no preço | Exceção registrada no DESIGN.md §3 |
| Q11 | Barra padrão na aba FOB | Não agora |
| Q12 | DES | FOB só em PEDIDO CONFIRMADO e FINALIZANDO CIT |
| Q13 | R-D | FOB só em FINALIZANDO CIT e PENDENTE PARTNUMBER FORNECEDOR |
| Q14 | Fornecedor vigente | O da última compra do código; sem compra, os outros fornecedores («outros») |
| Q15 | Destaque | Verde = fornecedor do item; branco = vigente/outros |
| Q16 | Onde | Detalhe (cartões), coluna «FOB (US$)» na lista, colunas no Excel |
| Q17 | Aba FOB com DES/R-D fora do catálogo | Não agora |
| Q18 | Fonte do verde | `FOB_FINAL` do servidor; sem ele, a planilha |
| Q19 | Servidor × planilha diferentes | Servidor em verde, «planilha: x» embaixo |
| Q20 | FOB_FINAL varia entre aplicações | O menor, com «varia: a–b» |
| Q21 | R-D sem FOB_FINAL | Só o branco e «sem FOB do fornecedor» |

## Terceira rodada (grill, 24/11/2026) — lentidão, erro ao salvar no Brands e busca do FOB

Relato: «na hora que preencho o código em Brands ele dá erro e não sobe, e em FOB pesquiso um item e não dá retorno», e lentidão.
Fatos: (a) com login ligado, `app.py` passava o usuário inteiro (dicionário) como «por» para `brands.vincular` e `cobertura.corrigir` → «Error binding parameter 5:
type 'dict'» — os testes e a prévia rodavam sem login; (b) cada busca do FOB levava ≈ 1,8 s (join com `upper(trim())` dos dois lados, sem índice) e a resposta de uma
busca antiga chegava depois e tomava o lugar da certa (digitado «AMD0907», tabela de «AMD0»); (c) Dashboard ≈ 1,6 s e contadores do menu ≈ 0,6 s a cada abertura.

| # | Pergunta | Decisão |
|---|---|---|
| Q1 | Erro ao salvar | «por» grava o nome do usuário; o teste de login (`test_10`) cobre Brands e Cobertura |
| Q2 | Busca do FOB | Só a última resposta é desenhada; a caixa de busca não é redesenhada; join pela chave primária (`fob_prices.codigo` já é maiúsculo e sem espaços) |
| Q3 | Itens só de DES/R-D na aba FOB (muda a Q17) | Com busca, entram com os selos «DES»/«R-D»; sem busca, só o catálogo |
| Q4 | Onde está a lentidão | FOB e Dashboard: Dashboard e menu guardados até o banco mudar, calculados ao abrir o app e ao fim da sincronização |

## Checkpoints

- [x] FOB: `fob_merge.read_fob` + teste `test_codigo_perfect_sem_partnumber_e_fornecedores_juntos` (AMD0637 → 8,29 XGM; E-WIN 8,35; ZS 8,50).
- [x] Brands: backend, rotas, tela, teste `test_36_vincular_item_perfect_em_brands`; conferido na cópia (vincular, selo, desfazer).
- [x] Sugestões `.psd-sug`: Comparação e Brands, claro e escuro, teclado e clique.
- [x] Escuro: Dashboard, Estoque, DES, Vendas, Comparação; claro conferido sem mudança.
- [x] Banco real: tabela FOB reimportada em 24/11/2026 13:48 («FOB (1).xlsx»), backup antes em `backups\antes_fob_etapa22_20261124_104836.db`.
      841 → 914 itens FOB; catálogo com FOB 767 de 914. AMD0637: FOB 8,29 (XGM) · E-WIN 8,35 · ZS 8,50 · códigos «AMD0637, 1BP36349AA».
- [x] 2ª rodada: `read_fob` pelo menor valor (Q1/Q7/Q8/Q9) e relativo (Q3); aba FOB e ficha em verde; `rd.fob_info` na lista, no detalhe e no Excel de DES/R-D;
      testes `test_fornecedor_pelo_valor_empate_minimo_e_relativo` e `test_fob_em_des_rd`; 4/4 verdes.
- [x] Banco real reimportado de novo em 24/11/2026 14:51 (backup `backups\antes_fob_etapa22b_20261124_115153.db`). Original × agora: 914 itens (841), 73 novos,
      117 ganharam fornecedor, 7 com FOB menor (AMD0637 e os 6 da XGM, agora com «Melhor preço» XGM e origem/data em branco), nenhum subiu ou sumiu, 25 empates.
      As 9 linhas 1BP sem PartNumber continuam fora: os 9 AMD relativos já têm linha própria na planilha (regra da Q3).
- [x] App real (instância só de leitura, porta 5056, sem login nem agendador): 25 telas no claro e no escuro sem erro de JavaScript nem aviso vermelho.
      FOB em DES/R-D: DES PEDIDO CONFIRMADO 62/62 com verde do servidor · FINALIZANDO CIT 11/11 · R-D FINALIZANDO CIT 212 de 214 (193 com comparação, 39 vigente) ·
      PENDENTE PARTNUMBER 11 de 30 com verde.
- [x] 3ª rodada: «por» com o nome do usuário (Brands e Cobertura, `test_10` com login); aba FOB com sequência de buscas, casca fixa e join pela chave
      (1,8 s → 0,03–0,07 s no banco real), busca com itens só de DES/R-D (`test_fob_em_des_rd`); Dashboard e menu por `database.versao` (`test_37`): no banco real
      Dashboard 67 ms na 1ª abertura (aquecido ao iniciar), menu 10 ms. Suíte 4/4 verde. Conferido no app real só de leitura: «AMD0907» digitado rápido fica certo,
      AMD5491 aparece com DES e R-D.
