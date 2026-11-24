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

## Checkpoints

- [x] FOB: `fob_merge.read_fob` + teste `test_codigo_perfect_sem_partnumber_e_fornecedores_juntos` (AMD0637 → 8,29 XGM; E-WIN 8,35; ZS 8,50).
- [x] Brands: backend, rotas, tela, teste `test_36_vincular_item_perfect_em_brands`; conferido na cópia (vincular, selo, desfazer).
- [x] Sugestões `.psd-sug`: Comparação e Brands, claro e escuro, teclado e clique.
- [x] Escuro: Dashboard, Estoque, DES, Vendas, Comparação; claro conferido sem mudança.
- [ ] No PC: reenviar a tabela FOB (Atualização de dados / FOB) para o AMD0637 mostrar XGM e ZS.
